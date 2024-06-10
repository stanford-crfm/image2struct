import argparse
import os
import time
import uuid
import json
import requests
import tarfile
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from urllib.parse import urlparse
from datetime import datetime
from typing import List


# List of URLs to be processed
urls = [
    "https://www.nytimes.com",
    "https://www.bbc.com",
    "https://www.wikipedia.org",
    "https://www.github.com",
    "https://www.reddit.com",
    "https://www.twitter.com",
    "https://www.facebook.com",
    "https://www.instagram.com",
    "https://www.linkedin.com",
    "https://www.youtube.com",
    "https://www.amazon.com",
    "https://www.apple.com",
    "https://www.microsoft.com",
    "https://www.ibm.com",
    "https://www.google.com",
    "https://www.yahoo.com",
    "https://www.bing.com",
    "https://www.duckduckgo.com",
    "https://www.netflix.com",
    "https://www.hulu.com",
    "https://www.disneyplus.com",
    "https://www.imdb.com",
    "https://www.metacritic.com",
    "https://www.rottentomatoes.com",
    "https://www.nationalgeographic.com",
    "https://www.nasa.gov",
    "https://www.cnn.com",
    "https://www.foxnews.com",
    "https://www.bloomberg.com",
    "https://www.cnbc.com",
    "https://www.forbes.com",
    "https://www.businessinsider.com",
    "https://www.techcrunch.com",
    "https://www.engadget.com",
    "https://www.arstechnica.com",
    "https://www.lifehacker.com",
    "https://www.theguardian.com",
    "https://www.independent.co.uk",
    "https://www.buzzfeed.com",
    "https://www.vox.com",
    "https://www.theverge.com",
    "https://www.wired.com",
    "https://www.polygon.com",
    "https://www.gamespot.com",
    "https://www.kotaku.com",
    "https://www.twitch.tv",
    "https://www.netflix.com",
    "https://www.hbo.com",
    "https://www.showtime.com",
    "https://www.cbs.com",
    "https://www.abc.com",
    "https://www.nbc.com",
    "https://www.criterion.com",
    "https://www.imdb.com",
    "https://www.rottentomatoes.com",
    "https://www.metacritic.com",
    "https://www.pitchfork.com",
    "https://www.billboard.com",
    "https://www.rollingstone.com",
    "https://www.npr.org",
    "https://www.bbc.co.uk",
    "https://www.thetimes.co.uk",
    "https://www.telegraph.co.uk",
    "https://www.guardian.co.uk",
    "https://www.independent.co.uk",
    "https://www.economist.com",
    "https://www.ft.com",
    "https://www.wsj.com",
    "https://www.nature.com",
    "https://www.scientificamerican.com",
    "https://www.newscientist.com",
    "https://www.sciencedaily.com",
    "https://www.space.com",
    "https://www.livescience.com",
    "https://www.popsci.com",
    "https://www.healthline.com",
    "https://www.webmd.com",
    "https://www.mayoclinic.org",
    "https://www.nih.gov",
    "https://www.cdc.gov",
    "https://www.who.int",
    "https://www.un.org",
    "https://www.nationalgeographic.com",
    "https://www.worldreallife.org",
    "https://www.greenpeace.org",
    "https://www.nrdc.org",
    "https://www.sierraclub.org",
    "https://www.amnesty.org",
    "https://www.hrw.org",
    "https://www.icrc.org",
    "https://www.redcross.org",
    "https://www.unicef.org",
    "https://www.savethechildren.org",
    "https://www.doctorswithoutborders.org",
    "https://www.wikimedia.org",
    "https://www.archive.org",
    "https://www.opendemocracy.net",
    "https://www.projectgutenberg.org",
    "https://www.khanacademy.org",
    "https://www.codecademy.com",
]


def get_parser():
    parser = argparse.ArgumentParser(description="Process images from a directory")
    parser.add_argument(
        "--subset",
        type=str,
        default="wild",
        help="The subset of the dataset",
    )
    parser.add_argument(
        "--save_dir",
        type=str,
        help="The directory to save the processed images",
        default="data/webpage",
    )
    parser.add_argument(
        "--width",
        type=int,
        default=1920,
        help="The width of the browser window",
    )
    parser.add_argument(
        "--height",
        type=int,
        default=1080,
        help="The height of the browser window",
    )
    parser.add_argument(
        "--delay",
        type=int,
        default=5,
        help="The delay in seconds before taking a screenshot",
    )
    return parser


