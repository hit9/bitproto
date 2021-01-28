"""
bitproto._main
~~~~~~~~~~~~~~

Entry inteface.
"""

import argparse

from bitproto import __description__, __version__
from bitproto.errors import NoLanguageArgument, ParserError, RendererError
from bitproto.linter import lint
from bitproto.parser import parse
from bitproto.renderer import render, renderer_registry
from bitproto.utils import fatal

EPILOG = """
example usage:

  bitproto c example.bitproto       build c language file
  bitproto go example.bitproto      build go language file
  bitproto py example.bitproto      build python language file
  bitproto -c example.bitproto      validate bitproto file syntax
  bitproto c example.bitproto out   build c language file to directory out
  bitproto c example.bitproto -q    option -q to disable builtin linter
  bitproto c example.bitproto -O    enable performance optimization in traditional mode
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
        "-O",
        "--optimize",
        dest="enable_optimize",
        action="store_true",
        help="enable performance optimization in traditional mode",
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
    main(
        args.filepath,
        lang=args.language,
        outdir=args.outdir,
        disable_linter=args.disable_linter,
        check=args.check,
    )


def main(
    filepath: str,
    lang: str = "",
    outdir: str = "",
    disable_linter: bool = False,
    check: bool = False,
) -> None:
    # Parse
    try:
        proto = parse(filepath)
    except ParserError as error:
        fatal(error.colored())
    except IOError as error:
        fatal(str(error))

    # Lint
    if not disable_linter:
        lint_warnings = lint(proto)

    if check:
        if lint_warnings > 0:
            fatal()
        return

    # Render
    if not lang:
        fatal(str(NoLanguageArgument()))

    try:
        render(proto, lang, outdir=outdir)
    except RendererError as error:
        fatal(error.colored())
    except IOError as error:
        fatal(str(error))


if __name__ == "__main__":
    run_bitproto()
