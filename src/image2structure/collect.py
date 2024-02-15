from typing import Dict, Tuple, List, Any
from dotenv import load_dotenv
from dataclasses import asdict

import argparse
import datetime
import json
import os
import shutil

from .runner import Runner
from .run_specs import _RUNNER_REGISTRY
from image2structure.fetch.fetcher import ScrapeResult
from image2structure.filter.utils import FilterError
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
        "--num-instances-at-once",
        type=int,
        default=50,
        help="The number of instances to scrape at once",
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

    # Cleanup function
    def cleanup(ided_instance_name: str) -> None:
        path_structure: str = os.path.join(structure_path, ided_instance_name)
        if os.path.exists(path_structure):
            shutil.rmtree(path_structure)
        path_image: str = os.path.join(image_path, f"{ided_instance_name}.png")
        if os.path.exists(path_image):
            os.remove(path_image)
        path_metadata: str = os.path.join(metadata_path, f"{ided_instance_name}.json")
        if os.path.exists(path_metadata):
            os.remove(path_metadata)

    # Scrape the data
    while num_instances_collected < args.num_instances:
        scrape_results: List[ScrapeResult] = runner.fetcher.scrape(
            args.num_instances_at_once
        )
        for scrape_result in scrape_results:
            # Flag to continue to the next instance
            should_continue: bool = False

            # Perform first filters: fetcher filtersf
            for filter in runner.fetch_filters:
                try:
                    accepted = filter.filter(scrape_result)
                    if not accepted:
                        print(
                            f"Data did not pass fetcher filter {filter.name}: {infos}"
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
            ided_instance_name: str = (
                f"{num_instances_collected:04d}_{scrape_result.instance_name}"
            )
            instance_structure_path = os.path.join(structure_path, ided_instance_name)
            metadata = {
                # Add all the ScrapeResult fields to the metadata
                **{k: v for k, v in asdict(scrape_result).items()},
                # Add additional metadata
                "category": args.category,
                "date": datetime.datetime.now().isoformat(),
                "instance_structure_path": instance_structure_path,
            }
            scrape_result.instance_name = ided_instance_name
            try:
                runner.fetcher.download(structure_path, scrape_result)
                num_instances_downloaded += 1
            except DownloadError as e:
                print(f"Failed to download data: {e}")
                cleanup(ided_instance_name)
                continue

            # Run file filters
            for filter in runner.file_filters:
                try:
                    accepted, infos = filter.filter(instance_structure_path)
                    if not accepted:
                        print(f"Data did not pass file filter {filter}: {infos}")
                        cleanup(ided_instance_name)
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
                cleanup(ided_instance_name)
                continue

            # Compile the data
            compiled_image_path: str = os.path.join(
                image_path, f"{ided_instance_name}.png"
            )
            try:
                compilation_info: Dict[str, Any] = runner.compiler.compile(
                    instance_structure_path, compiled_image_path
                )
                num_instances_compiled += 1
                if compilation_info:
                    metadata["compilation_info"] = compilation_info
            except CompilationError as e:
                print(f"Failed to compile data: {e}")
                cleanup(ided_instance_name)
                continue

            # Last filters: render filters
            for filter in runner.rendering_filters:
                try:
                    accepted, infos = filter.check_and_accept_image(compiled_image_path)
                    if not accepted:
                        print(f"Data did not pass post-filter {filter}: {infos}")
                        should_continue = True
                        break
                    elif infos:
                        if "rendering_filters" not in metadata:
                            metadata["rendering_filters"] = {}
                        metadata["rendering_filters"][filter.name] = infos
                except FilterError as e:
                    print(f"Failed to run rendering filter {filter.name}: {e}")
                    should_continue = True
                    break
            if should_continue:
                cleanup(ided_instance_name)
                continue

            # Save the metadata
            instance_metadata_path: str = os.path.join(
                metadata_path, f"{ided_instance_name}.json"
            )
            with open(instance_metadata_path, "w") as f:
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


def get_runner_from_args(args: argparse.Namespace) -> Runner:
    runner_name: str = args.runner_name
    runner_info = _RUNNER_REGISTRY[runner_name]
    runner_func = runner_info["func"]
    runner_args = {arg: getattr(args, arg) for arg in runner_info["args_info"].keys()}
    runner_args["verbose"] = args.verbose
    runner_args["date_created_after"] = args.date_from
    runner_args["date_created_before"] = args.date_to
    runner_args["subcategory"] = args.category
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
