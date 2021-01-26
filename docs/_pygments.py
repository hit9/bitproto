import re

from pygments.lexer import RegexLexer, words
from pygments.lexers._mapping import LEXERS
from pygments.style import Style
from pygments.token import (Comment, Keyword, Name, Number, Operator,
                            Punctuation, String, Text)

__all__ = ["BitprotoLexer"]


class BitprotoLexer(RegexLexer):
    name = "Bitproto"
    filenames = ["*.bitproto"]
    mimetypes = ["text/x-bitproto"]
    aliases = ["bitproto"]

    flags = re.MULTILINE | re.UNICODE

    tokens = {
        "root": [
            (r"\n", Text),
            (r"\s+", Text),
            (r"//(.*?)\n", Comment.Single),
            (r"(import|proto)\b", Keyword.Namespace),
            (r"(message|enum|type|const|option)\b", Keyword.Declaration),
            (r"(true|false|yes|no)\b", Keyword.Constant),
            (
                words(
                    ("int", "int8", "int16", "int32", "int64", "byte", "bool"),
                    suffix=r"\b",
                ),
                Keyword.Type,
            ),
            (r"(uint[0-9]+)\b", Keyword.Type),
            (r"0[xX][0-9a-fA-F]+", Number),
            (r"[0-9]+", Number),
            (r"\"([^\\\n]|(\\.))*?\"", String),
            (r"[a-zA-Z_][a-zA-Z0-9_]*", Name.Entity),
            (r"[+\-*/]", Operator),
            (r"[:;{}\[\]()=\\'.]", Punctuation),
        ]
    }


LEXERS["Bitproto"] = ("_pygments", "Bitproto", ("bitproto",), ("*.bitproto"), ())


class BitprotoStyle(Style):
    default_style = "bw"
    background_color = "#f5f5f5"
    styles = {
        Comment: "italic #999999",
        Comment.Preproc: "noitalic #333333",
        Comment.PreprocFile: "noitalic #333333",
        Keyword: "bold",
        Keyword.Namespace: "bold #364f6b",
        Keyword.Declaration: "bold #364f6b",
        Keyword.Type: "#fc5185",
        Keyword.Constant: "bold #364f6b",
        Number: "#333333",
        String: "#48466d",
        Name.Entity: "bold #4D5656",
    }
