"""
backend/app/logic/ast.py
First-Order Predicate Logic (FOPL) Abstract Syntax Tree (AST).
Provides classes for Terms (Variables, Constants, Functions), Predicates,
Literals, Clauses, and WFF Formulas.
"""

from __future__ import annotations
from typing import List, Dict, Optional, Any, Set, Tuple
import copy


# ============================================================================
# TERMS
# ============================================================================

class Term:
    """Base class for all FOPL terms."""
    def substitute(self, subst: Dict[str, Term]) -> Term:
        raise NotImplementedError

    def get_variables(self) -> Set[str]:
        raise NotImplementedError

    def term_depth(self) -> int:
        return 1

    def to_dict(self) -> Dict[str, Any]:
        raise NotImplementedError


class Variable(Term):
    """A first-order logic variable, e.g. x, y, n, party."""
    def __init__(self, name: str):
        self.name = str(name).strip()

    def substitute(self, subst: Dict[str, Term]) -> Term:
        if self.name in subst:
            val = subst[self.name]
            if isinstance(val, Variable) and val.name == self.name:
                return self
            rest = {k: v for k, v in subst.items() if k != self.name}
            return val.substitute(rest)
        return self

    def get_variables(self) -> Set[str]:
        return {self.name}

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"Var({self.name})"

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, Variable) and self.name == other.name

    def __hash__(self) -> int:
        return hash(("Variable", self.name))

    def to_dict(self) -> Dict[str, Any]:
        return {"type": "variable", "name": self.name}


class Constant(Term):
    """A named constant or ground numeric constant, e.g. tenant, landlord, 30, 90."""
    def __init__(self, name: str, is_numeric: Optional[bool] = None, numeric_value: Optional[float] = None):
        self.name = str(name).strip()
        # Automatically detect numeric constants
        if is_numeric is None:
            try:
                val = float(self.name)
                self.is_numeric = True
                self.numeric_value = val
            except ValueError:
                self.is_numeric = False
                self.numeric_value = None
        else:
            self.is_numeric = is_numeric
            self.numeric_value = numeric_value

    def substitute(self, subst: Dict[str, Term]) -> Term:
        return self

    def get_variables(self) -> Set[str]:
        return set()

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"Const({self.name})"

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, Constant) and self.name == other.name

    def __hash__(self) -> int:
        return hash(("Constant", self.name))

    def to_dict(self) -> Dict[str, Any]:
        d = {"type": "constant", "name": self.name}
        if self.is_numeric:
            d["numeric"] = True
            d["value"] = self.numeric_value
        return d


class FunctionTerm(Term):
    """A function term f(t1, t2, ...), e.g. Terminate(30), skolem_1(x)."""
    def __init__(self, name: str, args: List[Term]):
        self.name = str(name).strip()
        self.args = list(args)

    def substitute(self, subst: Dict[str, Term]) -> Term:
        return FunctionTerm(self.name, [arg.substitute(subst) for arg in self.args])

    def get_variables(self) -> Set[str]:
        vars_set: Set[str] = set()
        for arg in self.args:
            vars_set.update(arg.get_variables())
        return vars_set

    def term_depth(self) -> int:
        if not self.args:
            return 1
        return 1 + max(arg.term_depth() for arg in self.args)

    def __str__(self) -> str:
        args_str = ", ".join(str(a) for a in self.args)
        return f"{self.name}({args_str})"

    def __repr__(self) -> str:
        return f"Func({self.name}, {self.args})"

    def __eq__(self, other: Any) -> bool:
        return (
            isinstance(other, FunctionTerm)
            and self.name == other.name
            and len(self.args) == len(other.args)
            and all(a1 == a2 for a1, a2 in zip(self.args, other.args))
        )

    def __hash__(self) -> int:
        return hash(("FunctionTerm", self.name, tuple(self.args)))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "name": self.name,
            "args": [a.to_dict() for a in self.args]
        }


# ============================================================================
# PREDICATES & LITERALS
# ============================================================================

