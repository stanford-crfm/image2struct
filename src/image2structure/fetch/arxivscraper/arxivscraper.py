"""
A python program to retreive recrods from ArXiv.org in given
categories and specific date range.

Author: Mahdi Sadjadi (sadjadi.seyedmahdi[AT]gmail[DOT]com).
"""

from __future__ import print_function
import xml.etree.ElementTree as ET
import datetime
import time
from typing import Dict, List, Any, Optional

from urllib.request import urlopen
from urllib.error import HTTPError

from image2structure.fetch.arxivscraper.constants import OAI, ARXIV, BASE


class Record(object):
    """
    A class to hold a single record from ArXiv
    Each records contains the following properties:

    object should be of xml.etree.ElementTree.Element.
    """

    def __init__(self, xml_record):
        """if not isinstance(object,ET.Element):
        raise TypeError("")"""
        self.xml = xml_record
        self.id = self._get_text(ARXIV, "id")
        self.url = "https://arxiv.org/abs/" + self.id
        self.title = self._get_text(ARXIV, "title")
        self.abstract = self._get_text(ARXIV, "abstract")
        self.cats = self._get_text(ARXIV, "categories")
        self.created = self._get_text(ARXIV, "created")
        self.updated = self._get_text(ARXIV, "updated")
        self.doi = self._get_text(ARXIV, "doi")
        self.authors = self._get_authors()
        self.affiliation = self._get_affiliation()

    def _get_text(self, namespace: str, tag: str) -> str:
        """Extracts text from an xml field"""
        try:
            return (
                self.xml.find(namespace + tag).text.strip().lower().replace("\n", " ")
            )
        except Exception:
            return ""

    def _get_name(self, parent, attribute) -> str:
        """Extracts author name from an xml field"""
        try:
            return parent.find(ARXIV + attribute).text.lower()
        except Exception:
            return "n/a"

    def _get_authors(self) -> List:
        """Extract name of authors"""
        authors_xml = self.xml.findall(ARXIV + "authors/" + ARXIV + "author")
        last_names = [self._get_name(author, "keyname") for author in authors_xml]
        first_names = [self._get_name(author, "forenames") for author in authors_xml]
        full_names = [a + " " + b for a, b in zip(first_names, last_names)]
        return full_names

    def _get_affiliation(self) -> List[Any]:
        """Extract affiliation of authors"""
        authors = self.xml.findall(ARXIV + "authors/" + ARXIV + "author")
        try:
            affiliation = [
                author.find(ARXIV + "affiliation").text.lower() for author in authors
            ]
            return affiliation
        except Exception:
            return []

    def output(self) -> Dict[str, Any]:
        """Data for each paper record"""
        d = {
            "title": self.title,
            "id": self.id,
            "abstract": self.abstract,
            "categories": self.cats,
            "doi": self.doi,
            "created": self.created,
            "updated": self.updated,
            "authors": self.authors,
            "affiliation": self.affiliation,
            "url": self.url,
        }
        return d


