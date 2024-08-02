# This file defines unit tests for web page compiler.
import os
import pytest
import shutil

from PIL import Image

from image2struct.compilation.compiler import CompilationError, CompilationResult
from image2struct.compilation.webpage_compiler import WebpageCompiler
from image2struct.compilation.webpage.driver import ScreenshotOptions
from image2struct.compilation.webpage.jekyll_server import JekyllServer


class TestWebpageCompiler:
    def setup_method(self, method):
        self.compiler = WebpageCompiler(
            port=1234,
            timeout=30,
            verbose=False,
            screenshot_options=ScreenshotOptions(),
        )
        self.data_path: str = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "webpage/test_data"
        )
        self.repo_path: str = os.path.join(self.data_path, "valid_repo")
        self.image_path: str = os.path.join(self.repo_path, "rendering.png")

    def teardown_method(self, method):
        if os.path.exists(self.image_path):
            # Delete the output file
            os.remove(self.image_path)
        _site_path = os.path.join(self.repo_path, "_site")
        if os.path.exists(_site_path):
            # Delete the _site directory
            shutil.rmtree(_site_path)

    def test_compile_valid_repos(self):
        ref_image_path: str = os.path.join(self.repo_path, "output_ref.png")

        assert not os.path.exists(self.image_path)
        result: CompilationResult = self.compiler.compile(
            self.repo_path, self.repo_path
        )[0][0]
        assert result.text is not None and len(result.text) > 0
        assert os.path.exists(result.rendering_path)
        assert os.path.exists(result.data_path)
        assert result.assets_path == []
        assert result.data_path == self.repo_path
        assert result.rendering_path == self.image_path
        assert os.path.exists(ref_image_path)

        # Check that the two images are the same
        image = Image.open(self.image_path)
        ref_image = Image.open(ref_image_path)
        assert image.size == ref_image.size
        # Check each pixel
        # Check that no more than 5% of the pixels are different
        num_diff = 0
        for i in range(image.size[0]):
            for j in range(image.size[1]):
                if image.getpixel((i, j)) != ref_image.getpixel((i, j)):
                    num_diff += 1
        assert num_diff < 0.05 * image.size[0] * image.size[1]

    def test_fail_compile_invalid_repos(self):
        invalid_repo_path: str = os.path.join(self.data_path, "invalid_repo")
        image_path: str = os.path.join(invalid_repo_path, "rendering.png")
        with pytest.raises(CompilationError):
            self.compiler.compile(invalid_repo_path, invalid_repo_path)
        assert not os.path.exists(image_path)

    def test_closes_port(self):
        self.compiler.compile(self.repo_path, self.repo_path)
        assert not JekyllServer.is_port_in_use(1234)
