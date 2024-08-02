from dotenv import load_dotenv

import os
import pytest
import shutil

from image2struct.collect import run, get_args_parser, get_runner_from_args
from image2struct.runner import Runner


class TestRun:
    def setup_method(self, method):
        load_dotenv()
        self.data_path = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "test_data"
        )

    def teardown_method(self, method):
        shutil.rmtree(self.data_path)

    def test_webpage(self):
        args = get_args_parser()[0].parse_args(
            [
                "--destination-path",
                self.data_path,
                "--num-instances",
                "1",
                "--num-instances-at-once",
                "5",
                "--date-from",
                "2022-01-01",
                "--date-to",
                "2022-01-02",
                "webpage",
                "--language",
                "css",
                "--port",
                "8000",
                "--max_size_kb",
                "10",
            ]
        )
        runner: Runner = get_runner_from_args(args)
        run(runner, args)

    @pytest.mark.slow
    def test_latex(self):
        args = get_args_parser()[0].parse_args(
            [
                "--destination-path",
                self.data_path,
                "--num-instances",
                "1",
                "--num-instances-at-once",
                "5",
                "--date-from",
                "2022-01-01",
                "--date-to",
                "2022-02-01",
                "latex",
                "--subcategory",
                "econ",
            ]
        )
        runner: Runner = get_runner_from_args(args)
        run(runner, args)

    def test_musicsheet(self):
        args = get_args_parser()[0].parse_args(
            [
                "--destination-path",
                self.data_path,
                "--num-instances",
                "1",
                "--num-instances-at-once",
                "5",
                "--date-from",
                "2010-01-01",
                "--date-to",
                "2022-02-01",
                "musicsheet",
                "--subcategory",
                "music",
            ]
        )
        runner: Runner = get_runner_from_args(args)
        run(runner, args)
