from utils import MultiProgressBar, download_file, read_latex_file
import arxivscraper
from arxivscraper.constants import cats as ARXIV_CATEGORIES
import tarfile
import os
from typing import List, Optional, Tuple, Dict
from tqdm import tqdm
import shutil
import json
from PIL import Image
import time

from constants import TEX_DELIMITERS, TEX_BEGIN, TEX_END
from renderer import latex_to_image
import os
import re
import random
import numpy as np
from datetime import datetime, timedelta
import argparse


def gather_papers(
    category: str,
    date_from: str,
    date_until: str,
    num_to_do: Dict[str, int],
    dest_path: str = "data",
    max_elt_per_category: int = 3,
) -> Tuple[List[str], dict]:
    """Gather papers from arXiv.org.

    Args:
        category (str, optional): Category of the papers.
        date_from (str, optional): Starting date.
        date_until (str, optional): Ending date.

    Returns:
        papers (List[str]): List of papers tex codes.
    """

    # Scrape
    scraper = arxivscraper.Scraper(
        category=category,
        date_from=date_from,
        date_until=date_until,
    )
    outputs = scraper.scrape()
    if not isinstance(outputs, list):
        return
    random.shuffle(outputs)

    # Handle data
    os.makedirs(dest_path, exist_ok=True)
    asset_number = 0

    # Keep track of what still needs to be scraped
    progress_bars = MultiProgressBar(
        [(category, value) for category, value in num_to_do.items()]
        + [("papers", len(outputs))]
    )
    num_already_done = {category: 0 for category in num_to_do.keys()}

    for output in outputs:
        url = output["url"]
        doi = url.split("/")[-1]

        # Process the paper
        num_done, asset_number = process_doi(
            doi=doi,
            dest_path=dest_path,
            num_to_do=num_to_do.copy(),
            num_already_done=num_already_done,
            max_elt_per_category=max_elt_per_category,
            asset_number=asset_number,
        )
        # Remove the temporary directory (and its contents)
        shutil.rmtree("tmp")

        # Update counts
        for category in num_done:
            progress_bars.update(category, num_done[category])
            num_already_done[category] += num_done[category]
            num_to_do[category] -= num_done[category]
        progress_bars.update("papers", 1)

        # Check if we are done
        finished = True
        for _, value in num_to_do.items():
            if value > 0:
                finished = False
        if finished:
            progress_bars.close()
            print("Finished!")
            break


def process_doi(
    doi: str,
    dest_path: str,
    num_to_do: Dict[str, int],
    num_already_done: Dict[str, int],
    max_elt_per_category: int,
    asset_number: int,
) -> Tuple[Dict[str, int], int]:
    # Check on the inputs
    for category in num_to_do.keys():
        assert category in num_already_done
        num_to_do[category] = min(num_to_do[category], max_elt_per_category)

    os.makedirs("tmp", exist_ok=True)
    TMP_FILE = "tmp/src.tar.gz"
    TMP_SRC_DIR = "tmp/src"
    TMP_WORK_DIR = "tmp/work"

    # Download the .tar.gz file
    download_url = "https://arxiv.org/e-print/" + doi
    download_successful = download_file(download_url, filename=TMP_FILE)
    if not download_successful:
        return {}, asset_number

    # Extract the files
    # Extract the .tar.gz file in a temporary directory
    # Creates the dir (ok if it already exists)
    os.makedirs(TMP_SRC_DIR, exist_ok=True)
    os.makedirs(TMP_WORK_DIR, exist_ok=True)
    try:
        with tarfile.open(TMP_FILE, "r:gz") as tar:
            # Extract all the contents into the current directory
            tar.extractall(path=TMP_SRC_DIR)
    except tarfile.ReadError:
        return {}, asset_number

    # Search for all '.tex' file in the extracted directory
    list_tex_code: List[str] = []
    for root, dirs, files in os.walk(TMP_SRC_DIR):
        for file in files:
            if file.endswith(".tex"):
                # read the Latex file
                file_path: str = os.path.join(root, file)
                tex_code, read_successful = read_latex_file(file_path)
                if not read_successful:
                    continue

                # Rename the assets
                tex_code, asset_number = rename_and_save_assets(
                    tex_code=tex_code,
                    asset_number=asset_number,
                    src_path=TMP_SRC_DIR,
                    dest_path=TMP_WORK_DIR,
                )
                list_tex_code.append(tex_code)

    # Delimit the content
    categories = [category for category, value in num_to_do.items() if value > 0]
    delimited_content = {category: [] for category in categories}
    for src_code in list_tex_code:
        tmp_delimited_content = get_delimited_content(src_code, categories=categories)
        for category in delimited_content.keys():
            delimited_content[category] += tmp_delimited_content[category]

    # Shuffle the content
    for category in delimited_content.keys():
        random.shuffle(delimited_content[category])

    # Render and save some code
    num_done: Dict[str, int] = get_and_save_rendering_from_delimited_content(
        delimited_content=delimited_content,
        assets_path=TMP_WORK_DIR,
        dest_path=dest_path,
        offsets_per_category=num_already_done,
        num_per_category=num_to_do,
    )

    return num_done, asset_number


