"""
bitprotolib.bp
~~~~~~~~~~~~~~

Encoding support for generated python files.

Keep it simple:  No magic.
"""

import json
from abc import abstractmethod
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from dataclasses import field as dataclass_field
from typing import Any, Dict, Iterator, List, Optional, Tuple

# Flags
FLAG_BOOL: int = 1
FLAG_INT: int = 2
FLAG_UINT: int = 3
FLAG_BYTE: int = 4
FLAG_ENUM: int = 5
FLAG_ALIAS: int = 6
FLAG_ARRAY: int = 7
FLAG_MESSAGE: int = 8
FLAG_MESSAGE_FIELD: int = 9

# Python dosen't have a byte type, using int instead.
byte = int


def int8(i: int) -> int:
    return i if i < 128 else i - 256


def int16(i: int) -> int:
    return i if i < 32768 else i - 65536


def int32(i: int) -> int:
    return i if i < 2147483648 else i - 4294967296


def int64(i: int) -> int:
    return i if i < 9223372036854775808 else i - 18446744073709551616


class Error(Exception):
    """Error occurred during bitproto encoding or decoding."""


class NotEnoughBytes(Error):
    """Given bytearray is not enough to process."""


@dataclass
class ProcessContext:
    """ProcessContext is the context across all processor functions in a encoding or
    decoding process.

    :param is_encode: Indicates whether current processing is encoding.
    :param s: Bytes buffer processing. When encoding, s is the destination buffer to
       write; When decoding, s is the source buffer to read.
    :param i: Tracks the number of total bits processed.
    """

    is_encode: bool
    s: bytearray
    i: int = 0


@dataclass
class DataIndexer:
    """DataIndexer contains the argument to index data from current accessor.

    :param field_number: Current field number.
    :param aistack: Array index stack in case of nested array in a single message.
    """

    field_number: int
    aistack: List[int] = dataclass_field(default_factory=list)

    def is_valid(self) -> bool:
        """If this data indexer valid."""
        return self.field_number > 0

    def i(self, n: int) -> int:
        """Returns array element index at depth n."""
        return self.aistack[n]

    def index_stack_up(self) -> None:
        self.aistack.append(0)

    def index_stack_down(self) -> None:
        self.aistack.pop()

    @contextmanager
    def index_stack_maintain(self) -> Iterator[None]:
        try:
            self.index_stack_up()
            yield
        finally:
            self.index_stack_down()

    def index_stack_replace(self, k: int) -> None:
        self.aistack[-1] = k


# NIL_DATA_INDEXER indicates this indexer is useless.
NIL_DATA_INDEXER = DataIndexer(-1)


class Accessor:
    """Accessor is the data container.
    Assuming compiler generates these methods for messages.
    """

    @abstractmethod
    def bp_set_byte(self, di: DataIndexer, lshift: int, b: byte) -> None:
        """Sets given byte to target data, where the data will be lookedup by given
        indexer di from this accessor.
        This method is called only if target data is a single type.

        :param lshift: The number of bits to shift right on b before it's written onto the
           indexed data.
        """
        raise NotImplementedError

    @abstractmethod
    def bp_get_byte(self, di: DataIndexer, rshift: int) -> byte:
        """Returns the byte from the data lookedup by given indexer di from the accessor.
        Argument rshift is the number of bits to shift left on the data before it's cast
        to byte. This method is called only if target data is a single type.
        """
        raise NotImplementedError

    @abstractmethod
    def bp_get_accessor(self, di: DataIndexer) -> "Accessor":
        """Gets the child accessor data container by indexer di. This method is called
        only if target data is a message.
        """
        raise NotImplementedError


class NilAccessor(Accessor):
    """NilAccessor is a special accessor implementation, represents that this accessor is
    invalid and shouldn't be used further.
    """

    def bp_set_byte(self, di: DataIndexer, lshift: int, b: byte) -> None:
        pass

    def bp_get_byte(self, di: DataIndexer, rshift: int) -> byte:
        return byte(0)

    def bp_get_accessor(self, di: DataIndexer) -> "Accessor":
        return self


