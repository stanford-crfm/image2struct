from abc import ABC, abstractmethod
from typing import Any, Dict, Tuple

from image2struct.filter.utils import FilterError


class RenderingFilterError(FilterError):
    pass


class RenderingFilter(ABC):
    """This class is responsible for accepting or rejecting an image generated"""

    def __init__(self, name: str):
        """Initialize the filter with the name of the filter.

        Args:
            name (str): The name of the filter.
        """
        self.name = name

    @abstractmethod
    def check_and_accept_image(self, image_path: str) -> Tuple[bool, Dict[str, Any]]:
        """Check if the image meets the requirements and accept it if it does.

        Args:
            image_path (str): The path to the image to check.

        Returns:
            bool: True if the image meets the requirements, False otherwise.
            Dict[str, Any]: Additional information about the image.

        Raises:
            RenderingFilterError: If the filtering cannot be performed.
        """
        pass
