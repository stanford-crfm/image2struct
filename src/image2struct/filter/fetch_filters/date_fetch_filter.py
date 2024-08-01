from typing import Dict

import threading

from image2struct.filter.fetch_filters.fetch_filter import FetchFilter
from image2struct.fetch.fetcher import ScrapeResult


class DateFetchFilter(FetchFilter):
    def __init__(self, max_instances_per_date: int) -> None:
        super().__init__("DateFetchFilter")
        self._date_set: Dict[str, int] = {}
        self._max_instances_per_date: int = max_instances_per_date
        self._lock: threading.Lock = threading.Lock()

    def filter(self, scrape_result: ScrapeResult) -> bool:
        """Check if the fetch meets the requirements.

        Args:
            scrape_result (ScrapeResult): The result of the fetch to check.

        Returns:
            bool: True if the fetch meets the requirements, False otherwise.
        """

        date_str: str = scrape_result.date.strftime("%Y-%m-%d")
        with self._lock:
            if date_str not in self._date_set:
                self._date_set[date_str] = 0
            if self._date_set[date_str] >= self._max_instances_per_date:
                return False
            else:
                self._date_set[date_str] += 1
                return True
