from abc import ABC, abstractmethod
from typing import Any, Dict, Tuple

from image2struct.filter.utils import FilterError


class FileFilterError(FilterError):
    pass


class FileFilter(ABC):
    """This class is responsible for filtering files."""

    def __init__(self, name: str):
        """Initialize the filter with the name of the filter.

        Args:
            name (str): The name of the filter.
        """
        self.name = name

    @abstractmethod
    def filter(self, file_path: str) -> Tuple[bool, Dict[str, Any]]:
        """Check if the file meets the requirements.

        Args:
            file_path (str): The path to the file to check.

        Returns:
            bool: True if the file meets the requirements, False otherwise.
            Dict[str, Any]: Additional information about the file.

        Raises:
            FileFilterError: If the filtering cannot be performed.
        """
        pass
