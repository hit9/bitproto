"""
Renderer for Python.
"""
from typing import List

from bitproto._ast import MessageField
from bitproto.renderer.block import (Block, BlockAheadNotice, BlockComposition,
                                     BlockDefinition, BlockWrapper)
from bitproto.renderer.formatter import Formatter
from bitproto.renderer.impls.py.formatter import PyFormatter
from bitproto.renderer.renderer import Renderer
from bitproto.utils import cached_property, override

Renderer_ = Renderer[PyFormatter]
Block_ = Block[PyFormatter]
BlockComposition_ = BlockComposition[PyFormatter]
BlockWrapper_ = BlockWrapper[PyFormatter]
BlockDefinition_ = BlockDefinition[PyFormatter]


class BlockStatementPass(Block_):
    @override(Block_)
    def render(self) -> None:
        self.push("pass")


class BlockProtoDocstring(BlockDefinition_):
    @override(Block_)
    def render(self) -> None:
        self.push_definition_docstring()


class BlockGeneralImports(Block_):
    @override(Block_)
    def render(self) -> None:
        self.push("from dataclasses import dataclass, field")
        self.push("from typing import ClassVar, Dict, List")


class BlockGeneralFunctionInt8(Block_):
    @override(Block_)
    def render(self) -> None:
        self.push("def int8(i: int) -> int:")
        self.push("return i if i < 128 else i - 256", indent=4)


class BlockGeneralFunctionInt16(Block_):
    @override(Block_)
    def render(self) -> None:
        self.push("def int16(i: int) -> int:")
        self.push("return i if i < 32768 else i - 65536", indent=4)


class BlockGeneralFunctionInt32(Block_):
    @override(Block_)
    def render(self) -> None:
        self.push("def int32(i: int) -> int:")
        self.push("return i if i < 2147483648 else i - 4294967296", indent=4)


class BlockGeneralFunctionInt64(Block_):
    @override(Block_)
    def render(self) -> None:
        self.push("def int64(i: int) -> int:")
        self.push(
            "return i if i < 9223372036854775808 else i - 18446744073709551616",
            indent=4,
        )


class BlockGeneralGlobalFunctions(BlockComposition_):
    @override(BlockComposition_)
    def separator(self) -> str:
        return "\n\n\n"

    @override(BlockComposition_)
    def blocks(self) -> List[Block_]:
        return [
            BlockGeneralFunctionInt8(),
            BlockGeneralFunctionInt16(),
            BlockGeneralFunctionInt32(),
            BlockGeneralFunctionInt64(),
        ]


class BlockImportChildProto(BlockDefinition_):
    @override(Block_)
    def render(self) -> None:
        statement = self.formatter.format_import_statement(
            self.as_proto, as_name=self.definition_name
        )
        self.push(statement)


class BlockImportChildProtoList(BlockComposition_):
    @override(BlockComposition_)
    def blocks(self) -> List[Block_]:
        return [
            BlockImportChildProto(proto, name=name)
            for name, proto in self.bound.protos(recursive=False)
        ]

    @override(BlockComposition_)
    def separator(self) -> str:
        return "\n"


class BlockImportList(BlockComposition_):
    @override(BlockComposition_)
    def blocks(self) -> List[Block_]:
        return [
            BlockGeneralImports(),
            BlockImportChildProtoList(),
        ]

    @override(BlockComposition_)
    def separator(self) -> str:
        return "\n\n"


class BlockAlias(BlockDefinition_):
    @cached_property
    def alias_name(self) -> str:
        return self.formatter.format_alias_name(self.as_alias)

    @cached_property
    def alias_type(self) -> str:
        return self.formatter.format_type(self.as_alias.type)

    @override(Block_)
    def render(self) -> None:
        self.push_definition_comments()
        self.push(f"{self.alias_name} = {self.alias_type}")


class BlockAliasList(BlockComposition_):
    @override(BlockComposition_)
    def blocks(self) -> List[Block_]:
        return [
            BlockAlias(alias, name=name)
            for name, alias in self.bound.aliases(recursive=True, bound=self.bound)
        ]

    @override(BlockComposition_)
    def separator(self) -> str:
        return "\n"


