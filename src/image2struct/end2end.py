from typing import List
from dotenv import load_dotenv

import argparse
import os
import threading


def get_args_parser() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scrape data")

    # Common arguments
    parser.add_argument(
        "--destination-path",
        type=str,
        default="./data",
        help="The path to save the scraped data to",
    )
    parser.add_argument(
        "--type",
        type=str,
        required=True,
        help="The type of data to collect (e.g. webpage, latex)",
    )
    parser.add_argument(
        "--huggingface-base",
        type=str,
        required=True,
        help="The base path to the huggingface dataset. The dataset will be saved to {huggingface-base}/{type}",
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
        default=25,
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
        type=str,
        required=True,
        help="The earliest date to scrape data from",
    )
    parser.add_argument(
        "--date-to",
        type=str,
        required=True,
        help="The latest date to scrape data from",
    )
    return parser.parse_args()


def main():
    load_dotenv()
    args: argparse.Namespace = get_args_parser()

    command_base: str = (
        f"image2struct-collect --num-instances {args.num_instances}"
        f" --num-instances-at-once {args.num_instances_at_once}"
        f" --max-instances-per-date {args.max_instances_per_date}"
        f" --date-from {args.date_from} --date-to {args.date_to}"
        f" --timeout {args.timeout} --destination-path {args.destination_path}"
        " --verbose"
    )
    collect_commands: List[str] = []
    if args.type == "webpage":
        for i, category in enumerate(["css", "html", "javascript"]):
            webpage_suffix: str = (
                f"webpage --language {category} --port {4000 + i} --max_size_kb {100}"
            )
            collect_commands.append(
                f"{command_base} --tmp-path {args.destination_path}/tmp/{args.type}/{category} {webpage_suffix}"
                f" >> {args.destination_path}/logs/{args.type}/{category}.log"
            )
    elif args.type == "latex":
        for i, category in enumerate(
            ["cs", "econ", "math", "physics", "q-bio", "q-fin", "stat"]
        ):
            latex_suffix: str = f"latex --subcategory {category}"
            collect_commands.append(
                f"{command_base} --tmp-path {args.destination_path}/tmp/{args.type}/{category} {latex_suffix}"
                f" >> {args.destination_path}/logs/{args.type}/{category}.log"
            )
    elif args.type == "musicsheet":
        for i, category in enumerate(["music"]):
            music_suffix: str = f"musicsheet --subcategory {category}"
            collect_commands.append(
                f"{command_base} --tmp-path {args.destination_path}/tmp/{args.type}/{category} {music_suffix}"
                f" >> {args.destination_path}/logs/{args.type}/{category}.log"
            )
    else:
        raise ValueError(f"Invalid type: {args.type}")
    os.makedirs(f"{args.destination_path}/logs/{args.type}", exist_ok=True)

    # Run all the commands in parallel
    print("Running the following commands in parallel:")
    threads: List[threading.Thread] = []
    for command in collect_commands:
        print(f"\t- {command}")
        thread = threading.Thread(target=os.system, args=(command,))
        threads.append(thread)
        thread.start()
    print(f"Running {len(threads)} threads in parallel\n")

    for thread in threads:
        thread.join()

    # Upload the data to huggingface
    print(f"Uploading data to {args.huggingface_base}/{args.type}")
    upload_command: str = (
        f"image2struct-upload --data-path {args.destination_path}/{args.type}"
        f" --dataset-name {args.huggingface_base}/i2s-{args.type}"
    )
    print(f"Running the following command:\n\t- {upload_command}")
    # os.system(upload_command)
    print(f"Data uploaded to {args.huggingface_base}/i2s-{args.type}")
