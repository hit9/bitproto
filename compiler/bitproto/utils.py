import os
import re
import sys
from enum import Enum, unique
from functools import wraps
from typing import TYPE_CHECKING, Any, Callable, List, Optional
from typing import Type as T
from typing import TypeVar, Union, cast, overload

Function = Callable[..., Any]

I = TypeVar("I")  # Any Input
O = TypeVar("O")  # Ant Output
C = TypeVar("C", bound=T)  # Any Class
F = TypeVar("F", bound=Function)  # Any Function
M = TypeVar("M", bound=Union[Function, "cached_property"])

__all__ = (
    "F",
    "C",
    "final",
    "cache",
    "conditional_cache",
    "cached_property",
    "frozen",
    "safe_hash",
    "override",
    "override_docstring",
    "cast_or_raise",
    "overridable",
    "isabstractmethod",
    "write_file",
    "Color",
    "colored",
    "pascal_case",
    "snake_case",
    "write_stderr",
    "fatal",
)


from typing_extensions import final  # Compat 3.7

if TYPE_CHECKING:
    # Cheat mypy, which just won't let "try import" goes on.
    from functools import lru_cache as cache
else:
    try:
        from functools import cache  # 3.9+
    except ImportError:
        if sys.hexversion > 0x3080000:
            from functools import lru_cache as cache
        else:  # Compat 3.7
            from functools import lru_cache

            def cache(maxsize=128, typed=False):
                if callable(maxsize):  # user_function passed directly
                    user_function, maxsize = maxsize, 128
                    decorator = lru_cache(maxsize, typed)
                    return decorator(user_function)
                return lru_cache(maxsize, typed)


def conditional_cache(condition: Callable[..., bool]) -> Callable[[F], F]:
    """Cache given function until condition function returns True.

    >>> @conditional_cache(lambda fn, args, kwds: ...)
        def get_attr(self, *args, **kwds):
            pass
    """

    def decorator(user_function: F) -> F:
        """The decorator focus on given condition."""
        cache_decorated_function = cast(F, cache(user_function))

        @wraps(user_function)
        def decorated(*args: Any, **kwargs: Any) -> Any:
            """The decorated user function."""
            if not condition(user_function, args, kwargs):
                # Execute directly.
                return user_function(*args, **kwargs)
            return cache_decorated_function(*args, **kwargs)

        return cast(F, decorated)

    return decorator


class cached_property:
    """The famous cached_property:
    Original from:
    https://github.com/bottlepy/bottle/commit/fa7733e075da0d790d809aa3d2f53071897e6f76

        >>> class MyClass:
                @cached_property
                def name(self) -> str:
                    print("cached!")
                    return "name"
        >>> inst = MyClass()
        >>> inst.name
        cached!
        "name"
        >>> inst.name  # already cached
        "name"

    Notes: Python 3.9+ provides cached_property in library functools.
    This custom implementation existing for compatiable reason (3.7, 3.8).
    """

    def __init__(self, func: Callable[[I], O]) -> None:
        self.__doc__ = func.__doc__
        self.__name__ = func.__name__
        self.func = func

    @overload
    def __get__(self, obj: None, cls: T[I]) -> "cached_property":
        ...

    @overload
    def __get__(self, obj: I, cls: T[I]) -> O:
        ...

    def __get__(self, obj: Optional[I], cls: T[I]) -> Union["cached_property", O]:
        if obj is None:
            return self
        value = obj.__dict__[self.func.__name__] = self.func(obj)
        return value


@overload
def frozen(class_: C) -> C:
    ...


@overload
def frozen(*, safe_hash: bool = True, post_init: bool = True) -> Callable[[C], C]:
    ...


def frozen(
    class_: Optional[C] = None, *, safe_hash: bool = True, post_init: bool = True
):
    """Freeze a class.

    :param class_: The class to frozen.
    :param safe_hash: Whether to inject a `__hash__` method onto this class, checks
       decorator `safe_hash()`.
    :param post_init: Whether to freeze the instance after `__init__` function is called.

    Example::

        >>> @frozen
            class MyClass:
                def __init__(self, name):
                    self.name = name
        >>> inst = MyClass(name="ha")
        >>> inst.name = "changed"  # AttributeError

    Or::

        >>> @frozen(post_init=False)
            class MyClass:
                pass
        >>> inst = MyClass()
        >>> inst.name = "init-my-name"  # ok
        >>> inst.name = "changed"  # AttributeError

    """

    def wrap(class_: C) -> C:
        def freeze(class_self) -> None:
            if getattr(class_self, "__frozen__", False):
                raise AttributeError("Cannot freeze frozen instance")
            setattr(class_self, "__frozen__", True)

            if hasattr(class_self, "__post_freeze__"):
                post_freeze = getattr(class_self, "__post_freeze__")
                if callable(post_freeze):
                    post_freeze()

        def __setattr__(self, name, value):
            if getattr(self, "__frozen__", False):
                raise AttributeError("Cant setattr on frozen instance")
            else:
                object.__setattr__(self, name, value)

        def __delattr__(self, name):
            if getattr(self, "__frozen__", False):
                raise AttributeError("Cant delattr on frozen instance")
            else:
                object.__delattr__(self, name)

        setattr(class_, "__frozen__", False)
        setattr(class_, "freeze", freeze)
        setattr(class_, "__setattr__", __setattr__)
        setattr(class_, "__delattr__", __delattr__)

        if post_init:

            init_func = getattr(class_, "__init__")

            def decorate_init(func):
                @wraps(func)
                def decorated(class_self, *args, **kwds):
                    ret = func(class_self, *args, **kwds)
                    class_self.freeze()
                    return ret

                return decorated

            setattr(class_, "__init__", decorate_init(init_func))

        if safe_hash:
            return safe_hash_(class_)
        return class_

    if class_ is None:
        return wrap
    return wrap(class_)


