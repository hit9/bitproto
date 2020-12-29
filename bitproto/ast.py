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
from typing import List, Tuple, Union, Optional, Type as T, TypeVar, cast

from bitproto.errors import (
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
    DuplicatedMessageFieldNumber,
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

    def set_name(self, name: str) -> None:
        self.name = name

    def set_comment_block(self, comment_block: Tuple[Comment, ...]) -> None:
        self.comment_block = comment_block

    def __repr__(self) -> str:
        return "<definition {0}>".format(self.name)


_VALUE_MISSING = "_VALUE_MISSING"  # FIXME: how to represent value missing?


@dataclass
class Option(Definition):
    value: Union[str, int, bool] = _VALUE_MISSING

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
    value: Union[str, int, bool] = _VALUE_MISSING

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
        The recursion continues only if current node is a scope.
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

    def get_name_by_member(self, member: Definition) -> Optional[str]:
        """Get name in this scope by member."""
        for name, member_ in self.members.items():
            if member_ is member:
                return name
        return None

    def filter(
        self, t: T[T_Definition], recursive: bool = False,
    ) -> List[Tuple[str, T_Definition]]:
        """Filter member by given type. (dfs)"""
        items: List[Tuple[str, T_Definition]] = []
        for item in self.members.items():
            name, member = item
            if recursive:  # Child first
                if isinstance(member, Scope):
                    scope = cast(Scope, member)
                    items.extend(scope.filter(t, recursive=recursive))
            if isinstance(member, t):
                items.append((name, member))
        return items

    def options(self, recursive: bool = False) -> List[Tuple[str, "Option"]]:
        return self.filter(Option, recursive=recursive)

    def enums(self, recursive: bool = False) -> List[Tuple[str, "Enum"]]:
        return self.filter(Enum, recursive=recursive)

    def messages(self, recursive: bool = False) -> List[Tuple[str, "Message"]]:
        return self.filter(Message, recursive=recursive)

    def constants(self, recursive: bool = False) -> List[Tuple[str, "Constant"]]:
        return self.filter(Constant, recursive=recursive)

    def aliases(self, recursive: bool = False) -> List[Tuple[str, "Alias"]]:
        return self.filter(Alias, recursive=recursive)

    def protos(self, recursive: bool = False) -> List[Tuple[str, "Proto"]]:
        return self.filter(Proto, recursive=recursive)

    def enum_fields(self, recursive: bool = False) -> List[Tuple[str, "EnumField"]]:
        return self.filter(EnumField, recursive=recursive)

    def message_fields(
        self, recursive: bool = False
    ) -> List[Tuple[str, "MessageField"]]:
        return self.filter(MessageField, recursive=recursive)


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
class BaseType(Type):
    pass


@dataclass
class Bool(BaseType):
    def nbits(self) -> int:
        return 1

    def __repr__(self) -> str:
        return "bool"


@dataclass
class Byte(BaseType):
    def nbits(self) -> int:
        return 8

    def __repr__(self) -> str:
        return "byte"


@dataclass
class Integer(BaseType):
    pass


@dataclass
class Uint(Integer):
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
class Int(Integer):
    cap: int = 0

    def validate(self) -> None:
        if self.cap not in (8, 16, 32, 64):
            raise InvalidIntCap.from_token(token=self)

    def nbits(self) -> int:
        return self.cap

    def __repr__(self) -> str:
        return "int{0}".format(self.cap)


@dataclass
class ExtensibleType(Type):
    extensible: bool = False


@dataclass
class Array(ExtensibleType):
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

    def validate_type(self) -> bool:
        """It's allowed to alias to:
            * base types (bool, uint, int, byte)
            * array of base types
            * array of alias to base types
        """
        if isinstance(self.type, BaseType):
            return True
        if isinstance(self.type, Array):
            array = cast(Array, self.type)
            if isinstance(array.type, BaseType):
                return True
            if isinstance(array.type, Alias):
                alias = cast(Alias, array.type)
                if isinstance(alias.type, BaseType):
                    return True
        return False

    def validate(self) -> None:
        if not self.validate_type():
            raise InvalidAliasedType.from_token(token=self)

    def nbits(self) -> int:
        return self.type.nbits()

    @property
    def extensible(self) -> bool:
        if isinstance(self.type, ExtensibleType):
            extensible_type = cast(ExtensibleType, self.type)
            return extensible_type.extensible
        return False


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
class Enum(ExtensibleType, Scope):
    type: Uint = _UINT_MISSING

    def __repr__(self) -> str:
        return f"<enum {self.name}>"

    def nbits(self) -> int:
        return self.type.nbits()

    @property
    def fields(self) -> List[EnumField]:
        return [field for _, field in self.enum_fields(recursive=False)]

    def name_to_values(self) -> "dict_[str, int]":
        return dict_((field.name, field.value) for field in self.fields)

    def value_to_names(self) -> "dict_[int, str]":
        return dict_((field.value, field.name) for field in self.fields)

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
class Message(ExtensibleType, Scope):
    name: str = ""

    @property
    def fields(self) -> List[MessageField]:
        return [field for _, field in self.message_fields(recursive=False)]

    def nbits(self) -> int:
        return sum(field.type.nbits() for field in self.fields)

    def __repr__(self) -> str:
        return f"<message {self.name}>"

    def number_to_field(self) -> "dict_[int, MessageField]":
        return dict_((field.number, field) for field in self.fields)

    def number_to_field_sorted(self) -> "dict_[int, MessageField]":
        fields = sorted(self.fields, key=lambda field: field.number)
        return dict_((field.number, field) for field in fields)

    def validate_member_on_push(
        self, member: Definition, name: Optional[str] = None
    ) -> None:
        if isinstance(member, MessageField):
            self.validate_message_field_on_push(member)

    def validate_message_field_on_push(self, field: MessageField) -> None:
        # Field number already defined?
        if field.number in self.number_to_field():
            raise DuplicatedMessageFieldNumber.from_token(token=field)


@dataclass
class Proto(Scope):
    def __repr__(self) -> str:
        return f"<bitproto {self.name}>"