@dataclass
class IntAccessor(Accessor):
    """IntAccessor implements Accessor for int encoding and decoding."""

    data: int = 0

    def bp_set_byte(self, di: DataIndexer, lshift: int, b: byte) -> None:
        if di.field_number == 1:
            self.data |= int(b) << lshift

    def bp_get_byte(self, di: DataIndexer, rshift: int) -> byte:
        if di.field_number == 1:
            return (self.data >> rshift) & 255
        return byte(0)

    def bp_get_accessor(self, di: DataIndexer) -> "Accessor":
        return NilAccessor()


class MessageBase(Accessor):
    """MessageBase is the base class for all bitproto message classes."""

    def to_dict(self) -> Dict[str, Any]:
        """Converts this message to a dict."""
        return asdict(self)

    def to_json(
        self, indent: Optional[int] = None, separators: Optional[Tuple[str, str]] = None
    ) -> str:
        """Dumps this message to a json string."""
        return json.dumps(self.to_dict(), indent=indent, separators=separators)


class Processor:
    """Processor is the abstraction type the able to process encoding and decoding."""

    @abstractmethod
    def flag(self) -> int:
        raise NotImplementedError

    @abstractmethod
    def process(self, ctx: ProcessContext, di: DataIndexer, accessor: Accessor) -> None:
        raise NotImplementedError


@dataclass
class Bool(Processor):
    """Bool implements Processor for bool type."""

    def flag(self) -> int:
        return FLAG_BOOL

    def process(self, ctx: ProcessContext, di: DataIndexer, accessor: Accessor) -> None:
        process_base_type(1, ctx, di, accessor)


@dataclass
class Int(Processor):
    """Int implements Processor for int type.

    :param nbits: Number of bits this int occupy.
    """

    nbits: int

    def flag(self) -> int:
        return FLAG_INT

    def process(self, ctx: ProcessContext, di: DataIndexer, accessor: Accessor) -> None:
        process_base_type(self.nbits, ctx, di, accessor)


@dataclass
class Uint(Processor):
    """Uint implements Processor for uint type.

    :param nbits: Number of bits this uint occupy.
    """

    nbits: int

    def flag(self) -> int:
        return FLAG_UINT

    def process(self, ctx: ProcessContext, di: DataIndexer, accessor: Accessor) -> None:
        process_base_type(self.nbits, ctx, di, accessor)


@dataclass
class Byte(Processor):
    """Byte implements Processor for byte type."""

    def flag(self) -> int:
        return FLAG_BYTE

    def process(self, ctx: ProcessContext, di: DataIndexer, accessor: Accessor) -> None:
        process_base_type(8, ctx, di, accessor)


@dataclass
class Array(Processor):
    """Array implements Processor for array type.

    :param extensible: Indicates whether this array is extensible.
    :param capacity: Capacity of this array.
    :param element_processor: Processor of the array's element.
    """

    extensible: bool
    capacity: int
    element_processor: Processor

    def flag(self) -> int:
        return FLAG_ARRAY

    def process(self, ctx: ProcessContext, di: DataIndexer, accessor: Accessor) -> None:
        with di.index_stack_maintain():
            # Record current number of bits processed.
            i = ctx.i
            # Opponent array capacity if extensible set.
            ahead = 0

            if self.extensible:
                if ctx.is_encode:
                    # Encode extensible ahead  if extensible.
                    self.encode_extensible_ahead(ctx)
                else:
                    # Decode extensible ahead  if extensible.
                    ahead = self.decode_extensible_ahead(ctx)

            # Process array elements.
            for k in range(self.capacity):
                di.index_stack_replace(k)
                self.element_processor.process(ctx, di, accessor)

            # Skip redundant bits post decoding.
            if self.extensible and not ctx.is_encode:
                ito = i + ahead * self.capacity
                if ito >= ctx.i:
                    ctx.i = ito

    def encode_extensible_ahead(self, ctx: ProcessContext) -> None:
        """Encode the array capacity as the ahead flag to current bit encoding stream."""
        accessor = IntAccessor(data=self.capacity)
        di = DataIndexer(field_number=1)
        process_base_type(16, ctx, di, accessor)

    def decode_extensible_ahead(Self, ctx: ProcessContext) -> int:
        """Decode the ahead flag as the array capacity from current decoding stream."""
        accessor = IntAccessor()
        di = DataIndexer(field_number=1)
        process_base_type(16, ctx, di, accessor)
        return accessor.data


