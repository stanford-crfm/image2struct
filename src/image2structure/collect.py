import argparse
import datetime

from .runner import Runner
from .run_specs import _RUNNER_REGISTRY


def get_args_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Scrape data")

    # Common arguments
    parser.add_argument(
        "--data-type",
        type=str,
        required=True,
        choices=["latex", "webpage"],
        help="The type of data to scrape",
    )
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

    for runner_name, runner_info in _RUNNER_REGISTRY.items():
        subparser = subparsers.add_parser(runner_name, help=f"{runner_name} runner")
        for arg, arg_type in runner_info["args_info"].items():
            subparser.add_argument(f"--{arg}", type=arg_type, required=True)

    return parser


def main() -> None:
    parser: argparse.ArgumentParser = get_args_parser()
    args = parser.parse_args()

    runner_name = args.runner_name
    if runner_name:
        runner_info = _RUNNER_REGISTRY[runner_name]
        runner_func = runner_info["func"]
        # Extract runner-specific arguments using metadata
        runner_args = {arg: getattr(args, arg) for arg in runner_info["args_info"]}
        runner_args["verbose"] = args.verbose
        runner = runner_func(**runner_args)
        # Here you can use the runner along with the common arguments as needed
        print(runner)
    else:
        parser.print_help()
