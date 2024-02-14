from abc import ABC, abstractmethod

from image2structure.fetch.fetcher import ScrapeResult
from image2structure.filter.utils import FilterError


class FetchFilterError(FilterError):
    pass


class FetchFilter(ABC):
    """This class is responsible for filtering fetches."""

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
