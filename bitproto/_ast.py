"""
bitproto._ast
~~~~~~~~~~~~~

Abstraction syntax tree.

    Node
      |- Comment                        :Node
      |- Type                           :Node
      |    |- BaseType                  :Type:Node
      |    |    |- Bool                 :BaseType:Type:Node
      |    |    |- Byte                 :BaseType:Type:Node
      |    |    |- Int                  :BaseType:Type:Node
      |    |    |- Uint                 :BaseType:Type:Node
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
from typing import Any, Callable, ClassVar, List, Optional, Tuple, Dict
from typing import Type as T
from typing import TypeVar, Union, cast

from bitproto.utils import (
    conditional_cache,
    cache,
    frozen,
    safe_hash,
    final as final_,
)
from bitproto.errors import (
    DuplicatedDefinition,
    DuplicatedEnumFieldValue,
    DuplicatedMessageFieldNumber,
    DuplicatedOption,
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
from bitproto.options import (
    MESSAGE_OPTIONS,
    PROTO_OPTTIONS,
    OptionDescriptor,
    OptionDescriptors,
    Value as OptionValue,
    Validator as OptionValidator,
)

N = TypeVar("N", bound="Node")  # Node
D = TypeVar("D", bound="Definition")  # Definition
S = T[N]  # Type of Node.


ConstantValue = Union[bool, int, str]

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

    node_self = cast(Node, self)
    return node_self.__frozen__


# Decorator to cache given function if related node is frozen.
cache_if_frozen = conditional_cache(cache_if_frozen_condition)


def final(frozener: Callable[[S], S]) -> Callable[[S], S]:
    """Decorator to mark a node class to be a final node.
    A final node can't be inherit anymore.
    A final node is applied to following decorators:

        >>> @final_
            @safe_hash
            @frozener
            class LeafNode:
                pass
    """

    def decorator(node_class_: S) -> S:
        return final_((frozener(safe_hash(node_class_))))

    return decorator


def abstract(node_class_: S) -> S:
    """Decorator to mark a node class to be an abstract node.
    To distinguish from final node:
    An abstract node has no need to be frozen etc.
    """
    return node_class_


class _Meta(type):
    def __repr__(self) -> str:
        return getattr(self, "__repr_name__", self.__name__)


@abstract
@dataclass
class Node(metaclass=_Meta):
    token: str = ""
    lineno: int = 0
    filepath: str = ""

    # cheat mypy: overloads by @frozen
    __frozen__: ClassVar[bool] = False

    def is_frozen(self) -> bool:
        return self.__frozen__

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        pass

    def freeze(self) -> None:
        """Makes mypy happy.
        @frozen.later overloads this."""
        pass

    def __repr__(self) -> str:
        return "<{0}>".format(repr(type(self)))


@final(frozen.post_init)
@dataclass
class Comment(Node):
    @cache_if_frozen
    def content(self) -> str:
        """Returns the stripped content of this comment."""
        return self.token[2:].strip()

    def __str__(self) -> str:
        return self.content()


@abstract
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

    def __repr__(self) -> str:
        class_repr = repr(type(self))
        return f"<{class_repr} {self.name}>"


@abstract
@dataclass
class _NormalDefinition(Definition):
    "_NormalDefinition distinguishs from Proto."

    @property
    def bound(self) -> "Proto":
        if self._bound:
            return self._bound
        raise InternalError("_NormalDefinition got bound None")


_VALUE_MISSING = "_value_missing"


@abstract
@dataclass
class Option(_NormalDefinition):
    value: OptionValue = _VALUE_MISSING

    def __repr__(self) -> str:
        return "<option {0}={1}>".format(self.name, self.value)

    @classmethod
    def from_value(cls, value: OptionValue, **kwds: Any) -> "Option":
        """Creates an option from value with a right subclass."""
        class_ = cls.reflect_subclass_by_value_or_raise(value)
        return class_(value=value, **kwds)

    @classmethod
    def reflect_subclass_by_value(cls, value: OptionValue) -> Optional[T["Option"]]:
        if value is True or value is False:
            return BooleanOption
        elif isinstance(value, int):
            return IntegerOption
        elif isinstance(value, str):
            return StringOption
        return None

    @classmethod
    def reflect_subclass_by_value_or_raise(cls, value: OptionValue) -> T["Option"]:
        class_ = cls.reflect_subclass_by_value(value)
        if class_ is not None:
            return class_
        raise InvalidOptionValue(description=f"Invalid option value {value}")


@final(frozen.post_init)
@dataclass
class IntegerOption(Option):
    value: int = 0


@final(frozen.post_init)
@dataclass
class BooleanOption(Option):
    value: bool = False


@final(frozen.post_init)
@dataclass
class StringOption(Option):
    value: str = ""


@dataclass(frozen=True)
class OptionDescriptor_:
    """Wrapper around original OptionDescriptor.
    """

    name: str
    class_: T[Option]
    default: OptionValue
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


@abstract
@dataclass
class Constant(_NormalDefinition):
    value: ConstantValue = _VALUE_MISSING

    def __repr__(self) -> str:
        return "<constant {0}={1}>".format(self.name, self.value)

    def unwrap(self) -> ConstantValue:
        return self.value

    @classmethod
    def reflect_subclass_by_value(cls, value: ConstantValue) -> Optional[T["Constant"]]:
        if value is True or value is False:
            return BooleanConstant
        elif isinstance(value, int):
            return IntegerConstant
        elif isinstance(value, str):
            return StringConstant
        return None

    @classmethod
    def reflect_subclass_by_value_or_raise(cls, value: ConstantValue) -> T["Constant"]:
        class_ = cls.reflect_subclass_by_value(value)
        if class_ is not None:
            return class_
        raise InvalidOptionValue(description=f"Invalid constant value {value}")

    @classmethod
    def from_value(cls, value: ConstantValue, **kwds: Any) -> "Constant":
        """Creates a constant from value with a right subclass."""
        class_ = cls.reflect_subclass_by_value_or_raise(value)
        return class_(value=value, **kwds)


@final(frozen.post_init)
@dataclass
class IntegerConstant(Constant):
    value: int = 0


@final(frozen.post_init)
@dataclass
class BooleanConstant(Constant):
    value: bool = False


@final(frozen.post_init)
@dataclass
class StringConstant(Constant):
    value: str = ""


@abstract
@dataclass
class Scope(Definition):
    members: "dict_[str, Definition]" = dataclass_field(default_factory=dict_)

    def push_member(self, member: Definition, name: Optional[str] = None) -> None:
        """Push a definition `member`, and run hook functions around."""
        if self.is_frozen():
            raise InternalError("push on frozen scope.")

        if name is None:
            name = member.name
        if name in self.members:
            raise DuplicatedDefinition.from_token(token=member)

        self.validate_member_on_push(member, name)

        self.members[name] = member

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
        """Get name in this scope by member."""
        for name, member_ in self.members.items():
            if member_ is member:
                return name
        return None

    @cache_if_frozen
    def filter(
        self, t: T[D], recursive: bool = False, bound: Optional["Proto"] = None,
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
                if isinstance(member, _NormalDefinition):
                    if member.bound is not bound:
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


@abstract
@dataclass
class _NormalScope(Scope, _NormalDefinition):
    "_NormalScope distinguishs from Proto."
    pass


@abstract
@dataclass
class ScopeWithOptions(Scope):
    """Scope with options described."""

    def options(self) -> List[Tuple[str, Option]]:
        return self.filter(Option, recursive=False, bound=None)

    @cache_if_frozen
    def options_as_dict(self) -> "dict_[str, Option]":
        return dict_((name, option) for name, option in self.options())

    @cache
    def option_descriptors(self) -> Dict[str, OptionDescriptor_]:
        """Returns descriptors in format dict.
        Assuming subclass has attribute `__option_descriptors__` declared.
        """
        descriptors = getattr(self, "__option_descriptors__", None)
        if not descriptors:
            return {}
        wrappers = [OptionDescriptor_.wraps(d) for d in descriptors]
        return dict((w.name, w) for w in wrappers)

    def get_option_descriptor(self, name: str) -> Optional[OptionDescriptor_]:
        return self.option_descriptors().get(name, None)

    def validate_member_on_push(
        self, member: Definition, name: Optional[str] = None
    ) -> None:
        super(ScopeWithOptions, self).validate_member_on_push(member, name)

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

    def validate_option_on_push(self, option: Option) -> None:
        """Validate option on parser pushes."""
        # Is this option described?
        descriptor = self.get_option_descriptor(option.name)
        if not descriptor:
            raise UnsupportedOption.from_token(option)

        # Validate type.
        class_ = descriptor.class_
        if not isinstance(option, class_):
            message = f"invalid option type, requires {class_}"
            raise InvalidOptionValue.from_token(message=message, token=option)

        # Validate value
        validator = descriptor.validator
        description = descriptor.description

        if validator is not None:
            if not validator(option.value):
                message = f"invalid option value (description => {description})" or ""
                raise InvalidOptionValue.from_token(option, message=message)


@abstract
@dataclass
class Type(Node):
    _is_missing: bool = False

    def nbits(self) -> int:
        raise NotImplementedError

    @cache_if_frozen
    def nbytes(self) -> int:
        nbits = self.nbits()
        if nbits % 8 == 0:
            return int(nbits / 8)
        return int(nbits / 8) + 1


_TYPE_MISSING = Type(_is_missing=True)


@abstract
@dataclass
class BaseType(Type):
    pass


@final(frozen.post_init)
@dataclass
class Bool(BaseType):
    def nbits(self) -> int:
        return 1

    def __repr__(self) -> str:
        return "<type bool>"


@final(frozen.post_init)
@dataclass
class Byte(BaseType):
    def nbits(self) -> int:
        return 8

    def __repr__(self) -> str:
        return "<byte>"


@abstract
@dataclass
class Integer(BaseType):
    pass


@final(frozen.post_init)
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


@final(frozen.post_init)
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


@abstract
@dataclass
class ExtensibleType(Type):
    extensible: bool = False


@final(frozen.post_init)
@dataclass
class Array(ExtensibleType):
    type: Type = _TYPE_MISSING
    cap: int = 0

    @property
    def supported_types(self) -> Tuple[T[Type], ...]:
        return (Bool, Byte, Int, Uint, Enum, Message, Alias)

    def validate(self) -> None:
        self.validate_array_cap()
        self.validate_array_type()

    def validate_array_cap(self) -> None:
        if not (0 < self.cap < 1024):
            raise InvalidArrayCap.from_token(token=self)

    def validate_array_type(self) -> None:
        if not isinstance(self.type, self.supported_types):
            raise UnsupportedArrayType.from_token(token=self)

    @cache_if_frozen
    def nbits(self) -> int:
        if self.type is None:
            return 0
        return self.cap * self.type.nbits()

    def __repr__(self) -> str:
        extensible_flag = "'" if self.extensible else ""
        return "<type array ({0}, cap={1}){2}>".format(
            self.type, self.cap, extensible_flag
        )


@final(frozen.post_init)
@dataclass
class Alias(Type, _NormalDefinition):
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


@abstract
@dataclass
class Field(_NormalDefinition):
    pass


@final(frozen.post_init)
@dataclass
class EnumField(Field):
    value: int = 0

    def __repr__(self) -> str:
        return f"<enum-field {self.name}={self.value}>"

    def validate(self) -> None:
        if self.value < 0:
            raise InvalidEnumFieldValue.from_token(token=self)


@final(frozen.later)
@dataclass
class Enum(ExtensibleType, _NormalScope):
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


@final(frozen.post_init)
@dataclass
class MessageField(Field):
    type: Type = Type()
    number: int = 0

    def __repr__(self) -> str:
        return f"<message-field {self.name}={self.number}>"

    def validate(self) -> None:
        if not (0 < self.number < 256):
            raise InvalidMessageFieldNumber.from_token(token=self)


@final(frozen.later)
@dataclass
class Message(ExtensibleType, _NormalScope, ScopeWithOptions):
    name: str = ""
    __option_descriptors__: ClassVar[OptionDescriptors] = MESSAGE_OPTIONS

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
        super(Message, self).validate_member_on_push(member, name)

        if isinstance(member, MessageField):
            self.validate_message_field_on_push(member)

    def validate_message_field_on_push(self, field: MessageField) -> None:
        # Field number already defined?
        if field.number in self.number_to_field():
            raise DuplicatedMessageFieldNumber.from_token(token=field)


@final(frozen.later)
@dataclass
class Proto(ScopeWithOptions):
    __repr_name__: ClassVar[str] = "bitproto"
    __option_descriptors__: ClassVar[OptionDescriptors] = PROTO_OPTTIONS

    def __repr__(self) -> str:
        return f"<bitproto {self.name}>"
