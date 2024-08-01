from dotenv import load_dotenv

import os
import shutil

from image2struct.filter.file_filters.toxicity_filter import ToxicityFilter


class TestToxicityFilter:
    def setup_method(self):
        load_dotenv()
        self.repo_filter = ToxicityFilter(
            api_key=os.getenv("PERSPECTIVE_API_KEY"),
            toxicity_threshold=0.5,
            sexually_explicit_threshold=0.3,
        )
        self.data_path: str = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "test_data"
        )
        os.makedirs(self.data_path, exist_ok=True)

    def teardown_method(self):
        if os.path.exists(self.data_path):
            shutil.rmtree(self.data_path)

    def create_file(self, name: str, content: str):
        """Create a file with the given content

        Args:
            name (str): The name of the file
            content (str): The content of the file
        """
        with open(os.path.join(self.data_path, name), "w") as f:
            f.write(content)

    def test_filter_toxic_content(self):
        self.create_file("file.txt", "You are a dick")
        passes_filter, analysis = self.repo_filter.filter(self.data_path)
        assert not passes_filter
        assert "toxicity" in analysis.get("reason", "").lower()

    def test_filter_normal_content(self):
        self.create_file("file.txt", "Hey how are you doing today?")
        passes_filter, _ = self.repo_filter.filter(self.data_path)
        assert passes_filter

    def test_filter_latex(self):
        self.create_file(
            "file.tex",
            "(a + b)^n = C(n, 0)a^n b^0 + C(n, 1)a^(n-1) b^1 + ... + C(n, n-1)a^1 b^(n-1) + C(n, n)a^0 b^n",
        )
        passes_filter, _ = self.repo_filter.filter(self.data_path)
        assert passes_filter

    def test_filter_webpage(self):
        self.create_file(
            "index.html", "<html><body><h1>Hello, World!</h1></body></html>"
        )
        passes_filter, _ = self.repo_filter.filter(self.data_path)
        assert passes_filter

    def test_filter_webpage_several_files_including_one_toxic(self):
        self.create_file(
            "index.html", "<html><body><h1>Hello, World!</h1></body></html>"
        )
        self.create_file(
            "profile.html", "<html><body><p>Ahah screw you</p></body></html>"
        )
        passes_filter, analysis = self.repo_filter.filter(self.data_path)
        assert not passes_filter
        assert "toxicity" in analysis.get("reason", "").lower()

    def test_filter_webpage_with_explicit_image(self):
        self.create_file(
            "index.html", "<html><body><h1>Hello, World!</h1></body></html>"
        )
        self.create_file(
            "profile.html",
            "<html><body><img src='assets/explicit_nude.png'></body></html>",
        )
        passes_filter, analysis = self.repo_filter.filter(self.data_path)
        assert not passes_filter
        assert "sexually" in analysis.get("reason", "").lower()
