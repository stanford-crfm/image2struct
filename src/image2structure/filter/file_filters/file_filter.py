from abc import ABC, abstractmethod


class FileFilter(ABC):
    """This class is responsible for filtering files."""

    @abstractmethod
    def filter(self, file_path: str) -> bool:
        """Check if the file meets the requirements.

        Args:
            file_path (str): The path to the file to check.

        Returns:
            bool: True if the file meets the requirements, False otherwise.
        """
        pass
