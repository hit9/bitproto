import pytest

from bitproto.utils import (
    cache,
    cached_property,
    cast_or_raise,
    conditional_cache,
    frozen,
    keep_case,
    pascal_case,
    snake_case,
    upper_case,
    override_docstring,
)


def test_cached_property() -> None:
    counter: int = 0

    class MyClass:
        @cached_property
        def value(self) -> int:
            nonlocal counter
            counter += 1
            return counter

    inst = MyClass()
    assert inst.value == 1
    assert inst.value == 1
    assert inst.value == 1
    assert counter == 1


def test_cache() -> None:
    counter: int = 0

    @cache
    def increment(delta: int) -> int:
        nonlocal counter
        counter += delta
        return counter

    assert increment(1) == 1
    assert increment(1) == 1  # cached
    assert counter == 1

    assert increment(2) == 3
    assert increment(2) == 3
    assert counter == 3


def test_conditional_cache() -> None:
    enabled_cache: bool = False
    counter: int = 0

    def condition(fn, args, kwds) -> bool:
        return enabled_cache

    @conditional_cache(condition)
    def increment(delta: int) -> int:
        nonlocal counter
        counter += delta
        return counter

    assert increment(1) == 1
    assert increment(1) == 2
    assert counter == 2

    enabled_cache = True

    assert increment(1) == 3
    assert increment(1) == 3
    assert counter == 3


def test_frozen() -> None:
    @frozen
    class MyClass:
        def __init__(self, name: str) -> None:
            self.name = name

    inst = MyClass(name="name")

    with pytest.raises(AttributeError):
        inst.name = "name1"

    with pytest.raises(AttributeError):
        del inst.name

    @frozen(post_init=False)
    class MyClass1:
        def __init__(self, name: str) -> None:
            self.name = name

        def freeze(self) -> None:
            pass

    inst1 = MyClass1(name="name")
    inst1.name = "name1"
    inst1.freeze()

    with pytest.raises(AttributeError):
        inst1.name = "name2"

    with pytest.raises(AttributeError):
        del inst1.name


def test_keep_case() -> None:
    assert keep_case("KeepCase") == "KeepCase"


def test_upper_case() -> None:
    assert upper_case("upper_case") == "UPPER_CASE"
    assert upper_case("UpperCase") == "UPPERCASE"
    assert upper_case("upperCase") == "UPPERCASE"


def test_pascal_case() -> None:
    assert pascal_case("pascal_case") == "PascalCase"
    assert pascal_case("pascalCase") == "PascalCase"
    assert pascal_case("PASCAL_CASE") == "PascalCase"
    assert pascal_case("pascal_Case") == "PascalCase"
    assert pascal_case("PascalCase") == "PascalCase"


def test_snake_case() -> None:
    assert snake_case("snake_case") == "snake_case"
    assert snake_case("SnakeCase") == "snake_case"
    assert snake_case("snakeCase") == "snake_case"
    assert snake_case("SNAKE_CASE") == "snake_case"


def test_cast_or_raise() -> None:
    assert cast_or_raise(int, 1) == 1
    with pytest.raises(TypeError):
        cast_or_raise(int, "1")


def test_override_docstring() -> None:
    s = "this is new docstring"

    @override_docstring(s)
    def foo() -> None:
        """This is old docstring"""
        pass

    assert foo.__doc__ == s
