from typing import Dict, Any, 

from .post_processor import PostProcessor
from .image_filter import ImageFilter


class NewImagePostProcessor(PostProcessor):
    """A class to post process images.

    This post processor uses the ImageFilter class to filter images based on their content.
    It checks that images are not fully white and that they are not similar to other images.
    """

    def __init__(self, args: Dict[str, Any]):
        self._image_filter = ImageFilter(**args)

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
        added, additional_infos = self._image_filter.check_image(image_path)
        return added, additional_infos
