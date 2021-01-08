"""
bitproto.lib
~~~~~~~~~~~~~

Encoding support for generated python files.
"""

from dataclasses import dataclass
from typing import List, Union

Field = Union[bool, int]


@dataclass
class FieldDescriptor:
    field: Field
    nbits: int


def encode(descriptors: List[FieldDescriptor], s: List[int]) -> None:
    endecode(descriptors, s, True)


def decode(descriptors: List[FieldDescriptor], s: List[int]) -> None:
    endecode(descriptors, s, False)


def get_mask(k: int, c: int) -> int:
    if k == 0:
        return (1 << c) - 1
    return ((1 << (k + 1 + c)) - 1) - ((1 << (k + 1)) - 1)


def smart_shift(n: int, k: int) -> int:
    if k > 0:
        return n >> k
    if k < 0:
        return n << k
    return n


def get_number_of_bits_to_copy(i: int, j: int, n: int) -> int:
    return min(n - j, 8 - (j % 8), 8 - (i % 8))


def endecode(descriptors: List[FieldDescriptor], s: List[int], is_encode: bool) -> None:
    i = 0
    for descriptor in descriptors:
        j = 0
        n = descriptor.nbits
        while j < n:
            c = get_number_of_bits_to_copy(i, j, n)
            s_index = int(i / 8)
            field_shift = int(j / 8)
            # TODO
            j += c
            i += c
