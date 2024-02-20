# This file defines unit tests for web page compiler.
import os
import shutil

from image2structure.compilation.latex_compiler import LatexCompiler


class TestLatexCompiler:
    def setup_method(self, method):
        self.compiler = LatexCompiler(
            crop=True,
            num_instances=5,
            max_elt_per_category=3,
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
        self.compiler.compile(src_path, self.dest_path)