class BlockConstant(BlockDefinition_):
    @cached_property
    def constant_name(self) -> str:
        return self.formatter.format_constant_name(self.as_constant)

    @cached_property
    def constant_value(self) -> str:
        return self.formatter.format_value(self.as_constant.value)

    @cached_property
    def constant_type(self) -> str:
        return self.formatter.format_constant_type(self.as_constant)

    @override(Block_)
    def render(self) -> None:
        self.push_definition_comments()
        self.push(f"{self.constant_name}: {self.constant_type} = {self.constant_value}")


class BlockConstantList(BlockComposition_):
    @override(BlockComposition_)
    def blocks(self) -> List[Block_]:
        return [
            BlockConstant(constant, name=name)
            for name, constant in self.bound.constants(recursive=True, bound=self.bound)
        ]

    @override(BlockComposition_)
    def separator(self) -> str:
        return "\n"


class BlockEnumFieldBase(BlockDefinition_):
    @cached_property
    def field_name(self) -> str:
        return self.formatter.format_enum_field_name(self.as_enum_field)

    @cached_property
    def field_value(self) -> str:
        return self.formatter.format_int_value(self.as_enum_field.value)

    @cached_property
    def field_type(self) -> str:
        enum = self.as_enum_field.enum
        return self.formatter.format_enum_type(enum)


class BlockEnumField(BlockEnumFieldBase):
    @override(Block_)
    def render(self) -> None:
        self.push_definition_comments()
        self.push(f"{self.field_name}: {self.field_type} = {self.field_value}")


class BlockEnumBase(BlockDefinition_):
    @cached_property
    def enum_type_name(self) -> str:
        return self.formatter.format_enum_type(self.as_enum)


class BlockEnumFieldList(BlockEnumBase, BlockComposition_):
    @override(BlockComposition_)
    def blocks(self) -> List[Block_]:
        return [BlockEnumField(field) for field in self.as_enum.fields()]

    @override(BlockComposition_)
    def separator(self) -> str:
        return "\n"


class BlockEnumFieldListWrapper(BlockEnumBase, BlockWrapper_):
    @override(BlockWrapper_)
    def wraps(self) -> Block_:
        return BlockEnumFieldList(self.as_enum)

    @override(BlockWrapper_)
    def before(self) -> None:
        self.render_enum_type()

    def render_enum_type(self) -> None:
        self.push_definition_comments()
        self.push(f"{self.enum_type_name} = int")


class BlockEnumValueToNameMapItem(BlockEnumFieldBase):
    @override(Block_)
    def render(self) -> None:
        self.push(f'{self.field_value}: "{self.field_name}",')


class BlockEnumValueToNameMapItemList(BlockEnumBase, BlockComposition_):
    @override(BlockComposition_)
    def blocks(self) -> List[Block_]:
        return [
            BlockEnumValueToNameMapItem(field, indent=4)
            for field in self.as_enum.fields()
        ]

    @override(BlockComposition_)
    def separator(self) -> str:
        return "\n"


class BlockEnumValueToNameMap(BlockEnumBase, BlockWrapper_):
    @override(BlockWrapper_)
    def wraps(self) -> Block_:
        return BlockEnumValueToNameMapItemList(self.as_enum)

    @override(BlockWrapper_)
    def before(self) -> None:
        map_name = self.formatter.format_enum_value_to_name_map_name(self.as_enum)
        self.push(f"{map_name}: Dict[{self.enum_type_name}, str] = {{")

    @override(BlockWrapper_)
    def after(self) -> None:
        self.push("}")


class BlockEnum(BlockEnumBase, BlockComposition_):
    @override(BlockComposition_)
    def blocks(self) -> List[Block_]:
        return [
            BlockEnumFieldListWrapper(self.as_enum),
            BlockEnumValueToNameMap(self.as_enum),
        ]


