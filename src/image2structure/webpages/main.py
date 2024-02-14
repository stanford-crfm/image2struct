import os
import datetime
import numpy as np
import argparse
import imagehash
from PIL import Image
from typing import Optional, Tuple, Dict, Any
import json
import time

from deployment.server import JekyllServer
from fetcher.search import clone_repo, search_github_repos
from fetcher.filter import filter_repo
from renderer.driver import save_random_screenshot, ScreenshotOptions

# Github won't allow more than 1000 results
# So we have to break down the search into multiple queries
GITHUB_MAX_RESULTS = 1000


class ImageFilter:
    """A class to filter images based on their content."""

    def __init__(
        self,
        hashfunc: imagehash.ImageHash = imagehash.average_hash,
        hash_size_white_imgs: int = 8,
        hash_size_other_imgs: int = 5,
        max_background_percentage: float = 95.0,
        max_white_percentage: float = 25.0,
        verbose: bool = False,
    ):
        """
        Args:
            hashfunc: The hash function to use for comparing images.
            hash_size_white_imgs: The hash size to use for white images.
            hash_size_other_imgs: The hash size to use for other images.
            max_background_percentage: The maximum percentage of white pixels for a page to be considered a landing page.
            max_white_percentage: The maximum percentage of white pixels for a page to be considered a landing page.
            verbose: Whether to print the progress.
        """
        self.hashfunc: imagehash.ImageHash = hashfunc
        self.hash_size_white_imgs: int = hash_size_white_imgs
        self.hash_size_other_imgs: int = hash_size_other_imgs
        self.max_background_percentage: float = max_background_percentage
        self.max_white_percentage: float = max_white_percentage
        self.verbose: bool = verbose
        self.hashes: set = set()

    def add_hash(
        self,
        image: Image,
        image_np: Optional[np.ndarray] = None,
        percentage: Optional[float] = None,
    ) -> Tuple[bool, str]:
        """Compute the hash of the image and add it to the set of hashes.

        Images with white background are hashed with a larger hash size to reduce the number of false positives.

        Args:
            image: The image to hash.
            image_np: The NumPy array of the image.
            percentage: The percentage of white pixels in the image.
        Returns:
            Whether the image was added to the set of hashes or already existed.
            Hash of the image.
        """
        # Compute the hash
        if image_np is None:
            image_np = np.array(image)
        if percentage is None:
            percentage = self.compute_percentage_of_white_pixels(image_np)
        if percentage > self.max_background_percentage:
            hash = self.hashfunc(image, hash_size=self.hash_size_white_imgs)
        else:
            hash = self.hashfunc(image, hash_size=self.hash_size_other_imgs)

        # Add the hash to the set
        if hash in self.hashes:
            return False, hash
        self.hashes.add(hash)
        return True, hash

    def compute_percentage_of_white_pixels(self, image_np: np.ndarray) -> float:
        """Compute the percentage of white pixels in the image."""
        # Convert the image to grayscale and convert to NumPy array
        image_array = image_np
        if len(image_array.shape) == 3:
            # Average 3 channels to get a single channel
            image_array = np.mean(image_array, axis=2)

        # Count the number of white pixels
        white_pixels = np.sum(image_array == 255)

        # Compute the percentage of white pixels
        percentage = (
            white_pixels / (image_array.shape[0] * image_array.shape[1])
        ) * 100
        return percentage

    def compute_percentage_of_most_frequent_color(self, image_np: np.ndarray) -> float:
        """Compute the percentage of the most frequent color in the image."""
        # Reshape the image to a 2D array where each row is a pixel
        pixels = image_np.reshape(-1, image_np.shape[2])

        # Find the most frequent color
        # Here we convert each pixel to a tuple to make them hashable, then use np.unique to find the most frequent one
        unique_colors, counts = np.unique(
            [tuple(row) for row in pixels], axis=0, return_counts=True
        )
        most_frequent_color = unique_colors[np.argmax(counts)]
        frequency_of_most_frequent = np.max(counts)

        # Calculate the total number of pixels
        total_pixels = image_np.shape[0] * image_np.shape[1]

        # Calculate the percentage of the most frequent color
        percentage = (frequency_of_most_frequent / total_pixels) * 100

        return percentage

    def check_image(self, image_path: str) -> Tuple[bool, Dict[str, Any]]:
        """Check if the image meets the requirements."""
        # Open the image
        image = Image.open(image_path)
        image_np = np.array(image)

        # Compute the percentage of white pixels
        white_pixels_ratio = self.compute_percentage_of_white_pixels(image_np)
        if white_pixels_ratio > self.max_background_percentage:
            if self.verbose:
                print(
                    f"{image_path} has too many white pixels ({white_pixels_ratio:.2f}%)."
                )
            return False, {}

        # Add the hash to the set
        added, hash = self.add_hash(image, image_np, white_pixels_ratio)
        if not added:
            if self.verbose:
                print(f"{image_path} already exists in the set of hashes.")
            return False, {}

        # Compute the percentage of the most frequent color
        most_frequent_color_ratio = self.compute_percentage_of_most_frequent_color(
            image_np
        )
        if most_frequent_color_ratio > self.max_background_percentage:
            if self.verbose:
                print(
                    f"{image_path} has too many pixels of the most frequent color ({most_frequent_color_ratio:.2f}%)."
                )
            return False, {}

        return True, {
            "white_pixels_ratio": white_pixels_ratio,
            "most_frequent_color_ratio": most_frequent_color_ratio,
            "hash": str(hash),
        }


