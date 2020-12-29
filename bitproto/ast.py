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

from collections import OrderedDict as dict_
from dataclasses import dataclass
from dataclasses import field as dataclass_field
from typing import Any, Callable, ClassVar, List, Optional, Tuple, Dict
from typing import Type as T
from typing import TypeVar, Union, cast

from bitproto.errors import (
    DuplicatedDefinition,
    DuplicatedEnumFieldValue,
    DuplicatedMessageFieldNumber,
    EnumFieldValueOverflow,
    InternalError,
    InvalidAliasedType,
    InvalidArrayCap,
    InvalidEnumFieldValue,
    InvalidIntCap,
    InvalidMessageFieldNumber,
    InvalidOptionValue,
    InvalidUintCap,
    UnsupportedArrayType,
    UnsupportedOption,
)

T_Definition = TypeVar("T_Definition", bound="Definition")
OptionValue = Union[str, int, bool]
ConstantValue = Union[str, int, bool]


class _Meta(type):
    def __repr__(self) -> str:
        return getattr(self, "__repr_name__", self.__name__)


@dataclass
class Node(metaclass=_Meta):
    token: str = ""
    lineno: int = 0
    filepath: str = ""

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        pass

    def __repr__(self) -> str:
        return "<{0}>".format(repr(type(self)))


@dataclass
class Comment(Node):
    def content(self) -> str:
        """Returns the stripped content of this comment."""
        return self.token[2:].strip()

    def __str__(self) -> str:
        return self.content()


@dataclass
class Definition(Node):
    name: str = ""
    scope_stack: Tuple["Scope", ...] = tuple()
    comment_block: Tuple[Comment, ...] = tuple()
    _bound: Optional["Proto"] = None

    def set_name(self, name: str) -> None:
        self.name = name

    def set_comment_block(self, comment_block: Tuple[Comment, ...]) -> None:
        self.comment_block = comment_block

    @property
    def bound(self) -> Optional["Proto"]:
        """Returns the proto this definition bound."""
        if self._bound:
            return self._bound  # Parser helps collected.
        if isinstance(self, Proto):
            return None
        # Parser sucks, or lookup scope_stack reversely.
        for scope in self.scope_stack[::-1]:
            if isinstance(scope, Proto):
                return cast(Proto, scope)
        raise InternalError("non-proto definition has no bound")

    def __repr__(self) -> str:
        class_repr = repr(type(self))
        return f"<{class_repr} {self.name}>"


_VALUE_MISSING = "_VALUE_MISSING"  # FIXME: how to represent value missing?


@dataclass
class Option(Definition):
    value: OptionValue = _VALUE_MISSING

    def __repr__(self) -> str:
        return "<option {0}={1}>".format(self.name, self.value)

    @classmethod
    def from_value(cls, value: OptionValue, **kwds: Any) -> "Option":
        """Creates an option from value with a right subclass."""
        if value is True or value is False:
            # Avoid isinstance(True, int)
            return BooleanOption(value=value, **kwds)
        elif isinstance(value, int):
            return IntegerOption(value=value, **kwds)
        elif isinstance(value, str):
            return StringOption(value=value, **kwds)
        return Option(value=value, **kwds)


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
class OptionDescriptor:
    name: str
    type: T[Option]
    default: OptionValue
    validator: Optional[Callable[..., bool]] = None
    description: Optional[str] = None


