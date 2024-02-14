from typing import Any, Dict

from .compiler import Compiler, CompilationError
from .webpage.jekyll_server import JekyllServer
from .webpage.driver import save_random_screenshot, ScreenshotOptions


class WebpageCompiler(Compiler):

    def compile(
        self,
        destination_path: str,
        timeout: int,
        additional_args: Dict[str, Any],
    ) -> None:
        """
        Compile the given data into a webpage using Jekyll.

        Args:
            destination_path: The path to save the compiled data to.
            timeout: The maximum time in seconds to allow the compilation to run.
            additional_args: Additional arguments to pass to the compiler.
        """

        infos: Dict[str, Any] = {}

        # Check that the repo path exists
        assert "repo_path" in additional_args, "repo_path must be provided"
        assert type(additional_args["repo_path"]) == str, "repo_path must be a string"
        assert additional_args["repo_path"].exists(), "repo_path must exist"
        repo_path: str = additional_args.get("repo_path")
        verbose: bool = additional_args.get("verbose", False)
        port: int = additional_args.get("port", 4000)

        # Start the Jekyll server
        server = JekyllServer(repo_path, verbose, port)
        success: bool = server.start(timeout)
        if not success:
            print(f"Failed to start the server for {repo_path}. Skipping...")
            server.stop()
            raise CompilationError(f"Jekyll server failed to start: {repo_path}")

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
                destination_path, port=port, options=scheenshot_options
            )
            infos["actions"] = actions
        except Exception as e:
            print(f"Failed to take a screenshot: {e}")
            server.stop()
            raise CompilationError(f"Failed to take a screenshot: {e}")

        # Stop the server
        server.stop()

        return infos
