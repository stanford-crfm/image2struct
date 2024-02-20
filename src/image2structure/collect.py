from typing import Dict, Tuple, List, Any
from dotenv import load_dotenv
from dataclasses import asdict

import argparse
import datetime
import json
import os
import shutil
import tarfile

from .runner import Runner
from .run_specs import _RUNNER_REGISTRY
from image2structure.fetch.fetcher import ScrapeResult
from image2structure.filter.utils import FilterError
from image2structure.compilation.compiler import CompilationError, CompilationResult
from image2structure.fetch.fetcher import DownloadError


def get_args_parser() -> (
    Tuple[argparse.ArgumentParser, Dict[str, argparse.ArgumentParser]]
):
    parser = argparse.ArgumentParser(description="Scrape data")

    # Common arguments
    parser.add_argument(
        "--destination-path",
        type=str,
        default="./data",
        help="The path to save the scraped data to",
    )
    parser.add_argument(
        "--tmp-path",
        type=str,
        default="./data/tmp",
        help="The path to save the temporary files to",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="The maximum time in seconds to allow to download one file or compile it",
    )
    parser.add_argument(
        "--num-instances",
        type=int,
        default=100,
        help="The number of instances to scrape",
    )
    parser.add_argument(
        "--num-instances-at-once",
        type=int,
        default=50,
        help="The number of instances to scrape at once",
    )
    parser.add_argument(
        "--max-instances-per-date",
        type=int,
        default=40,
        help="The maximum number of instances to scrape per date",
    )
    parser.add_argument(
        "--date-from",
        type=lambda s: datetime.datetime.strptime(s, "%Y-%m-%d"),
        default=datetime.datetime.now() - datetime.timedelta(days=365),
        help="The earliest date to scrape data from",
    )
    parser.add_argument(
        "--date-to",
        type=lambda s: datetime.datetime.strptime(s, "%Y-%m-%d"),
        default=datetime.datetime.now(),
        help="The latest date to scrape data from",
    )
    parser.add_argument("--verbose", action="store_true", help="Print verbose output")

    # Setup for sub-commands (runners)
    subparsers = parser.add_subparsers(dest="runner_name", help="Available runners")
    subparsers_dict = {}

    for runner_name, runner_info in _RUNNER_REGISTRY.items():
        subparser = subparsers.add_parser(runner_name, help=f"{runner_name} runner")
        subparsers_dict[runner_name] = subparser  # Store the subparser
        for arg, arg_type in runner_info["args_info"].items():
            subparser.add_argument(f"--{arg}", type=arg_type, required=True)

    return parser, subparsers_dict


def num_files_in_dir(dir: str) -> int:
    return len(
        [name for name in os.listdir(dir) if os.path.isfile(os.path.join(dir, name))]
    )


