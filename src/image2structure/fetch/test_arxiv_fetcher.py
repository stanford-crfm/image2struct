import datetime
import os
import shutil
import pytest

from image2structure.fetch.arxiv_fetcher import ArxivFetcher
from image2structure.fetch.fetcher import ScrapeResult, DownloadError


class TestArxivFetcher:
    def setup_method(self, method):
        self.data_path = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "test_data"
        )
        os.makedirs(self.data_path, exist_ok=True)

        # Make fetcher
        self.fetcher = ArxivFetcher(
            # Set fixed dates to avoid flakiness
            date_created_after=datetime.datetime(2023, 1, 1),
            date_created_before=datetime.datetime(2023, 2, 1),
            subcategory="econ",
            timeout=30,
            verbose=False,
        )

    def teardown_method(self, method):
        shutil.rmtree(self.data_path)

    def test_scrape_runs(self):
        results = self.fetcher.scrape(1)
        assert len(results) == 1

    def test_scrape_count(self):
        results = self.fetcher.scrape(18)
        assert len(results) == 18

    def test_download_runs(self):
        results = self.fetcher.scrape(1)

        # Download the first result
        self.fetcher.download(self.data_path, results[0])
        file_path: str = os.path.join(self.data_path, results[0].instance_name)
        assert os.path.exists(file_path)

    def test_download_invalid_path(self):
        with pytest.raises(DownloadError):
            result = ScrapeResult(
                download_url="https://arxiv.org/src/fake",
                instance_name="fake_paper",
                additional_info={},
            )
            self.fetcher.download("invalid_path", result)
        assert not os.path.exists("invalid_path/fake_paper")
