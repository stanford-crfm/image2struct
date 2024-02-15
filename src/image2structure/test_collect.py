from dotenv import load_dotenv

import os
import shutil

from image2structure.collect import run, get_args_parser, get_runner_from_args
from image2structure.runner import Runner
from image2structure.run_specs import _RUNNER_REGISTRY


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
                "--category",
                "html",
                "--destination-path",
                self.data_path,
                "--timeout",
                "30",
                "--num-instances",
                "1",
                "--num-instances-at-once",
                "25",
                "--date-from",
                "2021-01-01",
                "--date-to",
                "2022-01-01",
                "webpage",
                "--port",
                "8000",
                "--timeout",
                "30",
                "--max_size_kb",
                "10000",
            ]
        )
        runner: Runner = get_runner_from_args(args)
        run(runner, args)
