from dataclasses import dataclass
from typing import List

from image2structure.fetch.fetcher import Fetcher
from image2structure.filter.file_filter import FileFilter
from image2structure.compilation.compiler import Compiler
from image2structure.postprocessing.post_processor import PostProcessor


@dataclass
class Runner:
    """Everything needed to run the pipeline."""

    # The fetcher to use
    fetcher: Fetcher

    # The file filters to use
    file_filters: List[FileFilter]

    # The compiler to use
    compiler: Compiler

    # The post processors to use
    post_processors: List[PostProcessor]