def next_dates(
    date_start: datetime, date_next: datetime, args: argparse.Namespace
) -> Tuple[datetime.datetime, datetime.datetime]:
    """Get the next dates to search for repositories"""
    date_start = date_next
    date_next = date_start + datetime.timedelta(days=args.day_interval)
    if date_start > datetime.datetime.now():
        raise ValueError("The date_start is in the future")
    return date_start, date_next


def previous_dates(
    date_start: datetime, date_next: datetime, args: argparse.Namespace
) -> Tuple[datetime.datetime, datetime.datetime]:
    """Get the previous dates to search for repositories"""
    date_next = date_start
    date_start = date_next - datetime.timedelta(days=args.day_interval)
    if date_start < datetime.datetime.strptime(args.query_created_after, "%Y-%m-%d"):
        raise ValueError("The date_start is before the query_created_after")
    return date_start, date_next


def main(args):
    file_path: str = os.path.dirname(os.path.realpath(__file__))
    path = os.path.join(file_path, args.save_path)
    if args.query_language is not None:
        path = os.path.join(path, args.query_language)
    os.makedirs(path, exist_ok=True)
    os.makedirs(os.path.join(path, "repos"), exist_ok=True)
    os.makedirs(os.path.join(path, "images"), exist_ok=True)
    metadata_path = os.path.join(path, "metadata")
    os.makedirs(metadata_path, exist_ok=True)

    # Variables to store the results
    num_websites_collected: int = 0
    page: int = 1
    image_filter = ImageFilter(
        max_background_percentage=args.max_background_percentage,
        verbose=True,
    )

    users_set = set()
    repos_set = set()

    date_next = datetime.datetime.now()
    date_start = max(
        datetime.datetime.strptime(args.query_created_after, "%Y-%m-%d"),
        date_next - datetime.timedelta(days=args.day_interval),
    )
    num_repos_previous_page: int = args.query_limits

    while num_websites_collected < args.num_websites_desired:
        if (
            page * args.query_limits >= GITHUB_MAX_RESULTS
            or num_repos_previous_page < args.query_limits
        ):
            # Github won't allow more than 1000 results
            # So we have to break down the search into multiple queries
            # Also therer could be less than 1000 results
            date_start, date_next = previous_dates(date_start, date_next, args)
            page = 1
        else:
            page += 1
        print(f"Page {page} of the search results for {date_start} to {date_next}")

        # Search for GitHub pages repositories
        try:
            repos = search_github_repos(
                created_after=date_start,
                created_before=date_next,
                language=args.query_language,
                max_size_kb=args.query_max_size_kb,
                limits=args.query_limits,
                page=page,
                verbose=True,
            )
            num_repos_previous_page = len(repos)
        except Exception as e:
            if "422" in str(e):
                # We probably reached the end of the results for these dates
                print(f"Found error 422: {e}")
                date_start, date_next = previous_dates(date_start, date_next, args)
                page = 1
                time.sleep(30)  # Just in case we have a rate limit
                continue

        # Clone the repositories and start the Jekyll server
        for repo in enumerate(repos):
            print("\n" + "=" * 50)
            repo = repo[1]
            name = (
                repo["full_name"]
                .replace("/", "_")
                .replace(".github.io", "")
                .replace(".", "_")
            )
            repo_name = f"{num_websites_collected}_{name}"
            repo_path = os.path.join(path, "repos", repo_name)
            clone_url = repo["clone_url"]
            port = args.port
            metadata = {**repo, "repo_name": repo_name, "repo_path": repo_path}

            # Check if we did not already collect from this user
            user = repo["owner"]["login"]
            if user in users_set:
                print(f"Already collected from {user}. Skipping...")
                continue

            # Check if we have already tested this repo
            if name in repos_set:
                print(f"Alrwady tried the repo {name}")
                continue
            repos_set.add(name)

            print(f"Cloning {clone_url} to {repo_path}")
            try:
                clone_repo(clone_url, os.path.join(path, "repos"), repo_name)
            except Exception as e:
                print(f"Failed to clone the repository: {e}")
                os.system(f"rm -rf {repo_path}")  # Delete the repository
                continue

            # Filter the repository
            filter_success, filter_results = filter_repo(repo_path)
            if not filter_success:
                print(f"{repo_name} does not meet the requirements. Skipping...")
                os.system(f"rm -rf {repo_path}")  # Delete the repository
                continue
            metadata["file_filter_results"] = filter_results

            # Start the Jekyll server
            server = JekyllServer(repo_path, verbose=True, port=port)
            success: bool = server.start()

            if not success:
                print(f"Failed to start the server for {repo_name}. Skipping...")
                server.stop()
                os.system(f"rm -rf {repo_path}")
                continue

            # Take a screenshot of a random page
            image_path = os.path.join(path, "images", f"{repo_name}.png")
            try:
                scheenshot_options = ScreenshotOptions()
                scheenshot_options.num_actions_range = (0, args.max_num_actions)
                actions = save_random_screenshot(
                    image_path, port=port, options=scheenshot_options
                )
            except Exception as e:
                print(f"Failed to take a screenshot: {e}")
                server.stop()
                os.system(f"rm -rf {repo_path}")
                continue

            # Open the image and check for duplicates or images with too many white / background pixels
            image_filter_success, image_filter_results = image_filter.check_image(
                image_path
            )
            if not image_filter_success:
                os.remove(image_path)  # Delete the screenshot
                server.stop()
                os.system(f"rm -rf {repo_path}")
                continue
            metadata["image_filter_results"] = image_filter_results

            # Print the actions performed
            if actions:
                print(f"Actions performed to take the screenshot of {repo_name}:")
                for j, action in enumerate(actions):
                    print(f"{j + 1}. {action}")

            # Stop the Jekyll server
            server.stop()
            num_websites_collected += 1

            # Delete build files
            os.system(f"rm -rf {repo_path}/_site")
            os.system(f"rm -rf {repo_path}/.jekyll-cache")

            # Save the metadata
            users_set.add(user)
            metadata_file = os.path.join(metadata_path, f"{repo_name}.json")
            with open(metadata_file, "w") as f:
                # Format as a nice JSON file
                f.write(json.dumps(metadata, indent=4))


