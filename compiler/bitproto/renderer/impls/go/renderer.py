"""
Renderer for Go.
"""

from abc import abstractmethod
from typing import List, Optional

from bitproto._ast import (Alias, Array, Bool, Byte, Enum, Int, Integer,
                           Message, MessageField, SingleType, Uint)
from bitproto.renderer.block import (Block, BlockAheadNotice, BlockBindAlias,
                                     BlockBindConstant, BlockBindEnum,
                                     BlockBindEnumField, BlockBindMessage,
                                     BlockBindMessageField, BlockBindProto,
                                     BlockComposition, BlockEmptyLine,
                                     BlockWrapper)
from bitproto.renderer.impls.go.formatter import GoFormatter as F
from bitproto.renderer.renderer import Renderer
from bitproto.utils import (cached_property, cast_or_raise, override,
                            snake_case, upper_case)

GO_LIB_IMPORT_PATH = "github.com/hit9/bitproto/lib/go"


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
        self.push(f'import bp "{GO_LIB_IMPORT_PATH}"')


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


class BlockAliasMethodBase(BlockBindAlias[F]):
    @cached_property
    def method_receiver(self) -> str:
        if isinstance(self.d.type, SingleType):
            return f"{self.alias_name}"
        return f"*{self.alias_name}"


class BlockAliasMethodXXXProcessor(BlockAliasMethodBase):
    @override(Block)
    def render(self) -> None:
        to = self.formatter.format_processor(self.d.type)
        self.push(f"func (m {self.method_receiver}) XXXProcessor() bp.Processor {{")
        self.push(f"return bp.NewAliasProcessor({to})", indent=self.indent + 1)
        self.push("}")


class BlockAliasDef(BlockBindAlias[F]):
    @override(Block)
    def render(self) -> None:
        self.push_definition_comments()
        self.push(f"type {self.alias_name} {self.aliased_type}")


class BlockAlias(BlockBindAlias[F], BlockComposition[F]):
    @override(BlockComposition)
    def blocks(self) -> List[Block[F]]:
        return [
            BlockAliasDef(self.d),
            BlockAliasMethodXXXProcessor(self.d),
        ]

    @override(BlockComposition)
    def separator(self) -> str:
        return "\n\n"


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


class BlockEnumMethodStringCaseItem(BlockBindEnumField[F]):
    @override(Block)
    def render(self) -> None:
        self.push(f"case {self.enum_field_value}:")
        self.push(f'return "{self.enum_field_name}"', indent=self.indent + 1)


class BlockEnumMethodStringCaseDefault(BlockBindEnum[F]):
    @override(Block)
    def render(self) -> None:
        self.push("default:")
        self.push(
            f'return "{self.enum_name}(" + strconv.FormatInt(int64(v), 10) + ")"',
            indent=self.indent + 1,
        )


class BlockEnumMethodStringCaseList(BlockBindEnum[F], BlockComposition[F]):
    @override(BlockComposition)
    def blocks(self) -> List[Block[F]]:
        bs: List[Block[F]] = [
            BlockEnumMethodStringCaseItem(field, indent=self.indent)
            for field in self.d.fields()
        ]
        bs.append(BlockEnumMethodStringCaseDefault(self.d, indent=self.indent))
        return bs

    @override(BlockComposition)
    def separator(self) -> str:
        return "\n"


class BlockEnumMethodXXXProcessor(BlockBindEnum[F]):
    @override(Block)
    def render(self) -> None:
        uint = self.formatter.format_processor_uint(self.d.type)
        extensible = self.formatter.format_bool_value(self.d.extensible)
        self.push(f"func (m {self.enum_name}) XXXProcessor() bp.Processor {{")
        self.push(
            f"return bp.NewEnumProcessor({extensible}, {uint})", indent=self.indent + 1
        )
        self.push("}")


class BlockEnumMethodString(BlockBindEnum[F], BlockWrapper[F]):
    @override(BlockWrapper)
    def wraps(self) -> Block:
        return BlockEnumMethodStringCaseList(self.d, indent=1)

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
            BlockEnumMethodXXXProcessor(self.d),
            BlockEnumMethodString(self.d),
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


