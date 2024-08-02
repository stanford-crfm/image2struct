from abc import ABC, abstractmethod

from image2struct.fetch.fetcher import ScrapeResult
from image2struct.filter.utils import FilterError


class FetchFilterError(FilterError):
    pass


class FetchFilter(ABC):
    """This class is responsible for filtering fetches."""

    def __init__(self, name: str):
        """Initialize the filter with the name of the filter.

        Args:
            name (str): The name of the filter.
        """
        self.name = name

    @abstractmethod
    def filter(self, scrape_result: ScrapeResult) -> bool:
        """Check if the fetch meets the requirements.

        Args:
            scrape_result (ScrapeResult): The result of the fetch to check.

        Returns:
            bool: True if the fetch meets the requirements, False otherwise.

        Raises:
            FetchFilterError: If the fetch requires additional information that is not provided,
                or if the filtering cannot be performed.
        """
        pass
