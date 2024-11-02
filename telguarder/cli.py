"""telguarder cli tool."""

from __future__ import annotations

import argparse
import asyncio
import logging

from rich.console import Console
from rich.logging import RichHandler
from rich.theme import Theme

from telguarder import TelguarderClient, __version__

console = Console(theme=Theme({"error": "bold red", "success": "bold green", "info": "bold blue"}))


def main_parser() -> argparse.ArgumentParser:
    """Create the ArgumentParser with all relevant subparsers."""
    parser = argparse.ArgumentParser(description="A simple executable to use and test the library.")
    parser.add_argument("-v", "--verbose", action="count", default=0, help="Logging verbosity level")
    parser.add_argument("-V", "--version", action="version", version=f"%(prog)s v{__version__}")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")

    subparsers = parser.add_subparsers(dest="cmd")
    subparsers.required = True

    #
    # Login
    #
    lookup_parser = subparsers.add_parser("lookup", description="Log in")
    lookup_parser.add_argument("phone_number", type=str, nargs="+", help="Phone number(s) to lookup")
    lookup_parser.set_defaults(func=lookup)

    return parser


async def lookup(args):
    """Login."""
    async with TelguarderClient() as client:
        result = await client.lookup(args.phone_number)
        console.print(result)


def main():
    """Run."""
    parser = main_parser()
    args = parser.parse_args()

    if args.debug:
        logging_level = logging.DEBUG
    elif args.verbose:
        logging_level = 50 - (args.verbose * 10)
        if logging_level <= 0:
            logging_level = logging.NOTSET
    else:
        logging_level = logging.ERROR

    logging.basicConfig(
        level=logging_level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(console=console)],
    )

    asyncio.run(args.func(args))


if __name__ == "__main__":
    main()
