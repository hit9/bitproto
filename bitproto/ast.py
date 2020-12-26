"""
bitproto.ast
~~~~~~~~~~~~

Abstraction syntax tree.

    Node
      |- Comment                        :Node
      |- Type                           :Node
      |    |- Bool                      :Type:Node
      |    |- Byte                      :Type:Node
      |    |- Int                       :Type:Node
      |    |- Uint                      :Type:Node
      |    |- Array                     :Type:Node
      |    |- Alias                     :Type:Node
      |    |- Enum                      :Type:Node
      |    |- Message                   :Type:Node
      |- Definition                     :Node
      |    |- Alias                     :Definition:Node
      |    |- Option                    :Definition:Node
      |    |    |- BooleanOption        :Option:Definition:Node
      |    |    |- IntegerOption        :Option:Definition:Node
      |    |    |- StringOption         :Option:Definition:Node
      |    |- Constant                  :Definition:Node
      |    |    |- BooleanConstant      :Constant:Definition:Node
      |    |    |- IntegerConstant      :Constant:Definition:Node
      |    |    |- StringConstant       :Constant:Definition:Node
      |    |- Field                     :Definition:Node
      |    |    |- EnumField            :Field:Definition:Node
      |    |    |- MessageField         :Field:Definition:Node
      |    |- Scope                     :Definition:Node
      |    |    |- Enum                 :Scope:Definition:Node
      |    |    |- Message              :Scope:Definition:Node
      |    |    |- Proto                :Scope:Definition:Node
"""

from dataclasses import dataclass, field as dataclass_field
from collections import OrderedDict as dict_
from typing import Tuple, Union, Optional, Type as T, TypeVar, cast

from bitproto.errors import (
    InternalError,
    UnsupportedArrayType,
    DuplicatedDefinition,
    InvalidArrayCap,
    InvalidIntCap,
    InvalidUintCap,
    InvalidEnumFieldValue,
    EnumFieldValueOverflow,
    DuplicatedEnumFieldValue,
    InvalidAliasedType,
    InvalidMessageFieldNumber,
)

T_Definition = TypeVar("T_Definition", bound="Definition")


@dataclass
class Node:
    token: str = ""
    lineno: int = 0
    filepath: str = ""

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        pass


@dataclass
class Comment(Node):
    def content(self) -> str:
        """Returns the stripped content of this comment."""
        return self.token[2:].strip()

    def __str__(self) -> str:
        return self.content()

    def __repr__(self) -> str:
        return "<comment {0}..>".format(self.token[:5])


@dataclass
class Definition(Node):
    name: str = ""
    scope_stack: Tuple["Scope", ...] = tuple()
    comment_block: Tuple[Comment, ...] = tuple()

    def docstring(self) -> str:
        """Returns the comment block in string format."""
        return "\n".join(str(c) for c in self.comment_block)

    def set_name(self, name: str) -> None:
        self.name = name

    def set_comment_block(self, comment_block: Tuple[Comment, ...]) -> None:
        self.comment_block = comment_block

    def __repr__(self) -> str:
        return "<definition {0}>".format(self.name)


@dataclass
class Option(Definition):
    value: Union[str, int, bool, None] = None

    def validate(self) -> None:
        assert self.value is not None, InternalError("Init Option with value None")

    def __repr__(self) -> str:
        return "<option {0}={1}>".format(self.name, self.value)


@dataclass
class IntegerOption(Option):
    value: int = 0


@dataclass
class BooleanOption(Option):
    value: bool = False


@dataclass
class StringOption(Option):
    value: str = ""


@dataclass
class Constant(Definition):
    value: Union[str, int, bool, None] = None

    def __repr__(self) -> str:
        return "<constant {0}={1}>".format(self.name, self.value)


@dataclass
class IntegerConstant(Constant):
    value: int = 0

    def __int__(self) -> int:
        return self.value

    def __repr__(self) -> str:
        return "<integer-constant {0}>".format(self.name)


@dataclass
class BooleanConstant(Constant):
    value: bool = False

    def __bool__(self) -> bool:
        return self.value

    def __repr__(self) -> str:
        return "<boolean-constant {0}>".format(self.name)


@dataclass
class StringConstant(Constant):
    value: str = ""

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return "<str-constant {0}>".format(self.name)


@dataclass
class Scope(Definition):
    members: "dict_[str, Definition]" = dataclass_field(default_factory=dict_)

    def __repr__(self) -> str:
        return f"<scope {self.name}"

    def validate_member_on_push(
        self, member: Definition, name: Optional[str] = None
    ) -> None:
        """Invoked on given member going to push as given name into this scope."""
        pass

    def push_member(self, member: Definition, name: Optional[str] = None) -> None:
        if name is None:
            name = member.name
        if name in self.members:
            raise DuplicatedDefinition.from_token(token=member)
        self.validate_member_on_push(member, name)
        self.members[name] = member

    def get_member(self, *names: str) -> Optional[Definition]:
        """Gets member by names recursively.
        Returns `None` if not found.
        The recursivion continues only if current node is a scope.
        """
        if not names:
            return None

        first, remain = names[0], names[1:]

        member = self.members.get(first, None)
        if member is None:
            return None

        if not remain:
            return member

        if not isinstance(member, Scope):
            return None
        return member.get_member(*remain)

    def filter(self, t: T[T_Definition]) -> "dict_[str, T_Definition]":
        return dict_(
            (name, member)
            for name, member in self.members.items()
            if isinstance(member, t)
        )

    def options(self) -> "dict_[str, Option]":
        return self.filter(Option)

    def enums(self) -> "dict_[str, Enum]":
        return self.filter(Enum)

    def messages(self) -> "dict_[str, Message]":
        return self.filter(Message)

    def constants(self) -> "dict_[str, Constant]":
        return self.filter(Constant)

    def protos(self) -> "dict_[str, Proto]":
        return self.filter(Proto)

    def enum_fields(self) -> "dict_[str, EnumField]":
        return self.filter(EnumField)

    def message_fields(self) -> "dict_[str, MessageField]":
        return self.filter(MessageField)


