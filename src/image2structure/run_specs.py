from typing import TypeVar, Dict, Callable, Union

import datetime

from image2structure.runner import Runner
from image2structure.fetch.fetcher import Fetcher
from image2structure.filter.file_filters.file_filter import FileFilter
from image2structure.compilation.compiler import Compiler
from image2structure.filter.rendering_filters.rendering_filter import RenderingFilter


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
    from image2structure.filter.rendering_filters.non_trivial_rendering_filter import (
        NonTrivialRenderingFilter,
    )
    from image2structure.filter.file_filters.repo_filter import (
        RepoFilter,
    )
    from image2structure.filter.fetch_filters.github_fetch_filter import (
        GitHubFetchFilter,
    )
    from image2structure.compilation.webpage.driver import ScreenshotOptions
    import imagehash

    fetcher = GitHubFetcher(
        date_created_after=date_created_after,
        date_created_before=date_created_before,
        subcategory=subcategory,
        timeout=timeout,
        max_size_kb=max_size_kb,
        verbose=verbose,
    )

    fetch_filters = [GitHubFetchFilter()]

    file_filters = [
        RepoFilter(
            min_num_lines=10,
            has_more_than_readme=True,
            max_num_files_code=5,
            max_num_assets=5,
            max_num_lines_code=1000,
            max_num_lines_style=2000,
        )
    ]

    compiler = WebpageCompiler(
        port=port,
        timeout=timeout,
        verbose=verbose,
        num_max_actions=0,  # Random clicks are disabled
        screenshot_options=ScreenshotOptions(),
    )

    rendering_filters = [
        NonTrivialRenderingFilter(
            hashfunc=imagehash.average_hash,
            hash_size_white_imgs=8,
            hash_size_other_imgs=5,
            max_background_percentage=95.0,
            threshold_white_percentage=50.0,
            verbose=False,
        )
    ]

    return Runner(
        fetcher=fetcher,
        fetch_filters=fetch_filters,
        file_filters=file_filters,
        compiler=compiler,
        rendering_filters=rendering_filters,
    )
