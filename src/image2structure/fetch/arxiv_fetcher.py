from typing import List, Dict, Any

from image2structure.fetch.arxivscraper.arxivscraper import Scraper
import datetime
import os
import math

from image2structure.fetch.fetcher import Fetcher, ScrapeResult
from image2structure.fetch.utils import download_file


class ArxivFetcher(Fetcher):

    DOWNLOAD_URL_BASE: str = "https://arxiv.org/src/"

    def __init__(
        self,
        date_created_after: datetime.datetime,
        date_created_before: datetime.datetime,
        subcategory: str,
        timeout: int,
        verbose: bool,
    ):
        super().__init__(date_created_after, date_created_before, timeout, verbose)
        self._subcategory = subcategory

        # Store the remaining results as we cannot fetch X results but only
        # results from a given date range
        self._remaining_results: List[Dict[str, str]] = []

        # Scraper
        self._scraper = Scraper(
            category=self._subcategory,
            timeout=self._timeout,
        )

        # Set the estimate for the number of papers per day
        # This is used to determine how many days to scrape in the next query
        # TODO: Use EMA for this
        self._estimate_paper_per_day: float = 100.0
        self._estimate_day_count: int = 1

    def scrape(self, num_instances: int) -> List[ScrapeResult]:
        """
        Scrape the data from the given scrape configuration.

        Args:
            scrape_config: The configuration for the scraping.

        Returns:
            List[ScrapeResult]: The results of the scraping.

        Raises:
            ScrapeError: If the scraping fails.
        """

        while len(self._remaining_results) < num_instances:
            num_papers_needed: int = num_instances - len(self._remaining_results)
            estimate_num_days: int = max(
                1, int(math.ceil(num_papers_needed / self._estimate_paper_per_day))
            )
            # Need to scrape some more
            self.change_internal_dates(days=estimate_num_days)
            outputs: List[Dict[str, Any]] = self._scraper.scrape(
                date_from=self._date_created_after_internal,
                date_until=self._date_created_before_internal,
            )

            # Update the estimate
            self._estimate_paper_per_day = (
                self._estimate_paper_per_day * self._estimate_day_count + len(outputs)
            ) / (self._estimate_day_count + estimate_num_days)
            self._estimate_day_count += estimate_num_days

            if len(outputs) == 0:
                continue

            assert isinstance(outputs[0], dict)
            self._remaining_results.extend(outputs)

        # Return the first num_instances results
        results: List[ScrapeResult] = []
        for output in self._remaining_results[:num_instances]:
            url: str = output["url"]
            doi: str = url.split("/")[-1]
            download_url: str = self.DOWNLOAD_URL_BASE + doi
            date_str = (
                output["updated"]
                if len(output.get("updated", "")) > 0
                else output["created"]
            )
            results.append(
                ScrapeResult(
                    download_url=download_url,
                    instance_name=doi + ".tar.gz",
                    date=datetime.datetime.strptime(date_str, "%Y-%m-%d"),
                    additional_info=output,
                )
            )

        # Remove the results we just used
        self._remaining_results = self._remaining_results[num_instances:]
        print("Finished scraping")

        return results

    def download(self, destination_path: str, scrape_result: ScrapeResult) -> None:
        """
        Download the data from the given scrape result to the given destination path.

        Args:
            destination_path: The path to save the downloaded data to.
            scrape_result: The result of the scraping.

        Returns:
            None

        Raises:
            DownloadError: If the download fails.
        """
        download_file(
            download_url=scrape_result.download_url,
            filename=os.path.join(destination_path, scrape_result.instance_name),
            timeout_seconds=self._timeout,
        )
