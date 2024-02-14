import pytest
from copy import deepcopy

from image2structure.filter.fetch_filters.github_fetch_filter import GitHubFetchFilter
from image2structure.filter.fetch_filters.fetch_filter import FetchFilterError
from image2structure.fetch.fetcher import ScrapeResult


class TestGitHubFetchFilter:

    def setup_method(self):
        self.fetch_filter = GitHubFetchFilter()

    def test_filter(self):
        # First scrape result
        scrape_result = ScrapeResult(
            instance_name="test",
            download_url="https://test.com",
            additional_info={"user": "test_user"},
        )
        assert self.fetch_filter.filter(scrape_result)

        # Different scrape result
        scrape_result_different = ScrapeResult(
            instance_name="test2",
            download_url="https://test2.com",
            additional_info={"user": "test_user_2"},
        )
        assert self.fetch_filter.filter(scrape_result_different)

        # Duplicate scrape result
        assert not self.fetch_filter.filter(deepcopy(scrape_result))

        # Duplicate user
        scrape_result_duplicate_user = ScrapeResult(
            instance_name="test3",
            download_url="https://test3.com",
            additional_info={"user": "test_user"},
        )
        assert not self.fetch_filter.filter(scrape_result_duplicate_user)

    def test_missing_user(self):
        scrape_result = ScrapeResult(
            instance_name="test",
            download_url="https://test.com",
            additional_info={},
        )
        with pytest.raises(FetchFilterError):
            self.fetch_filter.filter(scrape_result)
