from dataclasses import dataclass
from typing import List

from image2struct.fetch.fetcher import Fetcher
from image2struct.compilation.compiler import Compiler
from image2struct.filter.fetch_filters.fetch_filter import FetchFilter
from image2struct.filter.file_filters.file_filter import FileFilter
from image2struct.filter.rendering_filters.rendering_filter import RenderingFilter


@dataclass
class Runner:
    """Everything needed to run the pipeline."""

    # The fetcher to use
    fetcher: Fetcher

    # The fetch filters to use
    # These filters will run on the ScrapeResult
    # without downloading the file and only using the metadata
    # Examples: remove duplicates, filter by date, etc.
    fetch_filters: List[FetchFilter]

    # The file filters to use
    # These filters will run on the downloaded file
    # Examples: check the file size, the number of assets
    file_filters: List[FileFilter]

    # The compiler to use
    compiler: Compiler

    # The rendering filters to use
    # These filters will run on the compiled image
    # Examples: check that the output is not fully white
    rendering_filters: List[RenderingFilter]
