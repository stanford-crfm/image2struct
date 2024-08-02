from typing import Optional, Tuple

from pdf2image import convert_from_bytes
import io
from PIL import Image, ImageOps

from image2struct.compilation.compiler import CompilationError


def pdf_to_image(
    pdf_stream: io.BytesIO,
    crop: bool = False,
    resize_to: Optional[Tuple[int, int]] = None,
) -> Image.Image:
    """Convert a PDF stream to an image.

    Args:
        pdf_stream: The PDF stream to convert to an image.
        crop: Whether to crop the image to remove the white border.
        resize_to: The size to resize the image to.

    Returns:
        The image.

    Raises:
        CompilationError: If the PDF to Image conversion failed.
    """
    # Convert the first page of the PDF stream to an image
    images = convert_from_bytes(pdf_stream.read(), first_page=1, last_page=1)
    if images:
        image: Image.Image = images[0]

        # Removes the white border around the image
        if crop:
            # TODO: Clean this
            # We need to remove the bottom of the image first to remove the number of the page
            image = image.crop(
                (
                    0,
                    0,
                    image.size[0],
                    image.size[1] - int(image.size[1] * 0.13),
                )
            )
            image = image.crop(ImageOps.invert(image).getbbox())

        # Resize the image
        if resize_to:
            image = image.resize(resize_to)

        return image
    else:
        raise CompilationError("PDF to Image conversion failed")
