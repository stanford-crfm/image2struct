from abc import ABC, abstractmethod
from typing import Any, Dict, Tuple


class PostProcessor(ABC):
    """This class is responsible for accepting or rejecting an image generated"""

    @abstractmethod
    def check_and_accept_image(
        self, image_path: str, additional_args: Dict[str, Any]
    ) -> Tuple[bool, Dict[str, Any]]:
        """Check if the image meets the requirements and accept it if it does.

        Args:
            image_path (str): The path to the image to check.
            additional_args (Dict[str, Any]): Additional arguments to pass to the post

        Returns:
            bool: True if the image meets the requirements, False otherwise.
            Dict[str, Any]: Additional information about the image.
        """
        pass
