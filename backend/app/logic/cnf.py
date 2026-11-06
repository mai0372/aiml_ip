"""
backend/app/logic/cnf.py
Converts First-Order Logic Well-Formed Formulas (WFF) to Clausal Normal Form (CNF).
Records all 9 intermediate transformation steps for visual rendering in the Logic Lab.
"""

from __future__ import annotations
from typing import List, Dict, Set, Tuple, Optional, Any
import copy

from backend.app.logic.ast import (
    Term, Variable, Constant, FunctionTerm,
    Predicate, Literal, Clause,
    Formula, Atom, Not, And, Or, Implies, Iff, Forall, Exists
)


class CNFStep:
    """Represents a single intermediate transformation step in the WFF-to-CNF pipeline."""
    def __init__(self, step_number: int, name: str, description: str, formula_str: str):
        self.step_number = step_number
        self.name = name
        self.description = description
        self.formula_str = formula_str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_number": self.step_number,
            "name": self.name,
            "description": self.description,
            "formula_str": self.formula_str
        }


class CNFConverter:
    """Rigorous 9-step WFF to CNF transformation pipeline."""

    def __init__(self):
        self.var_counter = 0
        self.skolem_counter = 0

    def _fresh_var(self, base: str = "v") -> str:
        self.var_counter += 1
        return f"{base}_{self.var_counter}"

    def _fresh_skolem(self) -> str:
        self.skolem_counter += 1
        return f"sk_{self.skolem_counter}"

    def convert_with_steps(
        self,
        formula: Formula,
        source_id: Optional[str] = None,
        source_type: str = "contract"
    ) -> Tuple[List[Clause], List[CNFStep]]:
        """Executes all 9 steps, returning the final clauses and the transformation history."""
        steps: List[CNFStep] = []

        # Step 0: Input Formula
        current = copy.deepcopy(formula)
        steps.append(CNFStep(0, "Input Formula", "Initial Well-Formed Formula (WFF)", str(current)))

        # Step 1: Eliminate Biconditionals (P <-> Q  =>  (P -> Q) & (Q -> P))
        current = self._eliminate_biconditionals(current)
        steps.append(CNFStep(1, "Eliminate Biconditionals", "Replace A ↔ B with (A → B) ∧ (B → A)", str(current)))

        # Step 2: Eliminate Implications (P -> Q  =>  ~P | Q)
        current = self._eliminate_implications(current)
        steps.append(CNFStep(2, "Eliminate Implications", "Replace A → B with ¬A ∨ B", str(current)))

        # Step 3: Move Negations Inward (NNF) via De Morgan's Laws
        current = self._to_nnf(current)
        steps.append(CNFStep(3, "Move Negations Inward (NNF)", "Push ¬ inward using De Morgan's laws and duality", str(current)))

        # Step 4: Standardize Bound Variables Apart
        current = self._standardize_bound_variables(current, set(), {})
        steps.append(CNFStep(4, "Standardize Bound Variables", "Rename bound variables so each quantifier is unique", str(current)))

        # Step 5: Skolemization
        current = self._skolemize(current, [])
        steps.append(CNFStep(5, "Skolemization", "Replace ∃ variables with Skolem constants/functions of enclosing ∀", str(current)))

        # Step 6: Drop Universal Quantifiers
        current = self._drop_universals(current)
        steps.append(CNFStep(6, "Drop Universal Quantifiers", "Assume all remaining variables are universally quantified", str(current)))

        # Step 7: Distribute Disjunctions over Conjunctions
        current = self._distribute_or_over_and(current)
        steps.append(CNFStep(7, "Distribute Disjunctions", "Apply A ∨ (B ∧ C) ≡ (A ∨ B) ∧ (A ∨ C)", str(current)))

        # Step 8: Extract Clause Set
        raw_clauses = self._extract_clauses(current, source_id, source_type)
        clauses_str = " ∧ ".join(f"({c})" for c in raw_clauses)
        steps.append(CNFStep(8, "Extract Clause Set", "Decompose top-level conjunctions into individual disjunctive clauses", clauses_str))

        # Step 9: Standardize Variables Across Clauses
        final_clauses: List[Clause] = []
        for i, c in enumerate(raw_clauses):
            clause_id = f"{source_id}_C{i+1}" if source_id else f"C{i+1}"
            std_c = c.standardize_variables(f"cl{i+1}")
            std_c.clause_id = clause_id
            std_c.source_id = source_id or ""
            std_c.source_type = source_type
            if source_id:
                std_c.provenance_sources = {source_id}
            final_clauses.append(std_c)

        final_str = " ∧ ".join(f"{c.clause_id}: ({c})" for c in final_clauses)
        steps.append(CNFStep(9, "Standardize Clause Variables", "Standardize variable namespaces across independent clauses", final_str))

        return final_clauses, steps

    # --- Step 1: Eliminate Biconditionals ---
    def _eliminate_biconditionals(self, f: Formula) -> Formula:
        if isinstance(f, Atom):
            return f
        elif isinstance(f, Not):
            return Not(self._eliminate_biconditionals(f.body))
        elif isinstance(f, And):
            return And(self._eliminate_biconditionals(f.left), self._eliminate_biconditionals(f.right))
        elif isinstance(f, Or):
            return Or(self._eliminate_biconditionals(f.left), self._eliminate_biconditionals(f.right))
        elif isinstance(f, Implies):
            return Implies(self._eliminate_biconditionals(f.left), self._eliminate_biconditionals(f.right))
        elif isinstance(f, Iff):
            left = self._eliminate_biconditionals(f.left)
            right = self._eliminate_biconditionals(f.right)
            return And(Implies(left, right), Implies(right, left))
        elif isinstance(f, Forall):
            return Forall(f.var_name, self._eliminate_biconditionals(f.body))
        elif isinstance(f, Exists):
            return Exists(f.var_name, self._eliminate_biconditionals(f.body))
        return f

    # --- Step 2: Eliminate Implications ---
    def _eliminate_implications(self, f: Formula) -> Formula:
        if isinstance(f, Atom):
            return f
        elif isinstance(f, Not):
            return Not(self._eliminate_implications(f.body))
        elif isinstance(f, And):
            return And(self._eliminate_implications(f.left), self._eliminate_implications(f.right))
        elif isinstance(f, Or):
            return Or(self._eliminate_implications(f.left), self._eliminate_implications(f.right))
        elif isinstance(f, Implies):
            left = self._eliminate_implications(f.left)
            right = self._eliminate_implications(f.right)
            return Or(Not(left), right)
        elif isinstance(f, Forall):
            return Forall(f.var_name, self._eliminate_implications(f.body))
        elif isinstance(f, Exists):
            return Exists(f.var_name, self._eliminate_implications(f.body))
        return f

    # --- Step 3: Move Negations Inward (NNF) ---
    def _to_nnf(self, f: Formula) -> Formula:
        if isinstance(f, Atom):
            return f
        elif isinstance(f, Not):
            inner = f.body
            if isinstance(inner, Atom):
                return f
            elif isinstance(inner, Not):
                # Double negation: ¬¬P => P
                return self._to_nnf(inner.body)
            elif isinstance(inner, And):
                # De Morgan: ¬(A ∧ B) => ¬A ∨ ¬B
                return Or(self._to_nnf(Not(inner.left)), self._to_nnf(Not(inner.right)))
            elif isinstance(inner, Or):
                # De Morgan: ¬(A ∨ B) => ¬A ∧ ¬B
                return And(self._to_nnf(Not(inner.left)), self._to_nnf(Not(inner.right)))
            elif isinstance(inner, Forall):
                # ¬∀x P => ∃x ¬P
                return Exists(inner.var_name, self._to_nnf(Not(inner.body)))
            elif isinstance(inner, Exists):
                # ¬∃x P => ∀x ¬P
                return Forall(inner.var_name, self._to_nnf(Not(inner.body)))
            return f
        elif isinstance(f, And):
            return And(self._to_nnf(f.left), self._to_nnf(f.right))
        elif isinstance(f, Or):
            return Or(self._to_nnf(f.left), self._to_nnf(f.right))
        elif isinstance(f, Forall):
            return Forall(f.var_name, self._to_nnf(f.body))
        elif isinstance(f, Exists):
            return Exists(f.var_name, self._to_nnf(f.body))
        return f

    # --- Step 4: Standardize Bound Variables ---
    def _standardize_bound_variables(
        self,
        f: Formula,
        seen_vars: Set[str],
        var_map: Dict[str, str]
    ) -> Formula:
        if isinstance(f, Atom):
            subst = {old: Variable(new) for old, new in var_map.items()}
            return Atom(f.predicate.substitute(subst))
        elif isinstance(f, Not):
            return Not(self._standardize_bound_variables(f.body, seen_vars, var_map))
        elif isinstance(f, And):
            return And(
                self._standardize_bound_variables(f.left, seen_vars, var_map),
                self._standardize_bound_variables(f.right, seen_vars, var_map)
            )
        elif isinstance(f, Or):
            return Or(
                self._standardize_bound_variables(f.left, seen_vars, var_map),
                self._standardize_bound_variables(f.right, seen_vars, var_map)
            )
        elif isinstance(f, Forall):
            var_name = f.var_name
            new_var = var_name
            if var_name in seen_vars:
                new_var = self._fresh_var(var_name)
            seen_vars = seen_vars | {new_var}
            new_map = dict(var_map)
            new_map[var_name] = new_var
            return Forall(new_var, self._standardize_bound_variables(f.body, seen_vars, new_map))
        elif isinstance(f, Exists):
            var_name = f.var_name
            new_var = var_name
            if var_name in seen_vars:
                new_var = self._fresh_var(var_name)
            seen_vars = seen_vars | {new_var}
            new_map = dict(var_map)
            new_map[var_name] = new_var
            return Exists(new_var, self._standardize_bound_variables(f.body, seen_vars, new_map))
        return f

    # --- Step 5: Skolemization ---
    def _skolemize(self, f: Formula, universals: List[str]) -> Formula:
        if isinstance(f, Atom):
            return f
        elif isinstance(f, Not):
            return Not(self._skolemize(f.body, universals))
        elif isinstance(f, And):
            return And(self._skolemize(f.left, universals), self._skolemize(f.right, universals))
        elif isinstance(f, Or):
            return Or(self._skolemize(f.left, universals), self._skolemize(f.right, universals))
        elif isinstance(f, Forall):
            return Forall(f.var_name, self._skolemize(f.body, universals + [f.var_name]))
        elif isinstance(f, Exists):
            skolem_name = self._fresh_skolem()
            if not universals:
                # Skolem constant
                replacement_term: Term = Constant(skolem_name, is_numeric=False)
            else:
                # Skolem function f(x1, ..., xk)
                replacement_term = FunctionTerm(skolem_name, [Variable(u) for u in universals])

            # Substitute existential variable throughout body
            body_substituted = self._substitute_in_formula(f.body, f.var_name, replacement_term)
            return self._skolemize(body_substituted, universals)
        return f

    def _substitute_in_formula(self, f: Formula, var_name: str, term: Term) -> Formula:
        subst = {var_name: term}
        if isinstance(f, Atom):
            return Atom(f.predicate.substitute(subst))
        elif isinstance(f, Not):
            return Not(self._substitute_in_formula(f.body, var_name, term))
        elif isinstance(f, And):
            return And(self._substitute_in_formula(f.left, var_name, term), self._substitute_in_formula(f.right, var_name, term))
        elif isinstance(f, Or):
            return Or(self._substitute_in_formula(f.left, var_name, term), self._substitute_in_formula(f.right, var_name, term))
        elif isinstance(f, Forall):
            if f.var_name == var_name:
                return f
            return Forall(f.var_name, self._substitute_in_formula(f.body, var_name, term))
        elif isinstance(f, Exists):
            if f.var_name == var_name:
                return f
            return Exists(f.var_name, self._substitute_in_formula(f.body, var_name, term))
        return f

    # --- Step 6: Drop Universal Quantifiers ---
    def _drop_universals(self, f: Formula) -> Formula:
        if isinstance(f, Atom):
            return f
        elif isinstance(f, Not):
            return Not(self._drop_universals(f.body))
        elif isinstance(f, And):
            return And(self._drop_universals(f.left), self._drop_universals(f.right))
        elif isinstance(f, Or):
            return Or(self._drop_universals(f.left), self._drop_universals(f.right))
        elif isinstance(f, Forall):
            return self._drop_universals(f.body)
        elif isinstance(f, Exists):
            return self._drop_universals(f.body)
        return f

    # --- Step 7: Distribute Disjunctions over Conjunctions ---
    def _distribute_or_over_and(self, f: Formula) -> Formula:
        if isinstance(f, Atom) or isinstance(f, Not):
            return f
        elif isinstance(f, And):
            return And(self._distribute_or_over_and(f.left), self._distribute_or_over_and(f.right))
        elif isinstance(f, Or):
            left = self._distribute_or_over_and(f.left)
            right = self._distribute_or_over_and(f.right)

            # (A ∧ B) ∨ C  =>  (A ∨ C) ∧ (B ∨ C)
            if isinstance(left, And):
                return And(
                    self._distribute_or_over_and(Or(left.left, right)),
                    self._distribute_or_over_and(Or(left.right, right))
                )
            # A ∨ (B ∧ C)  =>  (A ∨ B) ∧ (A ∨ C)
            if isinstance(right, And):
                return And(
                    self._distribute_or_over_and(Or(left, right.left)),
                    self._distribute_or_over_and(Or(left, right.right))
                )
            return Or(left, right)
        return f

    # --- Step 8: Extract Clause Set ---
    def _extract_clauses(
        self,
        f: Formula,
        source_id: Optional[str] = None,
        source_type: str = "contract"
    ) -> List[Clause]:
        if isinstance(f, And):
            return self._extract_clauses(f.left, source_id, source_type) + self._extract_clauses(f.right, source_id, source_type)
        else:
            lits = self._extract_literals(f)
            return [Clause(
                literals=lits,
                source_id=source_id,
                source_type=source_type,
                provenance_sources={source_id} if source_id else set()
            )]

    def _extract_literals(self, f: Formula) -> List[Literal]:
        if isinstance(f, Atom):
            return [Literal(f.predicate, is_negated=False)]
        elif isinstance(f, Not):
            if isinstance(f.body, Atom):
                return [Literal(f.body.predicate, is_negated=True)]
            raise ValueError(f"Formula not in CNF: negation applied to non-atom: {f}")
        elif isinstance(f, Or):
            return self._extract_literals(f.left) + self._extract_literals(f.right)
        raise ValueError(f"Formula not in CNF: unexpected node type: {type(f)}")

