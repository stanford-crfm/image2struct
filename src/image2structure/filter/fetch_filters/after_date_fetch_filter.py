import datetime

from image2structure.filter.fetch_filters.fetch_filter import FetchFilter
from image2structure.fetch.fetcher import ScrapeResult


class AfterDateFetchFilter(FetchFilter):
    def __init__(self, _after_date: datetime.datetime):
        super().__init__("AfterDateFetchFilter")
        self.__after_date = _after_date

    def filter(self, scrape_result: ScrapeResult) -> bool:
        """Check if the fetch meets the requirements.

        Args:
            scrape_result (ScrapeResult): The result of the fetch to check.

        Returns:
            bool: True if the fetch meets the requirements, False otherwise.
        """
        return scrape_result.date >= self.__after_date
