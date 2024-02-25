from typing import Optional, Tuple

from pdf2image import convert_from_bytes
from PIL.Image import Image
from PIL import ImageOps


# Increase the maximum number of pixels allowed
Image.MAX_IMAGE_PIXELS = 400000000


def is_mostly_white(
    img: Image, white_threshold: int = 240, percentage_threshold: int = 80
) -> bool:
    """
    Check if an image is mostly white.

    :param img: The PIL image to check.
    :param white_threshold: The minimum value for each RGB component to be considered white or near-white.
    :param percentage_threshold: The percentage of white or near-white pixels required for the image to be
                                 considered mostly white.
    :return: True if the image is mostly white, False otherwise.
    """
    # Get the total number of pixels
    total_pixels = img.width * img.height

    # Count white or near-white pixels
    white_pixels = sum(
        1
        for pixel in img.getdata()
        if all(channel >= white_threshold for channel in pixel)
    )

    # Calculate the percentage of white or near-white pixels
    white_percentage = (white_pixels / total_pixels) * 100

    # Check if the image is mostly white
    return white_percentage >= percentage_threshold


def pdf_to_image(
    pdf_path: str,
    crop: bool = False,
    resize_to: Optional[Tuple[int, int]] = None,
    page_number: Optional[int] = None,
) -> Optional[Image]:
    """Pulls a single page from a PDF and converts it to an image."""
    with open(pdf_path, "rb") as pdf_stream:
        images = convert_from_bytes(
            pdf_stream.read(), first_page=page_number, last_page=page_number  # type: ignore
        )
        if len(images) > 0:
            image = images[0]

            # Removes the white border around the image
            if crop:
                (w, h) = image.size
                image = image.crop((0, 0, w, h - int(h * 0.13)))  # Remove pagination
                image = image.crop(
                    ImageOps.invert(image).getbbox()
                )  # Remove white border

            # Resize the image
            if resize_to:
                image = image.resize(resize_to)

            return image
        return None
