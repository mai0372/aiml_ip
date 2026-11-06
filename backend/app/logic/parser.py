"""
backend/app/logic/parser.py
Recursive-descent parser for First-Order Predicate Logic (FOPL) Well-Formed Formulas.
Produces strongly typed AST nodes and records exact error coordinates.
"""

from __future__ import annotations
from typing import List, Optional, Set

from backend.app.logic.ast import (
    Term, Variable, Constant, FunctionTerm,
    Predicate, Formula, Atom, Not, And, Or,
    Implies, Iff, Forall, Exists
)
from backend.app.logic.lexer import Lexer, Token, TokenType, LexerError


class ParserError(Exception):
    def __init__(self, message: str, line: int, col: int):
        self.message = message
        self.line = line
        self.col = col
        super().__init__(f"Parser error at line {line}, col {col}: {message}")


class Parser:
    """Parses a token stream into an AST Formula."""
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0
        self.bound_variables: Set[str] = set()
        # Known constants that should always be Constant even if lowercase
        self.known_constants = {"tenant", "landlord", "both", "none", "premises", "notice"}

    def _current(self) -> Token:
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return self.tokens[-1]

    def _peek_type(self, offset: int = 0) -> TokenType:
        idx = self.pos + offset
        if idx < len(self.tokens):
            return self.tokens[idx].type
        return TokenType.EOF

    def _match(self, token_type: TokenType) -> bool:
        if self._current().type == token_type:
            self.pos += 1
            return True
        return False

    def _expect(self, token_type: TokenType, err_msg: str) -> Token:
        curr = self._current()
        if curr.type == token_type:
            self.pos += 1
            return curr
        raise ParserError(
            f"Expected {err_msg}, found '{curr.value}' ({curr.type.name})",
            curr.line,
            curr.col
        )

    def parse(self) -> Formula:
        formula = self.parse_formula()
        if self._current().type != TokenType.EOF:
            curr = self._current()
            raise ParserError(f"Unexpected token after complete formula: '{curr.value}'", curr.line, curr.col)
        return formula

    def parse_formula(self) -> Formula:
        """Formula -> Quantified | Iff"""
        curr = self._current()
        if curr.type in (TokenType.FORALL, TokenType.EXISTS):
            is_forall = (curr.type == TokenType.FORALL)
            self.pos += 1

            # Read comma-separated variables: forall x, y:
            var_tokens: List[Token] = []
            var_token = self._expect(TokenType.IDENTIFIER, "variable name after quantifier")
            var_tokens.append(var_token)

            while self._match(TokenType.COMMA):
                next_var = self._expect(TokenType.IDENTIFIER, "variable name after comma")
                var_tokens.append(next_var)

            self._expect(TokenType.COLON, "':' or '.' after quantifier variables")

            # Add to bound variables
            var_names = [vt.value for vt in var_tokens]
            for vn in var_names:
                self.bound_variables.add(vn)

            try:
                body = self.parse_formula()
            finally:
                for vn in var_names:
                    self.bound_variables.discard(vn)

            # Build nested Forall/Exists nodes from right to left
            result = body
            for vn in reversed(var_names):
                result = Forall(vn, result) if is_forall else Exists(vn, result)
            return result

        return self.parse_iff()

    def parse_iff(self) -> Formula:
        """Iff -> Implies ('<->' Implies)*"""
        left = self.parse_implies()
        while self._match(TokenType.IFF):
            right = self.parse_implies()
            left = Iff(left, right)
        return left

    def parse_implies(self) -> Formula:
        """Implies -> Or ('->' Implies)? (right-associative)"""
        left = self.parse_or()
        if self._match(TokenType.IMPLIES):
            right = self.parse_implies()
            return Implies(left, right)
        return left

    def parse_or(self) -> Formula:
        """Or -> And ('v' And)*"""
        left = self.parse_and()
        while self._match(TokenType.OR):
            right = self.parse_and()
            left = Or(left, right)
        return left

    def parse_and(self) -> Formula:
        """And -> Unary ('^' Unary)*"""
        left = self.parse_unary()
        while self._match(TokenType.AND):
            right = self.parse_unary()
            left = And(left, right)
        return left

    def parse_unary(self) -> Formula:
        """Unary -> ('~' Unary) | Primary"""
        if self._match(TokenType.NOT):
            return Not(self.parse_unary())
        return self.parse_primary()

    def parse_primary(self) -> Formula:
        """Primary -> '(' Formula ')' | Predicate"""
        if self._match(TokenType.LPAREN):
            formula = self.parse_formula()
            self._expect(TokenType.RPAREN, "')' to close parentheses")
            return formula

        curr = self._current()
        if curr.type == TokenType.IDENTIFIER:
            pred_name = curr.value
            self.pos += 1
            args: List[Term] = []
            if self._match(TokenType.LPAREN):
                if not self._match(TokenType.RPAREN):
                    args.append(self.parse_term())
                    while self._match(TokenType.COMMA):
                        args.append(self.parse_term())
                    self._expect(TokenType.RPAREN, "')' after predicate arguments")
            return Atom(Predicate(pred_name, args))

        raise ParserError(f"Expected formula or predicate, found '{curr.value}'", curr.line, curr.col)

    def parse_term(self) -> Term:
        """Parses a Term: Variable, Number Constant, Named Constant, or FunctionTerm."""
        curr = self._current()

        # Numeric constant
        if curr.type == TokenType.NUMBER:
            self.pos += 1
            try:
                val = float(curr.value)
            except ValueError:
                val = 0.0
            return Constant(curr.value, is_numeric=True, numeric_value=val)

        # Identifier: could be FunctionTerm, Variable, or Constant
        if curr.type == TokenType.IDENTIFIER:
            name = curr.value
            self.pos += 1

            # Function term: Name(t1, t2, ...)
            if self._match(TokenType.LPAREN):
                args: List[Term] = []
                if not self._match(TokenType.RPAREN):
                    args.append(self.parse_term())
                    while self._match(TokenType.COMMA):
                        args.append(self.parse_term())
                    self._expect(TokenType.RPAREN, "')' after function arguments")
                return FunctionTerm(name, args)

            # Check if this identifier is in bound variable scope
            if name in self.bound_variables:
                return Variable(name)

            # Check standard variable conventions:
            # lowercase single character or names like x, y, z, n, p, party, or starting with '_'
            if name in self.known_constants:
                return Constant(name, is_numeric=False)

            if len(name) == 1 and name.islower():
                return Variable(name)
            if name.startswith("var_") or name.startswith("_"):
                return Variable(name)
            if name in {"x", "y", "z", "n", "m", "p", "q", "days", "amount"}:
                return Variable(name)

            # Otherwise, treat as Constant
            return Constant(name, is_numeric=False)

        raise ParserError(f"Expected term, found '{curr.value}' ({curr.type.name})", curr.line, curr.col)


def parse_fopl(text: str) -> Formula:
    """Helper function to parse a raw string into a Formula AST."""
    tokens = Lexer(text).tokenize()
    return Parser(tokens).parse()

