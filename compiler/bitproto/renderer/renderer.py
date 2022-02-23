"""
bitproto.renderer.renderer
~~~~~~~~~~~~~~~~~~~~~~~~~~

Renderer class base.
"""

import os
from abc import abstractmethod
from typing import Generic, List, Optional

from bitproto._ast import Proto
from bitproto.errors import InternalError, LanguageNotSupportOptimizationMode
from bitproto.renderer.block import Block, BlockRenderContext
from bitproto.renderer.formatter import F, Formatter
from bitproto.utils import final, overridable


class Renderer(Generic[F]):
    """Base renderer class.

    :param proto: The parsed bitproto instance.
    :param outdir: The directory to write files, defaults to the source
       bitproto's file directory, or cwd.
    :param optimization_mode: Whether the optimization_mode is enabled.
    """

    def __init__(
        self,
        proto: Proto,
        outdir: Optional[str] = None,
        optimization_mode: bool = False,
        optimization_mode_filter_messages: Optional[List[str]] = None,
    ) -> None:
        self.proto = proto
        self.outdir = outdir or self.get_outdir_default(proto)
        self.optimization_mode = optimization_mode
        self.check_proto_for_optimization_mode()
        self.optimization_mode_filter_messages = optimization_mode_filter_messages

        self.out_filename = self.get_out_filename()
        self.out_filepath = os.path.join(self.outdir, self.out_filename)

    def get_outdir_default(self, proto: Proto) -> str:
        """Returns outdir default.
        If the given proto is parsed from a file, then use the its directory.
        Otherwise, use current working directory.
        """
        if proto.filepath:  # Parsing from a file.
            return os.path.dirname(os.path.abspath(proto.filepath))
        return os.getcwd()

    def get_out_filename(self) -> str:
        """Returns the output file's name for this renderer."""
        extension = self.file_extension()
        formatter = self.formatter()
        return formatter.format_out_filename(self.proto, extension=extension)

    def render_string(self) -> str:
        """Render current proto to string."""
        formatter = self.formatter()
        block = self.block()
        assert block is not None, InternalError("block() returns None")

        ctx = BlockRenderContext(
            formatter=formatter,
            bound=self.proto,
            optimization_mode_filter_messages=self.optimization_mode_filter_messages,
        )
        block._render_with_ctx(ctx)
        return block._collect()

    def render(self) -> str:
        """Render current proto to file(s).
        Returns the filepath generated.
        """
        content = self.render_string()

        with open(self.out_filepath, "w") as f:
            f.write(content)
        return self.out_filepath

    @final
    def check_proto_for_optimization_mode(self) -> None:
        """Raises if proto contains non-traditional definitions.

        Proto's definitions and types aren't checked whether to be traditional here. The
        parser is enforced to traditional mode to check it during parsing.
        """
        if not self.optimization_mode:
            return
        if not self.support_optimization():
            raise LanguageNotSupportOptimizationMode(lang=self.language_name())

    @abstractmethod
    def language_name(self) -> str:
        """Returns the language name of this renderer."""
        raise NotImplementedError

    @abstractmethod
    def block(self) -> Block[F]:
        """Returns the block to render."""
        raise NotImplementedError

    @abstractmethod
    def file_extension(self) -> str:
        """Returns the file extension to generate.  e.g. ".c" """
        raise NotImplementedError

    @abstractmethod
    def formatter(self) -> F:
        """Returns the formatter of this renderer."""
        raise NotImplementedError

    @overridable
    def support_optimization(self) -> bool:
        """Returns `True` if this render supports optimization mode.
        Defaults to False.
        """
        return False
