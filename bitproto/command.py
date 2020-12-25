"""
bitproto.command
~~~~~~~~~~~~~~~~

Command inteface.
"""

import argparse

from bitproto.__version__ import __version__, __description__
from bitproto.parser import parse
from bitproto.errors import ParserError

EPILOG = """
example usage:

  bitproto c example.bitproto       build c language file
  bitproto go example.bitproto      build go language file
  bitproto py example.bitproto      build python language file
  bitproto -c example.bitproto      validate bitproto file syntax
  bitproto c example.bitproto out   build c language file to directory out
"""


def build_arg_parser() -> argparse.ArgumentParser:
    args_parser = argparse.ArgumentParser(
        description=__description__,
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    args_parser.add_argument(
        "language",
        metavar="lang",
        type=str,
        choices=["c", "go", "py"],
        nargs="?",
        help="one of: c, go, py",
    )
    args_parser.add_argument(
        "filepath", metavar="file", type=str, help="proto file path"
    )
    args_parser.add_argument(
        "-c", "--check", dest="check", action="store_true", help="check proto syntax"
    )
    args_parser.add_argument(
        "outdir", metavar="out", type=str, nargs="?", help="output directory"
    )
    args_parser.add_argument(
        "-v",
        "--version",
        dest="version",
        action="version",
        help="show version",
        version="%(prog)s {0}".format(__version__),
    )
    args_parser._positionals.title = "arguments"
    args_parser._optionals.title = "options"
    return args_parser


def run_bitproto() -> None:
    args_parser = build_arg_parser()
    args = args_parser.parse_args()

    # Parse:
    try:
        parse(args.filepath)
    except ParserError as error:
        args_parser.exit(1, message=str(error))

    if args.check:  #  Checks only.
        args_parser.exit(0, message="syntax ok")


if __name__ == "__main__":
    run_bitproto()
