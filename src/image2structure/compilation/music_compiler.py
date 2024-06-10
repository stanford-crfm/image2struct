from typing import Any, Dict, Optional, Tuple, List
from PIL import Image, ImageOps
from pdf2image.exceptions import PDFPageCountError

import os
import random
import numpy as np

from image2structure.compilation.compiler import (
    Compiler,
    CompilationError,
    CompilationResult,
)
from image2structure.fetch.fetcher import ScrapeResult
from image2structure.util.image_utils import pdf_to_image
from image2structure.compilation.musicsheet.classifier import SheetMusicClassifier


class MusicCompiler(Compiler):

    # The image should contain at least 50 % of white pixels
    WHITE_THRESHOLD: float = 0.5

    # Small value to compare floats
    EPSILON: float = 1e-6

    # A row is considered emnpty if it contains at least SEGMENT_MIN_EMPTY_ROW_SIZE_RELATIVE_THRESHOLD
    # lines of white pixels.
    SEGMENT_MIN_EMPTY_ROW_SIZE_RELATIVE_THRESHOLD: float = 0.01

    # A segment is considered to be a measure if it contains at least SEGMENT_MIN_ROW_SIZE_RELATIVE_THRESHOLD
    # lines of non-empty pixels.
    SEGMENT_MIN_ROW_SIZE_RELATIVE_THRESHOLD: float = 0.05

    def __init__(self, crop_sides: bool, timeout: int, verbose: bool = False):
        super().__init__(timeout=timeout, verbose=verbose)
        self._crop_sides = crop_sides
        self._model = SheetMusicClassifier()

    @staticmethod
    def get_page_number(total_num_pages: int) -> int:
        """Select a random page but preferably not the first two pages (which could be a title
        and not the sheet music) and the last two pages (which could be a blank page).

        Args:
            total_num_pages: The total number of pages.

        Returns:
            int: The selected page number.
        """
        page_number: int
        if total_num_pages > 4:
            page_number = random.randint(3, total_num_pages - 2)
        elif total_num_pages == 4:
            page_number = 3
        elif total_num_pages == 2 or total_num_pages == 3:
            page_number = 2
        else:
            page_number = 1
        return page_number

    def generate_sheet_image(
        self, pdf_path: str, page_number: int
    ) -> Tuple[bool, Optional[Image.Image]]:
        """
        Generates an image from the sheet music PDFs in `output_dir`

        :param pdf_path: Path to the PDF file
        :param output_path: Path to the output image
        :param page_number: Page number to extract
        :return: True if the image was generated successfully, False otherwise
        """
        # Read PDF file in binary mode
        image: Optional[Image.Image] = None
        try:
            image = pdf_to_image(pdf_path, page_number=page_number)

            if image is None:
                if self._verbose:
                    print(f"Could not generate image from {pdf_path}")
                return False, image

            if self._verbose:
                print(
                    f"Success: Extracted page {page_number} from {pdf_path} as an image."
                )
        except (RuntimeError, PDFPageCountError, Image.DecompressionBombError) as e:
            if self._verbose:
                print(f"Skipping: Error generating image from {pdf_path}: {e}")
            return False, image

        return True, image

    def filter(self, image: Image.Image) -> None:
        """
        Filter the image to check if it is a sheet music.

        Args:
            image: The image to filter.

        Raises:
            CompilationError: If the image does not contain enough white pixels or is not a sheet music.
        """
        # Count proportion of white pixels.
        image_np = np.array(image)
        white_pixels = np.sum(image_np == 255)
        proportion_white = white_pixels / image_np.size
        if proportion_white < self.WHITE_THRESHOLD:
            raise CompilationError(
                f"Image does not contain enough white pixels: {proportion_white}"
            )

        # Classify the image
        if not self._model.is_sheet_music(image):
            raise CompilationError("Image is not a sheet music.")

    def segment(self, image: np.ndarray) -> List[Tuple[int, int]]:
        """
        Segment the image into measures.

        Args:
            image: The image to segment.

        Returns:
            List[Tuple[int, int]]: The list of segments.
        """
        assert len(image.shape) == 2
        image = image.astype(np.float32) / 255.0
        inversed_sum = 1.0 - np.mean(image, axis=1)

        # Constants
        min_num_empty_rows = int(
            self.SEGMENT_MIN_EMPTY_ROW_SIZE_RELATIVE_THRESHOLD * image.shape[0]
        )
        min_num_rows = int(
            self.SEGMENT_MIN_ROW_SIZE_RELATIVE_THRESHOLD * image.shape[0]
        )

        # Segment inversed_sum in sections separated by at least
        # min_num_empty_rows empty rows (i.e. zeros in inversed_sum).
        # Example: [0, 0, 0, index_0_0, ...., index_0_1, 0, 0, 0, 0, index_1_0, ...., index_1_1, 0, 0, 0, ...]
        # with min_num_empty_rows = 3
        # The segments are [(index_0_0, index_0_1), (index_1_0, index_1_1)]
        segments = []
        count_empty_rows: int = 0
        start: Optional[int] = None
        for i in range(1, len(inversed_sum)):
            if start is not None:
                # We are currently in a segment
                if inversed_sum[i] < self.EPSILON:
                    # The current row is empty
                    # Only add the segment if it contains at least min_num_rows
                    if i - start >= min_num_rows:
                        segments.append((start, i))
                    start = None
            else:
                # We are currently not in a segment
                if inversed_sum[i] < self.EPSILON:
                    # The current row is empty
                    count_empty_rows += 1
                else:
                    # The current row is not empty and the previous ones were
                    if count_empty_rows >= min_num_empty_rows:
                        start = i
                    count_empty_rows = 0
        if start is not None and len(inversed_sum) - start >= min_num_rows:
            segments.append((start, len(inversed_sum)))

        return segments

    def compile(
        self,
        data_path: str,
        destination_path: str,
        scrape_result: Optional[ScrapeResult] = None,
    ) -> Tuple[List[CompilationResult], Dict[str, Any]]:
        """
        Compile the given data into a webpage using Jekyll.

        Args:
            data_path: The path to the repository to compile.
            destination_path: The path to save the compiled data to.
            scrape_result: The scrape that produced the data.

        Returns:
            List[CompilationResult]: The result of the compilation.
            Dict[str, Any]: The information about the compilation.

        Raises:
            CompilationError: If the compilation fails.
        """
        assert scrape_result is not None

        # This compile method is a bit hacky as it performs some sort of filtering
        # during compilation. This is not ideal and should be done before and after
        # with some file filters or compilation filters.

        infos: Dict[str, Any] = {}
        pdf_filename: str = data_path
        if not os.path.exists(pdf_filename):
            raise CompilationError(f"The file {pdf_filename} does not exist.")

        assert "page_count" in scrape_result.additional_info
        total_num_pages = scrape_result.additional_info["page_count"]
        page_number = self.get_page_number(total_num_pages)
        infos["page_number"] = page_number

        # Generate the image
        success, image = self.generate_sheet_image(pdf_filename, page_number)
        if not success:
            raise CompilationError(f"Could not generate image from {pdf_filename}")
        assert image is not None

        # Filter the image
        self.filter(image)

        # Crop the image to keep only the title and the first measure
        segments = self.segment(np.mean(np.array(image), axis=2))
        if page_number == 1:
            segments = segments[1:]  # Remove the title

        compilation_results: List[CompilationResult] = []
        for i, (start, end) in enumerate(segments):
            # Crop the segment
            cropped_image = image.crop((0, start, image.width, end))

            # Remove left and right empty space
            if self._crop_sides:
                cropped_image = cropped_image.crop(
                    ImageOps.invert(cropped_image).getbbox()
                )

            # Save the cropped image
            image_filename = os.path.join(
                destination_path, f"{scrape_result.instance_name}_{i}.png"
            )
            cropped_image.save(image_filename)
            compilation_result = CompilationResult(
                data_path=None,
                rendering_path=image_filename,
                category="music",
            )
            compilation_results.append(compilation_result)

        return compilation_results, infos
