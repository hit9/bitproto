import os

from bitproto.linter import lint
from bitproto.parser import GrammarError, parse


def bitproto_filepath(filename: str) -> str:
    return os.path.join(os.path.dirname(__file__), "linter-cases", filename)


def test_lint_drone() -> None:
    assert lint(parse(bitproto_filepath("drone.bitproto"))) == 0


def test_lint_definition_indent() -> None:
    assert lint(parse(bitproto_filepath("definition_indent.bitproto"))) > 0


def test_lint_alias_naming_style() -> None:
    assert lint(parse(bitproto_filepath("alias_naming_style.bitproto"))) > 0


def test_lint_constant_naming_style() -> None:
    assert lint(parse(bitproto_filepath("constant_naming_style.bitproto"))) > 0


def test_lint_enum_naming_style() -> None:
    assert lint(parse(bitproto_filepath("enum_naming_style.bitproto"))) > 0


def test_lint_enum_contains_0() -> None:
    assert lint(parse(bitproto_filepath("enum_contains_0.bitproto"))) > 0


def test_lint_enum_field_naming_style() -> None:
    assert lint(parse(bitproto_filepath("enum_field_naming_style.bitproto"))) > 0


def test_lint_message_naming_style() -> None:
    assert lint(parse(bitproto_filepath("message_naming_style.bitproto"))) > 0


def test_lint_message_field_naming_style() -> None:
    assert lint(parse(bitproto_filepath("message_field_naming_style.bitproto"))) > 0
