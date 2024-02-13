from .utils import (
    count_num_lines_in_files,
    filter_files_by_extension,
    list_files_in_dir,
)
from typing import Dict, Tuple


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


def analyze_repo(repo_path: str) -> Dict[str, Dict[str, int]]:
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
        file for file in files if file.lower() not in EXCLUDE_SPECIAL_FILES
    ]  # Exclude special files
    files = [
        file for file in files if not file.startswith(".")
    ]  # Exclude files starting with . (hidden files)

    # Filter the files by their extensions
    filtered_files = filter_files_by_extension(
        files, CODE_EXTENSIONS + STYLE_EXTENSIONS + ASSET_EXTENSIONS
    )

    # Check if files only contain readme.md
    all_code_files_without_readme = []
    for ext in CODE_EXTENSIONS:
        all_code_files_without_readme.extend(filtered_files[ext])
    only_contains_readme: bool = (
        len(all_code_files_without_readme) == 1
        and all_code_files_without_readme[0].lower() == "readme.md"
    )

    return {
        "only_contains_readme": only_contains_readme,
        "num_files": {
            "total": len(files),
            "code": sum(len(filtered_files[ext]) for ext in CODE_EXTENSIONS),
            "style": len(filtered_files["css"]),
            "asset": sum(len(filtered_files[ext]) for ext in ASSET_EXTENSIONS),
        },
        "num_lines": {
            "code": sum(
                count_num_lines_in_files(repo_path, filtered_files[ext])
                for ext in CODE_EXTENSIONS
            ),
            "style": count_num_lines_in_files(repo_path, filtered_files["css"]),
        },
    }


class RepoFilterParams:
    """A class to store the parameters for filtering repositories"""

    """The minimum number of lines in the repository"""
    min_lines: int = 10

    """Whether the repository should have more than just a README file"""
    has_more_than_readme: bool = True

    """The maximum number of code files in the repository (md, js, html)"""
    max_num_files_code: int = 5

    """Maximum number of assets in the repository (images, videos, etc.)"""
    max_num_assets: int = 5

    """The maximum number of lines in the code files. This includes all code files (js, html, md, py, rb, php, java, c, cpp)"""
    max_num_lines_code: int = 1000

    """The maximum number of lines in CSS files"""
    max_num_lines_style: int = 2000


def filter_repo(
    repo_path: str, params: RepoFilterParams = RepoFilterParams()
) -> Tuple[bool, Dict[str, Dict[str, int]]]:
    """Filter a repository based on the parameters

    Args:
        repo_path (str): The name of the repository
        params (RepoFilterParams, optional): The parameters to use for filtering. Defaults to RepoFilterParams().

    Returns:
        bool: Whether the repository passes the filter
        Dict[str, Dict[str, int]]: The analysis of the repository
    """
    # Analyze the repository
    analysis = analyze_repo(repo_path)

    # Check if the repository passes the filter
    passes_filter = (
        analysis["num_lines"]["code"] > params.min_lines
        and (not analysis["only_contains_readme"] or not params.has_more_than_readme)
        and analysis["num_files"]["code"] <= params.max_num_files_code
        and analysis["num_files"]["asset"] <= params.max_num_assets
        and analysis["num_lines"]["code"] <= params.max_num_lines_code
        and analysis["num_lines"]["style"] <= params.max_num_lines_style
    )

    return passes_filter, analysis
