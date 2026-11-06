import { useState } from 'react';
import type { ClauseIR, Finding } from '../types';
import { Search, FileText } from 'lucide-react';
import { cn } from '../lib/utils';

interface ClauseNavigatorProps {
  clauses: ClauseIR[];
  findings: Finding[];
  selectedClauseId: string | null;
  onSelectClause: (clauseId: string) => void;
}

export const ClauseNavigator = ({
  clauses,
  findings,
  selectedClauseId,
  onSelectClause,
}: ClauseNavigatorProps) => {
  const [filter, setFilter] = useState<'all' | 'conflicts' | 'risks' | 'clean'>('all');
  const [searchTerm, setSearchTerm] = useState('');

  // Map each clause to its findings
  const clauseFindingsMap = new Map<string, Finding[]>();
  findings.forEach(f => {
    f.affected_clause_ids.forEach(cid => {
      const arr = clauseFindingsMap.get(cid) || [];
      arr.push(f);
      clauseFindingsMap.set(cid, arr);
    });
  });

  const getClauseStatus = (clauseId: string): 'conflict' | 'risk' | 'clean' => {
    const list = clauseFindingsMap.get(clauseId) || [];
    if (list.some(f => f.kind === 'conflict')) return 'conflict';
    if (list.some(f => f.kind === 'legal_risk' || f.kind === 'missing')) return 'risk';
    return 'clean';
  };

  const filteredClauses = clauses.filter(c => {
    const status = getClauseStatus(c.id);
    if (filter === 'conflicts' && status !== 'conflict') return false;
    if (filter === 'risks' && status !== 'risk') return false;
    if (filter === 'clean' && status !== 'clean') return false;

    if (searchTerm.trim()) {
      const q = searchTerm.toLowerCase();
      const matchId = c.id.toLowerCase().includes(q);
      const matchText = c.text.toLowerCase().includes(q);
      const matchAction = c.action.toLowerCase().includes(q);
      return matchId || matchText || matchAction;
    }
    return true;
  });

  return (
    <aside className="w-80 shrink-0 border-r border-border bg-surface flex flex-col h-full overflow-hidden select-none">
      {/* Header & Search */}
      <div className="p-3 border-b border-border bg-surface-elevated/40 space-y-2">
        <div className="flex items-center justify-between text-xs font-semibold text-foreground">
          <div className="flex items-center space-x-1.5">
            <FileText className="w-3.5 h-3.5 text-primary" />
            <span>Clause Navigator</span>
          </div>
          <span className="font-mono text-[10px] text-foreground-muted px-1.5 py-0.5 rounded bg-surface border border-border">
            {filteredClauses.length} / {clauses.length}
          </span>
        </div>

        {/* Search Input */}
        <div className="relative">
          <Search className="w-3.5 h-3.5 text-foreground-muted absolute left-2.5 top-2" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Filter clauses..."
            className="w-full bg-surface border border-border rounded-md pl-8 pr-2.5 py-1 text-xs focus:outline-none focus:border-primary placeholder:text-foreground-muted"
          />
        </div>

        {/* Filter Pills */}
        <div className="flex items-center space-x-1 pt-1 text-[11px]">
          {(['all', 'conflicts', 'risks', 'clean'] as const).map(tab => (
            <button
              key={tab}
              onClick={() => setFilter(tab)}
              className={cn(
                'px-2 py-0.5 rounded text-xs capitalize transition-colors',
                filter === tab
                  ? 'bg-primary text-primary-fg font-medium'
                  : 'text-foreground-muted hover:bg-surface hover:text-foreground'
              )}
            >
              {tab === 'all' ? 'All' : tab === 'conflicts' ? 'Contradictions' : tab === 'risks' ? 'Risks' : 'Clean'}
            </button>
          ))}
        </div>
      </div>

      {/* Clause Item List */}
      <div className="flex-1 overflow-y-auto divide-y divide-border/40">
        {filteredClauses.length === 0 ? (
          <div className="p-6 text-center text-xs text-foreground-muted">
            No clauses match the current filter.
          </div>
        ) : (
          filteredClauses.map(clause => {
            const status = getClauseStatus(clause.id);
            const isSelected = selectedClauseId === clause.id;
            const relatedFindings = clauseFindingsMap.get(clause.id) || [];

            return (
              <button
                key={clause.id}
                onClick={() => onSelectClause(clause.id)}
                className={cn(
                  'w-full text-left p-3 transition-colors flex items-start space-x-2.5 relative group',
                  isSelected
                    ? 'bg-primary/10 text-foreground'
                    : 'hover:bg-surface-elevated/60 text-foreground-muted'
                )}
              >
                {/* Active Indicator Bar */}
                {isSelected && (
                  <div className="absolute left-0 top-0 bottom-0 w-1 bg-primary rounded-r" />
                )}

                {/* Status Dot */}
                <div className="pt-0.5 shrink-0">
                  {status === 'conflict' ? (
                    <span className="w-2.5 h-2.5 rounded-full bg-rose-500 inline-block shadow-[0_0_8px_rgba(236,72,153,0.6)]" title="Formal Contradiction Proved" />
                  ) : status === 'risk' ? (
                    <span className="w-2.5 h-2.5 rounded-full bg-amber-500 inline-block" title="Legal Risk / Unfair Term" />
                  ) : (
                    <span className="w-2.5 h-2.5 rounded-full bg-emerald-500/60 inline-block" title="No violations detected" />
                  )}
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between text-xs mb-0.5">
                    <span className={cn(
                      'font-mono font-semibold',
                      isSelected ? 'text-primary' : 'text-foreground'
                    )}>
                      {clause.id}
                    </span>
                    <span className="text-[10px] uppercase font-mono px-1 py-0.2 rounded bg-surface border border-border text-foreground-muted">
                      {clause.action}
                    </span>
                  </div>

                  <p className="text-[11px] line-clamp-2 leading-relaxed text-foreground-muted group-hover:text-foreground">
                    {clause.text.trim()}
                  </p>

                  {/* Findings count badge if any */}
                  {relatedFindings.length > 0 && (
                    <div className="mt-1.5 flex items-center space-x-1.5 text-[10px]">
                      {relatedFindings.some(f => f.kind === 'conflict') && (
                        <span className="text-rose-600 dark:text-rose-400 font-semibold bg-rose-500/10 px-1 rounded border border-rose-500/20">
                          Contradiction
                        </span>
                      )}
                      {relatedFindings.filter(f => f.kind !== 'conflict').length > 0 && (
                        <span className="text-amber-600 dark:text-amber-400 font-medium bg-amber-500/10 px-1 rounded border border-amber-500/20">
                          {relatedFindings.filter(f => f.kind !== 'conflict').length} warning(s)
                        </span>
                      )}
                    </div>
                  )}
                </div>
              </button>
            );
          })
        )}
      </div>
    </aside>
  );
};