@dataclass
class EnumProcessor(Processor):
    """Enum implements Processor for enum type.
    Assuming compiler generates a global function bp_processor_{enum_name}.

    :param ut: The uint type of this enum.
    """

    ut: Uint

    def flag(self) -> int:
        return FLAG_ENUM

    def process(self, ctx: ProcessContext, di: DataIndexer, accessor: Accessor) -> None:
        # Process inner uint.
        self.ut.process(ctx, di, accessor)


@dataclass
class AliasProcessor(Processor):
    """Alias implements Processor for alias type.
    AssertionError compiler generates a global function bp_processor_{alias_name}.

    :param to: The processor of the type it alias to.
    """

    to: Processor

    def flag(self) -> int:
        return FLAG_ALIAS

    def process(self, ctx: ProcessContext, di: DataIndexer, accessor: Accessor) -> None:
        self.to.process(ctx, di, accessor)


@dataclass
class MessageFieldProcessor(Processor):
    """MessageFieldProcessor implements Processor for message field.

    :param field_number: Field number.
    :param type_processor: The processor of the field's type.
    """

    field_number: int
    type_processor: Processor

    def flag(self) -> int:
        return FLAG_MESSAGE_FIELD

    def process(self, ctx: ProcessContext, di: DataIndexer, accessor: Accessor) -> None:
        # Ignore data indexer passed in, because accessor is rewrite.
        # Rewrite data indexer's fieldNumber.
        di = DataIndexer(field_number=self.field_number)
        self.type_processor.process(ctx, di, accessor)


@dataclass
class MessageProcessor(Processor):
    """MessageProcessor implements Processor for message.
    Assuming compiler generates Message a method: bp_processor to returns this.

    :param field_processors:  List of message field's processors.
    """

    extensible: bool
    nbits: int
    field_processors: List[Processor] = dataclass_field(default_factory=list)

    def flag(self) -> int:
        return FLAG_MESSAGE

    def process(self, ctx: ProcessContext, di: DataIndexer, accessor: Accessor) -> None:
        if di.is_valid():
            # Invalid DataIndexer NIL_DATA_INDEXER is passed in right after this message
            # is asked to process, indicates this message is the top level message on the
            # processing chain. The di will be dropped (or overwritten) by the
            # MessageFieldProcessor of this message and never be NIL_DATA_INDEXER again.
            #
            # Rewrite accessor if this message processor is called from a upper accessor.
            accessor = accessor.bp_get_accessor(di)

        # Record current number of bits processed.
        i = ctx.i
        # Opponent message nbits if extensible set.
        ahead = 0

        if self.extensible:
            if ctx.is_encode:
                # Encode extensible ahead  if extensible.
                self.encode_extensible_ahead(ctx)
            else:
                # Decode extensible ahead  if extensible.
                ahead = self.decode_extensible_ahead(ctx)

        # Process fields.
        for field_processor in self.field_processors:
            field_processor.process(ctx, di, accessor)

        # Skip redundant bits post decoding.
        if self.extensible and not ctx.is_encode:
            ito = i + ahead
            if ito >= ctx.i:
                ctx.i = ito

    def encode_extensible_ahead(self, ctx: ProcessContext) -> None:
        """Encode the message nbits as the ahead flag to current bit encoding stream."""
        accessor = IntAccessor(data=self.nbits)
        di = DataIndexer(field_number=1)
        process_base_type(16, ctx, di, accessor)

    def decode_extensible_ahead(self, ctx: ProcessContext) -> int:
        """Decode the message ahead flag as the nbits from current bit decoding stream."""
        accessor = IntAccessor()
        di = DataIndexer(field_number=1)
        process_base_type(16, ctx, di, accessor)
        return accessor.data


