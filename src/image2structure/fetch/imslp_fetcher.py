from typing import Optional, List, Set
from dotenv import load_dotenv
from imslp import client
from mwclient.page import Page
from mwclient.image import Image

from image2structure.fetch.fetcher import Fetcher, ScrapeResult, DownloadError


import requests
import datetime
import os
import imslp
import urllib.parse
import bs4
import mwclient.page
import re


# Regular expression to extract the page count
IMSLP_REGEXP_PAGE_COUNT = re.compile(r"(\d+)\s*pp*\.*")
Image.MAX_IMAGE_PIXELS = 700000000


# Source: https://github.com/jlumbroso/imslp/blob/main/imslp/interfaces/scraping.py
def fetch_images_metadata(page: mwclient.page.Page) -> list:
    """
    Fetches the metadata associated with the images of an IMSLP page, as
    specified by a `mwclient.page.Page` object. This contains the download
    counter which is not available through the MediaWiki API and requires
    scraping to obtain.

    :param page:
    :return:
    """

    if page is None:
        return list()

    esc_title = urllib.parse.quote(page.base_title.replace(" ", "_"))

    u = "https://imslp.org/wiki/{}".format(esc_title)

    r = requests.get(u)
    if not r.ok:
        return list()

    s = bs4.BeautifulSoup(r.content, features="html.parser")

    images = []

    for f in page.images():

        f_title = f.base_title
        f_esc_title = urllib.parse.quote(f_title.replace(" ", "_"))

        # Hacky way of finding the relevant metadata
        t1 = s.find(attrs={"href": "/wiki/File:{}".format(f_esc_title)})
        t2 = s.find(attrs={"title": "File:{}".format(f_title)})

        if t1 is None and t2 is None:
            continue

        t = t1 or t2
        if t.text.strip() == "":
            continue

        page_count = None
        m = IMSLP_REGEXP_PAGE_COUNT.search(t.parent.text)
        if m is not None:
            try:
                page_count = int(m.group(1))
            except ValueError:
                pass

        file_id = int(t.text.replace("#", ""))

        # Fix image URL
        if f.imageinfo["url"][0] == "/":
            # URL is //imslp.org/stuff...
            f.imageinfo["url"] = "http:" + f.imageinfo["url"]

        images.append(
            {
                "id": file_id,
                "title": f_title,
                "url": f.imageinfo["url"],
                "page_count": page_count,
                "size": f.imageinfo.get("size"),
                "obj": f,
            }
        )

    return images


class ImslpFetcher(Fetcher):
    """Fetcher for music scores from IMSLP."""

    IMSLP_URL: str = "https://imslp.org/wiki/"
    LIST_WORKS_COUNT: int = 100

    def __init__(
        self,
        date_created_after: datetime.datetime,
        date_created_before: datetime.datetime,
        timeout: int,
        verbose: bool,
    ):
        super().__init__(date_created_after, date_created_before, timeout, verbose)
        self._page: int = 0
        load_dotenv()

        # Get the IMLSP client
        username: Optional[str] = os.environ.get("IMSLP_USERNAME")
        password: Optional[str] = os.environ.get("IMSLP_PASSWORD")
        assert username is not None
        assert password is not None
        self._client = client.ImslpClient(username=username, password=password)

        # metadata
        self._metadata: Optional[
            Set[imslp.interfaces.internal.HashablePageRecord]
        ] = None

    def notify_change_dates(self):
        self.change_internal_dates(days=1)

    def scrape(self, num_instances: int) -> List[ScrapeResult]:
        """
        Scrape num_instances data points.

        Args:
            num_instances: The number of instances to scrape.

        Returns:
            List[ScrapeResult]: The results of the scraping.

        Raises:
            ScrapeError: If the scraping fails.
        """
        results: List[ScrapeResult] = []

        while len(results) < num_instances:
            if self._metadata is None or len(self._metadata) == 0:
                if self._verbose:
                    print(
                        f"Fetching page {self._page} of IMSLP works ({self.LIST_WORKS_COUNT} per page)"
                    )
                self._metadata = set(
                    imslp.interfaces.internal.list_works(
                        start=self._page * self.LIST_WORKS_COUNT,
                        count=self.LIST_WORKS_COUNT,
                        cache=False,
                    )
                )
                self._page += 1

            while len(self._metadata) > 0 and len(results) < num_instances:
                result: imslp.interfaces.internal.HashablePageRecord = (
                    self._metadata.pop()
                )
                url: str = result["permlink"]
                if not url.startswith(self.IMSLP_URL):
                    continue

                name: str = url.replace(self.IMSLP_URL, "")
                page = Page(self._client._site, name)
                image_metadatas = fetch_images_metadata(page)

                for metadata in image_metadatas:
                    if "obj" not in metadata or metadata["obj"] is None:
                        continue

                    image: Image = metadata["obj"]
                    timestamp: str = image.imageinfo["timestamp"]
                    # Timestamp is formadted as "2021-10-10T10:10:10Z"
                    date: datetime.datetime = datetime.datetime.strptime(
                        timestamp, "%Y-%m-%dT%H:%M:%SZ"
                    )
                    if (
                        date < self._date_created_after
                        or date > self._date_created_before
                    ):
                        continue

                    file_name: str = image.imageinfo["url"].split("/")[-1]
                    if not file_name.endswith(".pdf"):
                        continue

                    total_num_pages: Optional[int] = metadata["page_count"]
                    if total_num_pages is None:
                        continue

                    if self._verbose:
                        print(
                            f"\t- Found {file_name} with {total_num_pages} pages created at {date}"
                        )
                    results.append(
                        ScrapeResult(
                            download_url=image.imageinfo["url"],
                            instance_name=file_name,
                            date=date,
                            additional_info={
                                "metadata": metadata,
                                "page_count": total_num_pages,
                            },
                        )
                    )

        return results

    def download(self, download_path: str, scrape_result: ScrapeResult) -> None:
        """
        Download the data from the given scrape result to the given destination path.

        Args:
            download_path: The path to save the downloaded data to.
            scrape_result: The result of the scraping.

        Returns:
            None

        Raises:
            DownloadError: If the download fails.
        """
        if not os.path.exists(download_path):
            raise DownloadError(f"Download path {download_path} does not exist.")

        if (
            "metadata" not in scrape_result.additional_info
            or "obj" not in scrape_result.additional_info["metadata"]
            or not isinstance(scrape_result.additional_info["metadata"]["obj"], Image)
        ):
            raise DownloadError("No metadata or invalid metadata in the scrape result.")

        image: Image = scrape_result.additional_info["metadata"]["obj"]
        file_path: str = os.path.join(download_path, scrape_result.instance_name)
        with open(file_path, "wb") as file:
            image.download(file)
