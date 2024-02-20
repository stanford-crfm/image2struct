from typing import Any, Dict, List, Tuple, Optional

import os

from image2structure.compilation.compiler import (
    Compiler,
    CompilationError,
    CompilationResult,
)
from image2structure.compilation.webpage.jekyll_server import JekyllServer
from image2structure.compilation.webpage.driver import (
    save_random_screenshot,
    ScreenshotOptions,
)
from image2structure.fetch.fetcher import ScrapeResult


class WebpageCompiler(Compiler):
    def __init__(
        self,
        port: int,
        timeout: int,
        verbose: bool,
        screenshot_options: ScreenshotOptions,
    ):
        super().__init__(timeout, verbose)
        self._port = port
        self._screenshot_options = screenshot_options

    def compile(
        self,
        data_path: str,
        destination_path: str,
        scrape_result: Optional[ScrapeResult] = None,
    ) -> Tuple[List[CompilationResult], Dict[str, Any]]:
        """
        Compile the given data into a webpage using Jekyll.

        Args:
            data_path: The path to the data to compile.
            destination_path: The path to save the compiled data to.
            scrape_result: The scrape that produced the data.

        Returns:
            List[CompilationResult]: The result of the compilation.
            Dict[str, Any]: Information about the compilation.
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
        rendering_path: str = os.path.join(destination_path, "rendering.png")
        try:
            scheenshot_options = self._screenshot_options
            actions = save_random_screenshot(
                rendering_path, port=self._port, options=scheenshot_options
            )
            infos["actions"] = actions
        except Exception as e:
            print(f"Failed to take a screenshot: {e}")
            server.stop()
            raise CompilationError(f"Failed to take a screenshot: {e}")

        # Stop the server
        server.stop()

        category: str = "unknown"
        if scrape_result is not None and "language" in scrape_result.additional_info:
            category = scrape_result.additional_info["language"].lower()
        compilation_result = CompilationResult(
            data_path=data_path, rendering_path=rendering_path, category=category
        )
        return [compilation_result], infos
