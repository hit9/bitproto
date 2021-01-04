"""
bitproto.renderer.renderer
~~~~~~~~~~~~~~~~~~~~~~~~~~

Renderer class base.
"""

import os
from abc import abstractmethod
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
        """Returns the output file's name for this renderer. """
        extension = self.file_extension()
        formatter = self.formatter()
        return formatter.format_out_filename(self.proto, extension=extension)

    def render_string(self) -> str:
        """Render current proto to string."""
        formatter = self.formatter()
        block = self.block()
        block.set_bound(self.proto)
        block.set_formatter(formatter)
        block.render()
        return block.collect()

    def render(self) -> str:
        """Render current proto to file(s).
        Returns the filepath generated.
        """
        content = self.render_string()

        with open(self.out_filepath, "w") as f:
            f.write(content)
        return self.out_filepath

    @abstractmethod
    def block(self) -> Block:
        """Returns the block to render."""
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