@dataclass
class Constant(Definition):
    value: ConstantValue = _VALUE_MISSING

    def __repr__(self) -> str:
        return "<constant {0}={1}>".format(self.name, self.value)

    def unwrap(self) -> ConstantValue:
        return self.value

    @classmethod
    def from_value(cls, value: ConstantValue, **kwds: Any) -> "Constant":
        """Creates a constant from value with a right subclass."""
        if value is True or value is False:
            # Avoid isinstance(True, int)
            return BooleanConstant(value=value, **kwds)
        elif isinstance(value, int):
            return IntegerConstant(value=value, **kwds)
        elif isinstance(value, str):
            return StringConstant(value=value, **kwds)
        return Constant(value=value, **kwds)


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
    members: "dict_[str, Definition]" = dataclass_field(default_factory=dict_)

    def validate_member_on_push(
        self, member: Definition, name: Optional[str] = None
    ) -> None:
        """Invoked on given member going to push as given name into this scope."""
        pass

    def push_member(self, member: Definition, name: Optional[str] = None) -> None:
        """Push a definition `member`, and run hook functions around."""
        if name is None:
            name = member.name
        if name in self.members:
            raise DuplicatedDefinition.from_token(token=member)

        self.validate_member_on_push(member, name)

        if isinstance(member, Option):
            option = cast(Option, member)
            self.validate_option_on_push(option, name)

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
        self,
        t: T[T_Definition],
        recursive: bool = False,
        bound: Optional["Proto"] = None,
    ) -> List[Tuple[str, T_Definition]]:
        """Filter member by given type. (dfs)

        :param t: The type to filter.
        :param recursive: Whether filter recursively.
        :param bound: Filter definitions bound to given proto if provided.
        """
        items: List[Tuple[str, T_Definition]] = []
        for item in self.members.items():
            name, member = item
            if bound:
                if member.bound is not bound:
                    continue
            if recursive:  # Child first
                if isinstance(member, Scope):
                    scope = cast(Scope, member)
                    items.extend(scope.filter(t, recursive=recursive))
            if isinstance(member, t):
                items.append((name, member))
        return items

    def options(
        self, recursive: bool = False, bound: Optional["Proto"] = None
    ) -> List[Tuple[str, "Option"]]:
        return self.filter(Option, recursive=recursive, bound=bound)

    def enums(
        self, recursive: bool = False, bound: Optional["Proto"] = None
    ) -> List[Tuple[str, "Enum"]]:
        return self.filter(Enum, recursive=recursive, bound=bound)

    def messages(
        self, recursive: bool = False, bound: Optional["Proto"] = None
    ) -> List[Tuple[str, "Message"]]:
        return self.filter(Message, recursive=recursive, bound=bound)

    def constants(
        self, recursive: bool = False, bound: Optional["Proto"] = None
    ) -> List[Tuple[str, "Constant"]]:
        return self.filter(Constant, recursive=recursive, bound=bound)

    def aliases(
        self, recursive: bool = False, bound: Optional["Proto"] = None
    ) -> List[Tuple[str, "Alias"]]:
        return self.filter(Alias, recursive=recursive, bound=bound)

    def enum_fields(
        self, recursive: bool = False, bound: Optional["Proto"] = None
    ) -> List[Tuple[str, "EnumField"]]:
        return self.filter(EnumField, recursive=recursive, bound=bound)

    def message_fields(
        self, recursive: bool = False, bound: Optional["Proto"] = None
    ) -> List[Tuple[str, "MessageField"]]:
        return self.filter(MessageField, recursive=recursive, bound=bound)

    def protos(self, recursive: bool = False) -> List[Tuple[str, "Proto"]]:
        return self.filter(Proto, recursive=recursive, bound=None)  # proto has no bound

    def option_descriptors(self) -> Dict[str, OptionDescriptor]:
        """Subclasses may override this.
        The default implementation assuming attribute `_option_descriptors` is defined."""
        descriptors = getattr(self, "_option_descriptors", [])
        return dict((d.name, d) for d in descriptors)

    def get_option_descriptor(self, name: str) -> Optional[OptionDescriptor]:
        return self.option_descriptors().get(name, None)

    def option(self, name: str) -> Optional[Option]:
        """Obtain an option.
        Returns a default option if not defined.
        Returns None if not described.
        """
        options = dict_(self.options(recursive=False))
        if name in options:
            return options[name]

        descriptor = self.get_option_descriptor(name)
        if not descriptor:
            return None

        default = descriptor.type(value=descriptor.default, name=name)
        return default

    def get_option_or_raise(self, name: str) -> Option:
        """Obtain an option, or raise on invalid name."""
        option = self.option(name)
        if option:
            return option
        raise UnsupportedOption(message=f"get_option_or_raise({name}) got None")

    def get_option_as_int_or_raise(self, name: str) -> int:
        option = self.get_option_or_raise(name)
        if isinstance(option, IntegerOption):
            return cast(IntegerOption, option).value
        raise InternalError("option not integer")

    def get_option_as_string_or_raise(self, name: str) -> str:
        option = self.get_option_or_raise(name)
        if isinstance(option, StringOption):
            return cast(StringOption, option).value
        raise InternalError("option not string")

    def get_option_as_bool_or_raise(self, name: str) -> bool:
        option = self.get_option_or_raise(name)
        if isinstance(option, BooleanOption):
            return cast(BooleanOption, option).value
        raise InternalError("option not boolean")

    def validate_option_on_push(
        self, option: Option, name: Optional[str] = None
    ) -> None:
        """Validate option on parser pushes."""
        name = name or option.name

        # Is this option described?
        descriptor = self.get_option_descriptor(name)
        if not descriptor:
            raise UnsupportedOption.from_token(option)

        # Validate type
        if not isinstance(option, descriptor.type):
            message = f"invalid option type, requires {descriptor.type}"
            raise InvalidOptionValue.from_token(message=message, token=option)

        # Validate value
        validator = descriptor.validator
        description = descriptor.description

        if validator is not None:
            if not validator(option.value):
                message = f"invalid option value (description => {description})" or ""
                raise InvalidOptionValue.from_token(option, message=message)


