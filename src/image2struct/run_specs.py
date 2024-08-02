from typing import TypeVar, Dict, Callable, Union, List
from dotenv import load_dotenv

import datetime
import imagehash
import os

from image2struct.runner import Runner
from image2struct.filter.file_filters.toxicity_filter import ToxicityFilter
from image2struct.filter.fetch_filters.date_fetch_filter import DateFetchFilter
from image2struct.filter.fetch_filters.after_date_fetch_filter import (
    AfterDateFetchFilter,
)


F = TypeVar("F", bound=Callable[..., Runner])

_RUNNER_REGISTRY: Dict[
    str, Dict[str, Union[Callable[..., Runner], Dict[str, str]]]
] = {}


def register_runner(name: str, args_info=None) -> Callable[[F], F]:
    """Register a runner with argument metadata."""
    args_info = args_info or {}

    def wrapper(func: F) -> F:
        if name in _RUNNER_REGISTRY:
            raise ValueError(f"Runner {name} is already registered.")
        _RUNNER_REGISTRY[name] = {"func": func, "args_info": args_info}
        return func

    return wrapper


def get_toxicity_filter() -> ToxicityFilter:
    """Get a toxicity filter."""
    load_dotenv()
    return ToxicityFilter(
        api_key=os.getenv("PERSPECTIVE_API_KEY"),
        toxicity_threshold=0.5,
        sexually_explicit_threshold=0.3,
    )


@register_runner(
    "webpage",
    args_info={"language": str, "port": int, "max_size_kb": int},
)
def get_webpage_runner(
    date_created_after: datetime.datetime,
    date_created_before: datetime.datetime,
    timeout: int,
    num_instances: int,
    language: str,
    port: int,
    max_size_kb: int,
    max_instances_per_date: int,
    verbose: bool,
) -> Runner:
    """Get a runner for webpage data."""
    from image2struct.compilation.webpage_compiler import WebpageCompiler
    from image2struct.fetch.github_fetcher import GitHubFetcher
    from image2struct.filter.rendering_filters.non_trivial_rendering_filter import (
        NonTrivialRenderingFilter,
    )
    from image2struct.filter.file_filters.repo_filter import (
        RepoFilter,
    )
    from image2struct.filter.fetch_filters.github_fetch_filter import (
        GitHubFetchFilter,
    )
    from image2struct.compilation.webpage.driver import ScreenshotOptions

    fetcher = GitHubFetcher(
        date_created_after=date_created_after,
        date_created_before=date_created_before,
        language=language,
        timeout=timeout,
        max_size_kb=max_size_kb,
        verbose=verbose,
    )

    fetch_filters = [
        AfterDateFetchFilter(date_created_after),
        GitHubFetchFilter(),
        DateFetchFilter(max_instances_per_date=max_instances_per_date),
    ]

    file_filters = [
        RepoFilter(
            min_num_lines=10,
            has_more_than_readme=True,
            max_num_files_code=5,
            max_num_assets=5,
            max_num_lines_code=1000,
            max_num_lines_style=2000,
        ),
        get_toxicity_filter(),
    ]

    compiler = WebpageCompiler(
        port=port,
        timeout=timeout,
        verbose=verbose,
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


@register_runner(
    "latex",
    args_info={"subcategory": str},
)
def get_latex_runner(
    date_created_after: datetime.datetime,
    date_created_before: datetime.datetime,
    timeout: int,
    num_instances: int,
    subcategory: str,
    max_instances_per_date: int,
    verbose: bool,
) -> Runner:
    """Get a runner for webpage data."""
    from image2struct.compilation.latex_compiler import LatexCompiler
    from image2struct.fetch.arxiv_fetcher import ArxivFetcher
    from image2struct.filter.rendering_filters.non_trivial_rendering_filter import (
        NonTrivialRenderingFilter,
    )
    from image2struct.filter.fetch_filters.fetch_filter import FetchFilter
    from image2struct.filter.file_filters.file_filter import FileFilter

    fetcher = ArxivFetcher(
        date_created_after=date_created_after,
        date_created_before=date_created_before,
        subcategory=subcategory,
        timeout=timeout,
        verbose=verbose,
    )

    fetch_filters: List[FetchFilter] = [
        AfterDateFetchFilter(date_created_after),
        DateFetchFilter(max_instances_per_date=max_instances_per_date),
    ]
    file_filters: List[FileFilter] = [get_toxicity_filter()]

    compiler = LatexCompiler(
        crop=True,
        timeout=timeout,
        max_elt_per_category=3,
        num_instances=num_instances,
        verbose=verbose,
    )

    rendering_filters = [
        NonTrivialRenderingFilter(
            hashfunc=imagehash.average_hash,
            hash_size_white_imgs=8,
            hash_size_other_imgs=5,
            max_background_percentage=99.0,
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


@register_runner(
    "musicsheet",
    args_info={"subcategory": str},
)
def get_musicsheet_runner(
    date_created_after: datetime.datetime,
    date_created_before: datetime.datetime,
    timeout: int,
    num_instances: int,
    subcategory: str,
    max_instances_per_date: int,
    verbose: bool,
) -> Runner:
    """Get a runner for webpage data."""
    from image2struct.compilation.music_compiler import MusicCompiler
    from image2struct.fetch.imslp_fetcher import ImslpFetcher
    from image2struct.filter.rendering_filters.non_trivial_rendering_filter import (
        NonTrivialRenderingFilter,
    )
    from image2struct.filter.fetch_filters.fetch_filter import FetchFilter
    from image2struct.filter.file_filters.file_filter import FileFilter

    fetcher = ImslpFetcher(
        date_created_after=date_created_after,
        date_created_before=date_created_before,
        timeout=timeout,
        verbose=verbose,
    )

    fetch_filters: List[FetchFilter] = [
        AfterDateFetchFilter(date_created_after),
        DateFetchFilter(max_instances_per_date=max_instances_per_date),
    ]
    file_filters: List[FileFilter] = []

    compiler = MusicCompiler(
        crop_sides=True,
        timeout=timeout,
        verbose=verbose,
    )

    rendering_filters = [
        NonTrivialRenderingFilter(
            hashfunc=imagehash.average_hash,
            hash_size_white_imgs=8,
            hash_size_other_imgs=5,
            max_background_percentage=99.0,
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