class BlockMessageSizeConst(BlockBindMessage[F]):
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


class BlockMessageMethodSize(BlockBindMessage[F]):
    @override(Block)
    def render(self) -> None:
        self.push(f"func (m *{self.message_name}) Size() uint32 {{")
        self.push_string(f"return {self.message_nbytes}")
        self.push_string("}")


class BlockMessageMethodXXXProcessorFieldItem(BlockBindMessageField[F]):
    @override(Block)
    def render(self) -> None:
        field_number = self.formatter.format_int_value(self.d.number)
        processor = self.formatter.format_processor(self.d.type)
        self.push(f"bp.NewMessageFieldProcessor({field_number}, {processor}),")


class BlockMessageMethodXXXProcessorFieldList(BlockBindMessage[F], BlockComposition[F]):
    @override(BlockComposition)
    def blocks(self) -> List[Block[F]]:
        return [
            BlockMessageMethodXXXProcessorFieldItem(field, indent=self.indent)
            for field in self.d.sorted_fields()
        ]

    @override(BlockComposition)
    def separator(self) -> str:
        return "\n"


class BlockMessageMethodXXXProcessor(BlockBindMessage[F], BlockWrapper[F]):
    @override(BlockWrapper)
    def wraps(self) -> Block[F]:
        return BlockMessageMethodXXXProcessorFieldList(self.d, indent=self.indent + 2)

    @override(BlockWrapper)
    def before(self) -> None:
        self.push(f"func (m *{self.message_name}) XXXProcessor() bp.Processor {{")
        self.push(
            "fieldDescriptors := []*bp.MessageFieldProcessor{", indent=self.indent + 1
        )

    @override(BlockWrapper)
    def after(self) -> None:
        self.push("}", indent=self.indent + 1)
        self.push(
            "return bp.NewMessageProcessor(fieldDescriptors)", indent=self.indent + 1
        )
        self.push("}")


class BlockMessageMethodXXXGetSetByteItemBase(BlockBindMessageField[F]):
    def __init__(
        self, d: MessageField, name: Optional[str] = None, indent: int = 0,
    ) -> None:
        super().__init__(d, name, indent)
        self.array_depth: int = 0

    def format_data_ref(self) -> str:
        array_indexing = "".join(f"[di.I({i})]" for i in range(self.array_depth))
        return f"m.{self.message_field_name}" + array_indexing

    def render_case(self) -> None:
        field_number = self.formatter.format_int_value(self.d.number)
        self.push(f"case {field_number}:")

    @abstractmethod
    def render_single(self, single: SingleType, alias: Optional[Alias] = None) -> None:
        raise NotImplementedError

    def render_array(self, array: Array) -> None:
        try:
            self.array_depth += 1
            if isinstance(array.element_type, SingleType):
                return self.render_single(array.element_type)
            if isinstance(array.element_type, Alias):
                return self.render_alias(array.element_type)
        finally:
            self.array_depth -= 1

    def render_alias(self, alias: Alias) -> None:
        if isinstance(alias.type, SingleType):
            return self.render_single(alias.type, alias)
        if isinstance(alias.type, Array):
            return self.render_array(alias.type)

    @override(Block)
    def render(self) -> None:
        if isinstance(self.d.type, SingleType):
            return self.render_single(self.d.type)
        if isinstance(self.d.type, Array):
            return self.render_array(self.d.type)
        if isinstance(self.d.type, Alias):
            return self.render_alias(self.d.type)


class BlockMessageMethodXXXSetByteItem(BlockMessageMethodXXXGetSetByteItemBase):
    @override(BlockMessageMethodXXXGetSetByteItemBase)
    def render_single(self, single: SingleType, alias: Optional[Alias] = None) -> None:
        field_number = self.formatter.format_int_value(self.d.number)
        left = self.format_data_ref()
        assign = "|="

        type_name = self.formatter.format_type(single)
        if alias:
            type_name = self.formatter.format_type(alias)

        value = f"{type_name}(b)"
        shift = "<< lshift"

        if isinstance(single, Bool):
            assign = "="
            shift = ""
            value = "bp.Byte2bool(b)"
            if alias:
                value = f"{type_name}({value})"

        self.push(f"case {field_number}:")

        if shift:
            self.push(f"{left} {assign} ({value} {shift})", indent=self.indent + 1)
        else:
            self.push(f"{left} {assign} {value}", indent=self.indent + 1)


