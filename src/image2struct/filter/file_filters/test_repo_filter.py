from typing import Dict

import os
import shutil

from image2struct.filter.file_filters.repo_filter import RepoFilter


class TestRepoFilter:
    def setup_method(self):
        self.repo_filter = RepoFilter(
            min_num_lines=10,
            has_more_than_readme=True,
            max_num_files_code=5,
            max_num_assets=5,
            max_num_lines_code=1000,
            max_num_lines_style=2000,
        )
        self.data_path: str = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "test_data"
        )
        os.makedirs(self.data_path, exist_ok=True)

    def teardown_method(self):
        if os.path.exists(self.data_path):
            # Delete the output file
            shutil.rmtree(self.data_path)

    def create_repo(self, name: str, files: Dict[str, str]):
        """Create a repository with the given files

        Args:
            name (str): The name of the repository
            files (Dict[str, str]): The files to create in the repository.
                Associates the file name to its content
        """
        repo_path = os.path.join(self.data_path, name)
        os.makedirs(repo_path, exist_ok=True)
        for file_name, content in files.items():
            if "/" in file_name:
                os.makedirs(
                    os.path.join(repo_path, os.path.dirname(file_name)), exist_ok=True
                )
            with open(os.path.join(repo_path, file_name), "w") as f:
                f.write(content)

    def test_filter_valid_repo(self):
        # Create a valid repository
        self.create_repo(
            "valid_repo",
            {
                "index.html": "<html>\n  <body>\n    <h1>Hello, world!</h1>\n"  # 6 lines
                "<p>This is a test repository</p>\n  </body>\n</html>",
                "style.css": "body { color: red; }",  # 1 line
                "script.js": "console.log('Hello, world!')",  # 1 line
                "README.md": "This is a test repository\nAdding some more text\nOne last line",  # 3 lines
            },
        )
        passes_filter, analysis = self.repo_filter.filter(
            os.path.join(self.data_path, "valid_repo")
        )
        assert passes_filter
        assert analysis["only_contains_readme"] is False
        assert analysis["num_files"] == {
            "total": 4,
            "code": 3,
            "style": 1,
            "asset": 0,
        }
        assert analysis["num_lines"]["code"] == 10
        assert analysis["num_lines"]["style"] == 1

    def test_filter_repo_too_many_files(self):
        # Create a repository with too many files
        self.create_repo(
            "too_many_files_repo",
            {f"file_{i}.txt": f"File {i}" for i in range(20)},
        )
        passes_filter, analysis = self.repo_filter.filter(
            os.path.join(self.data_path, "too_many_files_repo")
        )
        assert not passes_filter
        assert analysis["num_files"]["total"] == 20

    def test_filter_repo_too_many_lines(self):
        # Create a repository with too many lines
        self.create_repo(
            "too_many_lines_repo",
            {
                "index.html": "<html>\n  <body>\n    <h1>Hello, world!</h1>\n"  # 6 lines
                "<p>This is a test repository</p>\n  </body>\n</html>",
                "index.js": "console.log('Hello, world!')\n" * 1000,  # 1000 lines
                "README.md": "This is a test repository\nAdding some more text\nOne last line",  # 3 lines
            },
        )
        passes_filter, analysis = self.repo_filter.filter(
            os.path.join(self.data_path, "too_many_lines_repo")
        )
        assert not passes_filter
        assert analysis["num_lines"]["code"] == 1009

    def test_style_count_is_separated(self):
        # Create a repository with too many lines
        self.create_repo(
            "lots_of_css_still_ok_repo",
            {
                "index.html": "<html>\n  <body>\n    <h1>Hello, world!</h1>\n"  # 6 lines
                "<p>This is a test repository</p>\n  </body>\n</html>",
                "style.css": "body { color: red; }\n" * 1000,  # 1000 lines
                "script.js": "console.log('Hello, world!')",  # 1 line
                "README.md": "This is a test repository\nAdding some more text\nOne last line",  # 3 lines
            },
        )
        passes_filter, analysis = self.repo_filter.filter(
            os.path.join(self.data_path, "lots_of_css_still_ok_repo")
        )
        assert passes_filter
        assert analysis["num_lines"]["style"] == 1000
        assert analysis["num_lines"]["code"] == 10
