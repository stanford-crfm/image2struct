import datetime

from image2structure.filter.fetch_filters.date_fetch_filter import DateFetchFilter
from image2structure.fetch.fetcher import ScrapeResult


class TestDateFetchFilter:
    def setup_method(self):
        self.fetch_filter = DateFetchFilter(max_instances_per_date=2)

    def test_filter(self):
        # First scrape result
        scrape_result = ScrapeResult(
            instance_name="test",
            download_url="https://test.com",
            date=datetime.datetime(2022, 1, 1),
            additional_info={"user": "test_user"},
        )
        assert self.fetch_filter.filter(scrape_result)

        # Different scrape result - same date
        scrape_result_different = ScrapeResult(
            instance_name="test2",
            download_url="https://test2.com",
            date=datetime.datetime(2022, 1, 1),
            additional_info={"user": "test_user_2"},
        )
        assert self.fetch_filter.filter(scrape_result_different)

        # Different scrape result - same date again
        scrape_result_different_2 = ScrapeResult(
            instance_name="test3",
            download_url="https://test3.com",
            date=datetime.datetime(2022, 1, 1),
            additional_info={"user": "test_user_3"},
        )
        assert not self.fetch_filter.filter(scrape_result_different_2)

        # Different scrape result - different date
        scrape_result_different_date = ScrapeResult(
            instance_name="test4",
            download_url="https://test4.com",
            date=datetime.datetime(2022, 1, 2),
            additional_info={"user": "test_user_4"},
        )
        assert self.fetch_filter.filter(scrape_result_different_date)
