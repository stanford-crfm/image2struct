import argparse
import os
import shutil
import json
import uuid
from datetime import datetime


def get_parser():
    parser = argparse.ArgumentParser(
        description="Generate LaTeX structures from images"
    )
    parser.add_argument(
        "--input-dir",
        type=str,
        default="data/equations_real",
        help="The path to the input directory",
    )
    parser.add_argument(
        "--save-dir",
        type=str,
        default="data/latex/wild",
        help="The path to the save directory",
    )
    return parser


def create_folders(save_dir: str):
    os.makedirs(save_dir, exist_ok=True)
    os.makedirs(os.path.join(save_dir, "metadata"), exist_ok=True)
    os.makedirs(os.path.join(save_dir, "assets"), exist_ok=True)
    os.makedirs(os.path.join(save_dir, "images"), exist_ok=True)
    os.makedirs(os.path.join(save_dir, "structures"), exist_ok=True)


def copy_screenshots(uuid: str, src_file: str, save_dir: str):
    dest_file = os.path.join(save_dir, "images", f"{uuid}.png")
    shutil.copyfile(src_file, dest_file)


def generate_metadata(uuid: str, url: str, save_dir: str):
    metadata = {
        "url": url,
        "instance_name": url.replace("https://www.", ""),
        "date_scrapped": datetime.now().isoformat(),
        "uuid": str(uuid),
        "category": "real",
        "additional_info": {},
        "assets": [],
    }
    with open(os.path.join(save_dir, "metadata", f"{uuid}.json"), "w") as f:
        json.dump(metadata, f, indent=4)


def create_structures(uuid: str, save_dir: str):
    # For Wikipedia, leave the structures folder empty
    pass


def process_image(src_file: str, url: str, save_dir: str):
    # Generate UUID
    uuid_str = str(uuid.uuid4())

    # Create folder structure
    create_folders(save_dir)

    # Copy screenshot to images folder and rename
    copy_screenshots(uuid_str, src_file, save_dir)

    # Generate metadata
    generate_metadata(uuid_str, url, save_dir)

    # Create structures folder
    create_structures(uuid_str, save_dir)


def main(input_dir: str, save_dir: str):
    print(f"Processing all images in {input_dir}")
    for filename in os.listdir(input_dir):
        print(f"Processing {filename}")
        if filename.endswith(".png") or filename.endswith(".jpg"):
            src_file = os.path.join(input_dir, filename)
            # Example URL for metadata since all screenshots are from Wikipedia
            url = "https://www.wikipedia.org"
            process_image(src_file, url, save_dir)


if __name__ == "__main__":
    parser = get_parser()
    args = parser.parse_args()
    main(args.input_dir, args.save_dir)
