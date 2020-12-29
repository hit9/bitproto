"""
bitproto.command
~~~~~~~~~~~~~~~~

Command inteface.
"""

import argparse

from bitproto.__version__ import __description__, __version__
from bitproto.errors import ParserError, RendererError
from bitproto.parser import parse
from bitproto.renderer import get_renderer_registry, render

EPILOG = """
example usage:

  bitproto c example.bitproto       build c language file
  bitproto go example.bitproto      build go language file
  bitproto py example.bitproto      build python language file
  bitproto -c example.bitproto      validate bitproto file syntax
  bitproto c example.bitproto out   build c language file to directory out
"""


def build_arg_parser() -> argparse.ArgumentParser:
    supported_languages = list(get_renderer_registry().keys())
    args_parser = argparse.ArgumentParser(
        description=__description__,
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    args_parser.add_argument(
        "language",
        metavar="lang",
        type=str,
        choices=supported_languages,
        nargs="?",
        help="one of: {0}".format(", ".join(supported_languages)),
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

    # Parse
    try:
        proto = parse(args.filepath)
    except ParserError as error:
        args_parser.exit(1, message=str(error))

    if args.check:  #  Checks only.
        args_parser.exit(0, message="syntax ok")

    # Render
    try:
        render(proto, args.language, outdir=args.outdir)
    except RendererError as error:
        args_parser.exit(1, message=str(error))


if __name__ == "__main__":
    run_bitproto()
