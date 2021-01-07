"""
Renderer for Go.
"""

from typing import List

from bitproto.renderer.block import (Block, BlockAheadNotice, BlockBindAlias,
                                     BlockBindConstant, BlockBindEnum,
                                     BlockBindEnumField, BlockBindMessage,
                                     BlockBindMessageField, BlockBindProto,
                                     BlockComposition, BlockWrapper)
from bitproto.renderer.impls.go.formatter import GoFormatter as F
from bitproto.renderer.renderer import Renderer
from bitproto.utils import cached_property, override, snake_case, upper_case


class BlockPackageName(BlockBindProto[F]):
    @override(Block)
    def render(self) -> None:
        self.push_definition_comments()
        self.push(f"package {self.d.name}")


class BlockGeneralImports(Block):
    @override(Block)
    def render(self) -> None:
        self.push(f'import "strconv"')
        self.push(f'import "encoding/json"')


class BlockImportChildProto(BlockBindProto[F]):
    @override(Block)
    def render(self) -> None:
        self.push(self.formatter.format_import_statement(self.d, as_name=self.name))


class BlockImportChildProtoList(BlockComposition[F]):
    @override(BlockComposition)
    def blocks(self) -> List[Block[F]]:
        return [
            BlockImportChildProto(proto, name)
            for name, proto in self.bound.protos(recursive=False)
        ]

    @override(BlockComposition)
    def separator(self) -> str:
        return "\n"


class BlockGeneralFunctionBool2Byte(Block[F]):
    @override(Block[F])
    def render(self) -> None:
        self.push("func bool2byte(b bool) byte {")
        self.push("if b {", indent=1)
        self.push("return 1", indent=2)
        self.push("}", indent=1)
        self.push("return 0", indent=1)
        self.push("}")


class BlockGeneralFunctionByte2Bool(Block[F]):
    @override(Block)
    def render(self) -> None:
        self.push("func byte2bool(b byte) bool {")
        self.push("if b > 0 {", indent=1)
        self.push("return true", indent=2)
        self.push("}", indent=1)
        self.push("return false", indent=1)
        self.push("}")


class BlockGeneralGlobalFunctions(BlockComposition[F]):
    @override(BlockComposition)
    def blocks(self) -> List[Block[F]]:
        return [
            BlockGeneralFunctionBool2Byte(),
            BlockGeneralFunctionByte2Bool(),
        ]

    @override(BlockComposition)
    def separator(self) -> str:
        return "\n\n"


class BlockAlias(BlockBindAlias[F]):
    @override(Block)
    def render(self) -> None:
        self.push_definition_comments()
        self.push(f"type {self.alias_name} {self.aliased_type}")


class BlockAliasList(BlockComposition[F]):
    @override(BlockComposition)
    def blocks(self) -> List[Block[F]]:
        return [
            BlockAlias(alias, name)
            for name, alias in self.bound.aliases(recursive=True, bound=self.bound)
        ]

    @override(BlockComposition)
    def separator(self) -> str:
        return "\n\n"


class BlockConstant(BlockBindConstant[F]):
    @override(Block)
    def render(self) -> None:
        self.push_definition_comments()
        self.push(
            f"const {self.constant_name} {self.constant_value_type} = {self.constant_value}"
        )


class BlockConstantList(BlockComposition[F]):
    @override(BlockComposition)
    def blocks(self) -> List[Block[F]]:
        return [
            BlockConstant(constant, name)
            for name, constant in self.bound.constants(recursive=True, bound=self.bound)
        ]

    @override(BlockComposition)
    def separator(self) -> str:
        return "\n\n"


class BlockEnumField(BlockBindEnumField[F]):
    @override(Block)
    def render(self) -> None:
        self.push_definition_comments()
        self.push(
            f"const {self.enum_field_name} {self.enum_field_type} = {self.enum_field_value}"
        )


class BlockEnumFieldList(BlockBindEnum[F], BlockComposition[F]):
    @override(BlockComposition)
    def blocks(self) -> List[Block[F]]:
        return [BlockEnumField(field) for field in self.d.fields()]

    @override(BlockComposition)
    def separator(self) -> str:
        return "\n"


class BlockEnumType(BlockBindEnum[F]):
    @override(Block)
    def render(self) -> None:
        self.push_definition_comments()
        self.push(f"type {self.enum_name} {self.enum_uint_type}")


class BlockEnumStringFunctionCaseItem(BlockBindEnumField[F]):
    @override(Block)
    def render(self) -> None:
        self.push(f"case {self.enum_field_value}:")
        self.push(f'return "{self.enum_field_name}"', indent=self.indent + 1)


class BlockEnumStringFunctionCaseDefault(BlockBindEnum[F]):
    @override(Block)
    def render(self) -> None:
        self.push("default:")
        self.push(
            f'return "{self.enum_name}(" + strconv.FormatInt(int64(v), 10) + ")"',
            indent=self.indent + 1,
        )


