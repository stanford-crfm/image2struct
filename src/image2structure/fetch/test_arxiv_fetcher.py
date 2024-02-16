import datetime
import os
import shutil

from image2structure.fetch.arxiv_fetcher import ArxivFetcher


class TestArxivFetcher:
    def setup_method(self, method):
        self.data_path = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "test_data"
        )
        os.makedirs(self.data_path, exist_ok=True)

    def teardown_method(self, method):
        shutil.rmtree(self.data_path)

    def test_scrape_runs(self):
        fetcher = ArxivFetcher(
            # Set fixed dates to avoid flakiness
            date_created_after=datetime.datetime(2021, 1, 1, 0, 0, 0),
            date_created_before=datetime.datetime(2021, 1, 2, 6, 0, 0),
            subcategory="cs",
            timeout=30,
            verbose=False,
        )
        results = fetcher.scrape(1)
        assert len(results) == 1

    # def test_scrape_invalid_subcategory(self):
    #     fetcher = ArxivFetcher(
    #         # Set fixed dates to avoid flakiness
    #         date_created_after=datetime.datetime(2021, 1, 1),
    #         date_created_before=datetime.datetime(2022, 1, 1),
    #         subcategory="test",
    #         timeout=30,
    #         verbose=False,
    #     )
    #     with pytest.raises(ScrapeError):
    #         fetcher.scrape(1)

    def test_scrape_count(self):
        fetcher = ArxivFetcher(
            # Set fixed dates to avoid flakiness
            date_created_after=datetime.datetime(2023, 1, 1),
            date_created_before=datetime.datetime(2023, 2, 1),
            subcategory="econ",
            timeout=30,
            verbose=False,
        )
        results = fetcher.scrape(18)
        assert len(results) == 18

    def test_download_runs(self):
        fetcher = ArxivFetcher(
            # Set fixed dates to avoid flakiness
            date_created_after=datetime.datetime(2023, 1, 1),
            date_created_before=datetime.datetime(2023, 2, 1),
            subcategory="econ",
            timeout=30,
            verbose=False,
        )
        results = fetcher.scrape(1)

        # Download the first result
        fetcher.download(self.data_path, results[0])
        file_path: str = os.path.join(self.data_path, results[0].instance_name)
        assert os.path.exists(file_path)

    # def test_download_invalid_path(self):
    #     self.fetcher = GitHubFetcher(
    #         # All parameters are irrelevant except for the timeout
    #         date_created_after=datetime.datetime(2021, 1, 1),
    #         date_created_before=datetime.datetime(2022, 1, 1),
    #         subcategory="html",
    #         timeout=30,
    #         max_size_kb=1,
    #         verbose=False,
    #     )
    #     with pytest.raises(DownloadError):
    #         result = ScrapeResult(
    #             download_url="https://github.com/fakeuser/fakerepo",
    #             instance_name="fakerepo",
    #             additional_info={},
    #         )
    #         self.fetcher.download("invalid_path", result)
    #     assert not os.path.exists("invalid_path/fake_repo")
