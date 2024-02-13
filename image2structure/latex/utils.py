from typing import Optional, Tuple

from tqdm import tqdm
import signal
from urllib.request import urlretrieve


class MultiProgressBar:
    def __init__(self, bars):
        self.bars = {desc: tqdm(total=total, desc=desc) for desc, total in bars}

    def update(self, bar_id, amount):
        if bar_id in self.bars:
            self.bars[bar_id].update(amount)

    def set_total(self, bar_id, new_total):
        if bar_id in self.bars:
            self.bars[bar_id].total = new_total
            self.bars[bar_id].refresh()  # Refresh to display the new total immediately

    def close(self):
        for bar in self.bars.values():
            bar.close()


# Define the function to handle the timeout
def handler(signum, frame):
    raise Exception("Download timed out")


# Function to download the file with exception handling and timeout
def download_file(download_url, filename, timeout_seconds=30):
    try:
        # Set the timeout signal
        signal.signal(signal.SIGALRM, handler)
        signal.alarm(timeout_seconds)

        # Attempt to download the file
        urlretrieve(download_url, filename)
        signal.alarm(0)  # Reset the alarm
        return True
    except Exception as e:
        return False


def read_latex_file(path: str) -> Tuple[Optional[str], bool]:
    try:
        with open(path, "r") as f:
            try:
                tex_code = f.read()
                return tex_code, True
            except UnicodeDecodeError:
                return None, False
    except FileNotFoundError:
        return None, False
