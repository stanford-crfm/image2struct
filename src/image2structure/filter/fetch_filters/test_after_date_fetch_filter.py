import datetime

from image2structure.filter.fetch_filters.after_date_fetch_filter import (
    AfterDateFetchFilter,
)
from image2structure.fetch.fetcher import ScrapeResult


class TestAfterDateFetchFilter:
    def setup_method(self):
        self.fetch_filter = AfterDateFetchFilter(datetime.datetime(2022, 1, 1))

    def test_filter(self):
        # First scrape result
        scrape_result = ScrapeResult(
            instance_name="test",
            download_url="https://test.com",
            date=datetime.datetime(2023, 1, 1),
            additional_info={"user": "test_user"},
        )
        assert self.fetch_filter.filter(scrape_result)

        # Different scrape result - before the filter date
        scrape_result_different = ScrapeResult(
            instance_name="test2",
            download_url="https://test2.com",
            date=datetime.datetime(2021, 1, 1),
            additional_info={"user": "test_user_2"},
        )
        assert not self.fetch_filter.filter(scrape_result_different)
