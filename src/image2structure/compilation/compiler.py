from abc import ABC, abstractmethod
from typing import Any, Dict


class CompilationError(Exception):
    pass


class Compiler(ABC):
    """Compiles data into a structure."""

    @abstractmethod
    def compile(
        self,
        destination_path: str,
        timeout: int,
        additional_args: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Compile the given data into a structure.

        Args:
            destination_path: The path to save the compiled data to.
            timeout: The maximum time in seconds to allow the compilation to run.
            additional_args: Additional arguments to pass to the compiler.

        Returns:
            Dict[str, Any]: Information about the compilation.

        Raises:
            CompilationError: If the compilation fails.
        """
        pass
