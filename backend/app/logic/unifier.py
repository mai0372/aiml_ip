"""
backend/app/logic/unifier.py
Robinson's First-Order Unification Algorithm with Occurs Check and Substitution Composition.
"""

from __future__ import annotations
from typing import Dict, Optional, Any

from backend.app.logic.ast import (
    Term, Variable, Constant, FunctionTerm,
    Predicate, Literal
)


def occurs_check(var: Variable, term: Term, subst: Optional[Dict[str, Term]] = None) -> bool:
    """
    Occurs check: Returns True if 'var' occurs inside 'term' (under current substitution).
    Prevents cyclic infinite terms like x = f(x).
    """
    subst = subst or {}
    if isinstance(term, Variable):
        if term.name == var.name:
            return True
        if term.name in subst:
            return occurs_check(var, subst[term.name], subst)
        return False
    elif isinstance(term, Constant):
        return False
    elif isinstance(term, FunctionTerm):
        return any(occurs_check(var, arg, subst) for arg in term.args)
    return False


def compose_substitutions(theta: Dict[str, Term], sigma: Dict[str, Term]) -> Dict[str, Term]:
    """
    Composes two substitutions theta and sigma (written theta o sigma):
    For each (x -> t) in theta: x -> t.substitute(sigma).
    Plus any (y -> s) in sigma where y is not in theta.
    Trivial identity bindings (x -> x) are eliminated.
    """
    result: Dict[str, Term] = {}
    for var, term in theta.items():
        applied = term.substitute(sigma)
        if not (isinstance(applied, Variable) and applied.name == var):
            result[var] = applied

    for var, term in sigma.items():
        if var not in theta:
            if not (isinstance(term, Variable) and term.name == var):
                result[var] = term

    return result


def unify_terms(term1: Term, term2: Term, subst: Optional[Dict[str, Term]] = None) -> Optional[Dict[str, Term]]:
    """
    Computes the Most General Unifier (MGU) of two terms.
    Returns None if terms cannot be unified.
    """
    if subst is None:
        subst = {}

    t1 = term1.substitute(subst)
    t2 = term2.substitute(subst)

    # Identical terms
    if t1 == t2:
        return subst

    # Variable 1
    if isinstance(t1, Variable):
        return _unify_var(t1, t2, subst)

    # Variable 2
    if isinstance(t2, Variable):
        return _unify_var(t2, t1, subst)

    # Both Constants
    if isinstance(t1, Constant) and isinstance(t2, Constant):
        if t1.name == t2.name:
            return subst
        return None

    # Both Functions
    if isinstance(t1, FunctionTerm) and isinstance(t2, FunctionTerm):
        if t1.name != t2.name or len(t1.args) != len(t2.args):
            return None
        current_subst = dict(subst)
        for a1, a2 in zip(t1.args, t2.args):
            res = unify_terms(a1, a2, current_subst)
            if res is None:
                return None
            current_subst = res
        return current_subst

    return None


def _unify_var(var: Variable, term: Term, subst: Dict[str, Term]) -> Optional[Dict[str, Term]]:
    """Helper to bind a variable to a term with occurs check."""
    if isinstance(term, Variable) and var.name == term.name:
        return subst

    if occurs_check(var, term, subst):
        # Occurs check failed: prevents cyclic binding x = f(x)
        return None

    new_binding = {var.name: term}
    return compose_substitutions(subst, new_binding)


def unify_predicates(p1: Predicate, p2: Predicate, subst: Optional[Dict[str, Term]] = None) -> Optional[Dict[str, Term]]:
    """Unifies two atomic predicates P(t1, ...) and P(s1, ...)."""
    if subst is None:
        subst = {}

    if p1.name != p2.name or len(p1.args) != len(p2.args):
        return None

    current_subst = dict(subst)
    for a1, a2 in zip(p1.args, p2.args):
        res = unify_terms(a1, a2, current_subst)
        if res is None:
            return None
        current_subst = res

    return current_subst


def unify_complementary_literals(l1: Literal, l2: Literal) -> Optional[Dict[str, Term]]:
    """
    Unifies two literals with opposite polarity (e.g. P(...) and ¬P(...)).
    Returns MGU substitution theta if complementary and unifiable, else None.
    """
    if not l1.is_complementary(l2):
        return None
    return unify_predicates(l1.predicate, l2.predicate)


def format_substitution(subst: Optional[Dict[str, Term]]) -> str:
    """Formats substitution dictionary for UI and debug traces."""
    if subst is None:
        return "{}"
    if not subst:
        return "{}"
    items = [f"{var} ↦ {term}" for var, term in sorted(subst.items())]
    return "{" + ", ".join(items) + "}"
