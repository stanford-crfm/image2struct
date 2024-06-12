from typing import Any, Dict, List
from tqdm import tqdm
from datasets import Dataset
from datasets import DatasetDict, Features, Value, Image as HFImage, Sequence

import argparse
import os
import io
from PIL import Image
import base64
import pandas as pd
import numpy as np
import json
import imagehash


def load_image(image_path: str) -> Image.Image:
    """Load an image from the specified path."""
    with open(image_path, "rb") as f:
        img = Image.open(io.BytesIO(f.read()))
        img.load()  # Ensure PIL doesn't close the stream
        return img


def load_file(file_path: str) -> str:
    """Read the content of a file."""
    with open(file_path, "r") as file:
        return file.read()


def load_archive(archive_path: str) -> str:
    """Load an archive from the specified path."""
    with open(archive_path, "rb") as zip_file:
        zip_content = zip_file.read()
    base64_encoded = base64.b64encode(zip_content).decode("utf-8")
    return base64_encoded


def transform(row: dict) -> dict:
    row["image"] = load_image(row["image"])
    metadata_str: str = load_file(row["metadata"])
    metadata: Dict[str, Any] = json.loads(metadata_str)
    for key in metadata:
        if key != "assets":
            row[key] = json.dumps(metadata[key], indent=4)
        else:
            assets: List[str] = []  # Base64 assets
            for asset in metadata[key]:
                with open(asset, "rb") as file:
                    assets.append(base64.b64encode(file.read()).decode("utf-8"))
            row[key] = assets

    del row["metadata"]
    if "assets" not in row:
        row["assets"] = []
    return row


