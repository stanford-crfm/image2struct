from typing import TypeVar, Dict, Callable, Union

import datetime

from image2structure.runner import Runner
from image2structure.fetch.fetcher import Fetcher
from image2structure.filter.file_filter import FileFilter
from image2structure.compilation.compiler import Compiler
from image2structure.postprocessing.post_processor import PostProcessor


F = TypeVar("F", bound=Callable[..., Runner])

_RUNNER_REGISTRY: Dict[str, Dict[str, Union[F, Dict[str, type]]]] = {}


def register_runner(name: str, args_info=None):
    """Register a runner with argument metadata."""
    args_info = args_info or {}

    def wrapper(func: F) -> F:
        if name in _RUNNER_REGISTRY:
            raise ValueError(f"Runner {name} is already registered.")
        _RUNNER_REGISTRY[name] = {"func": func, "args_info": args_info}
        return func

    return wrapper


@register_runner("webpage", args_info={"timeout": int, "port": int, "max_size_kb": int})
def get_webpage_runner(
    date_created_after: datetime.datetime,
    date_created_before: datetime.datetime,
    subcategory: str,
    timeout: int,
    port: int,
    max_size_kb: int,
    verbose: bool,
) -> Runner:
    """Get a runner for webpage data."""
    from image2structure.compilation.webpage_compiler import WebpageCompiler
    from image2structure.fetch.github_fetcher import GitHubFetcher
    from image2structure.postprocessing.new_image_post_processor import (
        NewImagePostProcessor,
    )

    fetcher = GitHubFetcher(
        date_created_after=date_created_after,
        date_created_before=date_created_before,
        subcategory=subcategory,
        timeout=timeout,
        port=port,
        max_size_kb=max_size_kb,
        verbose=verbose,
    )

    file_filters = []

    compiler = WebpageCompiler(
        port=port,
        timeout=timeout,
        verbose=verbose,
        num_max_actions=0,  # Random clicks are disabled
    )

    post_processors = [
        NewImagePostProcessor({"max_white_ratio": 0.99, "max_similarity_ratio": 0.99})
    ]

    return Runner(fetcher, file_filters, compiler, post_processors)
