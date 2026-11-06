"""
backend/tests/test_logic_engine.py
Mandatory test suite for the Logic-Based Contract Compliance Engine:
- Socrates syllogism
- Curiosity killed the cat puzzle
- Satisfiable set non-refutation (tri-state correctness)
- Skolemization with nested quantifiers
- Occurs-check failure
- CNF equivalence checked by truth-table brute force
- Builtin procedural arithmetic
- Worked contract contradiction example (Clause 3 vs Clause 12)
- Independent Proof Verifier validation & corruption catch
"""

import pytest
import itertools
import copy
from typing import Dict

from backend.app.logic.ast import (
    Variable, Constant, FunctionTerm, Predicate, Literal, Clause,
    Atom, Not, And, Or, Implies, Iff, Forall, Exists
)
from backend.app.logic.lexer import Lexer, TokenType
from backend.app.logic.parser import parse_fopl, ParserError
from backend.app.logic.cnf import CNFConverter
from backend.app.logic.unifier import (
    unify_terms, unify_predicates, unify_complementary_literals,
    occurs_check
)
from backend.app.logic.resolution import (
    ResolutionProver, ResolutionOutcome
)
from backend.app.logic.proof_checker import IndependentProofChecker


class TestLogicEngineMandatory:

    def test_01_socrates_syllogism(self):
        """
        Textbook syllogism:
        1. All men are mortal: forall x: (Man(x) -> Mortal(x))
        2. Socrates is a man: Man(Socrates)
        Goal to prove: Mortal(Socrates)
        Refutation: Add ~Mortal(Socrates) and derive empty clause []
        """
        conv = CNFConverter()
        c1, _ = conv.convert_with_steps(parse_fopl("forall x: (Man(x) -> Mortal(x))"), source_id="KB1")
        c2, _ = conv.convert_with_steps(parse_fopl("Man(Socrates)"), source_id="KB2")
        neg_goal, _ = conv.convert_with_steps(parse_fopl("~Mortal(Socrates)"), source_id="GOAL", source_type="goal")

        prover = ResolutionProver()
        result = prover.prove(c1 + c2 + neg_goal)

        assert result.outcome == ResolutionOutcome.REFUTATION_FOUND
        assert result.success is True
        assert result.empty_clause_id is not None
        assert "KB1" in result.minimal_conflict_clause_ids
        assert "KB2" in result.minimal_conflict_clause_ids
        assert "GOAL" in result.minimal_conflict_clause_ids

        # Independent verifier check
        checker = IndependentProofChecker()
        report = checker.verify_proof(result.to_dict())
        assert report.is_valid is True
        assert len(report.errors) == 0

    def test_02_curiosity_killed_the_cat(self):
        """
        Textbook puzzle: Curiosity killed the cat.
        - Everyone who loves all animals is loved by someone.
        - Anyone who kills an animal is loved by no one.
        - Jack loves all animals.
        - Either Jack or Curiosity killed the cat, whose name is Tuna.
        Goal: Curiosity killed Tuna.
        Simplified standard propositional/relational refutation instance:
        LovesAll(Jack)
        LovesAll(Jack) -> LovesSomeone(Jack)
        Kills(Jack, Tuna) -> ~LovesSomeone(Jack)
        Kills(Jack, Tuna) v Kills(Curiosity, Tuna)
        Negated goal: ~Kills(Curiosity, Tuna)
        """
        conv = CNFConverter()
        clauses = []
        clauses += conv.convert_with_steps(parse_fopl("LovesAll(Jack)"), "C1")[0]
        clauses += conv.convert_with_steps(parse_fopl("LovesAll(Jack) -> LovesSomeone(Jack)"), "C2")[0]
        clauses += conv.convert_with_steps(parse_fopl("Kills(Jack, Tuna) -> ~LovesSomeone(Jack)"), "C3")[0]
        clauses += conv.convert_with_steps(parse_fopl("Kills(Jack, Tuna) | Kills(Curiosity, Tuna)"), "C4")[0]
        clauses += conv.convert_with_steps(parse_fopl("~Kills(Curiosity, Tuna)"), "GOAL", "goal")[0]

        prover = ResolutionProver()
        result = prover.prove(clauses)

        assert result.outcome == ResolutionOutcome.REFUTATION_FOUND
        assert result.success is True
        assert result.empty_clause_id is not None

        checker = IndependentProofChecker()
        report = checker.verify_proof(result.to_dict())
        assert report.is_valid is True

    def test_03_satisfiable_set_no_refutation(self):
        """
        A consistent / satisfiable knowledge base must NOT derive a refutation.
        Outcome must be SATURATED_NO_REFUTATION or UNKNOWN, never REFUTATION_FOUND.
        """
        conv = CNFConverter()
        c1, _ = conv.convert_with_steps(parse_fopl("forall x: (Dog(x) -> Animal(x))"), "C1")
        c2, _ = conv.convert_with_steps(parse_fopl("Dog(Rex)"), "C2")
        c3, _ = conv.convert_with_steps(parse_fopl("Friendly(Rex)"), "C3")

        prover = ResolutionProver()
        result = prover.prove(c1 + c2 + c3)

        assert result.outcome != ResolutionOutcome.REFUTATION_FOUND
        assert result.success is False
        assert result.empty_clause_id is None
        assert result.outcome == ResolutionOutcome.SATURATED_NO_REFUTATION

    def test_04_skolemization_nested_quantifiers(self):
        """
        forall x: exists y: R(x, y) -> y becomes function sk_1(x)
        exists y: forall x: R(x, y) -> y becomes constant sk_2
        """
        conv = CNFConverter()
        f1 = parse_fopl("forall x: exists y: R(x, y)")
        cl1, steps1 = conv.convert_with_steps(f1)
        # Check that Skolem term in cl1 contains x as argument
        pred1 = cl1[0].literals[0].predicate
        sk_term = pred1.args[1]
        assert isinstance(sk_term, FunctionTerm)
        assert len(sk_term.args) == 1
        assert str(sk_term.args[0]).startswith("x")

        # Exists before Forall
        f2 = parse_fopl("exists y: forall x: R(x, y)")
        cl2, steps2 = conv.convert_with_steps(f2)
        pred2 = cl2[0].literals[0].predicate
        const_term = pred2.args[1]
        # In exists y: forall x, y has no enclosing universals, so it is a Skolem constant or 0-arg function
        assert isinstance(const_term, Constant)

    def test_05_occurs_check_failure(self):
        """Unifying variable x with term f(x) must fail due to occurs check."""
        x = Variable("x")
        fx = FunctionTerm("f", [x])
        res = unify_terms(x, fx)
        assert res is None, "Occurs check must reject recursive binding x = f(x)"

    def test_06_cnf_truth_table_equivalence(self):
        """
        Brute-force truth table verification of propositional formula vs CNF translation.
        Tests: (A -> B) & (B -> C) <-> (A -> C) & (A | ~B)
        """
        def eval_prop(formula, env: Dict[str, bool]) -> bool:
            if isinstance(formula, Atom):
                return env[formula.predicate.name]
            elif isinstance(formula, Not):
                return not eval_prop(formula.body, env)
            elif isinstance(formula, And):
                return eval_prop(formula.left, env) and eval_prop(formula.right, env)
            elif isinstance(formula, Or):
                return eval_prop(formula.left, env) or eval_prop(formula.right, env)
            elif isinstance(formula, Implies):
                return (not eval_prop(formula.left, env)) or eval_prop(formula.right, env)
            elif isinstance(formula, Iff):
                return eval_prop(formula.left, env) == eval_prop(formula.right, env)
            raise ValueError(f"Unknown formula node {type(formula)}")

        def eval_cnf(clauses, env: Dict[str, bool]) -> bool:
            for clause in clauses:
                clause_true = False
                for lit in clause.literals:
                    var_val = env[lit.predicate.name]
                    lit_val = (not var_val) if lit.is_negated else var_val
                    if lit_val:
                        clause_true = True
                        break
                if not clause_true:
                    return False
            return True

        test_formulas = [
            "A() -> (B() & C())",
            "(A() <-> B()) | ~C()",
            "~(A() & (B() | ~C()))",
            "(A() -> B()) & (B() -> C())"
        ]

        converter = CNFConverter()
        for f_str in test_formulas:
            orig = parse_fopl(f_str)
            clauses, _ = converter.convert_with_steps(orig)
            # Brute-force all assignments of A, B, C
            for a_val, b_val, c_val in itertools.product([True, False], repeat=3):
                env = {"A": a_val, "B": b_val, "C": c_val}
                orig_val = eval_prop(orig, env)
                cnf_val = eval_cnf(clauses, env)
                assert orig_val == cnf_val, f"CNF mismatch for '{f_str}' under env {env}"

    def test_07_builtin_arithmetic(self):
        """Tests procedural attachment for LessThan, GreaterThan, Equals on numbers."""
        p1 = Predicate("LessThan", [Constant("30"), Constant("90")])
        assert p1.evaluate_arithmetic() is True

        p2 = Predicate("LessThan", [Constant("90"), Constant("30")])
        assert p2.evaluate_arithmetic() is False

        p3 = Predicate("Equals", [Constant("30"), Constant("30")])
        assert p3.evaluate_arithmetic() is True

        # Non-ground predicate returns None
        p_var = Predicate("LessThan", [Variable("n"), Constant("90")])
        assert p_var.evaluate_arithmetic() is None

        # Clause simplification with arithmetic
        # Clause containing ~LessThan(30, 90) -> literal evaluates to False -> removed
        lit_false = Literal(p1, is_negated=True)
        c = Clause([lit_false])
        simplified = c.simplify_arithmetic()
        assert simplified is not None
        assert simplified.is_empty()

    def test_08_worked_rental_contradiction_example(self):
        """
        Worked example required by Section 3:
        Clause 3 lets the tenant terminate with 30 days' notice:
          Perm(tenant, Terminate(30))
        Clause 12 forbids early termination with less than 90 days' notice:
          forall n: (LessThan(n,90) -> Forb(tenant, Terminate(n)))
        Axiom:
          forall p, a: ~(Perm(p, a) & Forb(p, a))
        Resolution with n=30 and built-in LessThan(30,90) yields empty clause [],
        and the proof lists exactly clauses 3 and 12!
        """
        conv = CNFConverter()
        # Clause 3
        c3, _ = conv.convert_with_steps(parse_fopl("Perm(tenant, Terminate(30))"), source_id="Clause_3", source_type="contract")
        # Clause 12: LessThan(n,90) -> Forb(tenant, Terminate(n))
        c12, _ = conv.convert_with_steps(parse_fopl("forall n: (LessThan(n, 90) -> Forb(tenant, Terminate(n)))"), source_id="Clause_12", source_type="contract")
        # Axiom: Deontic exclusivity ~(Perm(p, a) & Forb(p, a))
        ax, _ = conv.convert_with_steps(parse_fopl("forall p, a: ~(Perm(p, a) & Forb(p, a))"), source_id="AXIOM_DEONTIC", source_type="axiom")

        prover = ResolutionProver()
        result = prover.prove(c3 + c12 + ax)

        assert result.outcome == ResolutionOutcome.REFUTATION_FOUND
        assert result.success is True
        assert result.empty_clause_id is not None

        # Check minimal conflicting set
        conflicts = result.minimal_conflict_clause_ids
        assert "Clause_3" in conflicts
        assert "Clause_12" in conflicts

        # Independent verifier validation
        checker = IndependentProofChecker()
        report = checker.verify_proof(result.to_dict())
        assert report.is_valid is True
        assert len(report.errors) == 0

    def test_09_proof_checker_catches_corruption(self):
        """Verifies that the independent proof checker detects corrupted proof steps."""
        conv = CNFConverter()
        c1, _ = conv.convert_with_steps(parse_fopl("Man(Socrates)"), "C1")
        c2, _ = conv.convert_with_steps(parse_fopl("~Man(Socrates)"), "C2")

        prover = ResolutionProver()
        result = prover.prove(c1 + c2)
        assert result.success is True

        proof_dict = result.to_dict()
        checker = IndependentProofChecker()

        # Valid proof passes
        assert checker.verify_proof(proof_dict).is_valid is True

        # Inject corruption: flip literal1 polarity so both are positive
        corrupted_dict = copy.deepcopy(proof_dict)
        corrupted_dict["steps"][0]["literal1"] = "Man(Socrates)"  # Both literal1 and literal2 are now positive!
        report = checker.verify_proof(corrupted_dict)
        assert report.is_valid is False
        assert len(report.errors) > 0
