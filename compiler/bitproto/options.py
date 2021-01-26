"""
bitproto.options
~~~~~~~~~~~~~~~~

Options bitproto supports.
"""

from dataclasses import dataclass
from typing import Callable, Optional, Tuple, Union, cast

Value = Union[bool, int, str]
Validator = Callable[..., bool]
OptionDescriptors = Tuple["OptionDescriptor", ...]


@dataclass(frozen=True)
class OptionDescriptor:
    """Describes an option."""

    name: str
    default: Value
    validator: Optional[Validator] = None
    description: Optional[str] = None


# Message Options
MESSAGE_OPTIONS: OptionDescriptors = (
    OptionDescriptor(
        "max_bytes",
        0,
        lambda v: v >= 0,
        "Setting the maximum limit of number of bytes for target message.",
    ),
)

# Proto Options
PROTO_OPTTIONS: OptionDescriptors = (
    OptionDescriptor(
        "c.struct_packing_alignment",
        0,
        lambda v: 0 <= v <= 8,
        "C language struct packing alignment, defaults to 0",
    ),
    OptionDescriptor(
        "c.name_prefix",
        "",
        None,
        "Name prefix of generated C defintions, defaults to empty.",
    ),
    OptionDescriptor(
        "go.package_path",
        "",
        None,
        "Package path of current golang package, to be imported, e.g.  github.com/path/to/example",
    ),
    OptionDescriptor(
        "py.module_name",
        "",
        None,
        "Module name of current python module, to be imported, e.g. example_bp",
    ),
)
