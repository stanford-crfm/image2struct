from typing import Optional, Tuple, Dict, Any, Callable
from PIL import Image

import numpy as np
import imagehash
import threading

from image2structure.filter.rendering_filters.rendering_filter import RenderingFilter


class NonTrivialRenderingFilter(RenderingFilter):
    """A class to post process images.

    This post processor uses the ImageFilter class to filter images based on their content.
    It checks that images are not fully white and that they are not similar to other images.
    """

    def __init__(
        self,
        hashfunc: Callable = imagehash.average_hash,
        hash_size_white_imgs: int = 8,
        hash_size_other_imgs: int = 5,
        max_background_percentage: float = 95.0,
        threshold_white_percentage: float = 50.0,
        verbose: bool = False,
    ):
        """
        Args:
            hashfunc: The hash function to use for comparing images.
            hash_size_white_imgs: The hash size to use for white images.
            hash_size_other_imgs: The hash size to use for other images.
            max_background_percentage: The maximum percentage of white pixels for a page
                to be considered a landing page.
            threshold_white_percentage: The maximum percentage of white pixels for a page
                to be considered a landing page.
            verbose: Whether to print the progress.
        """
        super().__init__("NonTrivialRenderingFilter")
        self.hashfunc: Callable = hashfunc
        self.hash_size_white_imgs: int = hash_size_white_imgs
        self.hash_size_other_imgs: int = hash_size_other_imgs
        self.max_background_percentage: float = max_background_percentage
        self.threshold_white_percentage: float = threshold_white_percentage
        self.verbose: bool = verbose
        self.hashes: set = set()
        self._lock: threading.Lock = threading.Lock()

    def add_hash(
        self,
        image: Image.Image,
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
        if percentage > self.threshold_white_percentage:
            hash = self.hashfunc(image, hash_size=self.hash_size_white_imgs)
        else:
            hash = self.hashfunc(image, hash_size=self.hash_size_other_imgs)

        # Add the hash to the set
        with self._lock:
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
        # most_frequent_color = unique_colors[np.argmax(counts)]
        frequency_of_most_frequent = np.max(counts)

        # Calculate the total number of pixels
        total_pixels = image_np.shape[0] * image_np.shape[1]

        # Calculate the percentage of the most frequent color
        percentage = (frequency_of_most_frequent / total_pixels) * 100

        return percentage

    def check_and_accept_image(self, image_path: str) -> Tuple[bool, Dict[str, Any]]:
        """Check if the image meets the requirements and accept it if it does.

        Args:
            image_path (str): The path to the image to check.
            additional_args (Dict[str, Any]): Additional arguments to pass to the post

        Returns:
            bool: True if the image meets the requirements, False otherwise.
            Dict[str, Any]: Additional information about the image.
        """
        # Open the image
        image = Image.open(image_path)
        image_np = np.array(image)
        infos: Dict[str, Any] = {}

        # Compute the percentage of white pixels
        white_pixels_ratio = self.compute_percentage_of_white_pixels(image_np)
        infos["white_pixels_ratio"] = white_pixels_ratio
        if white_pixels_ratio > self.max_background_percentage:
            if self.verbose:
                print(
                    f"{image_path} has too many white pixels ({white_pixels_ratio:.2f}%)."
                )
            return False, {**infos, "reason": "white image"}

        # Add the hash to the set
        added, hash = self.add_hash(image, image_np, white_pixels_ratio)
        infos["hash"] = str(hash)
        if not added:
            if self.verbose:
                print(f"{image_path} already exists in the set of hashes.")
            return False, {**infos, "reason": "similar image"}

        # Compute the percentage of the most frequent color
        most_frequent_color_ratio = self.compute_percentage_of_most_frequent_color(
            image_np
        )
        infos["most_frequent_color_ratio"] = most_frequent_color_ratio
        if most_frequent_color_ratio > self.max_background_percentage:
            if self.verbose:
                print(
                    f"{image_path} has too many pixels of the most frequent color ({most_frequent_color_ratio:.2f}%)."
                )
            return False, {**infos, "reason": "constant image"}

        return True, infos