def smart_shift(n: byte, k: int) -> byte:
    """Shifts given byte n by k bits.
    If k is larger than 0, performs a right shift, otherwise left.
    """
    if k > 0:
        return n >> k
    elif k < 0:
        return n << (0 - k)
    return n


def get_mask(k: int, c: int) -> int:
    """Returns the mask value to copy bits inside a single byte.

    :param k: The start bit index in the byte.
    :param c: The number of bits to copy.

    Examples of returned mask:

        Returns                Arguments
        00001111               k=0, c=4
        01111100               k=2, c=5
        00111100               k=2, c=4
    """
    if k == 0:
        return (1 << c) - 1
    return (1 << ((k + 1 + c) - 1)) - (1 << ((k + 1) - 1))


def get_nbits_to_copy(i: int, j: int, n: int) -> int:
    """Returns the number of bits to copy during a single byte process.
    :param i: the number of the total bits processed.
    :param j: the number of bits processed on current base type.
    :param n: the number of bits current base type occupy.
    """
    return min(n - j, 8 - (j % 8), 8 - (i % 8))


def encode_single_byte(
    ctx: ProcessContext, di: DataIndexer, accessor: Accessor, j: int, c: int
) -> None:
    """Encode number of c bits from data to given buffer s.
    Where the data is lookedup by data indexer di from data container accessor.
    And the buffer s is given in ProcessContext ctx.
    """
    # Number of bits to shift right to obtain byte from accessor.
    rshift = int(j / 8) * 8
    b = accessor.bp_get_byte(di, rshift)
    shift = (j % 8) - (ctx.i % 8)
    mask = get_mask(ctx.i % 8, c)
    # Shift and then take mask to get bits to copy.
    d = smart_shift(b, shift) & mask
    # Copy bits to buffer s.
    ctx.s[int(ctx.i / 8)] |= d


def decode_single_byte(
    ctx: ProcessContext, di: DataIndexer, accessor: Accessor, j: int, c: int
) -> None:
    """Decode number of c bits from buffer s to target data.
    Where the data is lookedup by data indexer di from data container accessor.
    And the buffer s is given in ProcessContext ctx.
    Byte decoding is finally done by accessor's generated function bp_set_byte.
    """
    b = ctx.s[int(ctx.i / 8)]
    shift = (ctx.i % 8) - (j % 8)
    mask = get_mask(j % 8, c)
    # Shift and then take mask to get bits to copy.
    d = smart_shift(b, shift) & mask
    # Number of bits to shift left to set byte to accessor.
    lshift = int(j / 8) * 8
    accessor.bp_set_byte(di, lshift, d)


def process_single_byte(
    ctx: ProcessContext, di: DataIndexer, accessor: Accessor, j: int, c: int
) -> None:
    """Dispatch process to encode_single_byte and decode_single_byte."""
    if ctx.is_encode:
        encode_single_byte(ctx, di, accessor, j, c)
    else:
        decode_single_byte(ctx, di, accessor, j, c)


def process_base_type(
    nbits: int, ctx: ProcessContext, di: DataIndexer, accessor: Accessor
) -> None:
    """Process encoding and decoding on a base type."""
    j: int = 0
    while j < nbits:
        c = get_nbits_to_copy(ctx.i, j, nbits)
        process_single_byte(ctx, di, accessor, j, c)
        ctx.i += c
        j += c