class Scraper(object):
    """
    A class to hold info about attributes of scraping,
    such as date range, categories, and number of returned
    records. If `from` is not provided, the first day of
    the current month will be used. If `until` is not provided,
    the current day will be used.

    Paramters
    ---------
    category: str
        The category of scraped records
    data_from: str
        starting date in format 'YYYY-MM-DD'. Updated eprints are included even if
        they were created outside of the given date range. Default: first day of current month.
    date_until: str
        final date in format 'YYYY-MM-DD'. Updated eprints are included even if
        they were created outside of the given date range. Default: today.
    t: int
        Waiting time between subsequent calls to API, triggred by Error 503.
    timeout: int
        Timeout in seconds after which the scraping stops. Default: 300s
    filter: dictionary
        A dictionary where keys are used to limit the saved results. Possible keys:
        subcats, author, title, abstract. See the example, below.

    Example:
    Returning all eprints from `stat` category:

    ```
        import arxivscraper.arxivscraper as ax
        scraper = ax.Scraper(category='stat',date_from='2017-12-23',date_until='2017-12-25',t=10,
                 filters={'affiliation':['facebook'],'abstract':['learning']})
        output = scraper.scrape()
    ```
    """

    def __init__(
        self,
        category: str,
        time_between_requests: float = 5.0,
        time_between_503: float = 5.0,
        timeout: int = 300,
        filters: Dict[str, str] = {},
    ):
        self.cat = str(category)
        self.time_between_requests = time_between_requests
        self.time_between_503 = time_between_503
        self.timeout = timeout
        self.filters = filters
        if not self.filters:
            self.append_all = True
        else:
            self.append_all = False
            self.keys = filters.keys()
        self._last_request: (
            datetime.datetime
        ) = datetime.datetime.now() - datetime.timedelta(
            seconds=self.time_between_requests
        )

    def scrape(
        self, date_from: datetime.datetime, date_until: datetime.datetime
    ) -> List[Dict[str, Any]]:
        """
        Fetch the records from ArXiv.org using Open Archives Initiative (OAI) protocol.

        Args:
            date_from: datetime.datetime
                starting date in format 'YYYY-MM-DD'. Updated eprints are included even if
                they were created outside of the given date range.
            date_until: datetime.datetime
                final date in format 'YYYY-MM-DD'. Updated eprints are included even if
                they were created outside of the given date range.

        Returns:
            List[Dict]: The results of the scraping.

        Raises:
            ScrapeError: If the scraping fails.
        """
        elapsed = 0.0
        print(
            f"fetching records in  {self.cat} category from "
            f"{date_from.strftime('%Y-%m-%d')} to {date_until.strftime('%Y-%m-%d')}..."
        )

        # Build the url
        url = (
            BASE
            + "from="
            + date_from.strftime("%Y-%m-%d")
            + "&until="
            + date_until.strftime("%Y-%m-%d")
            + "&metadataPrefix=arXiv&set=%s" % self.cat
        )
        accepted_records: List[Dict[str, Any]] = []
        k = 1

        ty: float
        tx: float = time.time()
        while True:
            print("\t- fetching up to ", 1000 * k, "records...")
            print("\t\t-> to url: ", url)
            previous_num_records: int = len(accepted_records)
            try:
                time_since_last_request: datetime.timedelta = (
                    datetime.datetime.now() - self._last_request
                )
                if time_since_last_request.total_seconds() < self.time_between_requests:
                    time.sleep(
                        self.time_between_requests
                        - time_since_last_request.total_seconds()
                    )
                response = urlopen(url)
                self._last_request = datetime.datetime.now()
            except HTTPError as e:
                if e.code == 503:
                    to = int(e.hdrs.get("retry-after", self.time_between_503))  # type: ignore
                    print("\t\t-> Got 503. Retrying after {0:d} seconds.".format(to))
                    time.sleep(to)
                    continue
                else:
                    raise
            k += 1
            xml = response.read()
            root = ET.fromstring(xml)
            records = root.findall(OAI + "ListRecords/" + OAI + "record")
            for record in records:
                elt: Optional[ET.Element] = record.find(OAI + "metadata")
                assert elt is not None
                meta = elt.find(ARXIV + "arXiv")
                rec: Dict[str, Any] = Record(meta).output()
                if self.append_all:
                    accepted_records.append(rec)
                else:
                    save_record = False
                    for key in self.keys:
                        for word in self.filters[key]:
                            if word.lower() in rec[key]:
                                save_record = True

                    if save_record:
                        accepted_records.append(rec)

            print(
                "\t\t-> fetched ",
                len(accepted_records) - previous_num_records,
                " records.",
            )

            try:
                elt_recs: Optional[ET.Element] = root.find(OAI + "ListRecords")
                assert elt_recs is not None
                token = elt_recs.find(OAI + "resumptionToken")
            except Exception:
                # No more results
                break
            if token is None or token.text is None:
                break
            else:
                url = BASE + "resumptionToken=%s" % token.text

            ty = time.time()
            elapsed += ty - tx
            if elapsed >= self.timeout:
                break
            else:
                tx = time.time()

        return accepted_records


def search_all(df, col, *words):
    """
    Return a sub-DataFrame of those rows whose Name column match all the words.
    source: https://stackoverflow.com/a/22624079/3349443
    """
    import numpy as np

    return df[np.logical_and.reduce([df[col].str.contains(word) for word in words])]
