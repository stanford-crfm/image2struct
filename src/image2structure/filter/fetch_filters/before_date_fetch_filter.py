import datetime

from image2structure.filter.fetch_filters.fetch_filter import FetchFilter
from image2structure.fetch.fetcher import ScrapeResult


class BeforeDateFetchFilter(FetchFilter):
    def __init__(self, before_date: datetime.datetime):
        super().__init__("BeforeDateFetchFilter")
        self._before_date = before_date

    def filter(self, scrape_result: ScrapeResult) -> bool:
        """Check if the fetch meets the requirements.

        Args:
            scrape_result (ScrapeResult): The result of the fetch to check.

        Returns:
            bool: True if the fetch meets the requirements, False otherwise.
        """
        return scrape_result.date >= self._before_date
