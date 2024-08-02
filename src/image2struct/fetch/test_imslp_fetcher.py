import pytest
import datetime
import os

from image2struct.fetch.imslp_fetcher import ImslpFetcher
from image2struct.fetch.fetcher import DownloadError, ScrapeResult


class TestImslpFetcher:
    def setup_method(self, method):
        self.fetcher = ImslpFetcher(
            # Set large dates as we cannot filter on precise dates,
            # so if the range is too small it might take a long time to get results
            date_created_after=datetime.datetime(2010, 1, 1),
            date_created_before=datetime.datetime(2020, 1, 1),
            timeout=30,
            verbose=False,
        )

    def test_scrape_runs(self):
        results = self.fetcher.scrape(1)
        assert len(results) == 1

    def test_download_runs(self):
        results = self.fetcher.scrape(1)

        # Download the first result
        tmp_path = os.path.dirname(__file__)
        self.fetcher.download(tmp_path, results[0])
        pdf_path: str = os.path.join(tmp_path, results[0].instance_name)
        assert os.path.exists(pdf_path)
        os.remove(pdf_path)

    def test_download_invalid_path(self):
        with pytest.raises(DownloadError):
            result = ScrapeResult(
                download_url="http://imslp.org/images/3/3d/fake.pdf",
                instance_name="fake.pdf",
                additional_info={"page_count": 10},
                date=datetime.datetime.now(),
            )
            self.fetcher.download("invalid_path", result)
        assert not os.path.exists("invalid_path/fake.pdf")
