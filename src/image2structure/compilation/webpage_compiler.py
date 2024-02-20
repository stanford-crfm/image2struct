from typing import Any, Dict

import os

from image2structure.compilation.compiler import Compiler, CompilationError
from image2structure.compilation.webpage.jekyll_server import JekyllServer
from image2structure.compilation.webpage.driver import (
    save_random_screenshot,
    ScreenshotOptions,
)


class WebpageCompiler(Compiler):
    def __init__(
        self,
        port: int,
        timeout: int,
        verbose: bool,
        screenshot_options: ScreenshotOptions,
    ):
        self._port = port
        self._timeout = timeout
        self._verbose = verbose
        self._screenshot_options = screenshot_options

    def compile(self, data_path: str, destination_path: str) -> Dict[str, Any]:
        """
        Compile the given data into a webpage using Jekyll.

        Args:
            data_path: The path to the repository to compile.
            destination_path: The path to save the compiled data to.
            timeout: The maximum time in seconds to allow the compilation to run.
        """

        infos: Dict[str, Any] = {}

        # Check that the repo path exists
        if not os.path.exists(data_path):
            raise CompilationError(f"Path does not exist: {data_path}")

        # Start the Jekyll server
        server = JekyllServer(
            repo_path=data_path, port=self._port, verbose=self._verbose
        )
        success: bool = server.start(self._timeout)
        if not success:
            print(f"Failed to start the server for {data_path}. Skipping...")
            server.stop()
            raise CompilationError(f"Jekyll server failed to start: {data_path}")

        # Take a screenshot of a random page
        try:
            scheenshot_options = self._screenshot_options
            actions = save_random_screenshot(
                destination_path, port=self._port, options=scheenshot_options
            )
            infos["actions"] = actions
        except Exception as e:
            print(f"Failed to take a screenshot: {e}")
            server.stop()
            raise CompilationError(f"Failed to take a screenshot: {e}")

        # Stop the server
        server.stop()

        return infos
