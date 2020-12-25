"""
bitproto.ast
~~~~~~~~~~~~

Abstraction syntax tree.

    Node
      |- Newline                        :Node
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
      |    |    |- Template             :Scope:Definition:Node
      |    |    |- Enum                 :Scope:Definition:Node
      |    |    |- Message              :Scope:Definition:Node
      |    |    |- Proto                :Scope:Definition:Node
"""

from dataclasses import dataclass, field as dataclass_field
from collections import OrderedDict
from typing import Tuple, Union, Optional, Type as T

from bitproto.errors import (
    InternalError,
    UnsupportedArrayType,
    DuplicatedDefinition,
    InvalidArrayCap,
    InvalidIntCap,
    InvalidUintCap,
)


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
class Newline(Node):
    pass


@dataclass
class Comment(Node):
    def content(self) -> str:
        """Returns the stripped content of this comment, without the starting slashes."""
        return self.token[2:].strip()

    def __str__(self) -> str:
        return self.content()


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


@dataclass
class Option(Definition):
    value: Union[str, int, bool, None] = None


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


@dataclass
class IntegerConstant(Constant):
    value: int = 0

    def __int__(self) -> int:
        return self.value


@dataclass
class BooleanConstant(Constant):
    value: bool = False

    def __bool__(self) -> bool:
        return self.value


@dataclass
class StringConstant(Constant):
    value: str = ""

    def __str__(self) -> str:
        return self.value


@dataclass
class Scope(Definition):
    members: "OrderedDict[str, Definition]" = dataclass_field(
        default_factory=OrderedDict
    )

    def push_member(self, member: Definition, name: Optional[str] = None) -> None:
        if name is None:
            name = member.name
        if name in self.members:
            raise DuplicatedDefinition(
                message="Duplicated definition",
                filepath=member.filepath,
                token=member.token,
                lineno=member.lineno,
            )
        self.members[name] = member

    def options(self) -> "OrderedDict[str, Option]":
        return OrderedDict(
            (name, member)
            for name, member in self.members.items()
            if isinstance(member, Option)
        )

    def enums(self) -> "OrderedDict[str, Enum]":
        return OrderedDict(
            (name, member)
            for name, member in self.members.items()
            if isinstance(member, Enum)
        )

    def messages(self) -> "OrderedDict[str, Message]":
        return OrderedDict(
            (name, member)
            for name, member in self.members.items()
            if isinstance(member, Message)
        )

    def constants(self) -> "OrderedDict[str, Constant]":
        return OrderedDict(
            (name, member)
            for name, member in self.members.items()
            if isinstance(member, Constant)
        )

    def protos(self) -> "OrderedDict[str, Proto]":
        return OrderedDict(
            (name, member)
            for name, member in self.members.items()
            if isinstance(member, Proto)
        )

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


@dataclass
class Template(Scope):
    name: str = ""
    lang: str = ""
    content: str = ""


@dataclass
class Type(Node):
    def nbits(self) -> int:
        raise NotImplementedError

    def nbytes(self) -> int:
        nbits = self.nbits()
        if nbits % 8 == 0:
            return int(nbits / 8)
        return int(nbits / 8) + 1


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
        if self.cap <= 0 or self.cap > 64:
            raise InvalidUintCap(
                filepath=self.filepath, token=self.token, lineno=self.lineno
            )

    def nbits(self) -> int:
        return self.cap

    def __repr__(self) -> str:
        return "uint{0}".format(self.cap)


@dataclass
class Int(Type):
    cap: int = 0

    def validate(self) -> None:
        if self.cap not in (8, 16, 32, 64):
            raise InvalidIntCap(
                filepath=self.filepath, token=self.token, lineno=self.lineno
            )

    def nbits(self) -> int:
        return self.cap

    def __repr__(self) -> str:
        return "int{0}".format(self.cap)


@dataclass
class Array(Type):
    type: Optional[Type] = None
    cap: int = 0

    @property
    def supported_types(self) -> Tuple[T[Type], ...]:
        return (Bool, Byte, Int, Uint, Enum, Message, Alias)

    def validate(self) -> None:
        if self.type is None:
            raise InternalError(description="No type to construct an array type")
        if not isinstance(self.type, self.supported_types):
            raise UnsupportedArrayType(
                filepath=self.filepath, token=self.token, lineno=self.lineno
            )

    def nbits(self) -> int:
        if self.type is None:
            return 0
        return self.cap * self.type.nbits()

    def __repr__(self) -> str:
        return "{0}[{1}]".format(self.type, self.cap)


@dataclass
class Alias(Type, Definition):
    type: Optional[Type] = None


@dataclass
class Field(Definition):
    pass


@dataclass
class EnumField(Field):
    pass


@dataclass
class Enum(Type, Scope):
    type: Optional[Uint] = None


@dataclass
class MessageFiled(Field):
    pass


@dataclass
class Message(Type, Scope):
    name: str = ""

    def __repr__(self) -> str:
        return f"<message {self.name}>"


@dataclass
class Proto(Scope):
    def __repr__(self) -> str:
        return f"<bitproto {self.name}>"
