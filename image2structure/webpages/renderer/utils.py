from typing import List
from selenium import webdriver
from selenium.webdriver.common.by import By


def find_clickable_elts(driver: webdriver.Chrome) -> List[str]:
    """Find all clickable elements on the page and return their urls

    Args:
        driver (webdriver.Chrome): The Chrome WebDriver

    Returns:
        List[str]: A list of URLs of all clickable elements
    """
    clickable_elements = driver.find_elements(
        By.XPATH, "//*[@href and (self::a or self::button)]"
    )
    clickable_ids = [
        element.get_attribute("href")
        for element in clickable_elements
        if element.is_displayed()
    ]
    return clickable_ids


def filter_clickable_elts(clickable_ids: List[str], url: str) -> List[str]:
    """Filter out the clickable elements that are not useful.
    This function removes duplicates, empty strings, non-URLs, and URLs that are not part of the website.

    Args:
        clickable_ids (List[str]): A list of URLs of all clickable elements
        url (str): The URL of the website. Usually "http://localhost:{port}".

    Returns:
        List[str]: A list of URLs of all useful clickable elements
    """
    # 1. Remove duplicates
    clickable_ids = list(set(clickable_ids))

    # 2. Remove empty strings
    clickable_ids = [id for id in clickable_ids if id]

    # 3. Remove non-URLs
    clickable_ids = [id for id in clickable_ids if id.startswith("http")]

    # 4. Remove URLs that are not part of the website
    clickable_ids = [id for id in clickable_ids if url in id]

    return clickable_ids
