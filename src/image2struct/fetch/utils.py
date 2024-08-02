import signal
from urllib.request import urlretrieve


from image2struct.fetch.fetcher import DownloadError


# Define the function to handle the timeout
def handler(signum, frame):
    raise DownloadError("Download timed out")


def download_file(download_url: str, filename: str, timeout_seconds: int = 30):
    """Download a file from the given URL to the given filename with a timeout.

    Args:
        download_url: The URL to download the file from.
        filename: The filename to save the downloaded file to.
        timeout_seconds: The timeout in seconds for the download.

    Raises:
        DownloadError: If the download fails.
    """
    try:
        # Set the timeout signal
        signal.signal(signal.SIGALRM, handler)
        signal.alarm(timeout_seconds)

        # Attempt to download the file
        urlretrieve(download_url, filename)
        signal.alarm(0)  # Reset the alarm
    except Exception as e:
        raise DownloadError(f"Download failed: {e}")
