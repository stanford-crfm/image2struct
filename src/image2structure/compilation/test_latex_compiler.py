from typing import Dict

import os
import shutil

from image2structure.compilation.latex_compiler import LatexCompiler


class TestLatexCompiler:
    def setup_method(self, method):
        self.compiler = LatexCompiler(
            crop=True,
            timeout=30,
            num_instances=5,
            max_elt_per_category=3,
            verbose=True,
        )
        self.data_path: str = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "tex/test_data"
        )
        self.dest_path: str = os.path.join(self.data_path, "output")
        os.makedirs(self.dest_path, exist_ok=True)

    def teardown_method(self, method):
        shutil.rmtree(self.dest_path)

    def test_compile_valid_repos(self):
        src_path: str = os.path.join(self.data_path, "cl_dice.tar.gz")
        compilation_result, _ = self.compiler.compile(src_path, self.dest_path)
        assert len(compilation_result) > 0

        # Count number of rendered images per category
        num_images: Dict[str, int] = {}
        for result in compilation_result:
            if result.category not in num_images:
                num_images[result.category] = 0
            num_images[result.category] += 1
        expected_num_images = {
            "equation": 3,
            "figure": 3,
            "algorithm": 2,
            "table": 1,
        }
        for category, count in expected_num_images.items():
            assert category in num_images
            assert num_images[category] == count
