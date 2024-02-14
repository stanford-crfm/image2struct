from typing import Dict, Tuple, List, Any
from dotenv import load_dotenv

import argparse
import datetime
import json
import os
import shutil

from .runner import Runner
from .run_specs import _RUNNER_REGISTRY
from image2structure.fetch.fetcher import ScrapeResult
from image2structure.filter.filter import FilterError
from image2structure.compilation.compiler import CompilationError
from image2structure.fetch.fetcher import DownloadError


def get_args_parser() -> (
    Tuple[argparse.ArgumentParser, Dict[str, argparse.ArgumentParser]]
):
    parser = argparse.ArgumentParser(description="Scrape data")

    # Common arguments
    parser.add_argument(
        "--category",
        type=str,
        required=True,
        help="The category of data to scrape, depending on the data type\n"
        " - For 'latex', the category is the name of the arXiv category\n"
        " - For 'webpage', the category is the main language defined by GitHub",
    )
    parser.add_argument(
        "--destination-path",
        type=str,
        default="./data",
        help="The path to save the scraped data to",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=10,
        help="The maximum time in seconds to allow to download one file",
    )
    parser.add_argument(
        "--num-instances",
        type=int,
        default=100,
        help="The number of instances to scrape",
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


def run(runner: Runner, args: argparse.Namespace) -> None:
    # Create the output directories
    output_path: str = os.path.join(
        args.destination_path, args.runner_name, args.category
    )
    image_path: str = os.path.join(output_path, "images")
    structure_path: str = os.path.join(output_path, "structure")
    metadata_path: str = os.path.join(output_path, "metadata")
    for path in [output_path, image_path, structure_path, metadata_path]:
        os.makedirs(path, exist_ok=True)

    # Variables to keep track of the progress
    num_instances_collected: int = 0
    num_instances_downloaded: int = 0
    num_instances_compiled: int = 0

    # Scrape the data
    while num_instances_collected < args.num_instances:
        scrape_results: List[ScrapeResult] = runner.fetcher.scrape()
        for scrape_result in scrape_results:
            # Download the data
            ided_instance_name: str = (
                f"{num_instances_collected:04d}_{scrape_result.instance_name}"
            )
            download_path = os.path.join(structure_path, ided_instance_name)
            metadata = {
                # Add all the ScrapeResult fields to the metadata
                **{k: v for k, v in scrape_result._asdict().items()},
                # Add additional metadata
                "category": args.category,
                "date": datetime.datetime.now().isoformat(),
                "download_path": download_path,
            }
            try:
                runner.fetcher.download(download_path, scrape_result)
                num_instances_downloaded += 1
            except DownloadError as e:
                print(f"Failed to download data: {e}")
                continue

            # Run filters
            for filter in runner.file_filters:
                try:
                    accepted, infos = filter.filter(download_path)
                    if not accepted:
                        print(f"Data did not pass filter {filter}: {infos}")
                        shutil.rmtree(download_path)
                        continue
                    elif infos:
                        if "filters" not in metadata:
                            metadata["filters"] = {}
                        metadata["filters"][filter.__class__.__name__] = infos
                except FilterError as e:
                    print(f"Failed to filter data: {e}")
                    continue

            # Compile the data
            image_path: str = os.path.join(image_path, f"{ided_instance_name}.png")
            try:
                compilation_info: Dict[str, Any] = runner.compiler.compile(
                    image_path, args.timeout, metadata
                )
                num_instances_compiled += 1
                if compilation_info:
                    metadata["compilation_info"] = compilation_info
            except CompilationError as e:
                print(f"Failed to compile data: {e}")
                continue

            # Post-process filters
            for filter in runner.post_processors:
                try:
                    accepted, infos = filter.check_and_accept_image(image_path)
                    if not accepted:
                        print(f"Data did not pass post-filter {filter}: {infos}")
                        shutil.rmtree(download_path)
                        continue
                    elif infos:
                        if "post_filters" not in metadata:
                            metadata["post_filters"] = {}
                        metadata["post_filters"][filter.__class__.__name__] = infos
                except FilterError as e:
                    print(f"Failed to post-filter data: {e}")
                    continue

            # Save the metadata
            metadata_path: str = os.path.join(
                metadata_path, f"{ided_instance_name}.json"
            )
            with open(metadata_path, "w") as f:
                json.dump(metadata, f, indent=4)

            # Increment the number of instances collected
            num_instances_collected += 1
            print(f"Instance {ided_instance_name} collected!")
            if num_instances_collected >= args.num_instances:
                break

    print("Scraping complete!")
    print(f" - {num_instances_downloaded} instances downloaded")
    print(f" - {num_instances_compiled} instances compiled")
    print(f" - {num_instances_collected} instances collected")


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

    runner_name = args.runner_name
    runner_info = _RUNNER_REGISTRY[runner_name]
    runner_func = runner_info["func"]
    runner_args = {arg: getattr(args, arg) for arg in runner_info["args_info"].keys()}
    runner_args["verbose"] = args.verbose
    runner_args["date_created_after"] = args.date_from
    runner_args["date_created_before"] = args.date_to
    runner_args["subcategory"] = args.category
    runner = runner_func(**runner_args)

    print(runner)