def setup_directories(save_dir: str, subset: str):
    os.makedirs(os.path.join(save_dir, subset, "metadata"), exist_ok=True)
    os.makedirs(os.path.join(save_dir, subset, "assets"), exist_ok=True)
    os.makedirs(os.path.join(save_dir, subset, "images"), exist_ok=True)
    os.makedirs(os.path.join(save_dir, subset, "structures"), exist_ok=True)


def is_element_in_viewport(driver, element):
    """Check if an element is in the viewport"""
    return driver.execute_script(
        "var rect = arguments[0].getBoundingClientRect();"
        "return (rect.top >= 0 && rect.left >= 0 && rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) && rect.right <= (window.innerWidth || document.documentElement.clientWidth));",  # noqa: E501
        element,
    )


def save_visible_images(driver: webdriver.Chrome, url: str, temp_assets_dir: str):
    # Extract image URLs and their positions using Selenium
    img_elements = driver.find_elements(By.TAG_NAME, "img")
    img_urls = []

    for img in img_elements:
        src = img.get_attribute("src")
        if src and is_element_in_viewport(driver, img):
            img_urls.append(src)

    # Download only the visible images
    for img_url in img_urls:
        try:
            img_response = requests.get(img_url)
            img_response.raise_for_status()
            img_name = os.path.basename(urlparse(img_url).path)
            img_file_path = os.path.join(temp_assets_dir, img_name)
            with open(img_file_path, "wb") as img_file:
                img_file.write(img_response.content)
        except requests.RequestException as e:
            print(f"Failed to download {img_url}: {e}")


def capture_screenshot(
    url: str,
    uuid_str: str,
    save_dir: str,
    subset: str,
    width: int = 1920,
    height: int = 1080,
    delay: int = 0,
):
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()), options=options
    )

    try:
        driver.set_window_size(width, height)
        driver.get(url)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        time.sleep(delay)  # Add delay here
        screenshot_path = os.path.join(save_dir, subset, "images", f"{uuid_str}.png")
        driver.save_screenshot(screenshot_path)

        # Save images that appear in the viewport
        temp_assets_dir = os.path.join(save_dir, subset, "assets", uuid_str)
        os.makedirs(temp_assets_dir, exist_ok=True)
        save_visible_images(driver, url, temp_assets_dir)
    finally:
        driver.quit()
    return temp_assets_dir


def compress_assets(temp_assets_dir: str, uuid_str: str, save_dir: str, subset: str):
    compressed_file_path = os.path.join(
        save_dir, subset, "structures", f"{uuid_str}.tar.gz"
    )
    with tarfile.open(compressed_file_path, "w:gz") as tar:
        tar.add(temp_assets_dir, arcname=os.path.basename(temp_assets_dir))
    # Remove the temporary assets directory after compression
    for root, dirs, files in os.walk(temp_assets_dir, topdown=False):
        for name in files:
            os.remove(os.path.join(root, name))
        for name in dirs:
            os.rmdir(os.path.join(root, name))
    os.rmdir(temp_assets_dir)


def save_metadata(url: str, uuid_str: str, save_dir: str, subset: str):
    metadata = {
        "url": url,
        "instance_name": url.replace("https://www.", ""),
        "date_scrapped": datetime.now().isoformat(),
        "uuid": uuid_str,
        "category": "real",
        "additional_info": {},
        "assets": [],
    }
    metadata_file_path = os.path.join(save_dir, subset, "metadata", f"{uuid_str}.json")
    with open(metadata_file_path, "w") as json_file:
        json.dump(metadata, json_file, indent=4)


def process_urls(
    urls: List[str],
    save_dir: str,
    subset: str,
    width: int = 1920,
    height: int = 1080,
    delay: int = 0,
):
    setup_directories(save_dir, subset)

    for url in urls:
        # Generate a UUID grounded by the URL
        url_uuid = str(uuid.uuid5(uuid.NAMESPACE_URL, url))
        uuid_path = os.path.join(save_dir, subset, "images", f"{url_uuid}.png")

        # Skip if already processed
        if os.path.exists(uuid_path):
            print(f"URL {url} has already been processed. Skipping.")
            continue

        print(f"Processing {url} with UUID {url_uuid}")
        temp_assets_dir = capture_screenshot(
            url, url_uuid, save_dir, subset, width, height, delay
        )
        compress_assets(temp_assets_dir, url_uuid, save_dir, subset)
        save_metadata(url, url_uuid, save_dir, subset)
        print(f"Processed {url} and saved assets to {uuid_path}")


if __name__ == "__main__":
    parser = get_parser()
    args = parser.parse_args()
    process_urls(urls, args.save_dir, args.subset, args.width, args.height, args.delay)
