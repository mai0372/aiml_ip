import { useState, useEffect } from 'react';
import { Search, Scale, FileText, FlaskConical, BookOpen, History, ShieldAlert, ArrowRight, X } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import type { ClauseIR, Finding } from '../types';

interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
  clauses?: ClauseIR[];
  findings?: Finding[];
  onSelectClause?: (clauseId: string) => void;
  onSelectFinding?: (findingId: string) => void;
  onRunWhatIf?: (question: string) => void;
}

export const CommandPalette = ({
  isOpen,
  onClose,
  clauses = [],
  findings = [],
  onSelectClause,
  onSelectFinding,
  onRunWhatIf,
}: CommandPaletteProps) => {
  const [query, setQuery] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        if (isOpen) onClose();
      }
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const filteredClauses = clauses.filter(c =>
    c.id.toLowerCase().includes(query.toLowerCase()) ||
    c.text.toLowerCase().includes(query.toLowerCase())
  ).slice(0, 5);

  const filteredFindings = findings.filter(f =>
    f.title.toLowerCase().includes(query.toLowerCase()) ||
    f.plain_explanation.toLowerCase().includes(query.toLowerCase())
  ).slice(0, 5);

  const whatIfPresets = [
    "Can the landlord enter without notice?",
    "How much notice to leave early?",
    "Can the security deposit be forfeited?",
    "Is the landlord responsible for repairs?"
  ].filter(q => q.toLowerCase().includes(query.toLowerCase()));

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-20 px-4 bg-black/50 backdrop-blur-sm animate-in fade-in duration-150">
      <div 
        className="w-full max-w-xl bg-surface border border-border shadow-2xl rounded-xl overflow-hidden flex flex-col text-foreground animate-in zoom-in-95 duration-150"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Search Input Bar */}
        <div className="flex items-center px-4 py-3 border-b border-border bg-surface-elevated/50">
          <Search className="w-4 h-4 text-foreground-muted mr-3 shrink-0" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Type a command, search clauses, or ask a question..."
            className="w-full bg-transparent text-sm focus:outline-none placeholder:text-foreground-muted"
            autoFocus
          />
          <button 
            onClick={onClose}
            className="text-foreground-muted hover:text-foreground p-1 rounded"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Results List */}
        <div className="max-h-96 overflow-y-auto p-2 divide-y divide-border/50 text-xs">
          {/* Quick Navigations */}
          <div className="py-2">
            <div className="text-[10px] uppercase font-bold text-foreground-muted tracking-wider px-2 mb-1.5">
              Pages & Workbenches
            </div>
            <button
              onClick={() => { navigate('/logic-lab'); onClose(); }}
              className="w-full flex items-center justify-between px-2.5 py-1.5 rounded-md hover:bg-primary/10 hover:text-primary transition-colors text-left"
            >
              <div className="flex items-center space-x-2">
                <FlaskConical className="w-4 h-4 text-amber-500" />
                <span className="font-medium">Logic Lab (WFF-to-CNF & Resolution Stepper)</span>
              </div>
              <ArrowRight className="w-3.5 h-3.5 opacity-50" />
            </button>
            <button
              onClick={() => { navigate('/rules'); onClose(); }}
              className="w-full flex items-center justify-between px-2.5 py-1.5 rounded-md hover:bg-primary/10 hover:text-primary transition-colors text-left"
            >
              <div className="flex items-center space-x-2">
                <BookOpen className="w-4 h-4 text-blue-500" />
                <span className="font-medium">Rulebook & Indian Statutory Sources</span>
              </div>
              <ArrowRight className="w-3.5 h-3.5 opacity-50" />
            </button>
            <button
              onClick={() => { navigate('/history'); onClose(); }}
              className="w-full flex items-center justify-between px-2.5 py-1.5 rounded-md hover:bg-primary/10 hover:text-primary transition-colors text-left"
            >
              <div className="flex items-center space-x-2">
                <History className="w-4 h-4 text-emerald-500" />
                <span className="font-medium">Analysis Audit History</span>
              </div>
              <ArrowRight className="w-3.5 h-3.5 opacity-50" />
            </button>
          </div>

          {/* Findings */}
          {filteredFindings.length > 0 && (
            <div className="py-2">
              <div className="text-[10px] uppercase font-bold text-foreground-muted tracking-wider px-2 mb-1.5">
                Audit Findings
              </div>
              {filteredFindings.map((f) => (
                <button
                  key={f.id}
                  onClick={() => { onSelectFinding?.(f.id); onClose(); }}
                  className="w-full flex items-center justify-between px-2.5 py-1.5 rounded-md hover:bg-surface-elevated transition-colors text-left"
                >
                  <div className="flex items-center space-x-2 overflow-hidden">
                    <ShieldAlert className="w-3.5 h-3.5 text-rose-500 shrink-0" />
                    <span className="truncate">{f.title}</span>
                  </div>
                  <span className="font-mono text-[10px] text-foreground-muted shrink-0 ml-2">
                    {f.affected_clause_ids.join(', ')}
                  </span>
                </button>
              ))}
            </div>
          )}

          {/* Clauses */}
          {filteredClauses.length > 0 && (
            <div className="py-2">
              <div className="text-[10px] uppercase font-bold text-foreground-muted tracking-wider px-2 mb-1.5">
                Contract Clauses
              </div>
              {filteredClauses.map((c) => (
                <button
                  key={c.id}
                  onClick={() => { onSelectClause?.(c.id); onClose(); }}
                  className="w-full flex items-center justify-between px-2.5 py-1.5 rounded-md hover:bg-surface-elevated transition-colors text-left"
                >
                  <div className="flex items-center space-x-2 overflow-hidden">
                    <FileText className="w-3.5 h-3.5 text-foreground-muted shrink-0" />
                    <span className="font-mono font-semibold text-[11px] shrink-0">{c.id}:</span>
                    <span className="truncate text-foreground-muted">{c.text.slice(0, 70)}...</span>
                  </div>
                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-surface-elevated text-foreground-muted shrink-0 ml-2">
                    {c.action}
                  </span>
                </button>
              ))}
            </div>
          )}

          {/* Preset What-Ifs */}
          {whatIfPresets.length > 0 && (
            <div className="py-2">
              <div className="text-[10px] uppercase font-bold text-foreground-muted tracking-wider px-2 mb-1.5">
                Ask What-If Questions
              </div>
              {whatIfPresets.map((q, idx) => (
                <button
                  key={idx}
                  onClick={() => { onRunWhatIf?.(q); onClose(); }}
                  className="w-full flex items-center justify-between px-2.5 py-1.5 rounded-md hover:bg-primary/10 hover:text-primary transition-colors text-left"
                >
                  <div className="flex items-center space-x-2">
                    <Scale className="w-3.5 h-3.5 text-primary" />
                    <span>{q}</span>
                  </div>
                  <span className="text-[10px] text-primary font-medium">Test &rarr;</span>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-4 py-2 bg-surface-elevated border-t border-border flex items-center justify-between text-[11px] text-foreground-muted font-mono">
          <span>Navigate with &uarr; &darr; &middot; Esc to close</span>
          <span>ClauseLens Compliance Engine</span>
        </div>
      </div>
    </div>
  );
};
