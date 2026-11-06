import { useRef, useEffect } from 'react';
import type { ClauseIR, Finding, Severity } from '../types';
import { cn } from '../lib/utils';
import { AlertTriangle, ShieldAlert } from 'lucide-react';

interface DocumentReaderProps {
  clauses: ClauseIR[];
  findings: Finding[];
  selectedClauseId: string | null;
  onSelectClause: (clauseId: string) => void;
  cleanText?: string;
}

export const DocumentReader = ({
  clauses,
  findings,
  selectedClauseId,
  onSelectClause,
}: DocumentReaderProps) => {
  const clauseRefs = useRef<Map<string, HTMLDivElement>>(new Map());

  // Scroll to selected clause
  useEffect(() => {
    if (selectedClauseId && clauseRefs.current.has(selectedClauseId)) {
      const el = clauseRefs.current.get(selectedClauseId);
      el?.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  }, [selectedClauseId]);

  // Map clause ID to highest severity finding
  const clauseFindingSeverity = new Map<string, 'conflict' | Severity>();
  findings.forEach(f => {
    f.affected_clause_ids.forEach(cid => {
      const current = clauseFindingSeverity.get(cid);
      if (f.kind === 'conflict') {
        clauseFindingSeverity.set(cid, 'conflict');
      } else if (!current || current === 'low') {
        clauseFindingSeverity.set(cid, f.severity);
      }
    });
  });

  return (
    <div className="flex-1 bg-surface flex flex-col h-full overflow-hidden">
      {/* Top Banner / Breadcrumb */}
      <div className="px-6 py-2.5 border-b border-border bg-surface-elevated/20 flex items-center justify-between text-xs text-foreground-muted select-none">
        <div className="flex items-center space-x-2">
          <span className="font-medium text-foreground">Document Reading View</span>
          <span>&middot;</span>
          <span className="font-serif italic">Indian Residential Tenancy Agreement</span>
        </div>
        <div className="flex items-center space-x-3 text-[11px]">
          <span className="flex items-center space-x-1">
            <span className="w-2 h-2 rounded-full bg-rose-500 inline-block" />
            <span>Contradiction</span>
          </span>
          <span className="flex items-center space-x-1">
            <span className="w-2 h-2 rounded-full bg-amber-500 inline-block" />
            <span>Legal Risk</span>
          </span>
          <span className="flex items-center space-x-1">
            <span className="w-2 h-2 rounded-full bg-emerald-500 inline-block" />
            <span>Clean</span>
          </span>
        </div>
      </div>

      {/* Contract Scrolling Content */}
      <div className="flex-1 overflow-y-auto px-8 py-8 max-w-4xl mx-auto w-full">
        <div className="space-y-6">
          {clauses.map((clause) => {
            const isSelected = selectedClauseId === clause.id;
            const severity = clauseFindingSeverity.get(clause.id);
            const relatedFindings = findings.filter(f => f.affected_clause_ids.includes(clause.id));

            return (
              <div
                key={clause.id}
                ref={(el) => {
                  if (el) clauseRefs.current.set(clause.id, el);
                  else clauseRefs.current.delete(clause.id);
                }}
                onClick={() => onSelectClause(clause.id)}
                className={cn(
                  'group relative rounded-lg p-4 transition-all duration-150 cursor-pointer border',
                  isSelected
                    ? 'ring-2 ring-primary ring-offset-2 ring-offset-background border-primary/40 bg-primary/[0.03]'
                    : severity === 'conflict'
                    ? 'border-rose-500/30 bg-rose-500/[0.04] hover:bg-rose-500/[0.08]'
                    : severity === 'high' || severity === 'medium'
                    ? 'border-amber-500/30 bg-amber-500/[0.04] hover:bg-amber-500/[0.08]'
                    : 'border-transparent hover:border-border hover:bg-surface-elevated/40'
                )}
              >
                {/* Clause Header Label with Tooltip Info */}
                <div className="flex items-center justify-between mb-2 select-none">
                  <div className="flex items-center space-x-2">
                    <span className="font-mono text-xs font-bold text-primary">
                      {clause.id}
                    </span>
                    {clause.raw_number && (
                      <span className="text-xs text-foreground-muted">
                        ({clause.raw_number})
                      </span>
                    )}

                    {/* Severity Badge */}
                    {severity === 'conflict' ? (
                      <span className="flex items-center space-x-1 px-1.5 py-0.2 rounded bg-rose-500/10 text-rose-600 dark:text-rose-400 border border-rose-500/20 text-[10px] font-semibold">
                        <ShieldAlert className="w-3 h-3" />
                        <span>Contradiction Proved</span>
                      </span>
                    ) : severity ? (
                      <span className="flex items-center space-x-1 px-1.5 py-0.2 rounded bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20 text-[10px] font-medium">
                        <AlertTriangle className="w-3 h-3" />
                        <span>Statutory Alert</span>
                      </span>
                    ) : (
                      <span className="text-[10px] text-emerald-600 dark:text-emerald-400 font-mono">
                        &check; Verified
                      </span>
                    )}
                  </div>

                  {/* IR Hover Metadata Summary Pill */}
                  <div className="hidden group-hover:flex items-center space-x-2 font-mono text-[10px] text-foreground-muted bg-surface-elevated px-2 py-0.5 rounded border border-border">
                    <span>Party: <b className="text-foreground">{clause.party}</b></span>
                    <span>&middot;</span>
                    <span>Modal: <b className="text-foreground">{clause.modality}</b></span>
                    <span>&middot;</span>
                    <span>Action: <b className="text-foreground">{clause.action}</b></span>
                  </div>
                </div>

                {/* Serif Contract Clause Body */}
                <div className="font-serif text-[15px] leading-relaxed text-foreground/90 whitespace-pre-wrap">
                  {clause.text}
                </div>

                {/* Inline Evidence Highlight Banner if findings exist */}
                {relatedFindings.length > 0 && (
                  <div className="mt-3 pt-2.5 border-t border-border/40 space-y-1.5">
                    {relatedFindings.map(f => (
                      <div
                        key={f.id}
                        className={cn(
                          'text-xs px-2.5 py-1.5 rounded-md flex items-start space-x-2',
                          f.kind === 'conflict'
                            ? 'bg-rose-500/10 text-rose-700 dark:text-rose-300 border border-rose-500/20'
                            : 'bg-amber-500/10 text-amber-700 dark:text-amber-300 border border-amber-500/20'
                        )}
                      >
                        {f.kind === 'conflict' ? (
                          <ShieldAlert className="w-3.5 h-3.5 shrink-0 mt-0.5 text-rose-600" />
                        ) : (
                          <AlertTriangle className="w-3.5 h-3.5 shrink-0 mt-0.5 text-amber-600" />
                        )}
                        <div className="flex-1">
                          <span className="font-semibold">{f.title}:</span>{' '}
                          <span>{f.plain_explanation}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
