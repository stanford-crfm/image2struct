import pytest
import datetime
import os
import shutil

from image2structure.fetch.github_fetcher import GitHubFetcher
from image2structure.fetch.fetcher import ScrapeError, DownloadError, ScrapeResult


class TestGitHubFetcher:
    def test_scrape_runs(self):
        fetcher = GitHubFetcher(
            # Set fixed dates to avoid flakiness
            date_created_after=datetime.datetime(2021, 1, 1),
            date_created_before=datetime.datetime(2022, 1, 1),
            language="html",
            timeout=30,
            max_size_kb=1,
            verbose=False,
        )
        results = fetcher.scrape(1)
        assert len(results) == 1

    def test_scrape_invalid_language(self):
        fetcher = GitHubFetcher(
            # Set fixed dates to avoid flakiness
            date_created_after=datetime.datetime(2021, 1, 1),
            date_created_before=datetime.datetime(2022, 1, 1),
            language="test",
            timeout=30,
            max_size_kb=1,
            verbose=False,
        )
        with pytest.raises(ScrapeError):
            fetcher.scrape(1)

    def test_scrape_count(self):
        fetcher = GitHubFetcher(
            # Set fixed dates to avoid flakiness
            date_created_after=datetime.datetime(2023, 1, 1),
            date_created_before=datetime.datetime(2023, 2, 1),
            language="css",
            timeout=30,
            max_size_kb=10,
            verbose=False,
        )
        results = fetcher.scrape(100)
        assert len(results) == 46

    def test_download_runs(self):
        fetcher = GitHubFetcher(
            # Set fixed dates to avoid flakiness
            date_created_after=datetime.datetime(2021, 1, 1),
            date_created_before=datetime.datetime(2021, 1, 2),
            language="html",
            timeout=30,
            max_size_kb=1,
            verbose=False,
        )
        results = fetcher.scrape(1)

        # Download the first result
        tmp_path = os.path.dirname(__file__)
        fetcher.download(tmp_path, results[0])
        repo_path: str = os.path.join(tmp_path, results[0].instance_name)
        assert os.path.exists(repo_path)
        shutil.rmtree(repo_path)

    def test_download_invalid_path(self):
        self.fetcher = GitHubFetcher(
            # All parameters are irrelevant except for the timeout
            date_created_after=datetime.datetime(2021, 1, 1),
            date_created_before=datetime.datetime(2022, 1, 1),
            language="html",
            timeout=30,
            max_size_kb=1,
            verbose=False,
        )
        with pytest.raises(DownloadError):
            result = ScrapeResult(
                download_url="https://github.com/fakeuser/fakerepo",
                instance_name="fakerepo",
                additional_info={},
                date=datetime.datetime.now(),
            )
            self.fetcher.download("invalid_path", result)
        assert not os.path.exists("invalid_path/fake_repo")
