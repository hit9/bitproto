"""
bitproto.lexer
~~~~~~~~~~~~~~

Lexer for bitproto.
"""

from contextlib import contextmanager
from typing import Tuple, Dict, Iterator, Optional

from ply import lex
from ply.lex import LexToken

from bitproto.errors import LexerError, InvalidEscapingChar
from bitproto.ast import Newline, Comment, Bool, Uint, Int, Byte


class Lexer:
    """Lexer for bitproto.

        >>> lexer = Lexer()
        >>> lexer.input("uint3 field")
        >>> lexer.token()
        LexToken(UINT_TYPE, uint3, 1, 0)

    """

    # Ignore whitespaces.
    t_ignore: str = " \t\r"

    # Literal symbols
    literals: str = ":;{}[]()=\\"

    # Reversed keywords
    keywords: Tuple[str, ...] = (
        "proto",
        "import",
        "option",
        "type",
        "const",
        "enum",
        "message",
        "template",
        "render",
    )
    keywords_tokens = tuple(map(lambda keyword: keyword.upper(), keywords))

    # Tokens
    tokens: Tuple[str, ...] = (
        # Misc
        "NEWLINE",
        "COMMENT",
        # Template
        "TEMPLATELINE",
        # Operators
        "PLUS",
        "MINUS",
        "TIMES",
        "DIVIDE",
        # Types
        "BOOL_TYPE",
        "UINT_TYPE",
        "INT_TYPE",
        "BYTE_TYPE",
        # Literals
        "HEX_LITERAL",
        "INT_LITERAL",
        "BOOL_LITERAL",
        "STRING_LITERAL",
        # IDENTIFIER
        "IDENTIFIER",
    ) + keywords_tokens

    # Supported escaping characters in strings.
    escaping_chars: Dict[str, str] = {
        "t": "\t",
        "r": "\r",
        "n": "\n",
        "\\": "\\",
        "'": "'",
        '"': '"',
    }

    # Expression operators.
    t_PLUS: str = r"\+"
    t_MINUS: str = r"-"
    t_TIMES: str = r"\*"
    t_DIVIDE: str = r"/"

    def __init__(self) -> None:
        self.lexer = lex.lex(object=self)
        self.filepath: str = ""

    def set_filepath(self, filepath: str) -> None:
        self.filepath = filepath

    def clear_filepath(self) -> None:
        self.filepath = ""

    @contextmanager
    def maintain_filepath(self, filepath: str) -> Iterator[str]:
        try:
            self.set_filepath(filepath)
            yield self.filepath
        finally:
            self.clear_filepath()

    def token(self) -> Optional[LexToken]:
        """Returns the next token lexed.
        Returns `None` if no token is lexed."""
        return self.lexer.token()

    def input(self, s: str) -> None:
        """Inputs a string to this lexer."""
        self.lexer.input(s)

    def t_error(self, t: LexToken) -> None:
        raise LexerError(
            message="Invalid token",
            filepath=self.filepath,
            token=t.value[0],
            lineno=t.lexer.lineno,
        )

    def t_newline(self, t: LexToken) -> LexToken:
        r"\n"
        t.lexer.lineno += 1
        t.type = "NEWLINE"
        t.value = Newline(token=t.value, lineno=t.lineno, filepath=self.filepath)
        return t

    def t_COMMENT(self, t: LexToken) -> LexToken:
        r"\/\/[^\n]*"
        t.value = Comment(token=t.value, lineno=t.lineno, filepath=self.filepath)
        return t

    def t_TEMPLATELINE(self, t: LexToken) -> LexToken:
        r"\\[^\n]*"
        t.value = t.value[1:]
        return t

    def t_BOOL_TYPE(self, t: LexToken) -> LexToken:
        r"\bbool\b"
        t.value = Bool(token=t.value, lineno=t.lineno, filepath=self.filepath)
        return t

    def t_UINT_TYPE(self, t: LexToken) -> LexToken:
        r"\buint[0-9]+\b"
        cap: int = int(t.value[4:])  # uint{n}
        t.value = Uint(cap=cap, token=t.value, lineno=t.lineno, filepath=self.filepath,)
        return t

    def t_INT_TYPE(self, t: LexToken) -> LexToken:
        r"\bint[0-9]+\b"
        # Why use the regexp `int[0-9]+` instead of `int(8|16|32|64)`?
        # We want the unsupported cases like `int0`, `int3` to raise an error instead of
        # lexing into identifiers.
        cap: int = int(t.value[3:])
        t.value = Int(cap=cap, token=t.value, lineno=t.lineno, filepath=self.filepath,)
        return t

    def t_BYTE_TYPE(self, t: LexToken) -> LexToken:
        r"\bbyte\b"
        t.value = Byte(token=t.value, lineno=t.lineno, filepath=self.filepath)
        return t

    def t_HEX_LITERAL(self, t: LexToken) -> LexToken:
        r"0x[0-9a-fA-F]+"
        t.value = int(t.value, 16)
        return t

    def t_INT_LITERAL(self, t: LexToken) -> LexToken:
        r"[0-9]+"
        # NOTE: Currently only non-negative integers are supported.
        # FIXME Negative integers?
        t.value = int(t.value)
        return t

    def t_BOOL_LITERAL(self, t: LexToken) -> LexToken:
        r"\b(true|false|yes|no)\b"
        t.value = t.value in ("true", "yes")
        return t

    def t_IDENTIFIER(self, t: LexToken) -> LexToken:
        r"\b[a-zA-Z_](\.[a-zA-Z_0-9])*\b"
        # This rule may match a keyword.
        if t.value in Lexer.keywords:
            # Converts the matched token to the keyword type
            t.type = t.value.upper()
            return t
        return t

    def t_STRING_LITERAL(self, t: LexToken) -> LexToken:
        r"\"([^\\\n]|(\\.))*?\""
        s: str = t.value[1:-1]

        # Escaping.
        i: int = 0
        val: str = ""
        while i < len(s):
            if s[i] == "\\":  # A single slash '\'
                i += 1
                if s[i] in Lexer.escaping_chars:
                    val += Lexer.escaping_chars[s[i]]
                else:
                    raise InvalidEscapingChar(
                        token=t.value, filepath=self.filepath, lineno=t.lexer.lineno
                    )
            else:
                val += s[i]
            i += 1
        t.value = val
        return t
