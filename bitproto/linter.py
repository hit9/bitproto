"""
bitproto.linter
~~~~~~~~~~~~~~~

Built-in linter, skipable but not configurable.
"""

import abc
from dataclasses import dataclass
from typing import Callable, Optional, Tuple, TypeVar, Type as T, Generic, List

from bitproto._ast import (
    Alias,
    BoundDefinition,
    Constant,
    Definition,
    Enum,
    EnumField,
    Message,
    MessageField,
    Node,
    Proto,
)
from bitproto.errors import warning
from bitproto.errors import (
    Warning,
    LintWarning,
    ConstantNameNotUpper,
    EnumNameNotPascal,
    EnumHasNoFieldValue0,
    EnumFieldNameNotUpper,
    IndentWarning,
    MessageNameNotPascal,
    MessageFieldNameNotSnake,
)
from bitproto.utils import pascal_case, snake_case


D = TypeVar("D", bound=Definition)

SUPPORTED_TYPES: Tuple[T[Definition], ...] = (
    Alias,
    Constant,
    Enum,
    EnumField,
    Message,
    MessageField,
    Proto,
    Definition,  # For generic rule.
    BoundDefinition,  # For generic rule in bound definition.
)


class Rule(Generic[D]):
    """Abstract class to describe a lint rule."""

    @abc.abstractmethod
    def target_class(self) -> T[D]:
        """Target ast class."""
        raise NotImplementedError

    @abc.abstractmethod
    def check(self, definition: D, name: Optional[str] = None) -> Optional[LintWarning]:
        """Checker function, returns warning and suggestion message.
        :param definition: The definition of typed D.
        :param name: The name this definition declared in its parent scope, if has.
        """
        raise NotImplementedError


class Linter:
    """The linter."""

    def filter_rules(self, target_class: T[D]) -> List[Rule[D]]:
        """Filter rule by target_class.
        Comparasion by operator `is`.
        """
        return [rule for rule in self.rules() if rule.target_class() is target_class]

    def run_rule_checker(
        self, rule: Rule[D], definition: D, name: Optional[str] = None
    ) -> None:
        """Run given rule's checker on given definition."""
        warning(rule.check(definition, name))

    def lint(self, proto: Proto) -> None:
        """Run lint rules for definitions bound to this proto."""
        for definition_type in SUPPORTED_TYPES:

            items: List[Tuple[str, Definition]]
            if definition_type is Proto:  # proto is not a member of itself.
                items = [(proto.name, proto)]
            else:
                items = proto.filter(definition_type, recursive=True, bound=proto)

            rules = self.filter_rules(definition_type)
            for name, definition in items:
                for rule in rules:
                    self.run_rule_checker(rule, definition, name=name)

    def rules(self) -> Tuple[Rule, ...]:
        """Rules collection.
        Subclasses could overload."""
        return (
            RuleDefinitionIndent(),
            RuleConstantNamingUpper(),
            RuleEnumNamingPascal(),
            RuleEnumContains0(),
            RuleEnumFieldNamingUpper(),
            RuleMessageNamingPascal(),
            RuleMessageFieldNamingSnake(),
        )


def lint(proto: Proto) -> None:
    """Run default linter on given proto."""
    return Linter().lint(proto)


# Rule Implementations


class RuleDefinitionIndent(Rule[BoundDefinition]):
    """Check definition indent."""

    def target_class(self) -> T[BoundDefinition]:
        return BoundDefinition

    def check(
        self, definition: BoundDefinition, name: Optional[str] = None
    ) -> Optional[LintWarning]:
        expect: int = (len(definition.scope_stack) - 1) * 4
        if definition.indent > 0 and expect >= 0 and definition.indent != expect:
            return IndentWarning.from_token(
                token=definition, suggestion=f"{expect} spaces"
            )
        return None


class RuleConstantNamingUpper(Rule[Constant]):
    """Check if constant name is in upper case."""

    def target_class(self) -> T[Constant]:
        return Constant

    def check(
        self, definition: Constant, name: Optional[str] = None
    ) -> Optional[LintWarning]:
        definition_name = name or definition.name
        if not definition_name.isupper():
            return ConstantNameNotUpper.from_token(
                token=definition, suggestion=definition_name.upper()
            )
        return None


class RuleEnumNamingPascal(Rule[Enum]):
    """Check if enum name is in pascal case."""

    def target_class(self) -> T[Enum]:
        return Enum

    def check(
        self, definition: Enum, name: Optional[str] = None
    ) -> Optional[LintWarning]:
        definition_name = name or definition.name
        expect = pascal_case(definition_name)
        if definition_name != expect:
            return EnumNameNotPascal.from_token(token=definition, suggestion=expect)
        return None


class RuleEnumContains0(Rule[Enum]):
    """Check if enum contains a field 0."""

    def target_class(self) -> T[Enum]:
        return Enum

    def check(
        self, definition: Enum, name: Optional[str] = None
    ) -> Optional[LintWarning]:
        for field in definition.fields:
            if field.value == 0:
                return None
        return EnumHasNoFieldValue0.from_token(token=definition, suggestion=None)


class RuleEnumFieldNamingUpper(Rule[EnumField]):
    """Check if enum field name is in upper case."""

    def target_class(self) -> T[EnumField]:
        return EnumField

    def check(
        self, definition: EnumField, name: Optional[str] = None
    ) -> Optional[LintWarning]:
        definition_name = name or definition.name
        if not definition_name.isupper():
            return EnumFieldNameNotUpper.from_token(
                token=definition, suggestion=definition_name.upper()
            )
        return None


class RuleMessageNamingPascal(Rule[Message]):
    """Check if message name is in pascal case."""

    def target_class(self) -> T[Message]:
        return Message

    def check(
        self, definition: Message, name: Optional[str] = None
    ) -> Optional[LintWarning]:
        definition_name = name or definition.name
        expect = pascal_case(definition_name)
        if expect != definition_name:
            return MessageNameNotPascal.from_token(token=definition, suggestion=expect)
        return None


class RuleMessageFieldNamingSnake(Rule[MessageField]):
    """Check if message field name is in snake case."""

    def target_class(self) -> T[MessageField]:
        return MessageField

    def check(
        self, definition: MessageField, name: Optional[str] = None
    ) -> Optional[LintWarning]:
        definition_name = name or definition.name
        expect = snake_case(definition_name)
        if expect != definition_name:
            return MessageFieldNameNotSnake.from_token(
                token=definition, suggestion=expect
            )
        return None
