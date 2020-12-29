import re
from typing import Callable, List, Optional, TypeVar, Type, TYPE_CHECKING

if TYPE_CHECKING:
    from functools import lru_cache as cache
else:
    try:
        from functools import cache  # 3.9+
    except ImportError:
        from functools import lru_cache as cache

T = TypeVar("T")
R = TypeVar("R")


class cached_property:
    """The famous cached_property:
    Original from:
    https://github.com/bottlepy/bottle/commit/fa7733e075da0d790d809aa3d2f53071897e6f76
    """

    def __init__(self, func: Callable[[T], R]) -> None:
        self.__doc__ = func.__doc__
        self.func = func

    def __get__(self, obj: Optional[T], cls: Type[T]) -> R:
        if obj is None:
            return self  # type: ignore
        value = obj.__dict__[self.func.__name__] = self.func(obj)
        return value


def write_file(filepath: str, s: str) -> None:
    """Write given s to filepath."""
    with open(filepath, "w") as f:
        f.write(s)


def pascal_case(word: str) -> str:
    """Converts given word to pascal case.

        >>> pascal_case("someWord")
        "SomeWord"
    """
    items: List[str] = []
    for part in word.split("_"):
        if part:
            first_char, remain_part = part[0], part[1:]
            items.append(first_char.upper() + remain_part)
    return "".join(items)


def snake_case(word: str) -> str:
    """Converts given word to snake case.


        >>> snake_case("someWord")
        "some_word"
    """
    underscore = "_"
    no_underscore_words = word.split(underscore)
    regex_head = r"[A-Z0-9]"
    regex_tail = r"[^A-Z0-9]"
    capital_match = re.compile(rf"({regex_head}+{regex_tail}*)")
    m_capital_match = re.compile(rf"^({regex_head}{{1,}})({regex_head}+{regex_tail}+)$")
    no_underscore_cases: List[str] = []

    for w in no_underscore_words:
        cases = filter(None, capital_match.split(w))
        for case in cases:
            subcases = filter(None, m_capital_match.split(case))
            if subcases:
                for subcase in subcases:
                    no_underscore_cases.append(subcase)
            else:
                no_underscore_cases.append(case)

    snake_word = ""
    for case in no_underscore_cases:
        if not case.isdigit():
            snake_word += underscore
        snake_word += case
    return snake_word.strip(underscore).lower()
