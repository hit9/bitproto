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
        type_name = self.formatter.format_alias_type(self.d)
        original_type_name = self.formatter.format_type(self.d.type)
        self.push_definition_comments()
        self.push(f"type {type_name} {original_type_name}")


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
        name = self.formatter.format_constant_name(self.d)
        value = self.formatter.format_value(self.d.value)
        value_type = self.formatter.format_constant_type(self.d)
        self.push(f"const {name} {value_type} = {value}")


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


class BlockEnumFieldBase(BlockBindEnumField[F]):
    @cached_property
    def field_value(self) -> str:
        return self.formatter.format_int_value(self.d.value)

    @cached_property
    def field_name(self) -> str:
        return self.formatter.format_enum_field_name(self.d)

    @cached_property
    def field_type(self) -> str:
        return self.formatter.format_enum_type(self.d.enum)


class BlockEnumField(BlockEnumFieldBase):
    @override(Block)
    def render(self) -> None:
        self.push_definition_comments()
        self.push(f"const {self.field_name} {self.field_type} = {self.field_value}")


class BlockEnumBase(BlockBindEnum[F]):
    @cached_property
    def enum_name(self) -> str:
        return self.formatter.format_enum_name(self.d)

    @cached_property
    def enum_type(self) -> str:
        return self.formatter.format_uint_type(self.d.type)


class BlockEnumFieldList(BlockEnumBase, BlockComposition[F]):
    @override(BlockComposition)
    def blocks(self) -> List[Block[F]]:
        return [BlockEnumField(field) for field in self.d.fields()]

    @override(BlockComposition)
    def separator(self) -> str:
        return "\n"


class BlockEnumType(BlockEnumBase):
    @override(Block)
    def render(self) -> None:
        self.push_definition_comments()
        self.push(f"type {self.enum_name} {self.enum_type}")


class BlockEnumStringFunctionCaseItem(BlockEnumFieldBase):
    @override(Block)
    def render(self) -> None:
        self.push(f"case {self.field_value}:")
        self.push(f'return "{self.field_name}"', indent=self.indent + 1)


class BlockEnumStringFunctionCaseDefault(BlockEnumBase):
    @override(Block)
    def render(self) -> None:
        self.push("default:")
        self.push(
            f'return "{self.enum_name}(" + strconv.FormatInt(int64(v), 10) + ")"',
            indent=self.indent + 1,
        )


class BlockEnumStringFunctionCaseList(BlockEnumBase, BlockComposition[F]):
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


class BlockEnumStringFunction(BlockEnumBase, BlockWrapper[F]):
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


class BlockEnum(BlockEnumBase, BlockComposition[F]):
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


class BlockMessageFieldBase(BlockBindMessageField[F]):
    @cached_property
    def field_name(self) -> str:
        return self.d.name

    @cached_property
    def field_type(self) -> str:
        return self.formatter.format_type(self.d.type)


class BlockMessageField(BlockMessageFieldBase):
    @override(Block)
    def render(self) -> None:
        self.push_definition_comments()
        snake_case_name = snake_case(self.field_name)
        self.push(f'{self.field_name} {self.field_type} `json:"{snake_case_name}"`')


class BlockMessageBase(BlockBindMessage[F]):
    @cached_property
    def struct_name(self) -> str:
        return self.formatter.format_message_name(self.d)

    @cached_property
    def size_string(self) -> str:
        return self.formatter.format_int_value(self.d.nbytes())

    @cached_property
    def struct_size_const_name(self) -> str:
        return upper_case(f"BYTES_LENGTH_{self.struct_name}")


class BlockMessageFieldList(BlockMessageBase, BlockComposition[F]):
    @override(BlockComposition)
    def blocks(self) -> List[Block[F]]:
        return [
            BlockMessageField(field, indent=self.indent)
            for field in self.d.sorted_fields()
        ]

    @override(BlockComposition)
    def separator(self) -> str:
        return "\n"


class BlockMessageSize(BlockMessageBase):
    @override(Block)
    def render(self) -> None:
        self.push_comment(f"Number of bytes to serialize struct {self.struct_name}")
        self.push(f"const {self.struct_size_const_name} uint32 = {self.size_string}")


class BlockMessageStruct(BlockMessageBase, BlockWrapper[F]):
    @override(BlockWrapper)
    def wraps(self) -> Block[F]:
        return BlockMessageFieldList(self.d, indent=1)

    @override(BlockWrapper)
    def before(self) -> None:
        self.push_definition_comments()
        self.push(f"type {self.struct_name} struct {{")

    @override(BlockWrapper)
    def after(self) -> None:
        self.push("}")


class BlockMessageFunctionSize(BlockMessageBase):
    @override(Block)
    def render(self) -> None:
        self.push_comment(f"Returns struct {self.struct_name} size.")
        self.push(f"func (m *{self.struct_name}) Size() uint32 {{")
        self.push(f"return {self.struct_size_const_name}", indent=1)
        self.push("}")


class BlockMessageFunctionString(BlockMessageBase):
    @override(Block)
    def render(self) -> None:
        self.push_comment(
            f"Returns string representation for struct {self.struct_name}."
        )
        self.push(f"func (m *{self.struct_name}) String() string {{")
        self.push(f"v, _ := json.Marshal(m)", indent=1)
        self.push(f"return string(v)", indent=1)
        self.push("}")


class BlockMessage(BlockMessageBase, BlockComposition[F]):
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
