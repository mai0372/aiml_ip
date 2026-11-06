# Architectural & Technical Decisions (ADR)

This document records the architectural decisions, trade-offs, and defaults adopted in **ClauseLens**.

---

### ADR-01: Pure-Python First-Order Logic Engine (No External Solvers)
- **Context**: ClauseLens serves as the formal core for an AI/ML course Module II ("Logic-Based Contract Compliance Engine"), covering knowledge representation, FOPL, WFF to CNF, and resolution refutation.
- **Decision**: Implement the entire logical pipeline (Lexer, Recursive-Descent Parser, 9-step CNF converter, Robinson Unifier with Occurs Check, and Resolution Refutation prover) from scratch in pure Python without external theorem proving packages (no Z3, PySMT, or SymPy logic).
- **Justification**:
  1. Complete control over step recording for the Logic Lab UI.
  2. Direct extraction of the minimal conflicting clause set from the refutation DAG.
  3. Strict alignment with academic Module II evaluation criteria.
- **Risk**: Python-level resolution loops can be slower than compiled C/C++ solvers. Mitigated by indexing, unit preference, set-of-support pruning, tautology elimination, and strict clause/term depth bounds.

---

### ADR-02: Procedural Attachment for Numeric Comparisons
- **Context**: Rental agreements constantly condition obligations on numbers (e.g. `LessThan(notice_days, 90)` or `GreaterThan(deposit_months, 2)`). Standard FOPL handles arithmetic awkwardly via Peano induction (causing exponential combinatorial explosion).
- **Decision**: Provide procedural attachments for arithmetic predicates (`LessThan`, `GreaterThan`, `Equals`). When both arguments are ground numeric constants, the engine evaluates the relation immediately during inference:
  - If true, `~LessThan(30, 90)` simplifies to contradiction; `LessThan(30, 90)` resolves out.
  - If false, the literal is reduced directly according to refutation semantics.
- **Justification**: Avoids infinite resolution branches on numeric terms while retaining pure FOPL unification for non-ground variables.
- **Risk**: Non-ground numeric terms must be bound before procedural evaluation occurs. Documented in the Logic Engine specification.

---

### ADR-03: Honest Tri-State Refutation Semantics
- **Context**: Non-negotiable Rule 3 prohibits ever claiming a contract is "consistent" or "compliant" because first-order logic is semi-decidable.
- **Decision**: The resolution engine returns one of three explicit outcomes:
  1. `REFUTATION_FOUND`: Contradiction proven; minimal conflicting set identified.
  2. `SATURATED_NO_REFUTATION`: Search space fully closed without contradiction (valid for finite propositions).
  3. `UNKNOWN_BUDGET_EXHAUSTED`: Search terminated due to clause budget or timeout limit.
- **Justification**: Ensures epistemological honesty; UI reflects this without false certainty.

---

### ADR-04: Offline-First Architecture with Optional Gemini LLM Provider
- **Context**: The product must run and demo seamlessly out of the box with zero internet access, zero API keys, and zero external costs, while also offering advanced LLM capabilities when a key is provided.
- **Decision**: Build a pluggable `LLMProvider` abstraction. Default to an offline, deterministic regex-and-lexical extractor mapping to the action ontology. When `GEMINI_API_KEY` is present and `LLM_PROVIDER=gemini`, use the modern `google-genai` SDK.
- **UI Exposure**: The current mode (`Offline (Deterministic)` vs `Gemini Live`) is clearly badged in the navigation header.

---

### ADR-05: Indian Legal Tenancy Context & Source-Verifiability
- **Context**: Residential tenancy in India is governed by a combination of Central statutes, model laws, and state enactments.
- **Decision**:
  1. Seed rules reference official statutes: Model Tenancy Act 2021, Transfer of Property Act 1882 (s. 106), and Indian Contract Act 1872 (s. 74).
  2. Every rule in `in_residential_generic.yaml` includes metadata fields: `statute_name`, `section`, `source_text`, `source_url`, `applicability`, `reviewed: false`.
  3. `source_text` is left empty for unverified rules so that no statute text is invented or hallucinated.
  4. The UI displays an "Unreviewed rule" badge for any rule where `reviewed: false` or `source_text` is empty, ensuring ethical compliance and legal accuracy.
  5. State variation notes explicitly warn that Model Tenancy Act provisions apply only in states that have enacted corresponding legislation.

---

### ADR-06: Decoupled Multi-Layer Verification
- **Context**: Modern LLMs suffer from hallucinations, missed numbers, and invented facts.
- **Decision**: Three strictly decoupled verifiers:
  1. **Extraction Verifier**: Dual-pass independent extraction diff + pure-code grounding validator (verifying that every number and action keyword appears in the raw clause text).
  2. **Proof Verifier (`proof_checker.py`)**: Independently re-checks resolution proof DAGs step by step without importing prover inference code.
  3. **Explanation Verifier**: Checks that generated summaries cite only real clauses and reproduce verbatim quotes without hallucinating legal provisions.

---

### ADR-07: Design System & Visual Restraint
- **Context**: Taste references: Spellbook, Ironclad, Raycast, Supabase. Legal software demands calm, density, and clarity over flashy trends.
- **Decision**:
  - Palette: Zinc/stone neutrals, warm off-white in light mode (`#FAFAF9`), deep charcoal in dark mode (`#0A0A0B`).
  - Single restrained accent: Deep ink blue / slate teal.
  - Typography: Inter for UI chrome, JetBrains Mono for formal logic, Source Serif 4 / Georgia for document reading.
  - Custom SVG proof tree visualization for inspectable, lightweight resolution DAGs.