class BlockEnumList(BlockComposition_):
    @override(BlockComposition_)
    def blocks(self) -> List[Block_]:
        return [
            BlockEnum(enum)
            for name, enum in self.bound.enums(recursive=True, bound=self.bound)
        ]

    @override(BlockComposition_)
    def separator(self) -> str:
        return "\n\n\n"


class BlockMessageField(BlockDefinition_):
    @cached_property
    def field_name(self) -> str:
        return self.as_message_field.name

    @cached_property
    def field_type(self) -> str:
        return self.formatter.format_type(self.as_message_field.type)

    @cached_property
    def field_default_value(self) -> str:
        return self.formatter.format_field_default_value(self.as_message_field.type)

    @override(Block_)
    def render(self) -> None:
        self.push_definition_comments()
        self.push(f"{self.field_name}: {self.field_type} = {self.field_default_value}")


class BlockMessageBase(BlockDefinition_):
    @cached_property
    def class_name(self) -> str:
        return self.formatter.format_message_name(self.as_message)


class BlockMessageSize(BlockMessageBase):
    @override(Block_)
    def render(self) -> None:
        self.push_comment(f"Number of bytes to serialize class {self.class_name}")
        nbytes = self.formatter.format_int_value(self.as_message.nbytes())
        self.push(f"MESSAGE_BYTES_LENGTH: ClassVar[int] = {nbytes}")


class BlockMessageFieldList(BlockMessageBase, BlockComposition_):
    @cached_property
    def fields(self) -> List[MessageField]:
        return self.as_message.sorted_fields()

    @override(BlockComposition_)
    def blocks(self) -> List[Block_]:
        fields = self.as_message.sorted_fields()
        return [BlockMessageField(field, indent=self.indent) for field in fields]

    @override(BlockComposition_)
    def separator(self) -> str:
        return "\n"


class BlockMessageClassDefs(BlockMessageBase, BlockComposition_):
    @override(BlockComposition_)
    def blocks(self) -> List[Block_]:
        return [
            BlockMessageSize(self.as_message, indent=self.indent),
            BlockMessageFieldList(self.as_message, indent=self.indent),
        ]

    @override(BlockComposition_)
    def separator(self) -> str:
        return "\n\n"


class BlockMessageClass(BlockMessageBase, BlockWrapper_):
    @override(BlockWrapper_)
    def wraps(self) -> Block_:
        return BlockMessageClassDefs(self.as_message, indent=4)

    @override(BlockWrapper_)
    def before(self) -> None:
        self.push("@dataclass")
        self.push(f"class {self.class_name}:")
        self.push_definition_docstring(indent=4)


class BlockMessage(BlockMessageBase, BlockComposition_):
    @override(BlockComposition_)
    def blocks(self) -> List[Block_]:
        return [BlockMessageClass(self.as_message)]


class BlockMessageList(BlockComposition_):
    @override(BlockComposition_)
    def blocks(self) -> List[Block_]:
        return [
            BlockMessage(message, name=name)
            for name, message in self.bound.messages(recursive=True, bound=self.bound)
        ]

    @override(BlockComposition_)
    def separator(self) -> str:
        return "\n\n\n"


class BlockHeadList(BlockComposition_):
    @override(BlockComposition_)
    def blocks(self) -> List[Block_]:
        return [
            BlockAheadNotice(),
            BlockProtoDocstring(self.bound),
            BlockImportList(),
        ]

    @override(BlockComposition_)
    def separator(self) -> str:
        return "\n\n"


class BlockList(BlockComposition_):
    @override(BlockComposition_)
    def blocks(self) -> List[Block_]:
        return [
            BlockHeadList(),
            BlockGeneralGlobalFunctions(),
            BlockAliasList(),
            BlockConstantList(),
            BlockEnumList(),
            BlockMessageList(),
        ]

    @override(BlockComposition_)
    def separator(self) -> str:
        return "\n\n\n"


class RendererPy(Renderer_):
    """Renderer for Python language."""

    @override(Renderer_)
    def file_extension(self) -> str:
        return ".py"

    @override(Renderer_)
    def formatter(self) -> PyFormatter:
        return PyFormatter()

    @override(Renderer_)
    def block(self) -> Block_:
        return BlockList()