def classify_difficulty(dataset, data_type: str, wild_data: bool = False):
    """
    Classify the difficulty of the instances in the dataset.
        - 1/3 of the instances are easy
        - 1/3 of the instances are medium
        - 1/3 of the instances are hard

    Args:
        dataset: The dataset to classify, expected to be an iterable of dictionaries.
        data_type: The type of data to classify (e.g., webpage, latex).

    Returns:
        The dataset with the difficulty classified.
    """
    if not wild_data:
        if data_type == "latex":
            lengths = [len(item["text"]) for item in dataset]
        elif data_type == "musicsheet":
            lengths = []
            for item in tqdm(dataset, desc="Computing difficulty"):
                with Image.open(io.BytesIO(item["image"]["bytes"])) as img:
                    img_array = np.array(img)
                    # Assuming the image is grayscale; update this if it's not
                    black_pixels = np.sum(img_array < np.max(img_array) / 4.0)
                    lengths.append(black_pixels)
        elif data_type == "webpage":
            lengths = [
                int(json.loads(item["file_filters"])["RepoFilter"]["num_lines"]["code"])
                + int(
                    json.loads(item["file_filters"])["RepoFilter"]["num_lines"]["style"]
                )
                for item in dataset
            ]
        else:
            raise ValueError(f"Unknown data type: {data_type}")

        # Sort lengths and find thresholds
        lengths_sorted = sorted(lengths)
        easy_threshold = lengths_sorted[len(lengths) // 3]
        medium_threshold = lengths_sorted[(len(lengths) // 3) * 2]

    # Assign difficulty based on thresholds
    # Add "difficulty" to the columns of the dataset
    df = pd.DataFrame(dataset)
    if wild_data:
        df["difficulty"] = "hard"
    else:
        df["length"] = lengths
        df["difficulty"] = "easy"
        df.loc[
            (df["difficulty"] == "easy") & (df["length"] > easy_threshold), "difficulty"
        ] = "medium"
        df.loc[
            (df["difficulty"] == "medium") & (df["length"] > medium_threshold),
            "difficulty",
        ] = "hard"
    return Dataset.from_pandas(df)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Upload collected data to huggingface")
    parser.add_argument(
        "--data-path",
        type=str,
        required=True,
        help="The path to the data to upload",
    )
    parser.add_argument(
        "--dataset-name",
        type=str,
        required=True,
        help="The name of the dataset to upload",
    )
    parser.add_argument(
        "--max-instances",
        type=int,
        default=-1,
        help="The maximum number of instances to upload",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    data_type: str = os.path.basename(args.data_path)
    print(f"\nUploading {data_type} dataset...")
    for category in ["wild"]:  # os.listdir(args.data_path):
        print(f"\nUploading {category} dataset...")
        data_path: str = os.path.join(args.data_path, category)

        # There should be 4 folders in the data_path
        # - images
        # - structures
        # - metadata
        # - assets
        image_path = os.path.join(data_path, "images")
        structure_path = os.path.join(data_path, "structures")
        metadata_path = os.path.join(data_path, "metadata")
        assets_path = os.path.join(data_path, "assets")
        text_path = os.path.join(data_path, "text")
        for path in [image_path, metadata_path, assets_path]:
            if not os.path.exists(path):
                raise FileNotFoundError(f"{path} does not exist")
        has_structure: bool = os.path.exists(structure_path)
        has_text: bool = os.path.exists(text_path)

        num_data_points: int = len(os.listdir(image_path))

        # Create the dataset.
        # It should have the following structure:
        # - structure (str) either with read_file or read_archive
        # - image (str) with read_image
        # - all the direct fields in the metadata folder. The only exception is the key "assets"
        #   in the metadat gives paths to the assets used. These assets should be loaded as a
        #   list of encoded strings and stored in the column "assets"

        # Figure out the extension of the structure files
        extension: str = ""
        if has_structure:
            first_file_name: str = os.listdir(structure_path)[0]
            extension = os.path.splitext(first_file_name)[-1]
            if first_file_name.endswith(".tar.gz"):
                extension = ".tar.gz"

        # Load the structure
        df: pd.DataFrame = pd.DataFrame()
        structure_set = set()
        file_names: List[str] = os.listdir(image_path)
        image_set = set()
        for i in tqdm(range(num_data_points), desc="Loading data"):
            try:
                values = {}
                file_name: str = file_names[i].replace(".png", "")

                if has_structure:
                    structure_file = os.path.join(
                        structure_path, f"{file_name}{extension}"
                    )
                    structure: str
                    if extension == ".tar.gz" or extension == ".zip":
                        structure = load_archive(structure_file)
                    else:
                        structure = load_file(structure_file)
                    if structure in structure_set:
                        continue
                    values["structure"] = [structure]
                    structure_set.add(structure)

                if has_text:
                    text: str = load_file(os.path.join(text_path, f"{file_name}.txt"))
                    values["text"] = [text]

                image = os.path.join(image_path, f"{file_name}.png")
                hashed_img: str = str(imagehash.average_hash(load_image(image)))
                if hashed_img in image_set:
                    continue
                image_set.add(hashed_img)
                values["image"] = [image]

                metadata = os.path.join(metadata_path, f"{file_name}.json")
                values["metadata"] = [metadata]

                df = pd.concat([df, pd.DataFrame(values)])

            except FileNotFoundError as e:
                print(
                    f"Skipping {file_name} as it is missing one of the required files: {e}"
                )
                continue

        # Remove duplicates
        # Only check the structure if present, otherwise check the image (path)
        if has_structure:
            df = df.drop_duplicates(subset=["structure"])
        else:
            df = df.drop_duplicates(subset=["image"])

        # Limit the number of instances
        if args.max_instances > 0:
            if len(df) > args.max_instances:
                print(f"Limiting the number of instances to {args.max_instances}")
            # Shuffle the dataset
            df = df.sample(frac=1)
            df = df.head(args.max_instances)

        valid_dataset = Dataset.from_pandas(df).map(transform).shuffle()

        # Classify the difficulty of the instances
        valid_dataset = classify_difficulty(
            valid_dataset, data_type, category == "wild"
        )
        # valid_dataset = Dataset.from_pandas(df)
        # Print first 5 instances

        # Remove the '__index_level_0__' column from the datasets
        if "__index_level_0__" in valid_dataset.column_names:
            print("Removing __index_level_0__")
            valid_dataset = valid_dataset.remove_columns("__index_level_0__")

        # Define the features of the dataset
        features_dict = {
            column: Value("string") for column in valid_dataset.column_names
        }
        features_dict["image"] = HFImage()
        features_dict["assets"] = Sequence(Value("string"))
        features = Features(features_dict)
        valid_dataset = valid_dataset.cast(features)

        # Push the dataset to the hub
        dataset_dict = DatasetDict({"validation": valid_dataset})
        dataset_dict.push_to_hub(args.dataset_name, config_name=category)


if __name__ == "__main__":
    main()
