from typing import List, Dict, Tuple

import os

from image2structure.filter.file_filters.file_filter import FileFilter


# The number of lines in a file that is considered to be a large number of lines
# Used in case of an error, to make sure that the repository is filtered out
LARGE_NUM_LINES = 1000000


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


class RepoFilter(FileFilter):
    """This class is responsible for filtering repositories.

    The filtering is done based on the number of files in the repository,
    as well as the number of lines of code in the files.
    """

    CODE_EXTENSIONS = ["js", "html", "md", "py", "rb", "php", "java", "c", "cpp"]
    STYLE_EXTENSIONS = ["css"]
    ASSET_EXTENSIONS = [
        "png",
        "jpg",
        "jpeg",
        "gif",
        "svg",
        "mp4",
        "webm",
        "mov",
        "avi",
        "flv",
        "wmv",
        "mkv",
    ]
    EXCLUDE_SPECIAL_FILES = [
        "license.md",
        "contributing.md",
        "gemfile",
        "gemfile.lock",
        "_config.yml",
    ]

    def __init__(
        self,
        min_num_lines: int,
        has_more_than_readme: bool,
        max_num_files_code: int,
        max_num_assets: int,
        max_num_lines_code: int,
        max_num_lines_style: int,
    ):
        """Initialize the filter with the minimum number of lines and files in the repository

        Args:
            min_num_lines (int): The minimum number of lines in the repository
            has_more_than_readme (bool): Whether the repository should have more than just a readme file
            max_num_files_code (int): The maximum number of code files in the repository (html, js, etc.)
            max_num_assets (int): The maximum number of assets in the repository (images, videos, etc.)
            max_num_lines_code (int): The maximum number of lines of code in the repository
            max_num_lines_style (int): The maximum number of lines of style in the repository (css)
        """
        super().__init__(name="RepoFilter")
        self.min_num_lines = min_num_lines
        self.has_more_than_readme = has_more_than_readme
        self.max_num_files_code = max_num_files_code
        self.max_num_assets = max_num_assets
        self.max_num_lines_code = max_num_lines_code
        self.max_num_lines_style = max_num_lines_style

    def analyze_repo(self, repo_path: str) -> Dict[str, Dict[str, int]]:
        """Analyze a repository
        Return the number of lines and files in the repository and the number of lines in each file type.

        Args:
            repo_path (str): The path to the repository

        Returns:
            Dict[str, Any]: The analysis of the repository
        """
        # Get the list of files in the repository
        files = list_files_in_dir(repo_path)
        files = [
            file for file in files if file.lower() not in self.EXCLUDE_SPECIAL_FILES
        ]  # Exclude special files
        files = [
            file for file in files if not file.startswith(".")
        ]  # Exclude files starting with . (hidden files)

        # Filter the files by their extensions
        filtered_files = filter_files_by_extension(
            files, self.CODE_EXTENSIONS + self.STYLE_EXTENSIONS + self.ASSET_EXTENSIONS
        )

        # Check if files only contain readme.md
        all_code_files_without_readme = []
        for ext in self.CODE_EXTENSIONS:
            all_code_files_without_readme.extend(filtered_files[ext])
        only_contains_readme: bool = (
            len(all_code_files_without_readme) == 1
            and all_code_files_without_readme[0].lower() == "readme.md"
        )

        return {
            "only_contains_readme": only_contains_readme,
            "num_files": {
                "total": len(files),
                "code": sum(len(filtered_files[ext]) for ext in self.CODE_EXTENSIONS),
                "style": len(filtered_files["css"]),
                "asset": sum(len(filtered_files[ext]) for ext in self.ASSET_EXTENSIONS),
            },
            "num_lines": {
                "code": sum(
                    count_num_lines_in_files(repo_path, filtered_files[ext])
                    for ext in self.CODE_EXTENSIONS
                ),
                "style": count_num_lines_in_files(repo_path, filtered_files["css"]),
            },
        }

    def filter(self, file_path: str) -> Tuple[bool, Dict[str, Dict[str, int]]]:
        """Filter a repository based on the parameters

        Args:
            file_path (str): The path to the repository

        Returns:
            bool: Whether the repository passes the filter
            Dict[str, Dict[str, int]]: The analysis of the repository
        """
        # Analyze the repository
        analysis: Dict[str, Dict[str, int]] = self.analyze_repo(file_path)

        # Check if the repository passes the filter
        passes_filter = (
            analysis["num_lines"]["code"] >= self.min_num_lines
            and (not analysis["only_contains_readme"] or not self.has_more_than_readme)
            and analysis["num_files"]["code"] <= self.max_num_files_code
            and analysis["num_files"]["asset"] <= self.max_num_assets
            and analysis["num_lines"]["code"] <= self.max_num_lines_code
            and analysis["num_lines"]["style"] <= self.max_num_lines_style
        )

        return passes_filter, analysis
