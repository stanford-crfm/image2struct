from typing import Any, Dict

from .compiler import Compiler, CompilationError
from .webpage.jekyll_server import JekyllServer
from .webpage.driver import save_random_screenshot, ScreenshotOptions


class WebpageCompiler(Compiler):

    def __init__(self, port: int, verbose: bool):
        self._port = port
        self._verbose = verbose

    def compile(
        self,
        data_path: str,
        destination_path: str,
        timeout: int,
        additional_args: Dict[str, Any],
    ) -> None:
        """
        Compile the given data into a webpage using Jekyll.

        Args:
            data_path: The path to the repository to compile.
            destination_path: The path to save the compiled data to.
            timeout: The maximum time in seconds to allow the compilation to run.
            additional_args: Additional arguments to pass to the compiler.
                - screenshot_options: Options to pass to the screenshot function.
                - max_actions: The maximum number of actions to perform on the page.
        """

        infos: Dict[str, Any] = {}

        # Check that the repo path exists
        assert data_path.exists(), "repo_path must exist"

        # Start the Jekyll server
        server = JekyllServer(data_path, self._verbose, self._port)
        success: bool = server.start(timeout)
        if not success:
            print(f"Failed to start the server for {data_path}. Skipping...")
            server.stop()
            raise CompilationError(f"Jekyll server failed to start: {data_path}")

        # Take a screenshot of a random page
        try:
            scheenshot_options: ScreenshotOptions = additional_args.get(
                "screenshot_options", ScreenshotOptions()
            )
            scheenshot_options.num_actions_range = (
                0,
                additional_args.get("max_actions", 0),
            )
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
