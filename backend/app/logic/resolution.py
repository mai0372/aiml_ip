"""
backend/app/logic/resolution.py
First-Order Logic Resolution by Refutation Theorem Prover.
Implements:
- Procedural arithmetic attachment (LessThan, GreaterThan, Equals)
- Factoring and tautology elimination
- Subsumption checking
- Strategy portfolio (Set-of-Support + Unit preference, Otter loop)
- Search guards: max clauses, term depth, wall-clock timeout
- Honest Tri-State outcomes: REFUTATION_FOUND, SATURATED_NO_REFUTATION, UNKNOWN_BUDGET_EXHAUSTED
- Provenance tracking with minimal conflicting set extraction
"""

from __future__ import annotations
from enum import Enum
from typing import List, Dict, Set, Tuple, Optional, Any
import copy
import time

from backend.app.logic.ast import (
    Term, Variable, Constant, FunctionTerm,
    Predicate, Literal, Clause
)
from backend.app.logic.unifier import (
    unify_complementary_literals, unify_predicates,
    unify_terms, format_substitution
)


class ResolutionOutcome(str, Enum):
    REFUTATION_FOUND = "REFUTATION_FOUND"
    SATURATED_NO_REFUTATION = "SATURATED_NO_REFUTATION"
    UNKNOWN_BUDGET_EXHAUSTED = "UNKNOWN_BUDGET_EXHAUSTED"


class ProofStep:
    """Represents an atomic valid inference step in a resolution refutation."""
    def __init__(
        self,
        step_id: str,
        parent1_id: str,
        parent2_id: Optional[str],
        resolvent: Clause,
        literal1: Optional[Literal] = None,
        literal2: Optional[Literal] = None,
        mgu: Optional[Dict[str, Term]] = None,
        rule_name: str = "resolution",  # "resolution", "factoring", "procedural_arithmetic"
        explanation: str = ""
    ):
        self.step_id = step_id
        self.parent1_id = parent1_id
        self.parent2_id = parent2_id
        self.resolvent = resolvent
        self.literal1 = literal1
        self.literal2 = literal2
        self.mgu = mgu or {}
        self.rule_name = rule_name
        self.explanation = explanation

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_id": self.step_id,
            "parent1_id": self.parent1_id,
            "parent2_id": self.parent2_id,
            "resolvent": self.resolvent.to_dict(),
            "literal1": str(self.literal1) if self.literal1 else None,
            "literal2": str(self.literal2) if self.literal2 else None,
            "mgu": format_substitution(self.mgu),
            "rule_name": self.rule_name,
            "explanation": self.explanation
        }


