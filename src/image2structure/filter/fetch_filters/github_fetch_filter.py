from typing import Optional

from image2structure.filter.fetch_filters.fetch_filter import (
    FetchFilter,
    FetchFilterError,
)
from image2structure.fetch.fetcher import ScrapeResult

import threading


class GitHubFetchFilter(FetchFilter):
    def __init__(self) -> None:
        super().__init__("GitHubFetchFilter")
        self._users_set: set = set()
        self._repositories_set: set = set()
        self._lock: threading.Lock = threading.Lock()

    def filter(self, scrape_result: ScrapeResult) -> bool:
        """Check if the fetch meets the requirements.

        Args:
            scrape_result (ScrapeResult): The result of the fetch to check.

        Returns:
            bool: True if the fetch meets the requirements, False otherwise.

        Raises:
            FetchFilterError: If the user is not provided in the additional_info.
        """

        # Check for duplicates
        with self._lock:
            if scrape_result.instance_name in self._repositories_set:
                return False
            self._repositories_set.add(scrape_result.instance_name)

        # Check for other repositories from the same user
        if not scrape_result.additional_info:
            raise FetchFilterError("Additional info not provided in the scrape result.")
        user: Optional[str] = scrape_result.additional_info.get("user", None)
        if user is None:
            raise FetchFilterError(
                "User not provided in the additional_info. Make sure to use the GitHubFetcher."
            )
        with self._lock:
            if user in self._users_set:
                return False
            self._users_set.add(user)

        return True
