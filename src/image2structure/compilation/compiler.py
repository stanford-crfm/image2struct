from abc import ABC, abstractmethod
from typing import Any, Dict, List, Tuple, Optional
from dataclasses import dataclass, field

from image2structure.fetch.fetcher import ScrapeResult


@dataclass
class CompilationResult:
    """The result of a compilation."""

    data_path: str
    """The path to the compiled data."""
    rendering_path: str
    """The path to the rendering of the compiled data."""
    category: str
    """The category of the compiled data.
    For TeX, this is the type of the environment (e.g. equation, figure, table, algorithm).
    For web pages, this can be the language used (HTML, CSS, JavaScript, etc.)."""
    assets_path: List[str] = field(default_factory=lambda: [])
    """The paths to the assets used in the rendering of the compiled data."""


class CompilationError(Exception):
    pass


class Compiler(ABC):
    """Compiles data into a structure."""

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
