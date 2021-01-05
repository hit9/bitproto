"""
Renderer for Go.
"""

from typing import List

from bitproto.renderer.block import (Block, BlockAheadNotice, BlockComposition,
                                     BlockDefinition, BlockWrapper)
from bitproto.renderer.formatter import Formatter
from bitproto.renderer.impls.go.formatter import GoFormatter
from bitproto.renderer.renderer import Renderer
from bitproto.utils import override, snake_case, upper_case

Renderer_ = Renderer[GoFormatter]
Block_ = Block[GoFormatter]
BlockComposition_ = BlockComposition[GoFormatter]
BlockWrapper_ = BlockWrapper[GoFormatter]
BlockDefinition_ = BlockDefinition[GoFormatter]


class BlockPackageName(BlockDefinition_):
    @override(Block_)
    def render(self) -> None:
        self.push_definition_docstring()
        self.push(f"package {self.as_proto.name}")


class BlockGeneralImports(Block_):
    @override(Block_)
    def render(self) -> None:
        self.push(f'import "strconv"')
        self.push(f'import "encoding/json"')


class BlockImportChildProto(BlockDefinition_):
    @override(Block_)
    def render(self) -> None:
        self.push(
            self.formatter.format_import_statement(
                self.as_proto, as_name=self.definition_name
            )
        )


class BlockImportChildProtoList(BlockComposition_):
    @override(BlockComposition_)
    def blocks(self) -> List[Block_]:
        return [
            BlockImportChildProto(proto, name)
            for name, proto in self.bound.protos(recursive=False)
        ]

    @override(BlockComposition_)
    def separator(self) -> str:
        return "\n"


class BlockGeneralFunctionBool2Byte(Block_):
    @override(Block_)
    def render(self) -> None:
        self.push("func bool2byte(b bool) byte {")
        self.push("if b {", indent=1)
        self.push("return 1", indent=2)
        self.push("}", indent=1)
        self.push("return 0", indent=1)
        self.push("}")


class BlockGeneralFunctionByte2Bool(Block_):
    @override(Block_)
    def render(self) -> None:
        self.push("func byte2bool(b byte) bool {")
        self.push("if b > 0 {", indent=1)
        self.push("return true", indent=2)
        self.push("}", indent=1)
        self.push("return false", indent=1)
        self.push("}")


class BlockGeneralGlobalFunctions(BlockComposition_):
    @override(BlockComposition_)
    def blocks(self) -> List[Block_]:
        return [
            BlockGeneralFunctionBool2Byte(),
            BlockGeneralFunctionByte2Bool(),
        ]

    @override(BlockComposition_)
    def separator(self) -> str:
        return "\n\n"


class BlockAlias(BlockDefinition_):
    @override(Block_)
    def render(self) -> None:
        t = self.as_alias
        type_name = self.formatter.format_alias_type(t)
        original_type_name = self.formatter.format_type(t.type)
        self.push_definition_docstring(as_comment=True)
        self.push(f"type {type_name} {original_type_name}")


class BlockAliasList(BlockComposition_):
    @override(BlockComposition_)
    def blocks(self) -> List[Block_]:
        return [
            BlockAlias(alias, name)
            for name, alias in self.bound.aliases(recursive=True, bound=self.bound)
        ]

    @override(BlockComposition_)
    def separator(self) -> str:
        return "\n\n"


class BlockConstant(BlockDefinition_):
    @override(Block_)
    def render(self) -> None:
        t = self.as_constant
        self.push_definition_docstring(as_comment=True)
        name = self.formatter.format_constant_name(t)
        value = self.formatter.format_value(t.value)
        value_type = self.formatter.format_constant_type(t)
        self.push(f"const {name} {value_type} = {value}")


class BlockConstantList(BlockComposition_):
    @override(BlockComposition_)
    def blocks(self) -> List[Block_]:
        return [
            BlockConstant(constant, name)
            for name, constant in self.bound.constants(recursive=True, bound=self.bound)
        ]

    @override(BlockComposition_)
    def separator(self) -> str:
        return "\n\n"


class BlockEnumFieldBase(BlockDefinition_):
    @property
    def field_value(self) -> str:
        return self.formatter.format_int_value(self.as_enum_field.value)

    @property
    def field_name(self) -> str:
        return self.formatter.format_enum_field_name(self.as_enum_field)

    @property
    def field_type(self) -> str:
        return self.formatter.format_enum_type(self.as_enum_field.enum)


class BlockEnumField(BlockEnumFieldBase):
    @override(Block_)
    def render(self) -> None:
        t = self.as_enum_field
        self.push_definition_docstring(as_comment=True)
        self.push(f"const {self.field_name} {self.field_type} = {self.field_value}")


class BlockEnumBase(BlockDefinition_):
    @property
    def enum_name(self) -> str:
        return self.formatter.format_enum_name(self.as_enum)

    @property
    def enum_type(self) -> str:
        return self.formatter.format_uint_type(self.as_enum.type)


class BlockEnumFieldList(BlockEnumBase, BlockComposition_):
    @override(BlockComposition_)
    def blocks(self) -> List[Block_]:
        return [BlockEnumField(field) for field in self.as_enum.fields()]

    @override(BlockComposition_)
    def separator(self) -> str:
        return "\n"


class BlockEnumType(BlockEnumBase):
    @override(Block_)
    def render(self) -> None:
        self.push_definition_docstring(as_comment=True)
        self.push(f"type {self.enum_name} {self.enum_type}")


class BlockEnumStringFunctionCaseItem(BlockEnumFieldBase):
    @override(Block_)
    def render(self) -> None:
        self.push(f"case {self.field_value}:")
        self.push(f'return "{self.field_name}"', indent=self.indent + 1)


