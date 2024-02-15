from abc import ABC, abstractmethod
from typing import Any, Dict


class CompilationError(Exception):
    pass


class Compiler(ABC):
    """Compiles data into a structure."""

    @abstractmethod
    def compile(self, data_path: str, destination_path: str) -> Dict[str, Any]:
        """
        Compile the given data into a structure.

        Args:
            data_path: The path to the data to compile.
            destination_path: The path to save the compiled data to.

        Returns:
            Dict[str, Any]: Information about the compilation.

        Raises:
            CompilationError: If the compilation fails.
        """
        pass
