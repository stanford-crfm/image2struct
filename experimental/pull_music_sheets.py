import argparse
import os
import random
import time
from typing import Dict, Optional, Tuple

from imslp import client
from imslp.interfaces.scraping import fetch_images_metadata
from mwclient.page import Page
from mwclient.image import Image
from pdf2image.exceptions import PDFPageCountError
from PIL import Image
from tqdm import tqdm
from torchvision import transforms, models
import torch

from image2structure.util.credentials_utils import get_credentials
from image2structure.util.hierarchical_logger import htrack_block, hlog
from image2structure.util.image_utils import pdf_to_image, is_mostly_white


# Increase the maximum number of pixels allowed
Image.MAX_IMAGE_PIXELS = 700000000


"""
Pull music sheets from IMSL (International Music Score Library Project) to generate the MusicSheets2LilyPond dataset.
The sheet music classifier was trained on sheet music up to 2012 and achieved an accuracy of 99.2% on the test set.

Usage: 
python experimental/pull_music_sheets.py <start_year> <end_year> -n <num_examples> -o <output_dir> -c <credentials_path>

Example usage: 
python experimental/pull_music_sheets.py 2000 2010 -n 10 -o data/sheetmusic2lilypond -c credentials/imslp.conf
"""


class SheetMusicClassifier:
    """
    A simple classifier to determine if an image is a sheet music or not.
    """

    def __init__(self, path_to_model: str = "experimental/sheet_music_classifier.pt"):
        with htrack_block(f"Loading the sheet music classifier from {path_to_model}"):
            self._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

            # Assume you have a model defined (or modified) as `model`
            model = models.resnet18(pretrained=False)  # Example: ResNet-18
            num_ftrs = model.fc.in_features
            model.fc = torch.nn.Linear(
                num_ftrs, 2
            )  # Adjusting for binary classification

            # Load the trained model weights
            model.load_state_dict(torch.load(path_to_model, map_location=self._device))

            # Set the model to evaluation mode
            model.eval()

            self._model = model.to(self._device)
            self._transform = transforms.Compose(
                [
                    transforms.Resize(1024),
                    transforms.CenterCrop(512),
                    transforms.ToTensor(),
                    transforms.Normalize(
                        mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]
                    ),
                ]
            )

    def is_sheet_music(self, image_path: str) -> bool:
        with torch.no_grad():
            # Open the image file
            image = Image.open(image_path)

            # Convert the image to RGB if it's not already (important for RGBA or grayscale images)
            if image.mode != "RGB":
                image = image.convert("RGB")

            # Apply transformations and move to the appropriate device
            image_tensor = self._transform(image).unsqueeze(0).to(self._device)

            # Perform inference
            outputs = self._model(image_tensor)
            _, predicted = torch.max(outputs, 1)

            # Return True if predicted class is 1 (sheet music), else False
            return predicted.item() == 1