class BlockEnumStringFunctionCaseList(BlockBindEnum[F], BlockComposition[F]):
    @override(BlockComposition)
    def blocks(self) -> List[Block[F]]:
        bs: List[Block[F]] = [
            BlockEnumStringFunctionCaseItem(field, indent=self.indent)
            for field in self.d.fields()
        ]
        bs.append(BlockEnumStringFunctionCaseDefault(self.d, indent=self.indent))
        return bs

    @override(BlockComposition)
    def separator(self) -> str:
        return "\n"


class BlockEnumStringFunction(BlockBindEnum[F], BlockWrapper[F]):
    @override(BlockWrapper)
    def wraps(self) -> Block:
        return BlockEnumStringFunctionCaseList(self.d, indent=1)

    @override(BlockWrapper)
    def before(self) -> None:
        self.push_comment("String returns the name of this enum item.")
        self.push(f"func (v {self.enum_name}) String() string {{")

    @override(BlockWrapper)
    def after(self) -> None:
        self.push("}")


class BlockEnum(BlockBindEnum[F], BlockComposition[F]):
    @override(BlockComposition)
    def blocks(self) -> List[Block[F]]:
        return [
            BlockEnumType(self.d),
            BlockEnumFieldList(self.d),
            BlockEnumStringFunction(self.d),
        ]

    @override(BlockComposition)
    def separator(self) -> str:
        return "\n\n"


class BlockEnumList(BlockComposition):
    @override(BlockComposition)
    def blocks(self) -> List[Block[F]]:
        return [
            BlockEnum(enum, name)
            for name, enum in self.bound.enums(recursive=True, bound=self.bound)
        ]


class BlockMessageField(BlockBindMessageField[F]):
    @override(Block)
    def render(self) -> None:
        self.push_definition_comments()
        snake_case_name = snake_case(self.message_field_name)
        self.push(
            f'{self.message_field_name} {self.message_field_type} `json:"{snake_case_name}"`'
        )


class BlockMessageFieldList(BlockBindMessage[F], BlockComposition[F]):
    @override(BlockComposition)
    def blocks(self) -> List[Block[F]]:
        return [
            BlockMessageField(field, indent=self.indent)
            for field in self.d.sorted_fields()
        ]

    @override(BlockComposition)
    def separator(self) -> str:
        return "\n"


class BlockMessageSize(BlockBindMessage[F]):
    @override(Block)
    def render(self) -> None:
        self.push_comment(f"Number of bytes to serialize struct {self.message_name}")
        self.push(
            f"const {self.message_size_constant_name} uint32 = {self.message_nbytes}"
        )


class BlockMessageStruct(BlockBindMessage[F], BlockWrapper[F]):
    @override(BlockWrapper)
    def wraps(self) -> Block[F]:
        return BlockMessageFieldList(self.d, indent=1)

    @override(BlockWrapper)
    def before(self) -> None:
        self.push_definition_comments()
        self.push(f"type {self.message_name} struct {{")

    @override(BlockWrapper)
    def after(self) -> None:
        self.push("}")


class BlockMessageFunctionSize(BlockBindMessage[F]):
    @override(Block)
    def render(self) -> None:
        self.push_comment(f"Returns struct {self.message_name} size.")
        self.push(f"func (m *{self.message_name}) Size() uint32 {{")
        self.push(f"return {self.message_nbytes}", indent=1)
        self.push("}")


class BlockMessageFunctionString(BlockBindMessage[F]):
    @override(Block)
    def render(self) -> None:
        self.push_comment(
            f"Returns string representation for struct {self.message_name}."
        )
        self.push(f"func (m *{self.message_name}) String() string {{")
        self.push(f"v, _ := json.Marshal(m)", indent=1)
        self.push(f"return string(v)", indent=1)
        self.push("}")


class BlockMessage(BlockBindMessage[F], BlockComposition[F]):
    @override(BlockComposition)
    def blocks(self) -> List[Block[F]]:
        return [
            BlockMessageSize(self.d),
            BlockMessageStruct(self.d),
            BlockMessageFunctionSize(self.d),
            BlockMessageFunctionString(self.d),
        ]


class BlockMessageList(BlockComposition[F]):
    @override(BlockComposition)
    def blocks(self) -> List[Block[F]]:
        return [
            BlockMessage(message, name)
            for name, message in self.bound.messages(recursive=True, bound=self.bound)
        ]


class BlockList(BlockComposition[F]):
    @override(BlockComposition)
    def blocks(self) -> List[Block[F]]:
        return [
            BlockAheadNotice(),
            BlockPackageName(self.bound),
            BlockGeneralImports(),
            BlockImportChildProtoList(),
            BlockGeneralGlobalFunctions(),
            BlockAliasList(),
            BlockConstantList(),
            BlockEnumList(),
            BlockMessageList(),
        ]


class RendererGo(Renderer[F]):
    """Renderer for Go language."""

    @override(Renderer)
    def file_extension(self) -> str:
        return ".go"

    @override(Renderer)
    def formatter(self) -> F:
        return F()

    @override(Renderer)
    def block(self) -> Block[F]:
        return BlockList()