class Predicate:
    """An n-ary relation Pred(t1, t2, ...), e.g. Perm(tenant, Terminate(30))."""
    def __init__(self, name: str, args: List[Term]):
        self.name = str(name).strip()
        self.args = list(args)

    def substitute(self, subst: Dict[str, Term]) -> Predicate:
        return Predicate(self.name, [a.substitute(subst) for a in self.args])

    def get_variables(self) -> Set[str]:
        vars_set: Set[str] = set()
        for arg in self.args:
            vars_set.update(arg.get_variables())
        return vars_set

    def is_ground(self) -> bool:
        return len(self.get_variables()) == 0

    def is_arithmetic(self) -> bool:
        return self.name in {"LessThan", "GreaterThan", "Equals", "NotEquals", "LessOrEqual", "GreaterOrEqual"}

    def evaluate_arithmetic(self) -> Optional[bool]:
        """
        Procedural arithmetic attachment:
        Evaluates comparison predicates if arguments are ground numeric constants.
        Returns True/False if evaluable, or None if non-ground or non-numeric.
        """
        if not self.is_arithmetic() or len(self.args) != 2:
            return None
        arg1, arg2 = self.args[0], self.args[1]
        if not (isinstance(arg1, Constant) and isinstance(arg2, Constant)):
            return None
        if not (arg1.is_numeric and arg2.is_numeric):
            return None
        
        v1, v2 = arg1.numeric_value, arg2.numeric_value
        if v1 is None or v2 is None:
            return None

        if self.name == "LessThan":
            return v1 < v2
        elif self.name == "GreaterThan":
            return v1 > v2
        elif self.name == "Equals":
            return v1 == v2
        elif self.name == "NotEquals":
            return v1 != v2
        elif self.name == "LessOrEqual":
            return v1 <= v2
        elif self.name == "GreaterOrEqual":
            return v1 >= v2
        return None

    def __str__(self) -> str:
        args_str = ", ".join(str(a) for a in self.args)
        return f"{self.name}({args_str})"

    def __repr__(self) -> str:
        return f"Pred({self.name}, {self.args})"

    def __eq__(self, other: Any) -> bool:
        return (
            isinstance(other, Predicate)
            and self.name == other.name
            and len(self.args) == len(other.args)
            and all(a1 == a2 for a1, a2 in zip(self.args, other.args))
        )

    def __hash__(self) -> int:
        return hash(("Predicate", self.name, tuple(self.args)))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "args": [a.to_dict() for a in self.args]
        }


class Literal:
    """A positive or negated predicate literal, e.g. ~Perm(tenant, Terminate(30))."""
    def __init__(self, predicate: Predicate, is_negated: bool = False):
        self.predicate = predicate
        self.is_negated = is_negated

    def negate(self) -> Literal:
        return Literal(self.predicate, not self.is_negated)

    def substitute(self, subst: Dict[str, Term]) -> Literal:
        return Literal(self.predicate.substitute(subst), self.is_negated)

    def is_complementary(self, other: Literal) -> bool:
        """Checks if two literals have opposing polarity."""
        return self.is_negated != other.is_negated

    def evaluate_ground_truth(self) -> Optional[bool]:
        """
        Evaluates literal truth if underlying predicate has procedural attachment.
        Returns:
          True: Literal evaluates to true (making containing clause a tautology)
          False: Literal evaluates to false (can be dropped from disjunctive clause)
          None: Cannot evaluate (e.g. non-arithmetic or non-ground)
        """
        pred_val = self.predicate.evaluate_arithmetic()
        if pred_val is None:
            return None
        return (not pred_val) if self.is_negated else pred_val

    def __str__(self) -> str:
        prefix = "¬" if self.is_negated else ""
        return f"{prefix}{self.predicate}"

    def __repr__(self) -> str:
        return f"Lit({self})"

    def __eq__(self, other: Any) -> bool:
        return (
            isinstance(other, Literal)
            and self.is_negated == other.is_negated
            and self.predicate == other.predicate
        )

    def __hash__(self) -> int:
        return hash(("Literal", self.is_negated, self.predicate))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "predicate": self.predicate.to_dict(),
            "is_negated": self.is_negated,
            "display": str(self)
        }


# ============================================================================
# CLAUSES
# ============================================================================

