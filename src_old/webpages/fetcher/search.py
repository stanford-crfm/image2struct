import requests
from typing import Optional, Any, Dict, List
from datetime import datetime
import os
import subprocess

from .utils import get_headers


def search_github_repos(
    created_after: datetime,
    created_before: Optional[datetime] = None,
    language: Optional[str] = None,
    max_size_kb: int = 1000,
    limits: int = 100,
    page: int = 1,
    verbose: bool = False,
) -> List[Dict[str, Any]]:
    """Search for GitHub pages repositories

    Args:
        created_after (datetime): The date to search from
        language (Optional[str], optional): The language to search for. Defaults to None.
        max_size_kb (int, optional): The maximum size of the repository in KB. Defaults to 1000.
        limits (int, optional): The maximum number of repositories to retrieve. Defaults to 100.
        page (int, optional): The page number. Defaults to 1.
        verbose (bool, optional): Whether to print the search query. Defaults to False.

    Returns:
        List[Dict[str, Any]]: A list of repositories that match the search criteria

    Raises:
        Exception: If the request fails
    """
    query_parameters = {
        "size": f"<={max_size_kb}",
        "created": (
            f">={created_after.strftime('%Y-%m-%d')}"
            if created_before is None
            else f"{created_after.strftime('%Y-%m-%d')}..{created_before.strftime('%Y-%m-%d')}"
        ),
    }
    if language:
        query_parameters["language"] = language
    search_query = "github.io in:name "
    search_query += " ".join(
        [f"{key}:{value}" for key, value in query_parameters.items()]
    )
    url = f"https://api.github.com/search/repositories?q={search_query}&per_page={limits}&page={page}&sort=updated&order=desc"
    if verbose:
        print("Searching for repositories with the following query:", url)
    try:
        response = requests.get(url, headers=get_headers(), timeout=30)
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to retrieve data: {e}")
    if response.status_code == 200:
        return response.json()["items"]
    else:
        raise Exception(f"Failed to retrieve data: {response.status_code}")


def clone_repo(repo_url: str, download_path: str, repo_name: str, timeout: int = 5):
    """Clone a repository from GitHub with a timeout

    Args:
        repo_url (str): The URL of the repository
        download_path (str): The path to download the repository to
        repo_name (str): The name of the repository
        timeout (int): The maximum time allowed for the cloning process in seconds
    Raises:
        TimeoutExpired: If the cloning process takes longer than `timeout` seconds
    """
    try:
        # Ensure the download path exists
        os.makedirs(download_path, exist_ok=True)
        # Execute the git clone command with a timeout
        subprocess.run(
            ["git", "clone", repo_url, os.path.join(download_path, repo_name)],
            timeout=timeout,
            check=True,
        )
    except subprocess.TimeoutExpired:
        raise Exception(
            f"Timeout expired: Cloning of {repo_name} took longer than {timeout} seconds"
        )
    except subprocess.CalledProcessError as e:
        raise Exception(f"Error during cloning: {e}")


if __name__ == "__main__":
    # Example usage
    repos = search_github_repos(
        datetime(2021, 1, 1), language="JavaScript", verbose=True, limits=10
    )
    for i, repo in enumerate(repos):
        print(f"{i+1}. {repo['full_name']}: {repo['clone_url']}")
