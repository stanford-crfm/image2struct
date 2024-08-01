from PIL import Image

import imagehash
import os
import shutil
import numpy as np

from image2struct.filter.rendering_filters.non_trivial_rendering_filter import (
    NonTrivialRenderingFilter,
)


class TestNonTrivialRenderingFilter:
    def setup_method(self):
        self.filter = NonTrivialRenderingFilter(
            hashfunc=imagehash.average_hash,
            hash_size_white_imgs=8,
            hash_size_other_imgs=5,
            max_background_percentage=95.0,
            threshold_white_percentage=50.0,
            verbose=False,
        )
        self.data_path: str = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "test_data"
        )
        os.makedirs(self.data_path, exist_ok=True)

    def teardown_method(self):
        # Delete the images created during the tests
        shutil.rmtree(self.data_path)

    def save_image(self, image: Image.Image, name: str) -> str:
        """Save the image to a file and return the path."""
        image_path: str = os.path.join(self.data_path, name)
        image.save(image_path)
        return image_path

    def get_random_image(self) -> Image.Image:
        """Return an image with random pixel values.
        The image cannot be fully white as it would get filtered out.
        """
        arr: np.ndarray = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        image: Image.Image = Image.fromarray(arr)
        return image

    def test_add_duplicate_hash(self):
        # Create image with random pixels
        image_path: str = self.save_image(self.get_random_image(), "random.png")
        first_accepted, _ = self.filter.check_and_accept_image(image_path)
        assert first_accepted  # Should be added the first time
        second_accepted, _ = self.filter.check_and_accept_image(image_path)
        assert not second_accepted  # Should not be added the second time

    def test_add_different_hash(self):
        # Create image with random pixels
        image_path: str = self.save_image(self.get_random_image(), "random.png")
        assert self.filter.check_and_accept_image(image_path)[0]
        # Create another image with random pixels
        image_path2: str = self.save_image(self.get_random_image(), "random2.png")
        assert self.filter.check_and_accept_image(image_path2)[0]

    def test_add_white_hash(self):
        # Create white image
        arr: np.ndarray = np.ones((100, 100, 3), dtype=np.uint8) * 255
        image: Image.Image = Image.fromarray(arr)
        image_path: str = self.save_image(image, "white.png")
        accepted, infos = self.filter.check_and_accept_image(image_path)
        assert not accepted  # Fully white images should be filtered out
        assert "white_pixels_ratio" in infos
        assert infos["white_pixels_ratio"] == 100.0
        assert "reason" in infos
        assert infos["reason"] == "white image"

    def test_add_black_hash(self):
        # Create black image
        arr: np.ndarray = np.zeros((100, 100, 3), dtype=np.uint8)
        image: Image.Image = Image.fromarray(arr)
        image_path: str = self.save_image(image, "black.png")
        accepted, infos = self.filter.check_and_accept_image(image_path)
        assert not accepted  # Constant images should be filtered out
        assert "white_pixels_ratio" in infos
        assert infos["white_pixels_ratio"] == 0.0
        assert "most_frequent_color_ratio" in infos
        assert infos["most_frequent_color_ratio"] == 100.0
        assert "reason" in infos
        assert infos["reason"] == "constant image"

    def test_similar_images_get_same_hash(self):
        # Create image with random pixels
        arr1: np.ndarray = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        arr2: np.ndarray = arr1.copy()
        arr2[0, 0, 0] = 0  # Change one pixel
        image_path_1: str = self.save_image(Image.fromarray(arr1), "random1.png")
        image_path_2: str = self.save_image(Image.fromarray(arr2), "random2.png")
        accepted1, infos1 = self.filter.check_and_accept_image(image_path_1)
        assert accepted1
        assert "hash" in infos1
        assert len(infos1["hash"])
        accepted2, infos2 = self.filter.check_and_accept_image(image_path_2)
        assert not accepted2
        assert "hash" in infos2
        assert infos1["hash"] == infos2["hash"]
        assert "reason" in infos2
        assert infos2["reason"] == "similar image"

    def test_ratio_correctly_computed(self):
        # Create image with 95% white pixels
        arr: np.ndarray = np.ones((100, 100, 3), dtype=np.uint8) * 255
        arr[:5, :, :] = 0  # Set 5% of the image to black
        image_path: str = self.save_image(Image.fromarray(arr), "accept.png")
        accepted, infos = self.filter.check_and_accept_image(image_path)
        assert accepted
        assert "white_pixels_ratio" in infos
        assert infos["white_pixels_ratio"] == 95.0

        # Add one white pixel
        arr[0, 0, :] = 255
        image_path = self.save_image(Image.fromarray(arr), "reject.png")
        accepted, infos = self.filter.check_and_accept_image(image_path)
        assert not accepted
        assert "white_pixels_ratio" in infos
        assert infos["white_pixels_ratio"] > 95.0