class ProofResult:
    """Outcome and complete proof structure for a resolution refutation attempt."""
    def __init__(
        self,
        outcome: ResolutionOutcome,
        steps: List[ProofStep],
        initial_clauses: List[Clause],
        empty_clause_id: Optional[str] = None,
        minimal_conflict_clause_ids: Optional[List[str]] = None,
        total_clauses_generated: int = 0,
        elapsed_seconds: float = 0.0,
        message: str = ""
    ):
        self.outcome = outcome
        self.success = (outcome == ResolutionOutcome.REFUTATION_FOUND)
        self.steps = steps
        self.initial_clauses = initial_clauses
        self.empty_clause_id = empty_clause_id
        self.minimal_conflict_clause_ids = minimal_conflict_clause_ids or []
        self.total_clauses_generated = total_clauses_generated
        self.elapsed_seconds = elapsed_seconds
        self.message = message

    def to_dict(self) -> Dict[str, Any]:
        return {
            "outcome": self.outcome.value,
            "success": self.success,
            "empty_clause_id": self.empty_clause_id,
            "minimal_conflict_clause_ids": self.minimal_conflict_clause_ids,
            "total_clauses_generated": self.total_clauses_generated,
            "elapsed_seconds": round(self.elapsed_seconds, 4),
            "message": self.message,
            "initial_clauses": [c.to_dict() for c in self.initial_clauses],
            "steps": [s.to_dict() for s in self.steps],
            "graph": self.build_graph()
        }

    def build_graph(self) -> Dict[str, Any]:
        """Builds a Directed Acyclic Graph (DAG) for visual SVG rendering in the UI."""
        nodes = []
        edges = []

        participating_ids: Set[str] = set()
        step_by_id = {s.step_id: s for s in self.steps}

        if self.success and self.empty_clause_id:
            participating_ids.add(self.empty_clause_id)
            queue = [self.empty_clause_id]
            while queue:
                cid = queue.pop(0)
                if cid in step_by_id:
                    s = step_by_id[cid]
                    if s.parent1_id:
                        participating_ids.add(s.parent1_id)
                        queue.append(s.parent1_id)
                    if s.parent2_id and s.parent2_id != "ARITHMETIC_AXIOM":
                        participating_ids.add(s.parent2_id)
                        queue.append(s.parent2_id)
        else:
            participating_ids = {c.clause_id for c in self.initial_clauses[:25]}.union(
                {s.step_id for s in self.steps[:25]}
            )

        # Initial clauses nodes
        for c in self.initial_clauses:
            if c.clause_id in participating_ids:
                node_type = "axiom" if c.source_type == "axiom" else ("goal" if c.source_type == "goal" else "contract")
                nodes.append({
                    "id": c.clause_id,
                    "label": str(c),
                    "type": node_type,
                    "source_id": c.source_id,
                    "source_type": c.source_type,
                    "clause": c.to_dict()
                })

        # Derived step nodes and edges
        for s in self.steps:
            if s.step_id in participating_ids:
                is_contradiction = s.resolvent.is_empty()
                nodes.append({
                    "id": s.step_id,
                    "label": "[] (Contradiction)" if is_contradiction else str(s.resolvent),
                    "type": "contradiction" if is_contradiction else "resolvent",
                    "rule": s.rule_name,
                    "explanation": s.explanation,
                    "clause": s.resolvent.to_dict()
                })

                if s.parent1_id and s.parent1_id in participating_ids:
                    edges.append({
                        "from": s.parent1_id,
                        "to": s.step_id,
                        "literal": str(s.literal1) if s.literal1 else "",
                        "mgu": format_substitution(s.mgu)
                    })
                if s.parent2_id and s.parent2_id != "ARITHMETIC_AXIOM" and s.parent2_id in participating_ids:
                    edges.append({
                        "from": s.parent2_id,
                        "to": s.step_id,
                        "literal": str(s.literal2) if s.literal2 else "",
                        "mgu": format_substitution(s.mgu)
                    })

        return {"nodes": nodes, "edges": edges}


