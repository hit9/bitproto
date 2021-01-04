"""
bitproto.command
~~~~~~~~~~~~~~~~

Command inteface.
"""

import argparse

from bitproto import __description__, __version__
from bitproto.errors import ParserError, RendererError
from bitproto.linter import lint
from bitproto.parser import parse
from bitproto.renderer import render, renderer_registry

EPILOG = """
example usage:

  bitproto c example.bitproto       build c language file
  bitproto go example.bitproto      build go language file
  bitproto py example.bitproto      build python language file
  bitproto -c example.bitproto      validate bitproto file syntax
  bitproto c example.bitproto out   build c language file to directory out
  bitproto c example.bitproto -q    option -q to disable builtin linter
"""


def build_arg_parser() -> argparse.ArgumentParser:
    supported_languages = list(renderer_registry.keys())
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
        "-q",
        "--disable-lint",
        dest="disable_linter",
        action="store_true",
        help="disable linter",
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

    exit_code = 0

    # Parse
    try:
        proto = parse(args.filepath)
    except ParserError as error:
        args_parser.exit(1, message=error.colored())

    if not args.disable_linter:
        if lint(proto) > 0:
            exit_code = 1

    if args.check:  #  Checks only.
        args_parser.exit(exit_code)

    # Render
    try:
        render(proto, args.language, outdir=args.outdir)
    except RendererError as error:
        args_parser.exit(1, message=error.colored())


if __name__ == "__main__":
    run_bitproto()