def rename_and_save_assets(
    tex_code: str, asset_number: int, src_path: str, dest_path: str
) -> Tuple[str, int]:
    asset_names: List[str] = get_asset_names_used(tex_code)
    asset_mapping: Dict[
        str, Tuple[str, str]
    ] = {}  # Associates the new path to [tex_name, original_path]

    # Rename the assets by replacing / by _ and adding num_extracted _ at the beginning
    for original_name in asset_names:
        original_name_with_extension = original_name
        if not "." in original_name_with_extension:
            # Find a file starting with the original_name to determine the extension
            file_name = original_name_with_extension.split("/")[-1]
            asset_dest = os.path.join(
                src_path, "/".join(original_name_with_extension.split("/")[:-1])
            )
            for _, _, files in os.walk(asset_dest):
                for file in files:
                    if file.startswith(file_name):
                        extension = os.path.splitext(file)[1]
                        original_name_with_extension += extension
                        break
        new_name = f'{asset_number}_{original_name_with_extension.replace("/", "_")}'
        asset_mapping[new_name] = [original_name, original_name_with_extension]
        asset_number += 1

    # Replace the occurences in the tex_code
    for new_name, [original_name, _] in asset_mapping.items():
        tex_code = tex_code.replace(original_name, new_name)

    # Move the assets
    for new_name, [_, original_name_with_extension] in asset_mapping.items():
        asset_path = os.path.join(src_path, original_name_with_extension)
        new_asset_path = os.path.join(dest_path, new_name)
        try:
            shutil.copy(asset_path, new_asset_path)
        except FileNotFoundError:
            pass

    return tex_code, asset_number


def get_asset_names_used(latex_code: str) -> List[str]:
    pattern = r"\\includegraphics(?:\[[^\]]+\])?\{([^}]+)\}"
    asset_names = re.findall(pattern, latex_code)
    return asset_names


def get_delimited_content(
    src_code: str, categories: Optional[List[str]] = None
) -> Dict[str, List[str]]:
    """Given a tex source code, return a dictionarry mapping categories (equation, plot, table, ...) to
    all the instances of that category in the source codes.

    Args:
        src_code (str): tex source code.
        categories (Optional[List[str]], optional): List of categories to look for. Defaults to None.
            when None, all categories are considered.

    Returns:
        Dict[str, List[str]]: Dictionnary mapping a category to the list of delimited instances
    """
    delimited_content: Dict[str, List[str]] = {}

    for category, (must_contain, delimiters) in TEX_DELIMITERS.items():
        # Skip the category if it is not in the list of categories
        if categories is not None and category not in categories:
            continue

        delimited_content[category] = []
        for delimiter in delimiters:
            start, end = delimiter
            lines = src_code.split("\n")  # Split the source code into lines
            start_idx, end_idx = None, None
            content = ""

            for line in lines:
                stripped_line = line.strip()

                # Skip commented lines
                if stripped_line.startswith("%"):
                    continue

                # Check for the start delimiter
                if start_idx is None:
                    if start in stripped_line:
                        start_idx = lines.index(line)
                        content += line + "\n"
                        continue

                # If we are in an environment, add the line to content
                if start_idx is not None:
                    content += line + "\n"

                # Check for the end delimiter
                if end in stripped_line:
                    end_idx = lines.index(line)
                    if start_idx is not None and end_idx is not None:
                        # We only add the content to the category if it contains the must_contain string
                        if must_contain is None or must_contain in content:
                            delimited_content[category].append(content)
                        start_idx, end_idx = None, None
                        content = ""

        # Remove duplicates
        delimited_content[category] = list(set(delimited_content[category]))

    return delimited_content


