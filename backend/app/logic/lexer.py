"""
backend/app/logic/lexer.py
Lexical analyzer for First-Order Predicate Logic (FOPL) Well-Formed Formulas.
Tracks line and column numbers to provide exact error positions.
"""

from __future__ import annotations
from enum import Enum, auto
from typing import List, Optional


class TokenType(Enum):
    FORALL = auto()        # forall, ∀
    EXISTS = auto()        # exists, ∃
    NOT = auto()           # ~, ¬, not, !
    AND = auto()           # &, ^, ∧, and
    OR = auto()            # |, v, ∨, or
    IMPLIES = auto()       # ->, =>, →, implies
    IFF = auto()           # <->, <=>, ↔, iff
    LPAREN = auto()        # (
    RPAREN = auto()        # )
    COMMA = auto()         # ,
    COLON = auto()         # :, .
    IDENTIFIER = auto()    # e.g. Perm, tenant, Terminate, x
    NUMBER = auto()        # e.g. 30, 90, 2.5
    EOF = auto()           # End of file


class Token:
    def __init__(self, token_type: TokenType, value: str, line: int, col: int):
        self.type = token_type
        self.value = value
        self.line = line
        self.col = col

    def __repr__(self) -> str:
        return f"Token({self.type.name}, '{self.value}', L{self.line}:C{self.col})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Token):
            return False
        return (
            self.type == other.type
            and self.value == other.value
            and self.line == other.line
            and self.col == other.col
        )


class LexerError(Exception):
    def __init__(self, message: str, line: int, col: int):
        self.message = message
        self.line = line
        self.col = col
        super().__init__(f"Lexer error at line {line}, col {col}: {message}")


class Lexer:
    """Tokenizes FOPL formula strings with position tracking."""
    def __init__(self, text: str):
        self.text = text
        self.pos = 0
        self.line = 1
        self.col = 1
        self.length = len(text)

    def _peek(self, offset: int = 0) -> Optional[str]:
        idx = self.pos + offset
        if idx < self.length:
            return self.text[idx]
        return None

    def _advance(self) -> Optional[str]:
        ch = self._peek()
        if ch is not None:
            self.pos += 1
            if ch == '\n':
                self.line += 1
                self.col = 1
            else:
                self.col += 1
        return ch

    def tokenize(self) -> List[Token]:
        tokens: List[Token] = []

        while self.pos < self.length:
            ch = self._peek()

            # Skip whitespace
            if ch in (' ', '\t', '\r', '\n'):
                self._advance()
                continue

            start_line = self.line
            start_col = self.col

            # Two or three-character operators
            # Biconditional: <-> or <=>
            if ch == '<':
                if self._peek(1) in ('-', '=') and self._peek(2) == '>':
                    op = ch + self.text[self.pos + 1 : self.pos + 3]
                    self._advance()
                    self._advance()
                    self._advance()
                    tokens.append(Token(TokenType.IFF, op, start_line, start_col))
                    continue

            # Implication: -> or =>
            if (ch == '-' and self._peek(1) == '>') or (ch == '=' and self._peek(1) == '>'):
                op = ch + self.text[self.pos + 1]
                self._advance()
                self._advance()
                tokens.append(Token(TokenType.IMPLIES, op, start_line, start_col))
                continue

            # Unicode connectives
            if ch == '↔':
                self._advance()
                tokens.append(Token(TokenType.IFF, ch, start_line, start_col))
                continue
            if ch == '→':
                self._advance()
                tokens.append(Token(TokenType.IMPLIES, ch, start_line, start_col))
                continue
            if ch in ('¬', '~', '!'):
                self._advance()
                tokens.append(Token(TokenType.NOT, ch, start_line, start_col))
                continue
            if ch in ('∧', '&', '^'):
                self._advance()
                tokens.append(Token(TokenType.AND, ch, start_line, start_col))
                continue
            if ch in ('∨', '|'):
                self._advance()
                tokens.append(Token(TokenType.OR, ch, start_line, start_col))
                continue
            if ch == '∀':
                self._advance()
                tokens.append(Token(TokenType.FORALL, ch, start_line, start_col))
                continue
            if ch == '∃':
                self._advance()
                tokens.append(Token(TokenType.EXISTS, ch, start_line, start_col))
                continue

            # Punctuation
            if ch == '(':
                self._advance()
                tokens.append(Token(TokenType.LPAREN, '(', start_line, start_col))
                continue
            if ch == ')':
                self._advance()
                tokens.append(Token(TokenType.RPAREN, ')', start_line, start_col))
                continue
            if ch == ',':
                self._advance()
                tokens.append(Token(TokenType.COMMA, ',', start_line, start_col))
                continue
            if ch in (':', '.'):
                self._advance()
                tokens.append(Token(TokenType.COLON, ch, start_line, start_col))
                continue

            # Numbers (e.g. 30, 90, 2.5)
            if ch.isdigit():
                num_str = ""
                has_dot = False
                while self._peek() is not None and (self._peek().isdigit() or (self._peek() == '.' and not has_dot and self._peek(1) and self._peek(1).isdigit())):
                    curr = self._advance()
                    if curr == '.':
                        has_dot = True
                    num_str += curr
                tokens.append(Token(TokenType.NUMBER, num_str, start_line, start_col))
                continue

            # Identifiers and keywords (e.g. forall, exists, not, and, or, implies, iff, Perm, etc.)
            if ch.isalpha() or ch == '_':
                ident_str = ""
                while self._peek() is not None and (self._peek().isalnum() or self._peek() == '_'):
                    ident_str += self._advance()

                lower_ident = ident_str.lower()
                if lower_ident == "forall":
                    tokens.append(Token(TokenType.FORALL, ident_str, start_line, start_col))
                elif lower_ident == "exists":
                    tokens.append(Token(TokenType.EXISTS, ident_str, start_line, start_col))
                elif lower_ident == "not":
                    tokens.append(Token(TokenType.NOT, ident_str, start_line, start_col))
                elif lower_ident == "and":
                    tokens.append(Token(TokenType.AND, ident_str, start_line, start_col))
                elif lower_ident == "or" or ident_str == "v":
                    tokens.append(Token(TokenType.OR, ident_str, start_line, start_col))
                elif lower_ident == "implies":
                    tokens.append(Token(TokenType.IMPLIES, ident_str, start_line, start_col))
                elif lower_ident == "iff":
                    tokens.append(Token(TokenType.IFF, ident_str, start_line, start_col))
                else:
                    tokens.append(Token(TokenType.IDENTIFIER, ident_str, start_line, start_col))
                continue

            # Unrecognized character
            raise LexerError(f"Unexpected character '{ch}'", self.line, self.col)

        tokens.append(Token(TokenType.EOF, "", self.line, self.col))
        return tokens
