"""
bitproto._ast
~~~~~~~~~~~~~

Abstraction syntax tree.

    Node
      |- Comment                        :Node
      |- Type                           :Node
      |    |- SingleType                :Type:Node
      |    |    |- BaseType             :SingleType:Node
      |    |    |    |- Bool            :BaseType:SingleType:Type:Node
      |    |    |    |- Byte            :BaseType:SingleType:Type:Node
      |    |    |    |- Int             :BaseType:SingleType:Type:Node
      |    |    |    |- Uint            :BaseType:SingleType:Type:Node
      |    |    |- Enum                 :SingleType:Type:Node
      |    |- CompositeType             :Type:Node
      |    |    |- Array                :CompositeType:Type:Node
      |    |    |- Message              :CompositeType:Type:Node
      |    |- ExtensibleType            :Type:Node
      |    |    |- Array                :ExtensibleType:Type:Node
      |    |    |- Enum                 :ExtensibleType:Type:Node
      |    |    |- Message              :ExtensibleType:Type:Node
      |    |- Alias                     :Type:Node
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
from typing import Any, Callable, ClassVar, Dict, List, Optional, Tuple
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
    MessageSizeOverflows,
    UnsupportedArrayType,
    UnsupportedOption,
)
from bitproto.options import (
    MESSAGE_OPTIONS,
    PROTO_OPTTIONS,
    OptionDescriptor,
    OptionDescriptors,
)
from bitproto.options import Validator as OptionValidator
from bitproto.utils import (
    cache,
    conditional_cache,
    final,
    frozen,
    overridable,
    override,
)

N = TypeVar("N", bound="Node")  # Node
D = TypeVar("D", bound="Definition")  # Definition
V = TypeVar("V", bool, int, str)  # Base value

Value = Union[bool, int, str]

_ENABLE_CACHE_ON_AST_FROZEN = True


def cache_if_frozen_condition(
    func: Callable, args: List[Any], kwargs: Dict[str, Any]
) -> bool:
    """Condition that cache given function if related node is frozen.
    Works only for ast node's method.
    Follows global cache switch: _ENABLE_CACHE_ON_AST_FROZEN.
    """
    if not _ENABLE_CACHE_ON_AST_FROZEN:
        return False

    if not args:
        return False

    self = args[0]
    if not self:
        return False

    if not isinstance(self, Node):
        return False

    return getattr(self, "__frozen__", False)


# Decorator to cache given function if related node is frozen.
cache_if_frozen = conditional_cache(cache_if_frozen_condition)


@dataclass
class Node:
    token: str = ""
    lineno: int = 0
    filepath: str = ""

    # cheat mypy: override by @frozen
    __frozen__: ClassVar[bool] = False

    def is_frozen(self) -> bool:
        return self.__frozen__

    def __post_freeze__(self) -> None:
        self.validate_post_freeze()

    @overridable
    def validate_post_freeze(self) -> None:
        """Validator hook function, invoked after node freezed."""
        pass

    def freeze(self) -> None:
        """Makes mypy happy.
        @frozen overrides this."""
        pass

    def __repr__(self) -> str:
        return "<{0}>".format(repr(type(self)))


@final
@frozen
@dataclass
class Comment(Node):
    """Represents a line of comment."""

    @cache_if_frozen
    def content(self) -> str:
        """Returns the stripped content of this comment."""
        return self.token[2:].strip()

    def __str__(self) -> str:
        return self.content()


@dataclass
class Definition(Node):
    """Definition base class.

    :param name: The name of this definition.
    :param scope_stack: The parent scope stack, snapshot from parser.
    :param comment_block: The comment lines of this definition.
    :param indent: The number of indent characters of the starting token.
    :param _bound: The proto instance this definition bound.
    """

    name: str = ""
    scope_stack: Tuple["Scope", ...] = tuple()
    comment_block: Tuple[Comment, ...] = tuple()
    indent: int = 0  # <0 for invalid.
    _bound: Optional["Proto"] = None  # None for Proto.

    def __repr__(self) -> str:
        class_repr = repr(type(self))
        return f"<{class_repr} {self.name}>"


@dataclass
class BoundDefinition(Definition):
    """BoundDefinition is definitions bound to a proto,
    distinguishs from Proto."""

    @property
    def bound(self) -> "Proto":
        if self._bound:
            return self._bound
        raise InternalError("BoundDefinition got bound None")


_VALUE_MISSING = "_value_missing"


@dataclass
class Option(BoundDefinition):
    value: Value = _VALUE_MISSING

    def __repr__(self) -> str:
        return "<option {0}={1}>".format(self.name, self.value)

    @classmethod
    def type_name(cls) -> str:
        return "option"

    @classmethod
    def from_value(cls, value: Value, **kwds: Any) -> "Option":
        """Creates an option from value with a right subclass."""
        class_ = cls.reflect_subclass_by_value_or_raise(value)
        return class_(value=value, **kwds)

    @classmethod
    def reflect_subclass_by_value(cls, value: Value) -> Optional[T["Option"]]:
        if value is True or value is False:
            return BooleanOption
        elif isinstance(value, int):
            return IntegerOption
        elif isinstance(value, str):
            return StringOption
        return None

    @classmethod
    def reflect_subclass_by_value_or_raise(cls, value: Value) -> T["Option"]:
        class_ = cls.reflect_subclass_by_value(value)
        if class_ is not None:
            return class_
        raise InvalidOptionValue(description=f"Invalid option value {value}")


@final
@frozen
@dataclass
class IntegerOption(Option):
    value: int = 0

    @classmethod
    def type_name(cls) -> str:
        return "integer"


@final
@frozen
@dataclass
class BooleanOption(Option):
    value: bool = False

    @classmethod
    def type_name(cls) -> str:
        return "boolean"


@final
@frozen
@dataclass
class StringOption(Option):
    value: str = ""

    @classmethod
    def type_name(cls) -> str:
        return "string"


@dataclass(frozen=True)
class OptionDescriptor_:
    """Wrapper around original OptionDescriptor.

    :param class_: The Option class reflect from default value in original descriptor.
    """

    name: str
    class_: T[Option]
    default: Value
    validator: Optional[OptionValidator] = None
    description: Optional[str] = None

    @classmethod
    def wraps(cls, descriptor: OptionDescriptor) -> "OptionDescriptor_":
        """Creates an OptionDescriptor_ wraps from given descriptor."""
        class_ = Option.reflect_subclass_by_value_or_raise(descriptor.default)
        return cls(
            name=descriptor.name,
            class_=class_,
            default=descriptor.default,
            validator=descriptor.validator,
            description=descriptor.description,
        )


@dataclass
class Constant(BoundDefinition):
    value: Value = _VALUE_MISSING

    def __repr__(self) -> str:
        return "<constant {0}={1}>".format(self.name, self.value)

    def unwrap(self) -> Value:
        return self.value

    @classmethod
    def reflect_subclass_by_value(cls, value: Value) -> Optional[T["Constant"]]:
        if value is True or value is False:
            return BooleanConstant
        elif isinstance(value, int):
            return IntegerConstant
        elif isinstance(value, str):
            return StringConstant
        return None

    @classmethod
    def reflect_subclass_by_value_or_raise(cls, value: Value) -> T["Constant"]:
        class_ = cls.reflect_subclass_by_value(value)
        if class_ is not None:
            return class_
        raise InvalidOptionValue(description=f"Invalid constant value {value}")

    @classmethod
    def from_value(cls, value: Value, **kwds: Any) -> "Constant":
        """Creates a constant from value with a right subclass."""
        class_ = cls.reflect_subclass_by_value_or_raise(value)
        return class_(value=value, **kwds)


@final
@frozen
@dataclass
class IntegerConstant(Constant):
    value: int = 0


@final
@frozen
@dataclass
class BooleanConstant(Constant):
    value: bool = False


@final
@frozen
@dataclass
class StringConstant(Constant):
    value: str = ""


@dataclass
class Scope(Definition):
    """Scope is a definition with child definitions as members.
    In bitproto syntax design, a pair of braces declares a scope.

        {                     => push_scope(scope)
            definitions       => scope.push_member()
        }                     => pop_scope(), scope.freeze()
    """

    members: "dict_[str, Definition]" = dataclass_field(default_factory=dict_)

    def push_member(self, member: Definition, name: Optional[str] = None) -> None:
        """Push a definition `member`, and run hook functions around.
        Raises error if given member's name already taken by another member.

        :param member: The member parsed.
        :param name: Optional name declared in this scope (instead of member.name).
        """
        if self.is_frozen():
            raise InternalError("push on frozen scope.")

        if name is None:
            name = member.name
        if name in self.members:
            raise DuplicatedDefinition.from_token(token=member)

        self.validate_member_on_push(member, name)

        self.members[name] = member

    @overridable
    def validate_member_on_push(
        self, member: Definition, name: Optional[str] = None
    ) -> None:
        """Invoked on given member going to push as given name into this scope.
        Subclasses may override this."""
        pass

    @cache_if_frozen
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

    @cache_if_frozen
    def get_name_by_member(self, member: Definition) -> Optional[str]:
        """Get name in this scope by member.
        Compared by operator `is`.
        """
        for name, member_ in self.members.items():
            if member_ is member:
                return name
        return None

    @cache_if_frozen
    def filter(
        self,
        t: T[D],
        recursive: bool = False,
        bound: Optional["Proto"] = None,
    ) -> List[Tuple[str, D]]:
        """Filter member by given type. (dfs)

        :param t: The type to filter.
        :param recursive: Whether filter recursively.
        :param bound: Filter definitions bound to given proto if provided.
        """
        items: List[Tuple[str, D]] = []
        for item in self.members.items():
            name, member = item
            if bound:
                if isinstance(member, BoundDefinition):
                    if member.bound is not bound:
                        continue
                else:  # skip directly.
                    continue
            if recursive:  # Child first
                if isinstance(member, Scope):
                    scope = cast(Scope, member)
                    items.extend(scope.filter(t, recursive=recursive))
            if isinstance(member, t):
                items.append((name, member))
        return items

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


@dataclass
class BoundScope(Scope, BoundDefinition):
    "BoundScope is the scope has a bound, distinguishs from Proto."
    pass


@dataclass
class ScopeWithOptions(Scope):
    """Scope with options described."""

    def __init_subclass__(cls) -> None:
        """Assuming subclasses define a class-level `__option_descriptors__`
        attribute."""
        if getattr(cls, "__option_descriptors__", None) is None:
            raise InternalError("no __option_descriptors__ defined")

    def options(self) -> List[Tuple[str, Option]]:
        return self.filter(Option, recursive=False, bound=self._bound)

    @cache_if_frozen
    def options_as_dict(self) -> "dict_[str, Option]":
        return dict_((name, option) for name, option in self.options())

    @cache
    def option_descriptors(self) -> Dict[str, OptionDescriptor_]:
        """Returns descriptors in format dict."""
        descriptors = getattr(self, "__option_descriptors__", None)
        if not descriptors:
            return {}
        wrappers = [OptionDescriptor_.wraps(d) for d in descriptors]
        return dict((w.name, w) for w in wrappers)

    def get_option_descriptor(self, name: str) -> Optional[OptionDescriptor_]:
        """Get an option descriptor by name, None on not found."""
        return self.option_descriptors().get(name, None)

    @override(Scope)
    def validate_member_on_push(
        self, member: Definition, name: Optional[str] = None
    ) -> None:
        super().validate_member_on_push(member, name)

        if isinstance(member, Option):
            option = cast(Option, member)
            self.validate_option_on_push(option)

    @cache_if_frozen
    def option(self, name: str) -> Optional[Option]:
        """Obtain an option.
        Returns a default option if not defined.
        Returns None if not described.
        """
        option_dict = self.options_as_dict()
        if name in option_dict:
            return option_dict[name]

        descriptor = self.get_option_descriptor(name)
        if not descriptor:
            return None

        default = descriptor.class_(value=descriptor.default, name=name)
        return default

    @cache_if_frozen
    def get_option_or_raise(self, name: str) -> Option:
        """Obtain an option, or raise on invalid name."""
        option = self.option(name)
        if option:
            return option
        raise UnsupportedOption(message=f"get_option_or_raise({name}) got None")

    def get_option_value_or_raise(self, name: str, value_type: T[V]) -> V:
        """Obtain an option and returns its value.

        :param value_type: The expecting type of the value.
        """
        option = self.get_option_or_raise(name)
        value = option.value
        if isinstance(value, value_type):
            return value
        raise InternalError(f"option value not {value_type}")

    def get_option_as_int_or_raise(self, name: str) -> int:
        return self.get_option_value_or_raise(name, int)

    def get_option_as_string_or_raise(self, name: str) -> str:
        return self.get_option_value_or_raise(name, str)

    def get_option_as_bool_or_raise(self, name: str) -> bool:
        return self.get_option_value_or_raise(name, bool)

    def validate_option_on_push(self, option: Option) -> None:
        """Validate option on parser pushes."""
        # Is this option described?
        descriptor = self.get_option_descriptor(option.name)
        if not descriptor:
            raise UnsupportedOption.from_token(option)

        # Validate type.
        class_ = descriptor.class_
        if not isinstance(option, class_):
            message = f"invalid option type, requires {class_.type_name()}"
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
    # Indicates if self is _TYPE_MISSING
    _is_missing: bool = False

    @overridable
    def nbits(self) -> int:
        """Returns number of bits this type occupy.
        Should be override by final type subclasses.
        """
        raise NotImplementedError

    @final
    @cache_if_frozen
    def nbytes(self) -> int:
        """Returns the number of bytes this type occupy,
        calculated by nbits().
        """
        nbits = self.nbits()
        if nbits % 8 == 0:
            return int(nbits / 8)
        return int(nbits / 8) + 1


_TYPE_MISSING = Type(_is_missing=True)


@dataclass
class SingleType(Type):
    """SingleType is the type of the value composed of a single element.
    In bitproto, base types and enum are single types.
    """


@dataclass
class CompositeType(Type):
    """CompositeType is the type of the value composed of multiple elements,
    aka the type of value containers.
    In bitproto, message and array are composite types.
    """


@dataclass
class BaseType(SingleType):
    """BaseType is the type of base values.
    In bitproto, bool, byte and integer are base types.
    """


@final
@frozen
@dataclass
class Bool(BaseType):
    @override(Type)
    def nbits(self) -> int:
        return 1

    def __repr__(self) -> str:
        return "<type bool>"


@final
@frozen
@dataclass
class Byte(BaseType):
    @override(Type)
    def nbits(self) -> int:
        return 8

    def __repr__(self) -> str:
        return "<byte>"


@dataclass
class Integer(BaseType):
    pass


@final
@frozen
@dataclass
class Uint(Integer):
    """Uint is the unsigned Integer.
    In bitproto, uint type supports capacity ranges from 1 to 64.
    """

    cap: int = 0

    @override(Node)
    def validate_post_freeze(self) -> None:
        if self._is_missing:
            return
        if not (0 < self.cap <= 64):
            raise InvalidUintCap.from_token(token=self)

    @override(Type)
    def nbits(self) -> int:
        return self.cap

    def __repr__(self) -> str:
        return "<type uint{0}>".format(self.cap)


_UINT_MISSING = Uint(_is_missing=True)


@final
@frozen
@dataclass
class Int(Integer):
    """Int is the signed Integer.
    Different from uint, int type only supports capacity: 8, 16, 32, 64.
    """

    cap: int = 0

    @override(Node)
    def validate_post_freeze(self) -> None:
        if self.cap not in (8, 16, 32, 64):
            raise InvalidIntCap.from_token(token=self)

    @override(Type)
    def nbits(self) -> int:
        return self.cap

    def __repr__(self) -> str:
        return "<type int{0}>".format(self.cap)


@dataclass
class ExtensibleType(Type):
    """ExtensibleType is the type able to extend its size for backward-compatiable
    concern. When setting the `extensible` parameter to True, a micro buffer that
    indicates the type size will be inserted at the head of encoded buffer.
    In bitproto, array, enum and message are extensible types.
    """

    extensible: bool = False

    @overridable
    def ahead_nbits(self) -> int:
        """Returns the number of bits the ahead flag occupy."""
        raise NotImplementedError


@final
@frozen
@dataclass
class Array(CompositeType, ExtensibleType):
    """Array, described by element type and capacity.
    :param type: The type of array element.
    :param cap: Max value of number of elements.

    Constraint: Capacity of array should be smaller than 65536.
    """

    element_type: Type = _TYPE_MISSING
    cap: int = 0

    @classmethod
    def element_type_constraints(cls) -> Tuple[T[Type], ...]:
        return (
            Bool,
            Byte,
            Int,
            Uint,
            Enum,
            Message,
            Alias,
        )

    @override(Node)
    def validate_post_freeze(self) -> None:
        self.validate_array_cap()
        self.validate_array_element_type()

    def validate_array_cap(self) -> None:
        if not (0 < self.cap < 65536):
            raise InvalidArrayCap.from_token(token=self)

    def validate_array_element_type(self) -> None:
        if not isinstance(self.element_type, self.element_type_constraints()):
            raise UnsupportedArrayType.from_token(token=self)

    @override(ExtensibleType)
    def ahead_nbits(self) -> int:
        return 16

    @override(Type)
    @cache_if_frozen
    def nbits(self) -> int:
        n = self.cap * self.element_type.nbits()
        if not self.extensible:
            return n
        return self.ahead_nbits() + n

    def __repr__(self) -> str:
        extensible_flag = "'" if self.extensible else ""
        return "<type array ({0}, cap={1}){2}>".format(
            self.element_type, self.cap, extensible_flag
        )


@final
@frozen
@dataclass
class Alias(Type, BoundDefinition):
    """Alias is the type that references to a type.
    Similar to `typedef` in C, `type A = B` in Go etc.
    :param type: The referenced type.
    """

    type: Type = _TYPE_MISSING

    def __repr__(self) -> str:
        return f"<alias {self.name}>"

    def validate_type(self) -> None:
        """Constraint type to alias: type but not definition."""
        if isinstance(self.type, Definition):
            message = (
                f"invalid type alias, "
                f"target type '{self.type.name}' already has a name."
            )
            raise InvalidAliasedType.from_token(token=self, message=message)

    @override(Node)
    def validate_post_freeze(self) -> None:
        self.validate_type()

    @override(Type)
    def nbits(self) -> int:
        return self.type.nbits()

    @property
    def extensible(self) -> bool:
        if isinstance(self.type, ExtensibleType):
            extensible_type = cast(ExtensibleType, self.type)
            return extensible_type.extensible
        return False


@dataclass
class Field(BoundDefinition):
    pass


@final
@frozen
@dataclass
class EnumField(Field):
    value: int = 0

    def __repr__(self) -> str:
        return f"<enum-field {self.name}={self.value}>"

    @override(Node)
    def validate_post_freeze(self) -> None:
        if self.value < 0:
            raise InvalidEnumFieldValue.from_token(token=self)

    @property
    def enum(self) -> "Enum":
        scope = self.scope_stack[-1]
        if isinstance(scope, Enum):
            return cast(Enum, self.scope_stack[-1])
        raise InternalError("enum_field's last scope not enum")


@final
@frozen(post_init=False)
@dataclass
class Enum(BoundScope, SingleType):
    """Enum.
    :param type: The type annotation of this enum.

    Enum in bitproto constraints to uint type.
    """

    type: Uint = _UINT_MISSING

    def __repr__(self) -> str:
        return f"<enum {self.name}>"

    @override(ExtensibleType)
    def ahead_nbits(self) -> int:
        return 8

    @override(Type)
    def nbits(self) -> int:
        return self.type.nbits()

    @cache_if_frozen
    def fields(self) -> List[EnumField]:
        """Returns the EnumField list in this enum scope."""
        return [field for _, field in self.enum_fields(recursive=False)]

    @cache_if_frozen
    def name_to_values(self) -> "dict_[str, int]":
        """Returns the dict of field name to field value."""
        return dict_((field.name, field.value) for field in self.fields())

    @cache_if_frozen
    def value_to_names(self) -> "dict_[int, str]":
        """Returns the dict of field value to field name."""
        return dict_((field.value, field.name) for field in self.fields())

    @override(Scope)
    def validate_member_on_push(
        self, member: Definition, name: Optional[str] = None
    ) -> None:
        super(Enum, self).validate_member_on_push(member, name)

        if isinstance(member, EnumField):
            self.validate_enum_field_on_push(member)

    def validate_enum_field_on_push(self, field: EnumField) -> None:
        # Value overflows?
        if field.value.bit_length() > self.nbits():
            raise EnumFieldValueOverflow.from_token(token=field)
        # Value already defined?
        if field.value in self.value_to_names():
            raise DuplicatedEnumFieldValue.from_token(token=field)


@final
@frozen
@dataclass
class MessageField(Field):
    type: Type = Type()
    number: int = 0

    def __repr__(self) -> str:
        return f"<message-field {self.name}={self.number}>"

    @property
    def message(self) -> "Message":
        scope = self.scope_stack[-1]
        if isinstance(scope, Message):
            return cast(Message, self.scope_stack[-1])
        raise InternalError("message_field's last scope not message")

    @override(Node)
    def validate_post_freeze(self) -> None:
        """Constraint message field number from 1 to 255."""
        if not (0 < self.number < 256):
            raise InvalidMessageFieldNumber.from_token(token=self)


@final
@frozen(post_init=False)
@dataclass
class Message(BoundScope, ScopeWithOptions, CompositeType, ExtensibleType):
    """Message (similar to protobuf's message)."""

    name: str = ""

    __option_descriptors__: ClassVar[OptionDescriptors] = MESSAGE_OPTIONS

    @cache_if_frozen
    def nfields(self) -> int:
        """Returns the number of fields this message contains."""
        return len(self.fields())

    @cache_if_frozen
    def fields(self) -> List[MessageField]:
        """Returns the MessageField list in this message scope."""
        return [field for _, field in self.message_fields(recursive=False)]

    @cache_if_frozen
    def sorted_fields(self) -> List[MessageField]:
        """Sorted version of fields(), by field number."""
        return sorted(self.fields(), key=lambda field: field.number)

    @override(ExtensibleType)
    def ahead_nbits(self) -> int:
        return 16

    @override(Type)
    @cache_if_frozen
    def nbits(self) -> int:
        n = sum(field.type.nbits() for field in self.fields())
        if not self.extensible:
            return n
        return self.ahead_nbits() + n

    def __repr__(self) -> str:
        extensible_flag = "'" if self.extensible else ""
        return f"<message {self.name}{extensible_flag}>"

    @cache_if_frozen
    def number_to_field(self) -> "dict_[int, MessageField]":
        """Returns the dict field number to field."""
        return dict_((field.number, field) for field in self.fields())

    @cache_if_frozen
    def number_to_field_sorted(self) -> "dict_[int, MessageField]":
        """Dict version of sorted_fields(), in format of field number to field."""
        return dict_((field.number, field) for field in self.sorted_fields())

    @override(Node)
    def validate_post_freeze(self) -> None:
        if self.nbits() > 65535:
            raise MessageSizeOverflows.from_token(token=self)

        max_bytes = self.get_option_as_int_or_raise("max_bytes")
        if max_bytes > 0 and self.nbytes() > max_bytes:
            message = f"Message size overflows constraint option, which configured to {max_bytes}bytes"
            raise MessageSizeOverflows.from_token(token=self, message=message)

    @override(Scope)
    def validate_member_on_push(
        self, member: Definition, name: Optional[str] = None
    ) -> None:
        super(Message, self).validate_member_on_push(member, name)

        if isinstance(member, MessageField):
            self.validate_message_field_on_push(member)

    def validate_message_field_on_push(self, field: MessageField) -> None:
        # Field number already defined?
        if field.number in self.number_to_field():
            raise DuplicatedMessageFieldNumber.from_token(token=field)


@final
@frozen(post_init=False)
@dataclass
class Proto(ScopeWithOptions):
    __option_descriptors__: ClassVar[OptionDescriptors] = PROTO_OPTTIONS

    def set_name(self, name: str) -> None:
        if self.is_frozen():
            raise InternalError("set_name on frozen proto")
        self.name = name

    def set_comment_block(self, comment_block: Tuple[Comment, ...]) -> None:
        if self.is_frozen():
            raise InternalError("set_comment_block on frozen proto")
        self.comment_block = comment_block

    def __repr__(self) -> str:
        return f"<bitproto {self.name}>"
