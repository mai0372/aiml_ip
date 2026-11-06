"""
backend/app/logic
The Logic-Based Contract Compliance Engine.
Pure-Python formal theorem prover implementing:
- Lexer & Recursive-Descent Parser
- 9-step WFF to CNF Converter
- Robinson Unification with Occurs Check
- Resolution Refutation with Procedural Arithmetic Attachment
- Independent Proof Verifier
"""

from backend.app.logic.ast import (
    Term, Variable, Constant, FunctionTerm,
    Predicate, Literal, Clause,
    Formula, Atom, Not, And, Or, Implies, Iff, Forall, Exists
)
from backend.app.logic.lexer import Lexer, Token, TokenType
from backend.app.logic.parser import Parser, parse_fopl
from backend.app.logic.cnf import CNFConverter, CNFStep
from backend.app.logic.unifier import (
    unify_terms, unify_predicates, unify_complementary_literals,
    occurs_check, compose_substitutions, format_substitution
)
from backend.app.logic.resolution import (
    ResolutionProver, ProofResult, ProofStep, ResolutionOutcome
)
from backend.app.logic.proof_checker import (
    IndependentProofChecker, ProofVerificationReport
)

__all__ = [
    "Term", "Variable", "Constant", "FunctionTerm",
    "Predicate", "Literal", "Clause",
    "Formula", "Atom", "Not", "And", "Or", "Implies", "Iff", "Forall", "Exists",
    "Lexer", "Token", "TokenType",
    "Parser", "parse_fopl",
    "CNFConverter", "CNFStep",
    "unify_terms", "unify_predicates", "unify_complementary_literals",
    "occurs_check", "compose_substitutions", "format_substitution",
    "ResolutionProver", "ProofResult", "ProofStep", "ResolutionOutcome",
    "IndependentProofChecker", "ProofVerificationReport"
]

