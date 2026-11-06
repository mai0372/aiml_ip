/**
 * frontend/src/types/index.ts
 * Shared TypeScript definitions matching backend Pydantic models.
 */

export type Party = 'landlord' | 'tenant' | 'both';
export type Modality = 'obligation' | 'permission' | 'prohibition' | 'right' | 'definition';
export type ClauseType = 
  | 'rent' | 'deposit' | 'term' | 'termination' | 'renewal' 
  | 'entry' | 'repairs' | 'utilities' | 'subletting' 
  | 'rent_increase' | 'lock_in' | 'penalty' | 'registration' | 'misc';

export type ActionOntology =
  | 'PayRent' | 'PayDeposit' | 'RefundDeposit' | 'EnterPremises'
  | 'Terminate' | 'IncreaseRent' | 'Sublet' | 'Repair'
  | 'CutUtilities' | 'ForfeitDeposit' | 'ChargeLateFee' | 'Renew'
  | 'Evict' | 'KeepPets' | 'Other';

export interface ClauseSpan {
  start: number;
  end: number;
}

export interface ClauseParams {
  amount_inr?: number;
  months?: number;
  days?: number;
  notice_days?: number;
  notice_months?: number;
  percent?: number;
  ratio?: number;
  extra?: Record<string, any>;
}

export interface VerificationCheck {
  name: string;
  passed: boolean;
  detail: string;
}

export type VerificationStatus = 'verified' | 'needs_review' | 'disputed';

export interface VerificationResult {
  status: VerificationStatus;
  checks: VerificationCheck[];
}

export interface ClauseIR {
  id: string;
  raw_number?: string;
  text: string;
  span: ClauseSpan;
  clause_type: ClauseType;
  party: Party;
  modality: Modality;
  action: ActionOntology;
  params: ClauseParams;
  conditions: string[];
  exceptions: string[];
  evidence_quote: string;
  confidence: number;
  verification?: VerificationResult;
}

export type FindingKind = 'conflict' | 'legal_risk' | 'advisory' | 'missing';
export type Severity = 'high' | 'medium' | 'low' | 'info';

export interface StatutorySource {
  statute_name: string;
  section: string;
  source_text: string;
  source_url: string;
  retrieved_on?: string;
  reviewed: boolean;
  reviewed_by?: string;
  reviewed_on?: string;
  applicability: string;
  jurisdiction_note: string;
}

export interface ResolutionStep {
  clause_id: string;
  literals: string[];
  parents?: string[];
  resolved_on?: string;
  unifier?: Record<string, string>;
  source_id?: string;
  source_type?: string;
}

export interface ProofTree {
  outcome: 'REFUTATION_FOUND' | 'SATURATED_NO_REFUTATION' | 'UNKNOWN_BUDGET_EXHAUSTED';
  success: boolean;
  total_clauses: number;
  steps: ResolutionStep[];
  empty_clause_id?: string;
  conflicting_clause_ids?: string[];
  duration_ms: number;
  arithmetic_evaluations: number;
}

export interface Finding {
  id: string;
  kind: FindingKind;
  severity: Severity;
  title: string;
  plain_explanation: string;
  why_it_matters: string;
  evidence_quote: string;
  suggestion: string;
  affected_clause_ids: string[];
  rule_id?: string;
  source?: StatutorySource;
  verification: VerificationResult;
  proof?: ProofTree;
}

export interface SeverityCounts {
  high: number;
  medium: number;
  low: number;
  info: number;
  conflict: number;
}

export interface AnalysisPayload {
  clean_text: string;
  clauses: ClauseIR[];
  findings: Finding[];
  severity_counts: SeverityCounts;
  risk_score: number;
  pii_redacted: boolean;
  llm_mode: string;
}

export interface AnalysisRecordSummary {
  id: string;
  created_at: string;
  filename: string;
  risk_score: number;
  clauses_count: number;
  findings_count: number;
  severity_counts: SeverityCounts;
  llm_mode: string;
}

export interface PipelineEventData {
  stage: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  duration_ms: number;
  detail: string;
  payload?: AnalysisPayload;
}

export interface RuleCatalogItem {
  id: string;
  title: string;
  kind: string;
  severity: string;
  formal_condition: string;
  target_clause_types: string[];
  plain_explanation: string;
  why_it_matters: string;
  suggestion: string;
  source: string;
  statute_name: string;
  section: string;
  source_text: string;
  source_url: string;
  retrieved_on: string;
  reviewed: boolean;
  reviewed_by?: string;
  applicability: string;
  jurisdiction_note: string;
}

export interface WhatIfResponse {
  question: string;
  answered: boolean;
  answer_text: string;
  reasoning: string;
  supporting_clause_ids: string[];
  proof?: ProofTree;
}

export interface LogicStep {
  step_number: number;
  step_name: string;
  description: string;
  formula: string;
}

export interface LogicConvertResponse {
  formula: string;
  ast: Record<string, any>;
  steps: LogicStep[];
  clauses: Array<{ id: string; literals: string[]; source_id: string }>;
}
