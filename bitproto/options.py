"""
bitproto.options
~~~~~~~~~~~~~~~~

Options bitproto supports.
"""

from dataclasses import dataclass
from typing import Callable, Optional, Union, Tuple, cast

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
        "c.target_platform_bits",
        32,
        lambda v: v in (32, 64),
        "C language target machine bits, 32 or 64",
    ),
    OptionDescriptor(
        "c.struct_packing_alignment",
        1,
        lambda v: 0 <= v <= 8,
        "C language struct packing alignment, defaults to 1",
    ),
    OptionDescriptor(
        "c.enable_render_json_formatter",
        True,
        None,
        "Whether render json formatter function for structs in C language, defaults to false",
    ),
    OptionDescriptor(
        "go.package_path",
        "",
        None,
        "Package path of current golang package, to be imported, e.g. github.com/path/to/shared_bp",
    ),
)