def parse_args():
    parser = argparse.ArgumentParser(description="Fetch and render GitHub pages")
    parser.add_argument(
        "--save_path",
        type=str,
        default="data",
        help="The path to save the repositories",
    )
    parser.add_argument(
        "--max_background_percentage",
        type=float,
        default=95.0,
        help="The maximum percentage of background pixels for a page to be considered a landing page",
    )
    parser.add_argument(
        "--max_num_actions",
        type=int,
        default=0,
        help="The maximum number of actions to take on a page",
    )
    parser.add_argument(
        "--query_language",
        type=str,
        default=None,
        help="The language to search for",
    )
    parser.add_argument(
        "--query_created_after",
        type=str,
        default="2023-07-01",
        help="The date to search for repositories created after",
    )
    parser.add_argument(
        "--query_max_size_kb",
        type=int,
        default=1000,
        help="The maximum size of the repository in KB",
    )
    parser.add_argument(
        "--query_limits",
        type=int,
        default=50,
        help="The maximum number of repositories to search for",
    )
    parser.add_argument(
        "--num_websites_desired",
        type=int,
        default=100,
        help="The number of websites to gather (after filtering)",
    )
    parser.add_argument(
        "--day_interval",
        type=int,
        default=1,
        help="The number of days between searches",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=4000,
        help="The port to use for the Jekyll server",
    )

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    main(args)