def get_and_save_rendering_from_delimited_content(
    delimited_content: Dict[str, List[str]],
    assets_path: str,
    dest_path: str,
    offsets_per_category: Dict[str, int],
    num_per_category: Dict[str, int],
):
    """Given a dictionnary of delimited content, render all the images.
    Save them directly.

    Args:
        delimited_content (Dict[str, List[str]]): Dictionnary mapping a category to the list of delimited instances
        infos (dict): informations on the scrapping process.
    """

    num_done: Dict[str, int] = {}

    for category, list_of_content in delimited_content.items():
        os.makedirs(f"{dest_path}/images/{category}s", exist_ok=True)
        os.makedirs(f"{dest_path}/contents/{category}s", exist_ok=True)
        os.makedirs(f"{dest_path}/assets", exist_ok=True)

        num_images = 0
        offset = offsets_per_category[category]
        num_max_image = num_per_category[category]

        for tex_code in list_of_content:
            try:
                # Render the image
                image, dimensions = latex_to_image(
                    TEX_BEGIN + tex_code + TEX_END,
                    assets_path=assets_path,
                    crop=True,
                )

                # Check if the image is not fully white
                if image is None or np.allclose(image, 255):
                    continue

                # Save the associated assets
                asset_names = get_asset_names_used(tex_code)
                for asset_name in asset_names:
                    asset_path = os.path.join(assets_path, asset_name)
                    new_asset_path = os.path.join(
                        f"{dest_path}/assets", asset_name.replace("/", "_")
                    )
                    try:
                        shutil.copy(asset_path, new_asset_path)
                    except FileNotFoundError as e:
                        # Could not copy one of the assets so ignore this tex_code
                        continue

                # Save the image
                image.save(
                    f"{dest_path}/images/{category}s/{category}_{num_images + offset}.png"
                )

                # Save the associated code
                with open(
                    f"{dest_path}/contents/{category}s/{category}_{num_images + offset}.tex",
                    "w",
                ) as f:
                    f.write(tex_code)

                # Once we have enough images, stop rendering
                num_images += 1
                if num_images >= num_max_image:
                    break

            # There was an error rendering or saving the code, go to the next code
            except Exception as e:
                continue

        num_done[category] = num_images

    return num_done


def get_day_before(date_str: str, days: int = 1) -> str:
    # Convert string to datetime object
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")

    # Subtract one day
    day_before = date_obj - timedelta(days=days)

    # Convert back to string
    day_before_str = day_before.strftime("%Y-%m-%d")
    return day_before_str


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Arxiv Scraper")
    parser.add_argument("--category", type=str, help="Category to scrape")
    args = parser.parse_args()

    category = args.category

    # Rest of the code
    date_until: str = "2024-01-15"
    num_instances_per_tex_category = {
        "equation": 250,
        "figure": 125,
        "table": 125,
        "algorithm": 125,
        "plot": 125,
    }

    gather_papers(
        category=category,
        date_from=get_day_before(date_until, days=14),
        date_until=date_until,
        num_to_do=num_instances_per_tex_category,
        dest_path=f"data/{category}",
        max_elt_per_category=3,
    )