class Clause:
    """
    A disjunction of literals: L1 v L2 v ... v Lk.
    An empty literal list represents the empty clause [] (contradiction).
    """
    def __init__(
        self,
        literals: List[Literal],
        clause_id: Optional[str] = None,
        source_id: Optional[str] = None,
        source_type: str = "derived",  # "contract", "axiom", "rule", "goal", "derived"
        provenance_sources: Optional[Set[str]] = None
    ):
        self.literals = list(literals)
        self.clause_id = clause_id or ""
        self.source_id = source_id or ""
        self.source_type = source_type
        # Set of origin source_ids that contributed to this clause
        if provenance_sources is not None:
            self.provenance_sources = set(provenance_sources)
        elif source_id:
            self.provenance_sources = {source_id}
        else:
            self.provenance_sources = set()

    def is_empty(self) -> bool:
        return len(self.literals) == 0

    def is_unit(self) -> bool:
        return len(self.literals) == 1

    def get_variables(self) -> Set[str]:
        vars_set: Set[str] = set()
        for lit in self.literals:
            vars_set.update(lit.predicate.get_variables())
        return vars_set

    def substitute(self, subst: Dict[str, Term]) -> Clause:
        new_lits = [lit.substitute(subst) for lit in self.literals]
        return Clause(
            literals=new_lits,
            clause_id=self.clause_id,
            source_id=self.source_id,
            source_type=self.source_type,
            provenance_sources=self.provenance_sources
        )

    def standardize_variables(self, suffix: str) -> Clause:
        """Renames all variables in this clause with a unique suffix, e.g. x -> x_p1."""
        vars_in_clause = self.get_variables()
        subst: Dict[str, Term] = {v: Variable(f"{v}_{suffix}") for v in vars_in_clause}
        return Clause(
            literals=[lit.substitute(subst) for lit in self.literals],
            clause_id=self.clause_id,
            source_id=self.source_id,
            source_type=self.source_type,
            provenance_sources=self.provenance_sources
        )

    def simplify_arithmetic(self) -> Optional[Clause]:
        """
        Simplifies ground arithmetic literals:
        - If any literal is True, the entire clause is a tautology (return None).
        - If any literal is False, it is dropped from the disjunction.
        - If all literals were False, returns empty clause Clause([]).
        """
        remaining_lits: List[Literal] = []
        for lit in self.literals:
            val = lit.evaluate_ground_truth()
            if val is True:
                # Disjunction containing True is trivially True
                return None
            elif val is False:
                # Disjunction literal is False, can be removed
                continue
            else:
                remaining_lits.append(lit)
        
        # Deduplicate literals
        deduped: List[Literal] = []
        for lit in remaining_lits:
            if lit not in deduped:
                deduped.append(lit)

        return Clause(
            literals=deduped,
            clause_id=self.clause_id,
            source_id=self.source_id,
            source_type=self.source_type,
            provenance_sources=self.provenance_sources
        )

    def __str__(self) -> str:
        if self.is_empty():
            return "[]"
        return " ∨ ".join(str(lit) for lit in self.literals)

    def __repr__(self) -> str:
        return f"Clause({self})"

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Clause):
            return False
        if len(self.literals) != len(other.literals):
            return False
        # Set comparison of literals
        return set(self.literals) == set(other.literals)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "clause_id": self.clause_id,
            "source_id": self.source_id,
            "source_type": self.source_type,
            "display": str(self),
            "literals": [lit.to_dict() for lit in self.literals],
            "provenance_sources": sorted(list(self.provenance_sources))
        }


# ============================================================================
# WELL-FORMED FORMULAS (WFF)
# ============================================================================

class Formula:
    """Base class for First-Order Logic Well-Formed Formulas."""
    def to_dict(self) -> Dict[str, Any]:
        raise NotImplementedError

    def get_free_variables(self, bound: Optional[Set[str]] = None) -> Set[str]:
        raise NotImplementedError


class Atom(Formula):
    """An atomic formula P(t1, ...)."""
    def __init__(self, predicate: Predicate):
        self.predicate = predicate

    def get_free_variables(self, bound: Optional[Set[str]] = None) -> Set[str]:
        bound = bound or set()
        return self.predicate.get_variables() - bound

    def __str__(self) -> str:
        return str(self.predicate)

    def __repr__(self) -> str:
        return f"Atom({self.predicate})"

    def to_dict(self) -> Dict[str, Any]:
        return {"type": "atom", "predicate": self.predicate.to_dict()}


