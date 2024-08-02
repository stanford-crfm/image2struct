import os
import shutil
import datetime
import pytest

from image2struct.compilation.music_compiler import MusicCompiler
from image2struct.fetch.fetcher import ScrapeResult
from image2struct.compilation.compiler import CompilationError


class TestMusicCompiler:
    def setup_method(self, method):
        self.compiler = MusicCompiler(
            crop_sides=True,
            timeout=30,
            verbose=True,
        )
        self.data_path: str = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "musicsheet/test_data"
        )
        self.dest_path: str = os.path.join(self.data_path, "output")
        os.makedirs(self.dest_path, exist_ok=True)

    def teardown_method(self, method):
        shutil.rmtree(self.dest_path)

    def test_compile_valid_musicsheet(self):
        scrape_result = ScrapeResult(
            download_url="empty",
            instance_name="test_0.pdf",
            date=datetime.datetime.now(),
            additional_info={"page_count": 2},
        )
        data_path: str = os.path.join(self.data_path, scrape_result.instance_name)
        compilation_results, _ = self.compiler.compile(
            data_path, self.dest_path, scrape_result
        )
        assert len(compilation_results) == 8
        for compilation_result in compilation_results:
            assert compilation_result.text is None
            assert os.path.exists(compilation_result.rendering_path)
            assert compilation_result.data_path is None
            assert compilation_result.assets_path == []

    def test_compile_invalid_musicsheet(self):
        scrape_result = ScrapeResult(
            download_url="empty",
            instance_name="test_1.pdf",
            date=datetime.datetime.now(),
            additional_info={"page_count": 2},
        )
        with pytest.raises(CompilationError):
            data_path: str = os.path.join(self.data_path, scrape_result.instance_name)
            self.compiler.compile(data_path, self.dest_path, scrape_result)

    def test_compile_non_existing_musicsheet(self):
        scrape_result = ScrapeResult(
            download_url="empty",
            instance_name="non_existing.pdf",
            date=datetime.datetime.now(),
            additional_info={"page_count": 2},
        )
        with pytest.raises(CompilationError):
            data_path: str = os.path.join(self.data_path, scrape_result.instance_name)
            self.compiler.compile(data_path, self.dest_path, scrape_result)