@dataclass
class Type(Node):
    _is_missing: bool = False

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
        return "<type bool>"


@dataclass
class Byte(BaseType):
    def nbits(self) -> int:
        return 8

    def __repr__(self) -> str:
        return "<byte>"


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
        return "<type uint{0}>".format(self.cap)


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
        return "<type int{0}>".format(self.cap)


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
        extensible_flag = "'" if self.extensible else ""
        return "<type array ({0}, cap={1}){2}>".format(
            self.type, self.cap, extensible_flag
        )


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
        extensible_flag = "'" if self.extensible else ""
        return f"<enum {self.name}{extensible_flag}>"

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

    _option_descriptors: ClassVar[List[OptionDescriptor]] = [
        OptionDescriptor(
            "max_bytes",
            IntegerOption,
            0,
            lambda v: v >= 0,
            "Setting the maximum limit of number of bytes for target message.",
        ),
    ]

    @property
    def fields(self) -> List[MessageField]:
        return [field for _, field in self.message_fields(recursive=False)]

    def nbits(self) -> int:
        return sum(field.type.nbits() for field in self.fields)

    def __repr__(self) -> str:
        extensible_flag = "'" if self.extensible else ""
        return f"<message {self.name}{extensible_flag}>"

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
    __repr_name__: ClassVar[str] = "bitproto"
    _option_descriptors: ClassVar[List[OptionDescriptor]] = [
        OptionDescriptor(
            "c.target_platform_bits",
            IntegerOption,
            32,
            lambda v: v in (32, 64),
            "C language target machine bits, 32 or 64",
        ),
        OptionDescriptor(
            "c.struct_packing_alignment",
            IntegerOption,
            1,
            lambda v: 0 <= v <= 8,
            "C language struct packing alignment, defaults to 1",
        ),
        OptionDescriptor(
            "c.enable_render_json_formatter",
            BooleanOption,
            True,
            None,
            "Whether render json formatter function for structs in C language, defaults to false",
        ),
        OptionDescriptor(
            "go.package_path",
            StringOption,
            "",
            None,
            "Package path of current golang package, to be imported, e.g. github.com/path/to/shared_bp",
        ),
    ]

    def __repr__(self) -> str:
        return f"<bitproto {self.name}>"