@dataclass
class Type(Node):
    _is_missing: bool = False

    def __repr__(self) -> str:
        return "<type base>"

    def nbits(self) -> int:
        raise NotImplementedError

    def nbytes(self) -> int:
        nbits = self.nbits()
        if nbits % 8 == 0:
            return int(nbits / 8)
        return int(nbits / 8) + 1


_TYPE_MISSING = Type(_is_missing=True)


@dataclass
class Bool(Type):
    def nbits(self) -> int:
        return 1

    def __repr__(self) -> str:
        return "bool"


@dataclass
class Byte(Type):
    def nbits(self) -> int:
        return 8

    def __repr__(self) -> str:
        return "byte"


@dataclass
class Uint(Type):
    cap: int = 0

    def validate(self) -> None:
        if self._is_missing:
            return
        if not (0 < self.cap <= 64):
            raise InvalidUintCap.from_token(token=self)

    def nbits(self) -> int:
        return self.cap

    def __repr__(self) -> str:
        return "uint{0}".format(self.cap)


_UINT_MISSING = Uint(_is_missing=True)


@dataclass
class Int(Type):
    cap: int = 0

    def validate(self) -> None:
        if self.cap not in (8, 16, 32, 64):
            raise InvalidIntCap.from_token(token=self)

    def nbits(self) -> int:
        return self.cap

    def __repr__(self) -> str:
        return "int{0}".format(self.cap)


@dataclass
class Array(Type):
    type: Type = _TYPE_MISSING
    cap: int = 0

    @property
    def supported_types(self) -> Tuple[T[Type], ...]:
        return (Bool, Byte, Int, Uint, Enum, Message, Alias)

    def validate(self) -> None:
        if not (0 < self.cap < 1024):
            raise InvalidArrayCap.from_token(token=self)
        if not isinstance(self.type, self.supported_types):
            raise UnsupportedArrayType.from_token(token=self)

    def nbits(self) -> int:
        if self.type is None:
            return 0
        return self.cap * self.type.nbits()

    def __repr__(self) -> str:
        return "{0}[{1}]".format(self.type, self.cap)


@dataclass
class Alias(Type, Definition):
    type: Type = _TYPE_MISSING

    def __repr__(self) -> str:
        return f"<alias {self.name}>"

    def validate(self) -> None:
        # TODO: Should we check this? FIXME
        t = (Bool, Uint, Int, Byte)
        allow = False
        if isinstance(self.type, t):  # Alias to base types
            allow = True
        elif isinstance(self.type, Array):
            array = cast(Array, self.type)
            if isinstance(array.type, t):  # Alias to array of base types
                allow = True
            if isinstance(array.type, Alias):  # Alias to array of alias
                allow = True
        if not allow:
            raise InvalidAliasedType.from_token(token=self)

    def nbits(self) -> int:
        return self.type.nbits()


@dataclass
class Field(Definition):
    pass


@dataclass
class EnumField(Field):
    value: int = 0

    def __repr__(self) -> str:
        return f"<enum-field {self.name}={self.value}>"

    def validate(self) -> None:
        if self.value < 0:
            raise InvalidEnumFieldValue.from_token(token=self)


@dataclass
class Enum(Type, Scope):
    type: Uint = _UINT_MISSING

    def __repr__(self) -> str:
        return f"<enum {self.name}>"

    def nbits(self) -> int:
        return self.type.nbits()

    def name_to_values(self) -> "dict_[str, int]":
        return dict_((name, field.value) for name, field in self.enum_fields().items())

    def value_to_names(self) -> "dict_[int, str]":
        return dict_((field.value, name) for name, field in self.enum_fields().items())

    def validate_member_on_push(
        self, member: Definition, name: Optional[str] = None
    ) -> None:
        if isinstance(member, EnumField):
            self.validate_enum_field_on_push(member)

    def validate_enum_field_on_push(self, field: EnumField) -> None:
        # Value overflows?
        if field.value.bit_length() > self.nbits():
            raise EnumFieldValueOverflow.from_token(token=field)
        # Value already defined?
        if field.value in self.value_to_names():
            raise DuplicatedEnumFieldValue.from_token(token=field)


@dataclass
class MessageField(Field):
    type: Type = Type()
    number: int = 0

    def __repr__(self) -> str:
        return f"<message-field {self.name}={self.number}>"

    def validate(self) -> None:
        if not (0 < self.number < 256):
            raise InvalidMessageFieldNumber.from_token(token=self)


@dataclass
class Message(Type, Scope):
    name: str = ""

    def nbits(self) -> int:
        return sum(field.type.nbits() for field in self.message_fields().values())

    def __repr__(self) -> str:
        return f"<message {self.name}>"


@dataclass
class Proto(Scope):
    def __repr__(self) -> str:
        return f"<bitproto {self.name}>"
