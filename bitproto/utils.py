from typing import Callable, Optional, TypeVar, Type, Union, cast, TYPE_CHECKING

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

    def __get__(self, obj: Optional[T], cls: Type[T]) -> Union[T, R]:
        if obj is None:
            return cast(T, self)
        value = obj.__dict__[self.func.__name__] = self.func(obj)
        return value


def write_file(filepath: str, s: str) -> None:
    """Write given s to filepath."""
    with open(filepath, "w") as f:
        f.write(s)
