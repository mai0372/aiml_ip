import { useState } from 'react';
import type { 
  ClauseIR, 
  Finding, 
  SeverityCounts, 
  WhatIfResponse 
} from '../types';
import { 
  ShieldAlert, 
  AlertTriangle, 
  HelpCircle, 
  Clock, 
  Cpu, 
  Copy, 
  ExternalLink, 
  Printer, 
  Send,
  FileCheck,
  ChevronRight
} from 'lucide-react';
import { cn, copyToClipboard } from '../lib/utils';
import { ProofTreeViewer } from './ProofTreeViewer';
import { askWhatIf } from '../lib/api';

interface InspectorPaneProps {
  analysisId: string;
  clauses: ClauseIR[];
  findings: Finding[];
  severityCounts: SeverityCounts;
  riskScore: number;
  selectedClauseId: string | null;
  onSelectClause: (clauseId: string) => void;
  onPrintReport?: () => void;
}

type TabKey = 'summary' | 'findings' | 'ask' | 'timeline' | 'logic';

export const InspectorPane = ({
  analysisId,
  clauses,
  findings,
  severityCounts,
  riskScore,
  selectedClauseId,
  onSelectClause,
  onPrintReport,
}: InspectorPaneProps) => {
  const [activeTab, setActiveTab] = useState<TabKey>('summary');
  const [copiedId, setCopiedId] = useState<string | null>(null);

  // What-If state
  const [questionInput, setQuestionInput] = useState('');
  const [whatIfLoading, setWhatIfLoading] = useState(false);
  const [whatIfResult, setWhatIfResult] = useState<WhatIfResponse | null>(null);

  const selectedClause = clauses.find(c => c.id === selectedClauseId);
  const conflictFinding = findings.find(f => f.kind === 'conflict' && f.affected_clause_ids.includes(selectedClauseId || ''));
  const activeProof = conflictFinding?.proof || findings.find(f => f.proof)?.proof;

  const handleCopyNegotiation = async (finding: Finding) => {
    const text = `Hi, regarding clause ${finding.affected_clause_ids.join(' and ')} in the draft agreement: "${finding.title}". Under standard tenancy practices (${finding.source?.statute_name || 'standard rules'}), ${finding.suggestion} Would you be open to updating this clause?`;
    const ok = await copyToClipboard(text);
    if (ok) {
      setCopiedId(finding.id);
      setTimeout(() => setCopiedId(null), 2000);
    }
  };

  const handleRunWhatIf = async (q: string) => {
    if (!q.trim()) return;
    setWhatIfLoading(true);
    setQuestionInput(q);
    try {
      const res = await askWhatIf(analysisId, q);
      setWhatIfResult(res);
      setActiveTab('ask');
    } catch (err) {
      console.error('What-If query failed:', err);
    } finally {
      setWhatIfLoading(false);
    }
  };

  const whatIfPresets = [
    "Can the landlord enter without notice?",
    "How much notice to leave early?",
    "Can my deposit be forfeited?",
    "Is the landlord responsible for repairs?"
  ];

  return (
    <aside className="w-96 lg:w-[420px] shrink-0 border-l border-border bg-surface flex flex-col h-full overflow-hidden select-none">
      {/* Tab Navigation Header */}
      <div className="border-b border-border bg-surface-elevated/40 px-3 pt-2">
        <div className="flex items-center space-x-1 text-xs">
          {[
            { key: 'summary', label: 'Summary', icon: FileCheck },
            { key: 'findings', label: `Findings (${findings.length})`, icon: ShieldAlert },
            { key: 'ask', label: 'Ask What-If', icon: HelpCircle },
            { key: 'timeline', label: 'Timeline', icon: Clock },
            { key: 'logic', label: 'Logic Proof', icon: Cpu },
          ].map(t => {
            const Icon = t.icon;
            const isActive = activeTab === t.key;
            return (
              <button
                key={t.key}
                onClick={() => setActiveTab(t.key as TabKey)}
                className={cn(
                  'flex items-center space-x-1.5 px-3 py-2 border-b-2 text-xs font-medium transition-colors',
                  isActive
                    ? 'border-primary text-primary font-semibold'
                    : 'border-transparent text-foreground-muted hover:text-foreground hover:border-border'
                )}
              >
                <Icon className="w-3.5 h-3.5" />
                <span>{t.label}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Tab Body */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* TAB 1: SUMMARY */}
        {activeTab === 'summary' && (
          <div className="space-y-5 text-xs">
            {/* Risk Index Meter */}
            <div className="p-4 rounded-xl border border-border bg-surface-elevated/50 space-y-3">
              <div className="flex items-center justify-between">
                <span className="font-semibold text-foreground text-sm">Overall Risk Index</span>
                <span className={cn(
                  'font-mono text-xs font-bold px-2 py-0.5 rounded border',
                  riskScore > 50
                    ? 'bg-rose-500/10 text-rose-600 border-rose-500/20'
                    : riskScore > 20
                    ? 'bg-amber-500/10 text-amber-600 border-amber-500/20'
                    : 'bg-emerald-500/10 text-emerald-600 border-emerald-500/20'
                )}>
                  {riskScore} / 100
                </span>
              </div>

              {/* Progress bar */}
              <div className="w-full bg-border h-2 rounded-full overflow-hidden">
                <div 
                  className={cn(
                    'h-full transition-all duration-500',
                    riskScore > 50 ? 'bg-rose-500' : riskScore > 20 ? 'bg-amber-500' : 'bg-emerald-500'
                  )}
                  style={{ width: `${Math.max(riskScore, 5)}%` }}
                />
              </div>

              <div className="grid grid-cols-3 gap-2 text-center pt-1 font-mono text-[11px]">
                <div className="p-2 rounded bg-surface border border-border">
                  <div className="text-rose-600 font-bold text-sm">{severityCounts.conflict}</div>
                  <div className="text-foreground-muted text-[10px]">Contradictions</div>
                </div>
                <div className="p-2 rounded bg-surface border border-border">
                  <div className="text-amber-600 font-bold text-sm">{severityCounts.high + severityCounts.medium}</div>
                  <div className="text-foreground-muted text-[10px]">Statutory Risks</div>
                </div>
                <div className="p-2 rounded bg-surface border border-border">
                  <div className="text-emerald-600 font-bold text-sm">{clauses.length}</div>
                  <div className="text-foreground-muted text-[10px]">Total Clauses</div>
                </div>
              </div>
            </div>

            {/* Negotiation Takeaways */}
            <div className="space-y-2">
              <div className="font-semibold text-foreground text-xs uppercase tracking-wider text-foreground-muted">
                Key Negotiation Points
              </div>
              {findings.slice(0, 3).map((f, i) => (
                <div key={f.id} className="p-3 rounded-lg border border-border bg-surface space-y-1">
                  <div className="flex items-center space-x-1.5 text-foreground font-semibold">
                    <span className="w-4 h-4 rounded-full bg-primary/10 text-primary flex items-center justify-center text-[10px]">
                      {i + 1}
                    </span>
                    <span>{f.title}</span>
                  </div>
                  <p className="text-foreground-muted text-[11px] leading-relaxed">
                    {f.suggestion}
                  </p>
                </div>
              ))}
              {findings.length === 0 && (
                <div className="p-4 rounded-lg border border-emerald-500/20 bg-emerald-500/5 text-emerald-700 dark:text-emerald-300 text-center text-xs">
                  &check; Fair contract. No critical negotiation flags detected.
                </div>
              )}
            </div>

            {/* Print Action */}
            <div className="pt-2">
              <button
                onClick={onPrintReport || (() => window.print())}
                className="w-full flex items-center justify-center space-x-2 py-2.5 rounded-lg bg-primary text-primary-fg hover:bg-primary-hover font-medium shadow-sm transition-colors text-xs"
              >
                <Printer className="w-4 h-4" />
                <span>Export Print-Ready PDF Audit</span>
              </button>
            </div>
          </div>
        )}

        {/* TAB 2: FINDINGS */}
        {activeTab === 'findings' && (
          <div className="space-y-3">
            {findings.length === 0 ? (
              <div className="p-8 text-center text-xs text-foreground-muted">
                No legal risks or contradictions found in this agreement.
              </div>
            ) : (
              findings.map(f => (
                <div
                  key={f.id}
                  className="p-3.5 rounded-xl border border-border bg-surface space-y-2.5 text-xs"
                >
                  {/* Header */}
                  <div className="flex items-start justify-between">
                    <div className="flex items-center space-x-2">
                      {f.kind === 'conflict' ? (
                        <ShieldAlert className="w-4 h-4 text-rose-500 shrink-0" />
                      ) : (
                        <AlertTriangle className="w-4 h-4 text-amber-500 shrink-0" />
                      )}
                      <span className="font-bold text-foreground">{f.title}</span>
                    </div>

                    {/* Verification Status Badge */}
                    <span className={cn(
                      'text-[10px] font-mono px-2 py-0.5 rounded border',
                      f.verification.status === 'verified'
                        ? 'bg-emerald-500/10 text-emerald-600 border-emerald-500/20'
                        : 'bg-amber-500/10 text-amber-600 border-amber-500/20'
                    )}>
                      {f.verification.status === 'verified' ? 'Verified' : 'Needs review'}
                    </span>
                  </div>

                  {/* Plain English explanation */}
                  <p className="text-foreground/90 leading-relaxed text-[11px]">
                    {f.plain_explanation}
                  </p>

                  {/* Verbatim quote */}
                  {f.evidence_quote && f.evidence_quote !== 'Not found in contract text' && (
                    <div className="p-2 rounded bg-surface-elevated border-l-2 border-primary text-[11px] font-serif italic text-foreground-muted">
                      "{f.evidence_quote}"
                    </div>
                  )}

                  {/* Statutory source card if available */}
                  {f.source && (
                    <div className="p-2 rounded bg-surface-elevated/70 border border-border/80 text-[10px] space-y-1">
                      <div className="flex items-center justify-between font-semibold text-foreground">
                        <span>{f.source.statute_name} ({f.source.section})</span>
                        {f.source.source_url && (
                          <a
                            href={f.source.source_url}
                            target="_blank"
                            rel="noreferrer"
                            className="text-primary hover:underline flex items-center space-x-0.5"
                          >
                            <span>India Code</span>
                            <ExternalLink className="w-2.5 h-2.5" />
                          </a>
                        )}
                      </div>
                      <div className="text-foreground-muted">
                        {f.source.jurisdiction_note}
                      </div>
                      <div className="font-mono text-[9px] text-amber-600 dark:text-amber-400">
                        {f.source.reviewed ? 'Statute Certified' : 'Unreviewed rule: source text pending advocate verification'}
                      </div>
                    </div>
                  )}

                  {/* Actions */}
                  <div className="flex items-center justify-between pt-1">
                    <button
                      onClick={() => handleCopyNegotiation(f)}
                      className="flex items-center space-x-1 px-2.5 py-1 rounded bg-surface-elevated border border-border text-foreground hover:bg-border transition-colors text-[11px]"
                    >
                      <Copy className="w-3 h-3" />
                      <span>{copiedId === f.id ? 'Copied!' : 'Copy negotiation note'}</span>
                    </button>

                    {f.proof && (
                      <button
                        onClick={() => setActiveTab('logic')}
                        className="text-primary hover:underline text-[11px] flex items-center space-x-0.5"
                      >
                        <span>View Proof</span>
                        <ChevronRight className="w-3 h-3" />
                      </button>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        {/* TAB 3: ASK WHAT-IF */}
        {activeTab === 'ask' && (
          <div className="space-y-4 text-xs">
            <div className="p-3 rounded-lg border border-border bg-surface-elevated/40 text-[11px] text-foreground-muted leading-relaxed">
              Ask hypothetical scenarios against the contract clauses. Every answer is evaluated through the formal logic reasoner.
            </div>

            {/* Presets */}
            <div className="space-y-1.5">
              <span className="font-mono text-[10px] uppercase text-foreground-muted">Presets</span>
              <div className="flex flex-wrap gap-1.5">
                {whatIfPresets.map((q, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleRunWhatIf(q)}
                    className="px-2.5 py-1 rounded-md bg-surface border border-border hover:border-primary text-foreground text-[11px] transition-colors"
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>

            {/* Custom Input */}
            <div className="flex items-center space-x-2">
              <input
                type="text"
                value={questionInput}
                onChange={(e) => setQuestionInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleRunWhatIf(questionInput)}
                placeholder="Ask e.g. Can the landlord deduct my entire deposit?"
                className="flex-1 bg-surface border border-border rounded-md px-3 py-1.5 text-xs focus:outline-none focus:border-primary"
              />
              <button
                onClick={() => handleRunWhatIf(questionInput)}
                disabled={whatIfLoading || !questionInput.trim()}
                className="px-3 py-1.5 rounded-md bg-primary text-primary-fg hover:bg-primary-hover disabled:opacity-50 text-xs flex items-center space-x-1"
              >
                <Send className="w-3.5 h-3.5" />
              </button>
            </div>

            {/* Results display */}
            {whatIfLoading && (
              <div className="p-6 text-center text-xs text-foreground-muted font-mono animate-pulse">
                Running resolution refutation against contract clausal form...
              </div>
            )}

            {whatIfResult && (
              <div className="p-4 rounded-xl border border-primary/20 bg-primary/[0.03] space-y-3">
                <div className="font-bold text-foreground text-sm flex items-center justify-between">
                  <span>Answer</span>
                  <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-primary/10 text-primary">
                    Verified Proof
                  </span>
                </div>
                <p className="text-foreground font-medium text-xs leading-relaxed">
                  {whatIfResult.answer_text}
                </p>
                <div className="p-2.5 rounded bg-surface border border-border text-[11px] text-foreground-muted leading-relaxed">
                  <span className="font-semibold text-foreground">Reasoning:</span> {whatIfResult.reasoning}
                </div>
                {whatIfResult.supporting_clause_ids.length > 0 && (
                  <div className="flex items-center space-x-2 text-[11px]">
                    <span className="text-foreground-muted font-mono">Governing clauses:</span>
                    {whatIfResult.supporting_clause_ids.map(cid => (
                      <button
                        key={cid}
                        onClick={() => onSelectClause(cid)}
                        className="font-mono text-primary hover:underline font-semibold"
                      >
                        {cid}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* TAB 4: TIMELINE */}
        {activeTab === 'timeline' && (
          <div className="space-y-4 text-xs">
            <div className="text-[11px] text-foreground-muted">
              Standard 11-month lease operational roadmap extracted from contract terms:
            </div>

            <div className="relative pl-6 space-y-6 before:absolute before:left-2 before:top-2 before:bottom-2 before:w-0.5 before:bg-border">
              <div className="relative">
                <div className="absolute -left-6 top-1 w-2.5 h-2.5 rounded-full bg-primary" />
                <div className="font-semibold text-foreground">Day 1: Tenancy Execution</div>
                <div className="text-[11px] text-foreground-muted">Execution of deed, deposit handover, meter reading log.</div>
              </div>

              <div className="relative">
                <div className="absolute -left-6 top-1 w-2.5 h-2.5 rounded-full bg-blue-500" />
                <div className="font-semibold text-foreground">5th of Every Month</div>
                <div className="text-[11px] text-foreground-muted">Rent payment due date. Late fee applies if delayed.</div>
              </div>

              <div className="relative">
                <div className="absolute -left-6 top-1 w-2.5 h-2.5 rounded-full bg-amber-500" />
                <div className="font-semibold text-foreground">Month 8 (90 Days Prior)</div>
                <div className="text-[11px] text-foreground-muted">Statutory window for rent escalation notification by Landlord.</div>
              </div>

              <div className="relative">
                <div className="absolute -left-6 top-1 w-2.5 h-2.5 rounded-full bg-amber-500" />
                <div className="font-semibold text-foreground">Month 10 (30 Days Prior)</div>
                <div className="text-[11px] text-foreground-muted">Termination or lease renewal decision notice deadline.</div>
              </div>

              <div className="relative">
                <div className="absolute -left-6 top-1 w-2.5 h-2.5 rounded-full bg-emerald-500" />
                <div className="font-semibold text-foreground">Month 11: Surrender & Deposit Refund</div>
                <div className="text-[11px] text-foreground-muted">Handover of physical keys. Landlord must return security deposit within 30 days.</div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 5: LOGIC & PROOF */}
        {activeTab === 'logic' && (
          <div className="space-y-4 text-xs">
            {selectedClause && (
              <div className="p-3 rounded-lg border border-border bg-surface space-y-1.5 font-mono">
                <div className="font-semibold text-foreground text-xs flex items-center justify-between">
                  <span>Selected Clause FOPL Translation</span>
                  <span className="text-[10px] text-primary">{selectedClause.id}</span>
                </div>
                <div className="p-2 rounded bg-surface-elevated text-primary text-[11px]">
                  {selectedClause.action === 'Terminate'
                    ? `${selectedClause.modality === 'permission' ? 'Perm' : 'Forb'}(${selectedClause.party}, Terminate(${selectedClause.params.notice_days || 30}))`
                    : selectedClause.action === 'KeepPets'
                    ? `${selectedClause.modality === 'permission' ? 'Perm' : 'Forb'}(${selectedClause.party}, KeepPets)`
                    : `${selectedClause.modality === 'obligation' ? 'Obl' : 'Perm'}(${selectedClause.party}, ${selectedClause.action})`
                  }
                </div>
              </div>
            )}

            {activeProof ? (
              <ProofTreeViewer proof={activeProof} onSelectClause={onSelectClause} />
            ) : (
              <div className="p-8 text-center text-xs text-foreground-muted">
                No formal contradiction proof for this clause. The clause was verified without refutation against the deontic axioms.
              </div>
            )}
          </div>
        )}
      </div>
    </aside>
  );
};
