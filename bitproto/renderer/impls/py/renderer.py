"""
Renderer for Python.
"""
from typing import List, cast

from bitproto.renderer.block import (Block, BlockAheadNotice, BlockComposition,
                                     BlockDefinition, BlockWrapper)
from bitproto.renderer.formatter import Formatter
from bitproto.renderer.impls.py.formatter import PyFormatter
from bitproto.renderer.renderer import Renderer
from bitproto.utils import override


class BlockGeneralImports(Block):
    @override(Block)
    def render(self) -> None:
        self.push("import json")
        self.push("from typing import Dict")


class BlockGeneralFunctionInt8(Block):
    @override(Block)
    def render(self) -> None:
        self.push("def int8(i: int) -> int:")
        self.push("if i < 128:", indent=4)
        self.push("return int(i)", indent=8)
        self.push("return i - 256", indent=4)


class BlockGeneralFunctionInt16(Block):
    @override(Block)
    def render(self) -> None:
        self.push("def int16(i: int) -> int:")
        self.push("if i < 32768:", indent=4)
        self.push("return int(i)", indent=8)
        self.push("return i - 65536", indent=4)


class BlockGeneralFunctionInt32(Block):
    @override(Block)
    def render(self) -> None:
        self.push("def int32(i: int) -> int:")
        self.push("if i < 2147483648:", indent=4)
        self.push("return int(i)", indent=8)
        self.push("return i - 4294967296", indent=4)


class BlockGeneralFunctionInt64(Block):
    @override(Block)
    def render(self) -> None:
        self.push("def int64(i: int) -> int:")
        self.push("if i < 9223372036854775808:", indent=4)
        self.push("return int(i)", indent=8)
        self.push("return i - 18446744073709551616", indent=4)


class BlockGeneralGlobalFunctions(BlockComposition):
    @override(BlockComposition)
    def blocks(self) -> List[Block]:
        return [
            BlockGeneralFunctionInt8(),
            BlockGeneralFunctionInt16(),
            BlockGeneralFunctionInt32(),
            BlockGeneralFunctionInt64(),
        ]


class BlockImportChildproto(BlockDefinition):
    @override(Block)
    def render(self) -> None:
        statement = self.formatter.format_import_statement(
            self.as_proto, as_name=self.definition_name
        )
        self.push(statement)


class BlockImportList(BlockComposition):
    @override(BlockComposition)
    def blocks(self) -> List[Block]:
        return [
            BlockImportChildproto(proto, name=name)
            for name, proto in self.bound.protos(recursive=False)
        ]


class BlockConstant(BlockDefinition):
    @property
    def constant_name(self) -> str:
        return self.formatter.format_constant_name(self.as_constant)

    @property
    def constant_value(self) -> str:
        return self.formatter.format_value(self.as_constant.value)

    @override(Block)
    def render(self) -> None:
        self.push_docstring(as_comment=True)
        self.push(f"{self.constant_name} = {self.constant_value}")
        self.push_location_doc()


class BlockConstantList(BlockComposition):
    @override(BlockComposition)
    def blocks(self) -> List[Block]:
        return [
            BlockConstant(constant, name=name)
            for name, constant in self.bound.constants(recursive=True, bound=self.bound)
        ]


class BlockEnumFieldBase(BlockDefinition):
    @property
    def field_name(self) -> str:
        return self.formatter.format_enum_field_name(self.as_enum_field)

    @property
    def field_value(self) -> str:
        return self.formatter.format_int_value(self.as_enum_field.value)


class BlockEnumField(BlockEnumFieldBase):
    @override(Block)
    def render(self) -> None:
        self.push(f"{self.field_name}: int = {self.field_value}")


class BlockEnumBase(BlockDefinition):
    pass


class BlockEnumFieldList(BlockEnumBase, BlockComposition):
    @override(BlockComposition)
    def blocks(self) -> List[Block]:
        return [BlockEnumField(field) for field in self.as_enum.fields()]

    @override(BlockComposition)
    def separator(self) -> str:
        return "\n"


class BlockEnumFieldListWrapper(BlockEnumBase, BlockWrapper):
    @override(BlockWrapper)
    def wraps(self) -> Block:
        return BlockEnumFieldList(self.as_enum)

    @override(BlockWrapper)
    def before(self) -> None:
        self.push_docstring(as_comment=True)


class BlockEnumValueToNameMapItem(BlockEnumFieldBase):
    @override(Block)
    def render(self) -> None:
        self.push(f'{self.field_value}: "{self.field_name}",')


class BlockEnumValueToNameMapItemList(BlockEnumBase, BlockComposition):
    @override(BlockComposition)
    def blocks(self) -> List[Block]:
        return [
            BlockEnumValueToNameMapItem(field, indent=4)
            for field in self.as_enum.fields()
        ]

    @override(BlockComposition)
    def separator(self) -> str:
        return "\n"


class BlockEnumValueToNameMap(BlockEnumBase, BlockWrapper):
    @override(BlockWrapper)
    def wraps(self) -> Block:
        return BlockEnumValueToNameMapItemList(self.as_enum)

    @override(BlockWrapper)
    def before(self) -> None:
        formatter = cast(PyFormatter, self.formatter)
        map_name = formatter.format_enum_value_to_name_map_name(self.as_enum)
        self.push(f"{map_name}: Dict[int, str] = {{")

    @override(BlockWrapper)
    def after(self) -> None:
        self.push("}")


class BlockEnum(BlockEnumBase, BlockComposition):
    @override(BlockComposition)
    def blocks(self) -> List[Block]:
        return [
            BlockEnumFieldListWrapper(self.as_enum),
            BlockEnumValueToNameMap(self.as_enum),
        ]


class BlockEnumList(BlockComposition):
    @override(BlockComposition)
    def blocks(self) -> List[Block]:
        return [
            BlockEnum(enum)
            for name, enum in self.bound.enums(recursive=True, bound=self.bound)
        ]


class RendererPy(Renderer):
    """Renderer for Python language."""

    def file_extension(self) -> str:
        return ".py"

    def formatter(self) -> Formatter:
        return PyFormatter()

    def blocks(self) -> List[Block]:
        return [
            BlockAheadNotice(),
            BlockGeneralImports(),
            BlockImportList(),
            BlockGeneralGlobalFunctions(),
            BlockConstantList(),
            BlockEnumList(),
        ]
