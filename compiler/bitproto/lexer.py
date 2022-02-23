"""
bitproto.lexer
~~~~~~~~~~~~~~

Token lexer for bitproto.
"""

from contextlib import contextmanager
from dataclasses import dataclass
from typing import Dict, Iterator, List, Optional, Tuple

from ply import lex  # type: ignore
from ply.lex import LexToken  # type: ignore

from bitproto._ast import Bool, Byte, Comment, Int, Uint
from bitproto.errors import InvalidEscapingChar, LexerError


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
    literals: str = ":;{}[]()/=\\'."

    # Keywords
    keywords: Tuple[str, ...] = (
        "proto",
        "import",
        "option",
        "type",
        "const",
        "enum",
        "message",
        "typedef",  # Reserved for deprecated warning.
    )
    keywords_tokens = tuple(map(lambda k: k.upper(), keywords))

    # Tokens
    tokens: Tuple[str, ...] = (
        # Misc
        "NEWLINE",
        "COMMENT",
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
        # Indentifer
        "IDENTIFIER",
    ) + keywords_tokens  # Keywords

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

    def __init__(self, filepath_stack: Optional[List[str]] = None) -> None:
        self.lexer = lex.lex(object=self)
        self.filepath_stack: List[str] = filepath_stack or []

    def push_filepath(self, filepath: str) -> None:
        self.filepath_stack.append(filepath)

    def pop_filepath(self) -> str:
        return self.filepath_stack.pop()

    def current_filepath(self) -> str:
        if self.filepath_stack:
            return self.filepath_stack[-1]
        return ""

    @contextmanager
    def maintain_filepath(self, filepath: str) -> Iterator[str]:
        try:
            self.push_filepath(filepath)
            yield filepath
        finally:
            self.pop_filepath()

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
            filepath=self.current_filepath(),
            token=t.value[0],
            lineno=t.lineno,
        )

    def t_newline(self, t: LexToken) -> LexToken:
        r"\n"
        t.lexer.lineno += 1
        t.type = "NEWLINE"
        return t

    def t_COMMENT(self, t: LexToken) -> LexToken:
        r"\/\/[^\n]*"
        t.value = Comment(
            token=t.value, lineno=t.lineno, filepath=self.current_filepath()
        )
        return t

    def t_BOOL_TYPE(self, t: LexToken) -> LexToken:
        r"\bbool\b"
        t.value = Bool(token=t.value, lineno=t.lineno, filepath=self.current_filepath())
        return t

    def t_UINT_TYPE(self, t: LexToken) -> LexToken:
        r"\buint[0-9]+\b"
        cap: int = int(t.value[4:])  # uint{n}
        t.value = Uint(
            cap=cap, token=t.value, lineno=t.lineno, filepath=self.current_filepath()
        )
        return t

    def t_INT_TYPE(self, t: LexToken) -> LexToken:
        r"\bint[0-9]+\b"
        # Why use the regexp `int[0-9]+` instead of `int(8|16|32|64)`?
        # We want the unsupported cases like `int0`, `int3` to raise an error instead of
        # lexing into identifiers.
        cap: int = int(t.value[3:])
        t.value = Int(
            cap=cap, token=t.value, lineno=t.lineno, filepath=self.current_filepath()
        )
        return t

    def t_BYTE_TYPE(self, t: LexToken) -> LexToken:
        r"\bbyte\b"
        t.value = Byte(token=t.value, lineno=t.lineno, filepath=self.current_filepath())
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
        r"[a-zA-Z_][a-zA-Z0-9_]*"
        if t.value in self.keywords:
            # May match keywords.
            t.type = t.value.upper()
            return t
        return t

    def t_STRING_LITERAL(self, t: LexToken) -> LexToken:
        r"\"([^\\\n]|(\\.))*?\" "
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
                        token=t.value,
                        filepath=self.current_filepath(),
                        lineno=t.lexer.lineno,
                    )
            else:
                val += s[i]
            i += 1
        t.value = val
        return t