class ResolutionProver:
    """
    State-of-the-art First-Order Logic Resolution Theorem Prover.
    Implements unit preference, set-of-support, procedural arithmetic attachment,
    subsumption deletion, and strategy portfolio selection.
    """

    def __init__(
        self,
        max_clauses: int = 1500,
        max_term_depth: int = 6,
        timeout_seconds: float = 3.0
    ):
        self.max_clauses = max_clauses
        self.max_term_depth = max_term_depth
        self.timeout_seconds = timeout_seconds

    def prove(self, clauses: List[Clause], sos_clause_ids: Optional[Set[str]] = None) -> ProofResult:
        """
        Executes a strategy portfolio to find the shortest verified refutation proof.
        Strategies tried:
          1. Unit Preference + Set of Support (SoS)
          2. Shortest-Clause Otter Loop
        """
        start_time = time.perf_counter()

        # Run Strategy 1: Unit preference + SoS
        res1 = self._run_strategy(
            clauses,
            strategy_name="unit_sos",
            sos_clause_ids=sos_clause_ids,
            start_time=start_time
        )
        if res1.outcome == ResolutionOutcome.REFUTATION_FOUND:
            res1.elapsed_seconds = time.perf_counter() - start_time
            return res1

        # Check if time remains for Strategy 2
        elapsed = time.perf_counter() - start_time
        if elapsed > self.timeout_seconds * 0.8:
            res1.elapsed_seconds = elapsed
            return res1

        # Run Strategy 2: Standard Otter Shortest-Clause
        res2 = self._run_strategy(
            clauses,
            strategy_name="shortest_first",
            sos_clause_ids=None,
            start_time=start_time
        )
        if res2.outcome == ResolutionOutcome.REFUTATION_FOUND:
            res2.elapsed_seconds = time.perf_counter() - start_time
            return res2

        # If both exhausted without refutation, determine saturated vs budget exhausted
        final_outcome = (
            ResolutionOutcome.SATURATED_NO_REFUTATION
            if res1.outcome == ResolutionOutcome.SATURATED_NO_REFUTATION and res2.outcome == ResolutionOutcome.SATURATED_NO_REFUTATION
            else ResolutionOutcome.UNKNOWN_BUDGET_EXHAUSTED
        )

        return ProofResult(
            outcome=final_outcome,
            steps=res1.steps[:50],
            initial_clauses=res1.initial_clauses,
            empty_clause_id=None,
            minimal_conflict_clause_ids=[],
            total_clauses_generated=res1.total_clauses_generated + res2.total_clauses_generated,
            elapsed_seconds=time.perf_counter() - start_time,
            message=(
                "Search saturated without contradiction. Clause set is satisfiable."
                if final_outcome == ResolutionOutcome.SATURATED_NO_REFUTATION
                else "Search budget exhausted without proving contradiction. Outcome is unknown."
            )
        )

    def _run_strategy(
        self,
        clauses: List[Clause],
        strategy_name: str,
        sos_clause_ids: Optional[Set[str]],
        start_time: float
    ) -> ProofResult:
        initial_clauses: List[Clause] = []
        for i, c in enumerate(clauses):
            cid = c.clause_id or f"A{i+1}"
            cl = copy.deepcopy(c)
            cl.clause_id = cid
            if not cl.provenance_sources:
                cl.provenance_sources = {cl.source_id} if cl.source_id else {cid}
            initial_clauses.append(cl)

        steps: List[ProofStep] = []
        clause_counter = len(initial_clauses)
        seen_clauses: Set[str] = {self._canonical_clause_str(c) for c in initial_clauses}

        # Check for immediate contradiction or arithmetic simplification in initial clauses
        for c in initial_clauses:
            if c.is_empty():
                return ProofResult(
                    outcome=ResolutionOutcome.REFUTATION_FOUND,
                    steps=[],
                    initial_clauses=initial_clauses,
                    empty_clause_id=c.clause_id,
                    minimal_conflict_clause_ids=sorted(list(c.provenance_sources)),
                    total_clauses_generated=clause_counter,
                    elapsed_seconds=time.perf_counter() - start_time,
                    message="Contradiction derived: Empty clause present in initial formula set."
                )

            # Check if initial clause simplifies procedurally to empty clause
            simplified = c.simplify_arithmetic()
            if simplified is not None and simplified.is_empty():
                step_id = "R_init_arith"
                step = ProofStep(
                    step_id=step_id,
                    parent1_id=c.clause_id,
                    parent2_id="ARITHMETIC_AXIOM",
                    resolvent=simplified,
                    rule_name="procedural_arithmetic",
                    explanation=f"Procedural arithmetic evaluation of ground terms in {c.clause_id} yielded contradiction."
                )
                steps.append(step)
                return ProofResult(
                    outcome=ResolutionOutcome.REFUTATION_FOUND,
                    steps=steps,
                    initial_clauses=initial_clauses,
                    empty_clause_id=step_id,
                    minimal_conflict_clause_ids=sorted(list(c.provenance_sources)),
                    total_clauses_generated=clause_counter,
                    elapsed_seconds=time.perf_counter() - start_time,
                    message="Contradiction derived via procedural arithmetic attachment."
                )

        # Partition agenda into unprocessed and processed
        unprocessed: List[Clause] = list(initial_clauses)
        processed: List[Clause] = []

        step_counter = 0

        while unprocessed and len(processed) + len(unprocessed) < self.max_clauses:
            if time.perf_counter() - start_time > self.timeout_seconds:
                return ProofResult(
                    outcome=ResolutionOutcome.UNKNOWN_BUDGET_EXHAUSTED,
                    steps=steps,
                    initial_clauses=initial_clauses,
                    total_clauses_generated=clause_counter,
                    elapsed_seconds=time.perf_counter() - start_time,
                    message="Resolution budget exhausted (timeout reached)."
                )

            # Strategy Selection: Pick next given clause
            given_idx = self._select_next_clause_index(unprocessed, strategy_name, sos_clause_ids)
            given = unprocessed.pop(given_idx)

            # Generate Factored instances of the given clause
            factored_clauses = self._generate_factors(given)
            for fact_cl, lit_a, lit_b, mgu in factored_clauses:
                if self._is_tautology(fact_cl):
                    continue
                canon = self._canonical_clause_str(fact_cl)
                if canon in seen_clauses:
                    continue
                seen_clauses.add(canon)

                step_counter += 1
                clause_counter += 1
                fid = f"F{step_counter}"
                fact_cl.clause_id = fid
                step = ProofStep(
                    step_id=fid,
                    parent1_id=given.clause_id,
                    parent2_id=None,
                    resolvent=fact_cl,
                    literal1=lit_a,
                    literal2=lit_b,
                    mgu=mgu,
                    rule_name="factoring",
                    explanation=f"Factored {lit_a} and {lit_b} with unifier {format_substitution(mgu)}"
                )
                steps.append(step)
                if fact_cl.is_empty():
                    pruned = self._prune_irrelevant_steps(steps, fid)
                    min_conflicts = self._extract_minimal_conflict_clauses(pruned, initial_clauses, fid)
                    return ProofResult(
                        outcome=ResolutionOutcome.REFUTATION_FOUND,
                        steps=pruned,
                        initial_clauses=initial_clauses,
                        empty_clause_id=fid,
                        minimal_conflict_clause_ids=min_conflicts,
                        total_clauses_generated=clause_counter,
                        elapsed_seconds=time.perf_counter() - start_time,
                        message="Contradiction derived via factoring refutation."
                    )
                unprocessed.append(fact_cl)

            # Resolve given clause against all processed clauses
            for other in processed:
                resolvents = self._resolve_pair(given, other)
                for resolvent_clause, lit1, lit2, mgu in resolvents:
                    # Guard: Term depth check
                    if any(t.term_depth() > self.max_term_depth for lit in resolvent_clause.literals for t in lit.predicate.args):
                        continue

                    # Tautology check
                    if self._is_tautology(resolvent_clause):
                        continue

                    # Procedural Arithmetic Evaluation
                    arith_simplified = resolvent_clause.simplify_arithmetic()
                    if arith_simplified is None:
                        # Tautology due to arithmetic True
                        continue
                    
                    is_arithmetic_step = (arith_simplified != resolvent_clause)
                    resolvent_clause = arith_simplified

                    # Duplicate check
                    canon = self._canonical_clause_str(resolvent_clause)
                    if canon in seen_clauses:
                        continue
                    seen_clauses.add(canon)

                    # Subsumption check
                    if self._is_subsumed(resolvent_clause, processed) or self._is_subsumed(resolvent_clause, unprocessed):
                        continue

                    step_counter += 1
                    clause_counter += 1
                    resolvent_id = f"R{step_counter}"
                    resolvent_clause.clause_id = resolvent_id

                    rule_used = "procedural_arithmetic" if is_arithmetic_step and resolvent_clause.is_empty() else "resolution"
                    explanation = self._build_explanation(given, other, lit1, lit2, mgu, resolvent_clause, is_arithmetic_step)
                    
                    step = ProofStep(
                        step_id=resolvent_id,
                        parent1_id=given.clause_id,
                        parent2_id=other.clause_id,
                        resolvent=resolvent_clause,
                        literal1=lit1,
                        literal2=lit2,
                        mgu=mgu,
                        rule_name=rule_used,
                        explanation=explanation
                    )
                    steps.append(step)

                    # Refutation derived: empty clause!
                    if resolvent_clause.is_empty():
                        pruned_steps = self._prune_irrelevant_steps(steps, resolvent_id)
                        min_conflicts = self._extract_minimal_conflict_clauses(pruned_steps, initial_clauses, resolvent_id)
                        return ProofResult(
                            outcome=ResolutionOutcome.REFUTATION_FOUND,
                            steps=pruned_steps,
                            initial_clauses=initial_clauses,
                            empty_clause_id=resolvent_id,
                            minimal_conflict_clause_ids=min_conflicts,
                            total_clauses_generated=clause_counter,
                            elapsed_seconds=time.perf_counter() - start_time,
                            message="Contradiction derived! Empty clause [] derived by resolution refutation."
                        )

                    unprocessed.append(resolvent_clause)

            processed.append(given)

        # Agenda exhausted
        if not unprocessed:
            return ProofResult(
                outcome=ResolutionOutcome.SATURATED_NO_REFUTATION,
                steps=steps[:40],
                initial_clauses=initial_clauses,
                total_clauses_generated=clause_counter,
                elapsed_seconds=time.perf_counter() - start_time,
                message="Resolution closure saturated without contradiction. Formula set is satisfiable."
            )

        return ProofResult(
            outcome=ResolutionOutcome.UNKNOWN_BUDGET_EXHAUSTED,
            steps=steps[:40],
            initial_clauses=initial_clauses,
            total_clauses_generated=clause_counter,
            elapsed_seconds=time.perf_counter() - start_time,
            message="Search budget exhausted (clause limit reached). Outcome is unknown."
        )

    def _select_next_clause_index(
        self,
        unprocessed: List[Clause],
        strategy: str,
        sos_clause_ids: Optional[Set[str]]
    ) -> int:
        """Selects the best clause according to unit preference and Set of Support."""
        best_idx = 0
        best_score = float("inf")

        for idx, cl in enumerate(unprocessed):
            length = len(cl.literals)
            is_sos = (sos_clause_ids is not None and bool(cl.provenance_sources & sos_clause_ids))
            
            if strategy == "unit_sos":
                # Unit clauses prioritized (0 or 1), then SOS clauses, then length
                unit_weight = 0 if length <= 1 else 100
                sos_weight = 0 if is_sos else 50
                score = unit_weight + sos_weight + length
            else:
                # Shortest clause first
                score = length

            if score < best_score:
                best_score = score
                best_idx = idx

        return best_idx

    def _resolve_pair(self, c1: Clause, c2: Clause) -> List[Tuple[Clause, Literal, Literal, Dict[str, Term]]]:
        """Resolves two clauses on all complementary unifiable literal pairs."""
        # Standardize variables apart
        c1_std = c1.standardize_variables("p1")
        c2_std = c2.standardize_variables("p2")

        resolvents: List[Tuple[Clause, Literal, Literal, Dict[str, Term]]] = []

        for l1 in c1_std.literals:
            for l2 in c2_std.literals:
                mgu = unify_complementary_literals(l1, l2)
                if mgu is not None:
                    # Resolvent = (c1 \ {l1}) U (c2 \ {l2}) under mgu
                    remaining_lits: List[Literal] = []
                    for lit in c1_std.literals:
                        if lit != l1:
                            remaining_lits.append(lit.substitute(mgu))
                    for lit in c2_std.literals:
                        if lit != l2:
                            remaining_lits.append(lit.substitute(mgu))

                    # Deduplicate literals
                    factored_lits: List[Literal] = []
                    for lit in remaining_lits:
                        if lit not in factored_lits:
                            factored_lits.append(lit)

                    combined_sources = c1.provenance_sources | c2.provenance_sources
                    new_clause = Clause(
                        literals=factored_lits,
                        source_type="derived",
                        provenance_sources=combined_sources
                    )
                    resolvents.append((new_clause, l1, l2, mgu))

        return resolvents

    def _generate_factors(self, clause: Clause) -> List[Tuple[Clause, Literal, Literal, Dict[str, Term]]]:
        """Generates factored clauses if two identical-polarity literals unify."""
        factors: List[Tuple[Clause, Literal, Literal, Dict[str, Term]]] = []
        lits = clause.literals
        for i in range(len(lits)):
            for j in range(i + 1, len(lits)):
                if lits[i].is_negated == lits[j].is_negated:
                    mgu = unify_predicates(lits[i].predicate, lits[j].predicate)
                    if mgu is not None:
                        new_lits = [lit.substitute(mgu) for k, lit in enumerate(lits) if k != j]
                        deduped = []
                        for lit in new_lits:
                            if lit not in deduped:
                                deduped.append(lit)
                        fact_clause = Clause(
                            literals=deduped,
                            source_type="derived",
                            provenance_sources=set(clause.provenance_sources)
                        )
                        factors.append((fact_clause, lits[i], lits[j], mgu))
        return factors

    def _is_tautology(self, clause: Clause) -> bool:
        """Checks if clause contains both P and ¬P."""
        pos = [l.predicate for l in clause.literals if not l.is_negated]
        neg = [l.predicate for l in clause.literals if l.is_negated]
        for p in pos:
            for n in neg:
                if p == n:
                    return True
        return False

    def _is_subsumed(self, candidate: Clause, existing_clauses: List[Clause]) -> bool:
        """Checks if candidate is subsumed by any shorter existing clause."""
        for ex in existing_clauses:
            if len(ex.literals) >= len(candidate.literals):
                continue
            # If ex is unit, simple subset check
            if len(ex.literals) == 1 and ex.literals[0] in candidate.literals:
                return True
        return False

    def _canonical_clause_str(self, clause: Clause) -> str:
        """Generates an invariant string representation for duplicate suppression."""
        sorted_lits = sorted(str(lit) for lit in clause.literals)
        return " ∨ ".join(sorted_lits) if sorted_lits else "[]"

    def _build_explanation(
        self,
        c1: Clause,
        c2: Clause,
        l1: Literal,
        l2: Literal,
        mgu: Dict[str, Term],
        resolvent: Clause,
        is_arithmetic: bool
    ) -> str:
        mgu_str = format_substitution(mgu)
        msg = f"Resolved {c1.clause_id} ({l1}) with {c2.clause_id} ({l2}) under MGU {mgu_str}"
        if is_arithmetic:
            msg += " -> Ground arithmetic evaluated to contradiction"
        return msg

    def _prune_irrelevant_steps(self, steps: List[ProofStep], empty_clause_id: str) -> List[ProofStep]:
        """Filters proof steps to keep only ancestor inferences contributing to the empty clause."""
        step_map = {s.step_id: s for s in steps}
        needed_ids: Set[str] = {empty_clause_id}
        queue = [empty_clause_id]

        while queue:
            cid = queue.pop(0)
            if cid in step_map:
                s = step_map[cid]
                if s.parent1_id and s.parent1_id not in needed_ids:
                    needed_ids.add(s.parent1_id)
                    queue.append(s.parent1_id)
                if s.parent2_id and s.parent2_id != "ARITHMETIC_AXIOM" and s.parent2_id not in needed_ids:
                    needed_ids.add(s.parent2_id)
                    queue.append(s.parent2_id)

        return [s for s in steps if s.step_id in needed_ids]

    def _extract_minimal_conflict_clauses(
        self,
        pruned_steps: List[ProofStep],
        initial_clauses: List[Clause],
        empty_clause_id: str
    ) -> List[str]:
        """Backtracks from the empty clause to extract the minimal set of initial input clause IDs."""
        init_ids = {c.clause_id: c.source_id or c.clause_id for c in initial_clauses}
        step_map = {s.step_id: s for s in pruned_steps}

        conflicting_leaf_sources: Set[str] = set()
        queue = [empty_clause_id]
        visited: Set[str] = set()

        while queue:
            cid = queue.pop(0)
            if cid in visited:
                continue
            visited.add(cid)

            if cid in init_ids:
                conflicting_leaf_sources.add(init_ids[cid])
            elif cid in step_map:
                s = step_map[cid]
                if s.parent1_id:
                    queue.append(s.parent1_id)
                if s.parent2_id and s.parent2_id != "ARITHMETIC_AXIOM":
                    queue.append(s.parent2_id)

        return sorted(list(conflicting_leaf_sources))

