"""
bitproto.renderer.renderer
~~~~~~~~~~~~~~~~~~~~~~~~~~

Renderer class base.
"""

from abc import abstractmethod
import os
from typing import List, Optional

from bitproto._ast import Proto
from bitproto.renderer.block import Block
from bitproto.renderer.formatter import Formatter


class Renderer:
    """Base renderer class.

    :param proto: The parsed bitproto instance.
    :param outdir: The directory to write files, defaults to the source
       bitproto's file directory, or cwd.
    """

    def __init__(self, proto: Proto, outdir: Optional[str] = None) -> None:
        self.proto = proto
        self.outdir = outdir or self.get_outdir_default(proto)

        self.out_filename = self.format_out_filename()
        self.out_filepath = os.path.join(self.outdir, self.out_filename)

    def get_outdir_default(self, proto: Proto) -> str:
        """Returns outdir default.
        If the given proto is parsed from a file, then use the its directory.
        Otherwise, use current working directory.
        """
        if proto.filepath:  # Parsing from a file.
            return os.path.dirname(os.path.abspath(proto.filepath))
        return os.getcwd()

    def format_out_filename(self, extension: Optional[str] = None) -> str:
        """Returns the output file's name for given extension.

            >>> format_out_filepath(".go")
            example_bp.go
        """
        out_base_name = self.proto.name
        extension = extension or self.file_extension()
        if self.proto.filepath:
            proto_base_name = os.path.basename(self.proto.filepath)
            out_base_name = os.path.splitext(proto_base_name)[0]  # remove extension
        out_filename = out_base_name + "_bp" + extension
        return out_filename

    def render_string(self) -> str:
        """Render current proto to string."""
        blocks = self.blocks()
        strings = []
        formatter = self.formatter()

        # Sets formatter
        for block in blocks:
            block.set_formatter(formatter)

        # Executes `render()`.
        for block in blocks:
            block.render()
            strings.append(block.collect())

        # Executes `defer()`.
        reversed_blocks = blocks[::-1]
        for block in reversed_blocks:
            try:
                block.defer()
                strings.append(block.collect())
            except NotImplementedError:
                pass
        return "\n\n".join(strings)

    def render(self) -> str:
        """Render current proto to file(s).
        Returns the filepath generated.
        """
        content = self.render_string()

        with open(self.out_filepath, "w") as f:
            f.write(content)
        return self.out_filepath

    @abstractmethod
    def blocks(self) -> List[Block]:
        """Returns the block list to render."""
        raise NotImplementedError

    @abstractmethod
    def file_extension(self) -> str:
        """Returns the file extension to generate.  e.g. ".c"
        """
        raise NotImplementedError

    @abstractmethod
    def formatter(self) -> Formatter:
        """Returns the formatter of this renderer."""
        raise NotImplementedError