def safe_hash(class_: C) -> C:
    """Corresponding to dataclass's unsafe_hash,
    which is hash(dataclass_fields)."""

    def __hash__(self) -> int:
        return hash("__safe_hash__id__{0}".format(id(self)))

    setattr(class_, "__hash__", __hash__)
    return class_


safe_hash_ = safe_hash  # Alias


def override(c: C) -> Callable[[M], M]:
    """Just a simple mark indicates this method is overriding super method.

    >>> @override(SuperClass)
        def some_func(self):
            pass
    """

    def decorator(f: M) -> M:
        super_f = getattr(c, f.__name__)
        if not getattr(super_f, "__overridable__", False):
            if not getattr(super_f, "__isabstractmethod__", False):
                raise AttributeError(f"Cant override {super_f.__name__}")
        return f

    return decorator


def overridable(f: M) -> M:
    """Just a simple mark indicates this method could be overrided by future subclass
    method implementation."""
    setattr(f, "__overridable__", True)
    return f


def isabstractmethod(f: F) -> bool:
    """Returns True if given f is an abstract method."""
    return getattr(f, "__isabstractmethod__", False)


def cast_or_raise(t: T[I], v: Any) -> I:
    """Cast given value v to type t.
    Raises `TypeError` if v is not an instance of t.
    """
    if isinstance(v, t):
        return v
    raise TypeError(f"Cant cast {v} to {t}")


def write_file(filepath: str, s: str) -> None:
    """Write given s to filepath."""
    with open(filepath, "w") as f:
        f.write(s)


def write_stderr(s: str) -> None:
    """Write a line of string to stderr."""
    sys.stderr.write(s + "\n")


def fatal(s: str = "", code: int = 1) -> None:
    """Exit the whole program with given code and message."""
    if s:
        write_stderr(s)
    os._exit(code)


def override_docstring(string: str) -> Callable[[F], F]:
    """Returns a decorator that wraps given string as this function's docstring.

    >>> @override_docstring(s)
    def foo():
        pass
    """

    def decorator(function: F) -> F:
        function.__doc__ = string
        return function

    return decorator


@unique
class Color(Enum):
    BLACK: int = 0
    RED: int = 1
    GREEN: int = 2
    YELLOW: int = 3
    BLUE: int = 4
    MAGENTA: int = 5
    CYAN: int = 6
    WHITE: int = 7


def colored(text: str, color: Color) -> str:
    """Color given text."""
    return "\033[3%dm%s\033[0m" % (color.value, text)


def keep_case(word: str) -> str:
    """Returns the word as it is."""
    return word


def upper_case(word: str) -> str:
    """Converts given word to upper case."""
    return word.upper()


def pascal_case(word: str) -> str:
    """Converts given word to pascal case.

    >>> pascal_case("someWord")
    "SomeWord"
    """
    items: List[str] = []
    parts = word.split("_")
    contains_underscore = len(parts) > 1
    for part in parts:
        if part:
            if contains_underscore:
                items.append(part.title())
            else:
                first_char, remain_part = part[0], part[1:]
                items.append(first_char.upper() + remain_part)
    return "".join(items)


_snake_case_regex_head = r"[A-Z0-9]"
_snake_case_regex_tail = r"[^A-Z0-9]"
_snake_case_regex_capital_match = re.compile(
    rf"({_snake_case_regex_head}+{_snake_case_regex_tail}*)"
)
_snake_case_regex_m_capital_match = re.compile(
    rf"^({_snake_case_regex_head}{{1,}})({_snake_case_regex_head}+{_snake_case_regex_tail}+)$"
)


def snake_case(word: str) -> str:
    """Converts given word to snake case.

    >>> snake_case("someWord")
    "some_word"
    """
    underscore = "_"
    no_underscore_words = word.split(underscore)
    no_underscore_cases: List[str] = []

    for w in no_underscore_words:
        cases = filter(None, _snake_case_regex_capital_match.split(w))
        for case in cases:
            subcases = filter(None, _snake_case_regex_m_capital_match.split(case))
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
