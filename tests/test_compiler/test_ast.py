from dataclasses import dataclass

from bitproto._ast import (BooleanConstant, BooleanOption, Comment, Constant,
                           IntegerConstant, IntegerOption, Node, Option, Scope,
                           StringConstant, StringOption, cache_if_frozen)
from bitproto.utils import frozen


def test_cache_if_frozen() -> None:
    counter: int = 0

    @frozen
    @dataclass
    class N(Node):
        @cache_if_frozen
        def increment(self, delta: int) -> int:
            nonlocal counter
            counter += delta
            return counter

    n = N()
    assert n.increment(1) == 1
    assert n.increment(1) == 1
    assert counter == 1

    assert n.increment(2) == 3
    assert counter == 3


def test_comment() -> None:
    c = Comment(token="// This is a line of comment.")
    assert c.content() == "This is a line of comment."


def test_option() -> None:
    assert isinstance(Option.from_value(1), IntegerOption)
    assert isinstance(Option.from_value(False), BooleanOption)
    assert isinstance(Option.from_value(""), StringOption)


def test_constant() -> None:
    assert isinstance(Constant.from_value(1), IntegerConstant)
    assert isinstance(Constant.from_value(False), BooleanConstant)
    assert isinstance(Constant.from_value(""), StringConstant)


def test_scope_push_member() -> None:
    pass
