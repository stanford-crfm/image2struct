from typing import Any, Dict

from .compiler import Compiler, CompilationError
from .webpage.jekyll_server import JekyllServer
from .webpage.driver import save_random_screenshot, ScreenshotOptions


class WebpageCompiler(Compiler):

    def __init__(
        self,
        port: int,
        timeout: int,
        verbose: bool,
        num_max_actions: int,
        screenshot_options: ScreenshotOptions,
    ):
        self._port = port
        self._timeout = timeout
        self._verbose = verbose
        self._num_max_actions = num_max_actions
        self._screenshot_options = screenshot_options

    def compile(self, data_path: str, destination_path: str) -> None:
        """
        Compile the given data into a webpage using Jekyll.

        Args:
            data_path: The path to the repository to compile.
            destination_path: The path to save the compiled data to.
            timeout: The maximum time in seconds to allow the compilation to run.
        """

        infos: Dict[str, Any] = {}

        # Check that the repo path exists
        assert data_path.exists(), "repo_path must exist"

        # Start the Jekyll server
        server = JekyllServer(data_path, self._verbose, self._port)
        success: bool = server.start(self._timeout)
        if not success:
            print(f"Failed to start the server for {data_path}. Skipping...")
            server.stop()
            raise CompilationError(f"Jekyll server failed to start: {data_path}")

        # Take a screenshot of a random page
        try:
            scheenshot_options = self._screenshot_options
            scheenshot_options.num_actions_range = (0, self._num_max_actions)
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
