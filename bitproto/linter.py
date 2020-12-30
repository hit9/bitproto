"""
bitproto.linter
~~~~~~~~~~~~~~~

Built-in linter, skipable but not configurable.
"""

import abc
from dataclasses import dataclass
from typing import Callable, Optional, Tuple, TypeVar, Type as T, Generic, List

from bitproto._ast import Node, Enum, Proto
from bitproto.errors import warning
from bitproto.errors import Warning, EnumNameNotPascal

Result = Tuple[Optional[Warning], Optional[str]]

N = TypeVar("N")


class Rule(Generic[N]):
    """Describes a lint rule."""

    @abc.abstractmethod
    def description(self) -> str:
        """Rule description."""
        raise NotImplementedError

    @abc.abstractmethod
    def target_class(self) -> T[N]:
        """Target ast class."""
        raise NotImplementedError

    @abc.abstractmethod
    def checker(self, node: N, name: Optional[str] = None) -> Result:
        """Checker function, returns warning and suggestion message.
        :param node: The node of typed N.
        :param name: The name this node declared in its parent scope, if has.
        """
        raise NotImplementedError


class RuleEnumNamingPascal(Rule[Enum]):
    def description(self) -> str:
        return "Check if enum name is in pascal case."

    def target_class(self) -> T[Enum]:
        return Enum

    def checker(self, node: Enum, name: Optional[str] = None) -> Result:
        # TODO
        return EnumNameNotPascal(), "using abc"


class Linter:
    def filter_rules(self, target_class: T[N]) -> List[Rule[N]]:
        """Filter rule by target_class."""
        return [rule for rule in self.rules() if rule.target_class() is target_class]

    def run_rule_checker(
        self, rule: Rule[N], node: N, name: Optional[str] = None
    ) -> None:
        """Run given rule's checker on given node."""
        warning(*rule.checker(node, name=name))

    def lint_enums(self, enums: List[Tuple[str, Enum]]) -> None:
        for rule in self.filter_rules(Enum):
            for name, enum in enums:
                self.run_rule_checker(rule, enum, name=name)

    def lint(self, proto: Proto) -> None:
        self.lint_enums(proto.enums(recursive=True, bound=proto))
        # TODO: messages etc.

    def rules(self) -> Tuple[Rule, ...]:
        """Rules collection.
        Subclasses could overload."""
        return (RuleEnumNamingPascal(),)


def lint(proto: Proto) -> None:
    """Run default linter on given proto."""
    return Linter().lint(proto)
