from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List
import datetime


@dataclass
class ScrapeResult:
    """Dataclass for store infos returned by scrapping of fetching an API."""

    # Where to download the actual data
    download_url: str

    # Name of the instance
    instance_name: str

    # Additional information about the result
    additional_info: Dict[str, Any]


class ScrapeError(Exception):
    pass


class DownloadError(Exception):
    pass


class Fetcher(ABC):

    def __init__(
        self,
        date_created_after: datetime.datetime,
        date_created_before: datetime.datetime,
        subcategory: str,
        timeout: int,
        verbose: bool,
    ):
        self._subcategory = subcategory
        self._date_created_after = date_created_after
        self._date_created_before = date_created_before
        self._timeout = timeout
        self._verbose = verbose

    @abstractmethod
    def scrape(self, num_instances: int) -> List[ScrapeResult]:
        """
        Scrape the data from the given scrape configuration.

        Args:
            scrape_config: The configuration for the scraping.

        Returns:
            List[ScrapeResult]: The results of the scraping.

        Raises:
            ScrapeError: If the scraping fails.
        """
        pass

    @abstractmethod
    def download(self, destination_path: str, scrape_result: ScrapeResult) -> None:
        """
        Download the data from the given scrape result to the given destination path.

        Args:
            destination_path: The path to save the downloaded data to.
            scrape_result: The result of the scraping.

        Returns:
            None

        Raises:
            DownloadError: If the download fails.
        """
        pass
