from image2structure.fetch.fetcher import (
    Fetcher,
    DownloadError,
    ScrapeError,
    ScrapeResult,
)


import requests
from typing import Dict, List
import datetime
import os
import subprocess
import time


def get_headers() -> Dict[str, str]:
    """Get the headers for the GitHub API

    Returns:
        Dict[str, str]: The headers for the GitHub API
    """
    return {
        "Authorization": str(os.getenv("TOKEN_GITHUB")),
        "Accept": "application/vnd.github+json",
    }


class GitHubFetcher(Fetcher):
    """Fetcher for GitHub repositories."""

    # Github won't allow more than 1000 results
    # So we have to break down the search into multiple queries
    GITHUB_MAX_RESULTS = 1000

    def __init__(
        self,
        date_created_after: datetime.datetime,
        date_created_before: datetime.datetime,
        language: str,
        timeout: int,
        max_size_kb: int,
        verbose: bool,
    ):
        super().__init__(date_created_after, date_created_before, timeout, verbose)
        self._language: str = language
        self._page: int = 1
        self._max_size_kb: int = max_size_kb

        # Set internal dates to separate the search into multiple queries
        self._delay_days: int = 1
        self._date_created_before_internal = date_created_before
        self._date_created_after_internal = date_created_before - datetime.timedelta(
            days=self._delay_days
        )

    def change_internal_dates(self):
        """Change the internal dates for the next query"""
        self._page = 1
        self._date_created_before_internal = self._date_created_after_internal
        self._date_created_after_internal = (
            self._date_created_after_internal
            - datetime.timedelta(days=self._delay_days)
        )
        if self._date_created_after_internal < self._date_created_after:
            raise ScrapeError("No more results available for the given date range.")

    def scrape(self, num_instances: int) -> List[ScrapeResult]:
        """
        Scrape num_instances data points.

        Args:
            num_instances: The number of instances to scrape.

        Returns:
            List[ScrapeResult]: The results of the scraping.

        Raises:
            ScrapeError: If the scraping fails.
        """
        query_parameters = {
            "size": f"<={self._max_size_kb}",
            "created": (
                f">={self._date_created_after.strftime('%Y-%m-%d')}"
                if self._date_created_before is None
                else f"{self._date_created_after.strftime('%Y-%m-%d')}..{self._date_created_before.strftime('%Y-%m-%d')}"  # noqa: E501
            ),
        }
        if self._language.lower() not in [
            "html",
            "css",
            "javascript",
            "python",
        ]:
            raise ScrapeError(f"Invalid language: {self._language}")
        query_parameters["language"] = self._language
        search_query = "github.io in:name "
        search_query += " ".join(
            [f"{key}:{value}" for key, value in query_parameters.items()]
        )
        url = f"https://api.github.com/search/repositories?q={search_query}&per_page={num_instances}&page={self._page}&sort=updated&order=desc"  # noqa: E501

        # Increment the page number for the next query
        # Check that we won't exceed the maximum number of results
        self._page += 1
        if self._page * num_instances >= self.GITHUB_MAX_RESULTS:
            self.change_internal_dates()

        if self._verbose:
            print("Searching for repositories with the following query:", url)
        try:
            response = requests.get(url, headers=get_headers(), timeout=30)
        except requests.exceptions.RequestException as e:
            self.change_internal_dates()
            time.sleep(10)
            raise ScrapeError(f"Failed to retrieve data: {e}")

        if response.status_code == 200:
            # Check if we got num_instances results.
            # If we got less, it means, we have to change the dates for the next query
            if len(response.json()["items"]) < num_instances:
                self.change_internal_dates()

            return [
                ScrapeResult(
                    download_url=item["clone_url"],
                    instance_name=item["full_name"]
                    .replace("/", "_")
                    .replace(".github.io", "")
                    .replace(".", "_"),
                    additional_info={**item, "user": item["owner"]["id"]},
                )
                for item in response.json()["items"]
            ]
        else:
            self.change_internal_dates()
            time.sleep(10)
            raise ScrapeError(f"Failed to retrieve data: {response.status_code}")

    def download(self, download_path: str, scrape_result: ScrapeResult) -> None:
        """
        Download the data from the given scrape result to the given destination path.

        Args:
            download_path: The path to save the downloaded data to.
            scrape_result: The result of the scraping.

        Returns:
            None

        Raises:
            DownloadError: If the download fails.
        """
        repo_url: str = scrape_result.download_url
        repo_name: str = scrape_result.instance_name

        try:
            # Ensure the download path exists
            os.makedirs(download_path, exist_ok=True)
            # Execute the git clone command with a timeout
            subprocess.run(
                ["git", "clone", repo_url, os.path.join(download_path, repo_name)],
                timeout=self._timeout,
                check=True,
            )
        except subprocess.TimeoutExpired:
            raise DownloadError(
                f"Timeout expired: Cloning of {repo_name} took longer than {self._timeout} seconds"
            )
        except subprocess.CalledProcessError as e:
            raise DownloadError(f"Error during cloning: {e}")
