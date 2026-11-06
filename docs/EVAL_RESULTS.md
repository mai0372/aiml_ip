# ClauseLens Evaluation & Benchmark Report

**Date:** 2026-11-06 15:37:13 UTC  
**Evaluation Environment:** Local CPU, Deterministic Offline Mode (zero network dependency)

## 1. Executive Summary Table

| Dataset / Sample | Clauses | Expected | Seg. Acc | Found Conflicts | Expected Conflicts | Conflict Precision | Conflict Recall | Rule Recall | Total Latency |
|---|---|---|---|---|---|---|---|---|---|
| `sample_a_fair.txt` | 7 | 7 | 100.0% | 0 | 0 | 100.0% | 100.0% | 100.0% | 5.53 ms |
| `sample_b_problematic.txt` | 16 | 16 | 100.0% | 2 | 2 | 100.0% | 100.0% | 100.0% | 13.1 ms |
| `sample_c_messy.txt` | 8 | 8 | 100.0% | 0 | 0 | 100.0% | 100.0% | 100.0% | 2.88 ms |

## 2. Adversarial Verifier Integrity Test (5 Injected Corruptions)

**Target:** 5/5 Caught (100.0%)  
**Actual Catch Rate:** 5/5 (100.0%)

| Test Case | Corruption Type | Caught? | Independent Verifier Finding |
|---|---|---|---|
| Corruption 1: Flipped Party (tenant -> landlord) | Adversarial | **PASS (Caught)** | `Party 'landlord' ungrounded in clause text.; Party mismatch: landlord vs tenant` |
| Corruption 2: Altered Notice Days (30 -> 999) | Adversarial | **PASS (Caught)** | `Notice days '999' ungrounded in text` |
| Corruption 3: Fabricated Statute Citation ('Indian Martian Tenancy Code 2099') | Adversarial | **PASS (Caught)** | `Unrecognized or unverified statute citation: 'Indian Martian Tenancy Code 2099'` |
| Corruption 4: Modified Evidence Quote (non-verbatim string) | Adversarial | **PASS (Caught)** | `Evidence quote was not verbatim substring; adjusted to literal segment.` |
| Corruption 5: Inverted Modality (prohibition -> permission) | Adversarial | **PASS (Caught)** | `Modality mismatch: permission vs prohibition` |

## 3. Pipeline Latency Breakdown (Per-Stage Average on CPU)

| Stage | Name | Latency (ms) | Notes |
|---|---|---|---|
| `ingest` | Ingest Stage | 0.00 ms | Verified deterministic execution |
| `segment` | Segment Stage | 1.00 ms | Verified deterministic execution |
| `extract` | Extract Stage | 1.00 ms | Verified deterministic execution |
| `verify_extraction` | Verify_extraction Stage | 0.00 ms | Verified deterministic execution |
| `translate` | Translate Stage | 2.00 ms | Verified deterministic execution |
| `reason` | Reason Stage | 5.00 ms | Verified deterministic execution |
| `retrieve_rules` | Retrieve_rules Stage | 0.00 ms | Verified deterministic execution |
| `explain` | Explain Stage | 0.00 ms | Verified deterministic execution |
| **Total Pipeline** | Full End-to-End | **13.10 ms** | Well below 5000 ms budget (< 0.2s) |

## 4. Acceptance Criteria Verification

- **Conflict Precision & Recall = 100%:** PASSED
- **Adversarial Verifier Catch Rate = 100% (5/5):** PASSED
- **Offline Latency Budget (< 5.0s on CPU):** PASSED