class BlockMessageMethodXXXSetByteItemDefault(Block[F]):
    @override(Block)
    def render(self) -> None:
        self.push("default:")
        self.push("return", indent=self.indent + 1)


class BlockMessageMethodXXXSetByteItemList(BlockBindMessage[F], BlockComposition[F]):
    @override(BlockComposition)
    def blocks(self) -> List[Block[F]]:
        b: List[Block[F]] = [
            BlockMessageMethodXXXSetByteItem(field, indent=self.indent)
            for field in self.d.sorted_fields()
        ]
        b.append(BlockMessageMethodXXXSetByteItemDefault(indent=self.indent))
        return b

    @override(BlockComposition)
    def separator(self) -> str:
        return "\n"


class BlockMessageMethodXXXSetByte(BlockBindMessage[F], BlockWrapper[F]):
    @override(BlockWrapper)
    def wraps(self) -> Block[F]:
        return BlockMessageMethodXXXSetByteItemList(self.d, indent=self.indent + 2)

    @override(BlockWrapper)
    def before(self) -> None:
        self.push(
            f"func (m *{self.message_name}) XXXSetByte(di *bp.DataIndexer, lshift int, b byte) {{"
        )
        self.push("switch di.F() {", indent=self.indent + 1)

    @override(BlockWrapper)
    def after(self) -> None:
        self.push("}", indent=self.indent + 1)
        self.push("}")


class BlockMessageMethodXXXGetByteItem(BlockMessageMethodXXXGetSetByteItemBase):
    @override(BlockMessageMethodXXXGetSetByteItemBase)
    def render_single(self, single: SingleType, alias: Optional[Alias] = None) -> None:
        field_number = self.formatter.format_int_value(self.d.number)
        data = self.format_data_ref()
        shift = ">> lshift"

        type_name = self.formatter.format_type(single)
        if alias:
            type_name = self.formatter.format_type(alias)

        value = f"{type_name}({data} {shift})"

        if isinstance(single, Bool):
            value = "bp.Byte2bool(b)"
            if alias:
                value = f"{type_name}({value})"

        self.push(f"case {field_number}:")
        self.push(f"return {value}", indent=self.indent + 1)


class BlockMessageMethodXXXGetByteItemDefault(Block[F]):
    @override(Block)
    def render(self) -> None:
        self.push("default:")
        self.push("return byte(0)", indent=self.indent + 1)


class BlockMessageMethodXXXGetByteItemList(BlockBindMessage[F], BlockComposition[F]):
    @override(BlockComposition)
    def blocks(self) -> List[Block[F]]:
        b: List[Block[F]] = [
            BlockMessageMethodXXXGetByteItem(field, indent=self.indent)
            for field in self.d.sorted_fields()
        ]
        b.append(BlockMessageMethodXXXGetByteItemDefault(indent=self.indent))
        return b

    @override(BlockComposition)
    def separator(self) -> str:
        return "\n"


class BlockMessageMethodXXXGetByte(BlockBindMessage[F], BlockWrapper[F]):
    @override(BlockWrapper)
    def wraps(self) -> Block[F]:
        return BlockMessageMethodXXXGetByteItemList(self.d, indent=self.indent + 2)

    @override(BlockWrapper)
    def before(self) -> None:
        self.push(
            f"func (m *{self.message_name}) XXXGetByte(di *bp.DataIndexer, rshift int) byte {{"
        )
        self.push("switch di.F() {", indent=self.indent + 1)

    @override(BlockWrapper)
    def after(self) -> None:
        self.push("}", indent=self.indent + 1)
        self.push("}")


class BlockMessageMethodString(BlockBindMessage[F]):
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
            BlockMessageStruct(self.d),
            BlockMessageSizeConst(self.d),
            BlockMessageMethodSize(self.d),
            BlockMessageMethodString(self.d),
            BlockMessageMethodXXXProcessor(self.d),
            BlockMessageMethodXXXSetByte(self.d),
            BlockMessageMethodXXXGetByte(self.d),
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
