# This file defines unit tests for web page compiler.
import os
import pytest

from PIL import Image

from image2structure.compilation.compiler import CompilationError
from image2structure.compilation.webpage_compiler import WebpageCompiler
from image2structure.compilation.webpage.driver import ScreenshotOptions
from image2structure.compilation.webpage.jekyll_server import JekyllServer


class TestWebpageCompiler:

    def setup_method(self, method):
        self.compiler = WebpageCompiler(
            port=1234,
            timeout=30,
            verbose=False,
            num_max_actions=0,
            screenshot_options=ScreenshotOptions(),
        )
        self.data_path: str = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "webpage/test_data"
        )
        self.image_path: str = os.path.join(self.data_path, "output.png")

    def teardown_method(self, method):
        if os.path.exists(self.image_path):
            # Delete the output file
            os.remove(self.image_path)

    def test_compile_valid_repos(self):
        repo_path: str = os.path.join(self.data_path, "valid_repo")
        self.image_path: str = os.path.join(repo_path, "output.png")
        ref_image_path: str = os.path.join(repo_path, "output_ref.png")

        assert not os.path.exists(self.image_path)
        self.compiler.compile(repo_path, self.image_path)
        assert os.path.exists(self.image_path)
        assert os.path.exists(ref_image_path)

        # Check that the two images are the same
        image = Image.open(self.image_path)
        ref_image = Image.open(ref_image_path)
        assert image.size == ref_image.size
        assert image.mode == ref_image.mode
        # Check each pixel
        # Check that no more than 1% of the pixels are different
        num_diff = 0
        for i in range(image.size[0]):
            for j in range(image.size[1]):
                if image.getpixel((i, j)) != ref_image.getpixel((i, j)):
                    num_diff += 1
        assert num_diff < 0.01 * image.size[0] * image.size[1]

    def test_fail_compile_invalid_repos(self):
        repo_path: str = os.path.join(self.data_path, "invalid_repo")
        image_path: str = os.path.join(repo_path, "output.png")
        with pytest.raises(CompilationError):
            self.compiler.compile(repo_path, image_path)
        assert not os.path.exists(image_path)

    def test_compile_invalid_path(self):
        image_path: str = os.path.join(self.data_path, "output.png")
        with pytest.raises(CompilationError):
            self.compiler.compile("invalid_path", image_path)
        assert not os.path.exists(image_path)

    def test_closes_port(self):
        repo_path: str = os.path.join(self.data_path, "valid_repo")
        self.image_path: str = os.path.join(repo_path, "output.png")

        self.compiler.compile(repo_path, self.image_path)
        assert not JekyllServer.is_port_in_use(1234)