def fetch_music_sheets(
    num_examples: int,
    year_range: Tuple[int, int],
    output_dir: str,
    credentials_path: str,
) -> None:
    """
    Pulls music sheets from IMSLP (International Music Score Library Project) and outputs them to `output_dir`.
    Launched in 2006, IMSLP is a project aimed at creating a virtual library containing all public domain music
    scores, as well as scores from composers who are willing to share their music with the world free of charge.
    The IMSLP also includes recordings and educational materials related to music.

    In order to reduce duplicate sheets, we sample one sheet per work.

    :param num_examples: Number of examples to pull
    :param year_range: Tuple[int, int] representing the range of years to pull music sheets from (inclusive)
    :param output_dir: Output directory
    :param credentials_path: Path to the credentials file
    :return: None
    """
    # Validate arguments
    if num_examples < 1:
        raise ValueError("num_examples must be greater than 0.")
    if year_range[0] > year_range[1]:
        raise ValueError("year_range[0] must be less than or equal to year_range[1].")

    # We must login in order to bypass the disclaimer page
    credentials: Dict[str, str] = get_credentials(credentials_path)
    username: str = credentials["username"]
    password: str = credentials["password"]

    c = client.ImslpClient(username=username, password=password)
    hlog("Login to IMSLP was successful. Created ImslpClient.\n")

    # Initialize the sheet music classifier
    model = SheetMusicClassifier()

    # Create the output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Increase the maximum number of pixels allowed
    Image.MAX_IMAGE_PIXELS = 230000000
    imslp_url: str = "https://imslp.org/wiki/"

    with htrack_block(
        f"Attempting to generate {num_examples} examples from IMSLP between {year_range[0]} and {year_range[1]}..."
    ):
        # `search_works` without any arguments returns all works
        with htrack_block(
            "Searching for all works. Please be patient as this may take a few minutes."
        ):
            results = c.search_works()
            hlog(f"Found {len(results)} works.")

        generated_count: int = 0
        with htrack_block("Processing the results..."):
            for result in tqdm(results):
                url: str = result["permlink"]
                if not url.startswith(imslp_url):
                    continue

                name: str = url.replace(imslp_url, "")
                page = Page(c._site, name)
                image_metadatas = fetch_images_metadata(page)

                for metadata in image_metadatas:
                    if "obj" not in metadata or metadata["obj"] is None:
                        continue

                    image: Image = metadata["obj"]
                    timestamp: str = image.imageinfo["timestamp"]
                    year: Optional[int] = int(timestamp[:4])

                    if year is None or year < year_range[0] or year > year_range[1]:
                        continue

                    file_name: str = image.imageinfo["url"].split("/")[-1]
                    if not file_name.endswith(".pdf"):
                        continue

                    total_num_pages: Optional[int] = metadata["page_count"]
                    # Some PDF have many pages, filter those out
                    if total_num_pages is None or total_num_pages > 30:
                        hlog(
                            f"Skipping {file_name} with {total_num_pages} pages. Too many pages."
                        )
                        continue

                    file_path: str = os.path.join(output_dir, file_name)
                    hlog(f"Downloading {file_name} created at {timestamp}...")

                    # Download
                    with open(file_path, "wb") as f:
                        image.download(f)

                    image_path: str = os.path.join(
                        output_dir, file_name.replace(".pdf", ".png")
                    )

                    # Select a random page but preferably not the first two pages (which could be a title
                    # and not the sheet music) and the last two pages (which could be a blank page)
                    page_number: int
                    if total_num_pages > 4:
                        page_number = random.randint(3, total_num_pages - 2)
                    elif total_num_pages == 4:
                        page_number = 3
                    elif total_num_pages == 2 or total_num_pages == 3:
                        page_number = 2
                    else:
                        page_number = 1

                    generated: bool = generate_sheet_image(
                        file_path, image_path, page_number
                    )

                    # Remove the PDF file
                    os.remove(file_path)
                    if generated:
                        if not model.is_sheet_music(image_path):
                            hlog(
                                f"Removing {image_path} as it was identified as not a sheet music."
                            )
                            os.remove(image_path)
                            continue

                        generated_count += 1
                        hlog(f"Generated {generated_count} of {num_examples} examples.")
                        break

                    # Add a delay to avoid subscription prompt
                    hlog("Sleeping for 5 seconds...")
                    time.sleep(5)

                if generated_count >= num_examples:
                    hlog(f"Generated {num_examples} examples. Exiting...")
                    return


def generate_sheet_image(pdf_path: str, output_path: str, page_number: int) -> bool:
    """
    Generates an image from the sheet music PDFs in `output_dir`

    :param pdf_path: Path to the PDF file
    :param output_path: Path to the output image
    :param page_number: Page number to extract
    :return: True if the image was generated successfully, False otherwise
    """
    # Read PDF file in binary mode
    try:
        image: Optional[Image] = pdf_to_image(pdf_path, page_number=page_number)

        if image is None:
            hlog(f"Could not generate image from {pdf_path}")
            return False

        # Check that the image is mostly white
        if not is_mostly_white(image):
            hlog(f"Skipping: {pdf_path} is not mostly white")
            return False

        image.save(output_path, "PNG")
        hlog(f"Success: Extracted page {page_number} from {pdf_path} as an image.")
    except (RuntimeError, PDFPageCountError) as e:
        hlog(f"Skipping: Error generating image from {pdf_path}: {e}")
        return False

    return True


def main():
    fetch_music_sheets(
        num_examples=args.num_examples,
        year_range=(args.start_year, args.end_year),
        output_dir=args.output_dir,
        credentials_path=args.credentials_path,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "start_year",
        type=int,
        help="The start year to pull music sheets from",
    )
    parser.add_argument(
        "end_year",
        type=int,
        help="The end year to pull music sheets from",
    )
    parser.add_argument(
        "-n",
        "--num-examples",
        type=int,
        default=20,
        help="The number of examples to pull",
    )
    parser.add_argument(
        "-c",
        "--credentials-path",
        type=str,
        help="Where to read the credentials from",
        default="credentials/imslp.conf",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        type=str,
        help="Where to save the music sheets",
        default="data/sheet2lilypond",
    )
    args = parser.parse_args()
    main()