class BlockEnumStringFunctionCaseDefault(BlockEnumBase):
    @override(Block_)
    def render(self) -> None:
        self.push("default:")
        self.push(
            f'return "{self.enum_name}(" + strconv.FormatInt(int64(v), 10) + ")"',
            indent=self.indent + 1,
        )


class BlockEnumStringFunctionCaseList(BlockEnumBase, BlockComposition_):
    @override(BlockComposition_)
    def blocks(self) -> List[Block_]:
        t = self.as_enum
        bs: List[Block_] = [
            BlockEnumStringFunctionCaseItem(field, indent=self.indent)
            for field in t.fields()
        ]
        bs.append(BlockEnumStringFunctionCaseDefault(t, indent=self.indent))
        return bs

    @override(BlockComposition_)
    def separator(self) -> str:
        return "\n"


class BlockEnumStringFunction(BlockEnumBase, BlockWrapper_):
    @override(BlockWrapper_)
    def wraps(self) -> Block_:
        return BlockEnumStringFunctionCaseList(self.as_enum, indent=1)

    @override(BlockWrapper_)
    def before(self) -> None:
        self.push_docstring("String returns the name of this enum item.")
        self.push(f"func (v {self.enum_name}) String() string {{")

    @override(BlockWrapper_)
    def after(self) -> None:
        self.push("}")


class BlockEnum(BlockEnumBase, BlockComposition_):
    @override(BlockComposition_)
    def blocks(self) -> List[Block_]:
        return [
            BlockEnumType(self.as_enum),
            BlockEnumFieldList(self.as_enum),
            BlockEnumStringFunction(self.as_enum),
        ]

    @override(BlockComposition_)
    def separator(self) -> str:
        return "\n\n"


class BlockEnumList(BlockComposition_):
    @override(BlockComposition_)
    def blocks(self) -> List[Block_]:
        return [
            BlockEnum(enum, name)
            for name, enum in self.bound.enums(recursive=True, bound=self.bound)
        ]


class BlockMessageFieldBase(BlockDefinition_):
    @property
    def field_name(self) -> str:
        return self.as_message_field.name

    @property
    def field_type(self) -> str:
        return self.formatter.format_type(self.as_message_field.type)


class BlockMessageField(BlockMessageFieldBase):
    @override(Block_)
    def render(self) -> None:
        self.push_definition_docstring(as_comment=True)
        snake_case_name = snake_case(self.field_name)
        self.push(f'{self.field_name} {self.field_type} `json:"{snake_case_name}"`')


class BlockMessageBase(BlockDefinition_):
    @property
    def struct_name(self) -> str:
        return self.formatter.format_message_name(self.as_message)

    @property
    def size_string(self) -> str:
        return self.formatter.format_int_value(self.as_message.nbytes())

    @property
    def struct_size_const_name(self) -> str:
        return upper_case(f"BYTES_LENGTH_{self.struct_name}")


class BlockMessageFieldList(BlockMessageBase, BlockComposition_):
    @override(BlockComposition_)
    def blocks(self) -> List[Block_]:
        return [
            BlockMessageField(field, indent=self.indent)
            for field in self.as_message.sorted_fields()
        ]

    @override(BlockComposition_)
    def separator(self) -> str:
        return "\n"


class BlockMessageSize(BlockMessageBase):
    @override(Block_)
    def render(self) -> None:
        self.push_comment(f"Number of bytes to serialize struct {self.struct_name}")
        self.push(f"const {self.struct_size_const_name} uint32 = {self.size_string}")


class BlockMessageStruct(BlockMessageBase, BlockWrapper_):
    @override(BlockWrapper_)
    def wraps(self) -> Block_:
        return BlockMessageFieldList(self.as_message, indent=1)

    @override(BlockWrapper_)
    def before(self) -> None:
        self.push_definition_docstring()
        self.push(f"type {self.struct_name} struct {{")

    @override(BlockWrapper_)
    def after(self) -> None:
        self.push("}")


class BlockMessageFunctionSize(BlockMessageBase):
    @override(Block_)
    def render(self) -> None:
        self.push_docstring(f"Returns struct {self.struct_name} size.")
        self.push(f"func (m *{self.struct_name}) Size() uint32 {{")
        self.push(f"return {self.struct_size_const_name}", indent=1)
        self.push("}")


class BlockMessageFunctionString(BlockMessageBase):
    @override(Block_)
    def render(self) -> None:
        self.push_docstring(
            f"Returns string representation for struct {self.struct_name}."
        )
        self.push(f"func (m *{self.struct_name}) String() string {{")
        self.push(f"v, _ := json.Marshal(m)", indent=1)
        self.push(f"return string(v)", indent=1)
        self.push("}")


class BlockMessage(BlockMessageBase, BlockComposition_):
    @override(BlockComposition_)
    def blocks(self) -> List[Block_]:
        return [
            BlockMessageSize(self.as_message),
            BlockMessageStruct(self.as_message),
            BlockMessageFunctionSize(self.as_message),
            BlockMessageFunctionString(self.as_message),
        ]


class BlockMessageList(BlockComposition_):
    @override(BlockComposition_)
    def blocks(self) -> List[Block_]:
        return [
            BlockMessage(message, name)
            for name, message in self.bound.messages(recursive=True, bound=self.bound)
        ]


class BlockList(BlockComposition_):
    @override(BlockComposition_)
    def blocks(self) -> List[Block_]:
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


class RendererGo(Renderer_):
    """Renderer for Go language."""

    @override(Renderer_)
    def file_extension(self) -> str:
        return ".go"

    @override(Renderer_)
    def formatter(self) -> GoFormatter:
        return GoFormatter()

    @override(Renderer_)
    def block(self) -> Block_:
        return BlockList()