class Not(Formula):
    """¬ body"""
    def __init__(self, body: Formula):
        self.body = body

    def get_free_variables(self, bound: Optional[Set[str]] = None) -> Set[str]:
        return self.body.get_free_variables(bound)

    def __str__(self) -> str:
        return f"¬({self.body})"

    def __repr__(self) -> str:
        return f"Not({self.body})"

    def to_dict(self) -> Dict[str, Any]:
        return {"type": "not", "body": self.body.to_dict()}


class And(Formula):
    """left ∧ right"""
    def __init__(self, left: Formula, right: Formula):
        self.left = left
        self.right = right

    def get_free_variables(self, bound: Optional[Set[str]] = None) -> Set[str]:
        return self.left.get_free_variables(bound) | self.right.get_free_variables(bound)

    def __str__(self) -> str:
        return f"({self.left} ∧ {self.right})"

    def __repr__(self) -> str:
        return f"And({self.left}, {self.right})"

    def to_dict(self) -> Dict[str, Any]:
        return {"type": "and", "left": self.left.to_dict(), "right": self.right.to_dict()}


class Or(Formula):
    """left ∨ right"""
    def __init__(self, left: Formula, right: Formula):
        self.left = left
        self.right = right

    def get_free_variables(self, bound: Optional[Set[str]] = None) -> Set[str]:
        return self.left.get_free_variables(bound) | self.right.get_free_variables(bound)

    def __str__(self) -> str:
        return f"({self.left} ∨ {self.right})"

    def __repr__(self) -> str:
        return f"Or({self.left}, {self.right})"

    def to_dict(self) -> Dict[str, Any]:
        return {"type": "or", "left": self.left.to_dict(), "right": self.right.to_dict()}


class Implies(Formula):
    """left → right"""
    def __init__(self, left: Formula, right: Formula):
        self.left = left
        self.right = right

    def get_free_variables(self, bound: Optional[Set[str]] = None) -> Set[str]:
        return self.left.get_free_variables(bound) | self.right.get_free_variables(bound)

    def __str__(self) -> str:
        return f"({self.left} → {self.right})"

    def __repr__(self) -> str:
        return f"Implies({self.left}, {self.right})"

    def to_dict(self) -> Dict[str, Any]:
        return {"type": "implies", "left": self.left.to_dict(), "right": self.right.to_dict()}


class Iff(Formula):
    """left ↔ right"""
    def __init__(self, left: Formula, right: Formula):
        self.left = left
        self.right = right

    def get_free_variables(self, bound: Optional[Set[str]] = None) -> Set[str]:
        return self.left.get_free_variables(bound) | self.right.get_free_variables(bound)

    def __str__(self) -> str:
        return f"({self.left} ↔ {self.right})"

    def __repr__(self) -> str:
        return f"Iff({self.left}, {self.right})"

    def to_dict(self) -> Dict[str, Any]:
        return {"type": "iff", "left": self.left.to_dict(), "right": self.right.to_dict()}


class Forall(Formula):
    """∀ var_name: body"""
    def __init__(self, var_name: str, body: Formula):
        self.var_name = str(var_name).strip()
        self.body = body

    def get_free_variables(self, bound: Optional[Set[str]] = None) -> Set[str]:
        bound = (bound or set()) | {self.var_name}
        return self.body.get_free_variables(bound)

    def __str__(self) -> str:
        return f"∀{self.var_name} ({self.body})"

    def __repr__(self) -> str:
        return f"Forall({self.var_name}, {self.body})"

    def to_dict(self) -> Dict[str, Any]:
        return {"type": "forall", "variable": self.var_name, "body": self.body.to_dict()}


class Exists(Formula):
    """∃ var_name: body"""
    def __init__(self, var_name: str, body: Formula):
        self.var_name = str(var_name).strip()
        self.body = body

    def get_free_variables(self, bound: Optional[Set[str]] = None) -> Set[str]:
        bound = (bound or set()) | {self.var_name}
        return self.body.get_free_variables(bound)

    def __str__(self) -> str:
        return f"∃{self.var_name} ({self.body})"

    def __repr__(self) -> str:
        return f"Exists({self.var_name}, {self.body})"

    def to_dict(self) -> Dict[str, Any]:
        return {"type": "exists", "variable": self.var_name, "body": self.body.to_dict()}
