import os
from dotenv import load_dotenv
from typing import Dict, List


# Load the .env file
load_dotenv()

LARGE_NUM_LINES = 1000000


def get_headers() -> Dict[str, str]:
    """Get the headers for the GitHub API

    Returns:
        Dict[str, str]: The headers for the GitHub API
    """
    load_dotenv()
    return {
        "Authorization": os.getenv("GITHUB_TOKEN"),
        "Accept": "application/vnd.github+json",
    }


def list_files_in_dir(path: str) -> List[str]:
    """List all the files in a directory
    If there are directories in the directory, the files in those directories are listed.
    This is done recursively.
    Here is an example:

    path/
    ├── dir1/
    │   ├── file1
    │   └── file2
    ├── dir2/
    │   ├── dir3/
    │   │   └── file3
    │   └── file4
    └── file5

    list_files_in_dir(path) -> ["dir1/file1", "dir1/file2", "dir2/dir3/file3", "dir2/file4", "file5"]

    Args:
        path (str): The path to the directory

    Returns:
        List[str]: The list of files in the directory
    """
    files_list = []

    # Walk through directory
    for root, _, files in os.walk(path):
        for file in files:
            # Construct the file's relative path
            relative_path = os.path.relpath(os.path.join(root, file), start=path)
            files_list.append(relative_path)

    return files_list


def filter_files_by_extension(
    files: List[str], extensions: List[str]
) -> Dict[str, List[str]]:
    """Filter files by their extensions (provided as a list of extensions)
    Put all the files that do not match the extensions in a "others" category.

    Args:
        files (List[str]): The list of files
        extensions (List[str]): The list of extensions to filter by

    Returns:
        Dict[str, List[str]]: The filtered files
    """
    filtered_files = {ext: [] for ext in extensions}
    filtered_files["others"] = []

    for file in files:
        # Get the file's extension
        ext = os.path.splitext(file)[-1][1:].lower()

        # Add the file to the appropriate category
        if ext in extensions:
            filtered_files[ext].append(file)
        else:
            filtered_files["others"].append(file)

    return filtered_files


def count_num_lines_in_files(repo_path: str, files: List[str]) -> int:
    """Count the number of lines in the files

    Args:
        repo_path (str): Path to the root of the files
        files (List[str]): The list of files

    Returns:
        int: The number of lines in the files
    """
    num_lines = 0

    for file in files:
        try:
            with open(os.path.join(repo_path, file), "r") as f:
                num_lines += len(f.readlines())
        except:
            # An error occured, so we are just going to add a lot of lines so that this repository is not considered
            num_lines += LARGE_NUM_LINES

    return num_lines
