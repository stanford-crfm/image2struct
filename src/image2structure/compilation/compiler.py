from abc import ABC, abstractmethod
from typing import Any, Dict, List, Tuple, Optional
from dataclasses import dataclass, field

from image2structure.fetch.fetcher import ScrapeResult


@dataclass
class CompilationResult:
    """The result of a compilation."""

    rendering_path: str
    """The path to the rendering of the compiled data."""

    category: str
    """The category of the compiled data.
    For TeX, this is the type of the environment (e.g. equation, figure, table, algorithm).
    For web pages, this can be the language used (HTML, CSS, JavaScript, etc.)."""

    data_path: Optional[str] = None
    """The path to the compiled data."""

    text: Optional[str] = None
    """The text extracted from the compiled data."""

    assets_path: List[str] = field(default_factory=lambda: [])
    """The paths to the assets used in the rendering of the compiled data."""


class CompilationError(Exception):
    pass


class Compiler(ABC):
    """Compiles data into a structure."""

    def __init__(self, timeout: int, verbose: bool):
        self._timeout = timeout
        self._verbose = verbose

        # Keeps tracks of how many instances have been compiled
        # for each category
        self._num_compiled_instances: Dict[str, int] = {}

    @abstractmethod
    def compile(
        self,
        data_path: str,
        destination_path: str,
        scrape_result: Optional[ScrapeResult] = None,
    ) -> Tuple[List[CompilationResult], Dict[str, Any]]:
        """
        Compile the given data.
        This will output one or several images.

        Args:
            data_path: The path to the data to compile.
            destination_path: The path to save the compiled data to.
            scrape_result: The scrape that produced the data.

        Returns:
            List[CompilationResult]: The result of the compilation.
            Dict[str, Any]: Information about the compilation.

        Raises:
            CompilationError: If the compilation fails.
        """
        pass

    def acknowledge_compilation(self, category: str):
        """Acknowledge that an instance has been compiled."""
        if category not in self._num_compiled_instances:
            self._num_compiled_instances[category] = 0
        self._num_compiled_instances[category] += 1
        if self._verbose:
            print(
                f"Compiled {self._num_compiled_instances[category]} instances for {category}."
            )