def run(runner: Runner, args: argparse.Namespace) -> None:
    # Create the output directories
    output_path: str = os.path.join(args.destination_path, args.runner_name)
    os.makedirs(output_path, exist_ok=True)

    # Variables to keep track of the progress
    num_instances_compiled: int = 0
    num_instances_downloaded: int = 0
    num_instances_collected: Dict[str, int] = {}

    # Working directories
    tmp_dir: str = args.tmp_path
    tmp_structure_path = os.path.join(tmp_dir, "structure")
    tmp_image_path = os.path.join(tmp_dir, "images")

    # Scrape the data
    # Continue while num_instances_collected is empty or one of the category in num_instances_collected
    # is lower than args.num_instances
    while (
        not num_instances_collected
        or min(num_instances_collected.values()) < args.num_instances
    ):
        scrape_results: List[ScrapeResult] = runner.fetcher.scrape(
            args.num_instances_at_once
        )
        for scrape_result in scrape_results:
            # Create clean temporaty working directory
            if os.path.exists(tmp_dir):
                shutil.rmtree(tmp_dir)
            for path in [tmp_dir, tmp_structure_path, tmp_image_path]:
                os.makedirs(path, exist_ok=False)

            # Flag to continue to the next instance
            should_continue: bool = False

            # Perform first filters: fetcher filters
            for filter in runner.fetch_filters:
                try:
                    accepted = filter.filter(scrape_result)
                    if not accepted:
                        print(
                            f"Data did not pass fetcher filter {filter.name}: {scrape_result}"
                        )
                        should_continue = True
                        break
                except FilterError as e:
                    print(f"Failed to run fetch filter {filter.name}: {e}")
                    should_continue = True
                    break
            if should_continue:
                continue

            # Download the data
            metadata = {
                # Add all the ScrapeResult fields to the metadata
                **{k: v for k, v in asdict(scrape_result).items()},
                # Add additional metadata
                "date_scrapped": datetime.datetime.now().isoformat(),
            }
            # scrape_result.instance_name = ided_instance_name
            try:
                runner.fetcher.download(tmp_structure_path, scrape_result)
                num_instances_downloaded += 1
            except DownloadError as e:
                print(f"Failed to download data: {e}")
                continue

            # If extension is .tar.gz, extract the directory
            if scrape_result.instance_name.endswith(".tar.gz"):
                try:
                    with tarfile.open(
                        os.path.join(tmp_structure_path, scrape_result.instance_name),
                        "r:gz",
                    ) as tar:
                        scrape_result.instance_name = scrape_result.instance_name[:-7]
                        tar.extractall(
                            os.path.join(
                                tmp_structure_path, scrape_result.instance_name
                            )
                        )
                except tarfile.ReadError as e:
                    print(f"Failed to extract data: {e}")
                    continue

            # Run file filters
            download_path: str = os.path.join(
                tmp_structure_path, scrape_result.instance_name
            )
            for filter in runner.file_filters:
                try:
                    accepted, infos = filter.filter(download_path)
                    if not accepted:
                        print(f"Data did not pass file filter {filter}: {infos}")
                        should_continue = True
                        break
                    elif infos:
                        if "file_filters" not in metadata:
                            metadata["file_filters"] = {}
                        metadata["file_filters"][filter.name] = infos
                except FilterError as e:
                    print(f"Failed to run file filter {filter.name}: {e}")
                    should_continue = True
                    break
            if should_continue:
                continue

            # Compile the data
            try:
                compilation_results, compilation_info = runner.compiler.compile(
                    download_path, tmp_image_path, scrape_result
                )
                num_instances_compiled += 1
                if compilation_info:
                    metadata["compilation_info"] = compilation_info
            except CompilationError as e:
                print(f"Failed to compile data: {e}")
                continue

            # Last filters: render filters
            accepted_results: List[CompilationResult] = []
            for compilation_result in compilation_results:
                compiled_image_path: str = compilation_result.rendering_path
                should_be_saved: bool = True
                for filter in runner.rendering_filters:
                    try:
                        accepted, infos = filter.check_and_accept_image(
                            compiled_image_path
                        )
                        if not accepted:
                            print(f"Data did not pass post-filter {filter}: {infos}")
                            should_be_saved = False
                            break
                        elif infos:
                            if "rendering_filters" not in metadata:
                                metadata["rendering_filters"] = {}
                            metadata["rendering_filters"][filter.name] = infos
                    except FilterError as e:
                        print(f"Failed to run rendering filter {filter.name}: {e}")
                        should_be_saved = True
                        break
                if should_be_saved:
                    accepted_results.append(compilation_result)
            if should_continue:
                continue

            # Save the compiled data
            done: bool = False
            for compilation_result in accepted_results:
                category: str = compilation_result.category
                num_id: int = 0
                if category not in num_instances_collected:
                    # First time we collect this category
                    # Create the directories
                    for dir in ["metadata", "images", "structures", "assets"]:
                        os.makedirs(
                            os.path.join(output_path, category, dir), exist_ok=True
                        )
                    num_instances_collected[category] = 0
                else:
                    # Increment the number of instances collected
                    num_id = num_files_in_dir(
                        os.path.join(output_path, category, "metadata")
                    )

                # Copy shared metadata to compiled metadata
                compiled_metadata: Dict[str, Any] = {
                    **metadata,
                    "category": category,
                    "num_id": num_id,
                }

                # Save the metadata
                instance_metadata_path: str = os.path.join(
                    output_path, category, "metadata", f"{num_id}.json"
                )
                with open(instance_metadata_path, "w") as f:
                    json.dump(compiled_metadata, f, indent=4)

                # Save the image
                instance_image_path: str = os.path.join(
                    output_path, category, "images", f"{num_id}.png"
                )
                shutil.copy(compilation_result.rendering_path, instance_image_path)

                # Save the assets
                for asset_path in compilation_result.assets_path:
                    # All asset names should be unique
                    asset_name: str = os.path.basename(asset_path)
                    instance_asset_path: str = os.path.join(
                        output_path, category, "assets", asset_name
                    )
                    shutil.copy(asset_path, instance_asset_path)

                # Save the structure
                extension: str = (
                    os.path.splitext(compilation_result.data_path)[-1]
                    if "." in compilation_result.data_path
                    else ""
                )
                instance_structure_path: str = os.path.join(
                    output_path, category, "structures", f"{num_id}{extension}"
                )
                if os.path.isdir(compilation_result.data_path):
                    # Compress the directory in .tar.gz to the instance_structure_path
                    shutil.make_archive(
                        instance_structure_path,
                        "gztar",
                        compilation_result.data_path,
                    )
                else:
                    shutil.copy(compilation_result.data_path, instance_structure_path)

                # Increment the number of instances collected
                assert category in num_instances_collected
                num_instances_collected[category] += 1
                runner.compiler.acknowledge_compilation(category)
                print(f"Instance number {num_id} of category {category} collected")

                done = True
                for category in num_instances_collected.keys():
                    if num_instances_collected[category] < args.num_instances:
                        done = False
                        break
                if done:
                    break
            if done:
                break

    print("Scraping complete!")
    print(f" - {num_instances_downloaded} instances downloaded")
    print(f" - {num_instances_compiled} instances compiled")
    print(" - For each category:")
    for category, value in num_instances_collected.items():
        print(f"\t - {category}: {value} instances collected")


def get_runner_from_args(args: argparse.Namespace) -> Runner:
    runner_name: str = args.runner_name
    runner_info = _RUNNER_REGISTRY[runner_name]
    runner_func = runner_info["func"]
    runner_args = {arg: getattr(args, arg) for arg in runner_info["args_info"].keys()}
    runner_args["verbose"] = args.verbose
    runner_args["date_created_after"] = args.date_from
    runner_args["date_created_before"] = args.date_to
    runner_args["num_instances"] = args.num_instances
    runner_args["max_instances_per_date"] = args.max_instances_per_date
    runner_args["timeout"] = args.timeout
    runner = runner_func(**runner_args)
    return runner


def main() -> None:
    load_dotenv()
    parser, subparsers_dict = get_args_parser()
    args: argparse.Namespace

    try:
        args = parser.parse_args()
    except SystemExit:
        print("\nError parsing arguments")
        print("\n\n1. You must specify the shared arguments")
        parser.print_help()
        print("\n\n\n2. You must specify a runner along with its arguments")
        for runner_name, subparser in subparsers_dict.items():
            print(f"\nRunner: {runner_name}")
            subparser.print_help()
            print("")
        return

    runner: Runner = get_runner_from_args(args)
    run(runner, args)
