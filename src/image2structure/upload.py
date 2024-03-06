from typing import Any, Dict, List
from tqdm import tqdm
from datasets import Dataset
from sklearn.model_selection import train_test_split
from datasets import DatasetDict, Features, Value, Image as HFImage, Sequence

import argparse
import os
import io
from PIL import Image
import base64
import pandas as pd
import json


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

    for category in os.listdir(args.data_path):
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
        for path in [image_path, structure_path, metadata_path, assets_path, text_path]:
            if not os.path.exists(path):
                raise FileNotFoundError(f"{path} does not exist")

        num_data_points: int = len(os.listdir(image_path))

        # Create the dataset.
        # It should have the following structure:
        # - structure (str) either with read_file or read_archive
        # - image (str) with read_image
        # - all the direct fields in the metadata folder. The only exception is the key "assets"
        #   in the metadat gives paths to the assets used. These assets should be loaded as a
        #   list of encoded strings and stored in the column "assets"

        # Figure out the extension of the structure files
        file_name: str = os.listdir(structure_path)[0]
        extension: str = os.path.splitext(file_name)[-1]
        if file_name.endswith(".tar.gz"):
            extension = ".tar.gz"

        # Load the structure
        df: pd.DataFrame = pd.DataFrame()
        structure_set = set()
        for i in tqdm(range(num_data_points), desc="Loading data"):
            try:
                structure_file = os.path.join(structure_path, f"{i}{extension}")
                structure: str
                if extension == ".tar.gz" or extension == ".zip":
                    structure = load_archive(structure_file)
                else:
                    structure = load_file(structure_file)
                if structure in structure_set:
                    continue
                structure_set.add(structure)
                text: str = load_file(os.path.join(text_path, f"{i}.txt"))
                image = os.path.join(image_path, f"{i}.png")
                metadata = os.path.join(metadata_path, f"{i}.json")
                df = pd.concat(
                    [
                        df,
                        pd.DataFrame(
                            {
                                "structure": [structure],
                                "image": [image],
                                "metadata": [metadata],
                                "text": [text],
                            }
                        ),
                    ]
                )
            except FileNotFoundError as e:
                print(f"Skipping {i} as it is missing one of the required files: {e}")
                continue

        # Remove duplicates
        # Only check the structure
        df = df.drop_duplicates(subset=["structure"])

        # Limit the number of instances
        if args.max_instances > 0:
            if len(df) > args.max_instances:
                print(f"Limiting the number of instances to {args.max_instances}")
            # Shuffle the dataset
            df = df.sample(frac=1)
            df = df.head(args.max_instances)

        # Split the dataset
        valid_df, test_df = train_test_split(df, test_size=0.2)
        valid_dataset = Dataset.from_pandas(valid_df).map(transform).shuffle()
        test_dataset = Dataset.from_pandas(test_df).map(transform).shuffle()

        # Remove the '__index_level_0__' column from the datasets
        if "__index_level_0__" in valid_dataset.column_names:
            print("Removing __index_level_0__")
            valid_dataset = valid_dataset.remove_columns("__index_level_0__")
        if "__index_level_0__" in test_dataset.column_names:
            print("Removing __index_level_0__")
            test_dataset = test_dataset.remove_columns("__index_level_0__")

        # Define the features of the dataset
        features_dict = {
            column: Value("string") for column in valid_dataset.column_names
        }
        features_dict["image"] = HFImage()
        features_dict["assets"] = Sequence(Value("string"))
        features = Features(features_dict)
        valid_dataset = valid_dataset.cast(features)
        test_dataset = test_dataset.cast(features)

        # Push the dataset to the hub
        dataset_dict = DatasetDict({"validation": valid_dataset, "test": test_dataset})
        dataset_dict.push_to_hub(args.dataset_name, config_name=category)


if __name__ == "__main__":
    main()
