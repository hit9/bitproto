import re
from typing import Any, Callable, List, Optional, Type as T, TypeVar
from typing import TYPE_CHECKING
from functools import wraps

I = TypeVar("I")  # Any Input
O = TypeVar("O")  # Ant Output
C = TypeVar("C", bound=T)  # Any Class
F = TypeVar("F", bound=Callable[..., Any])  # Any Function

if TYPE_CHECKING:
    # Cheat mypy, which just won't let "try import" goes on.
    from functools import lru_cache as cache
else:
    try:
        from functools import cache  # 3.9+
    except ImportError:
        from functools import lru_cache as cache


if TYPE_CHECKING:
    from typing import final  # 3.8+
else:

    def final(class_: C) -> C:
        """Marks a class as a final class, which can't be inherit.
        We don't use mypy's final keyword."""

        def __init_subclass__(*args, **kwargs):
            raise TypeError("Final class can't be inherit.")

        setattr(class_, "__init_subclass__", __init_subclass__)
        return class_


def conditional_cache(condition):
    """Cache given function until condition function returns True.

        >>> @conditional_cache(lambda fn, args, kwds: ...)
            def get_attr(self, *args, **kwds):
                pass
    """

    def decorator(user_function):
        """The decorator focus on given condition."""
        cache_decorated_function = None

        @wraps(user_function)
        def decorated(*args, **kwargs):
            """The decorated user function."""
            if not condition(user_function, args, kwargs):
                # Execute directly.
                return user_function(*args, **kwargs)
            nonlocal cache_decorated_function
            if cache_decorated_function is None:
                cache_decorated_function = cache(user_function)
            return cache_decorated_function(*args, **kwargs)

        return decorated

    return decorator


class cached_property:
    """The famous cached_property:
    Original from:
    https://github.com/bottlepy/bottle/commit/fa7733e075da0d790d809aa3d2f53071897e6f76

        >>> @cached_property
            def name(self) -> str:
                return "cached!"
    """

    def __init__(self, func: Callable[[I], O]) -> None:
        self.__doc__ = func.__doc__
        self.func = func

    def __get__(self, obj: Optional[I], cls: T[O]) -> O:
        if obj is None:
            return self  # type: ignore
        value = obj.__dict__[self.func.__name__] = self.func(obj)
        return value


class frozen:
    """Freeze a class on its inition or later."""

    @classmethod
    def _create_setattr_func(cls):
        def __setattr__(self, name, value):
            if getattr(self, "__frozen__", False):
                raise AttributeError("Cant setattr on frozen instance")
            else:
                object.__setattr__(self, name, value)

        return __setattr__

    @classmethod
    def _create_delattr_func(cls):
        def __delattr__(self, name):
            if getattr(self, "__frozen__", False):
                raise AttributeError("Cant delattr on frozen instance")
            else:
                object.__delattr__(self, name)

        return __delattr__

    @classmethod
    def later(cls, class_: C) -> C:
        """Decorates given class to freeze on demand later init.

        >>> @frozen.later
            class MyClass:
                pass

        >>> inst = MyClass()
        >>> inst.name = "ha" # => ok
        >>> inst.freeze()
        >>> inst.name = "but" # => AttributeError
        >>> inst.is_frozen() # => True

        """

        def freeze(class_self) -> None:
            setattr(class_self, "__frozen__", True)

        setattr(class_, "__frozen__", False)
        setattr(class_, "freeze", freeze)
        setattr(class_, "__setattr__", cls._create_setattr_func())
        setattr(class_, "__delattr__", cls._create_delattr_func())
        return class_

    @classmethod
    def post_init(cls, class_: C) -> C:
        """Decorates given class to freeze post init.

        >>> @frozen.post_init
            class MyClass:
                def __init__(self, name):
                    self.name = name

        >>> inst = MyClass("sweet")
        >>> inst.name = "ha" # => AttributeError
        """
        func = getattr(class_, "__init__")

        def decorate_init(func):
            @wraps(func)
            def decorated(class_self, *args, **kwargs):
                ret = func(class_self, *args, **kwargs)
                setattr(class_self, "__frozen__", True)
                return ret

            return decorated

        setattr(class_, "__init__", decorate_init(func))
        setattr(class_, "__setattr__", cls._create_setattr_func())
        setattr(class_, "__delattr__", cls._create_delattr_func())
        return class_


def safe_hash(class_: C) -> C:
    """Corresponding to dataclass's unsafe_hash,
    which is hash(dataclass_fields)."""

    def __hash__(self) -> int:
        return hash("__safe_hash__id__{0}".format(id(self)))

    setattr(class_, "__hash__", __hash__)
    return class_


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
