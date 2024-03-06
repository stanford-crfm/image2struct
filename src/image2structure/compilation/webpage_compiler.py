from typing import Any, Dict, List, Tuple, Optional
from html2text import HTML2Text

import os
import time
import re

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
        screenschot_max_tries: int = 5,
    ):
        super().__init__(timeout, verbose)
        self._port = port
        self._screenshot_options = screenshot_options
        self._max_tries = screenschot_max_tries
        self._html2text = HTML2Text()
        self._html2text.ignore_links = True
        self._html2text.ignore_images = False
        self._html2text.single_line_break = True

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
        success = False
        error: Exception
        for i_try in range(self._max_tries):
            try:
                scheenshot_options = self._screenshot_options
                infos = save_random_screenshot(
                    rendering_path, port=self._port, options=scheenshot_options
                )
                success = True
                break  # We have successfully compiled the image
            except Exception as e:
                error = e
                if "net::ERR_CONNECTION_REFUSED" in str(e):
                    print(
                        f"Failed to take a screenshot: {e} (try {i_try + 1}/{self._max_tries})."
                        " Retrying..."
                    )
                    server.stop()
                    time.sleep(0.5)
                    server.start()
                    time.sleep(0.5)
                else:
                    # Do not retry
                    break

        if not success:
            print(f"Failed to take a screenshot after {self._max_tries} tries: {error}")
            raise CompilationError(f"Failed to take a screenshot: {error}")

        # Stop the server
        server.stop()

        category: str = "unknown"
        if scrape_result is not None and "language" in scrape_result.additional_info:
            category = scrape_result.additional_info["language"].lower()

        assert "html" in infos
        text: str = self._html2text.handle(infos["html"])
        # Normalize space sequences to a single space globally
        text = re.sub(r" +", " ", text)
        # Replace tabs with a single space
        text = re.sub(r"\t", " ", text)
        # Remove leading and trailing spaces on each line
        text = re.sub(r"^[ \t]+|[ \t]+$", "", text, flags=re.MULTILINE)
        # Remove unnecessary whitespace - multiple empty lines and tabulations
        text = re.sub(r"\n\s*\n", "\n", text)
        compilation_result = CompilationResult(
            data_path=data_path,
            rendering_path=rendering_path,
            text=text.strip(),
            category=category,
        )
        return [compilation_result], infos
