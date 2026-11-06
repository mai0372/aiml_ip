import { useState, useEffect } from 'react';
import type { AnalysisRecordSummary } from '../types';
import { listAnalyses } from '../lib/api';
import { History, FileText, ArrowRight, Clock } from 'lucide-react';
import { cn } from '../lib/utils';
import { useNavigate } from 'react-router-dom';

interface HistoryPageProps {
  onLoadAnalysis?: (id: string) => void;
}

export const HistoryPage = ({ onLoadAnalysis }: HistoryPageProps) => {
  const [records, setRecords] = useState<AnalysisRecordSummary[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    listAnalyses()
      .then(res => setRecords(res))
      .catch(err => console.error('Failed to load history:', err))
      .finally(() => setIsLoading(false));
  }, []);

  return (
    <div className="flex-1 overflow-y-auto p-6 sm:p-10 max-w-5xl mx-auto w-full space-y-8 select-none">
      {/* Header */}
      <div className="space-y-2">
        <div className="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-600 dark:text-emerald-400 text-xs font-semibold">
          <History className="w-3.5 h-3.5" />
          <span>Persistent SQLite Audit Trail</span>
        </div>
        <h1 className="text-3xl font-extrabold tracking-tight text-foreground">
          Analysis History & Audit Archive
        </h1>
        <p className="text-sm text-foreground-muted max-w-2xl leading-relaxed">
          Review previously analyzed contracts, inspect proved contradictions, and reopen full document reading sessions.
        </p>
      </div>

      {/* History List */}
      <div className="border border-border rounded-2xl bg-surface overflow-hidden divide-y divide-border/50 shadow-sm">
        {isLoading ? (
          <div className="p-12 text-center text-xs text-foreground-muted font-mono animate-pulse">
            Loading audit history from SQLite database...
          </div>
        ) : records.length === 0 ? (
          <div className="p-12 text-center text-xs text-foreground-muted space-y-2">
            <div>No previous analyses found in database.</div>
            <button
              onClick={() => navigate('/')}
              className="text-primary hover:underline font-semibold"
            >
              Analyze a sample contract now &rarr;
            </button>
          </div>
        ) : (
          records.map((rec) => (
            <div
              key={rec.id}
              className="p-4 sm:p-5 flex items-center justify-between hover:bg-surface-elevated/40 transition-colors"
            >
              <div className="flex items-start space-x-3.5">
                <div className="p-2.5 rounded-xl bg-surface-elevated border border-border text-foreground shrink-0 mt-0.5">
                  <FileText className="w-5 h-5 text-primary" />
                </div>
                <div className="space-y-1">
                  <div className="flex items-center space-x-2">
                    <span className="font-bold text-sm text-foreground">{rec.filename}</span>
                    <span className="font-mono text-[10px] text-foreground-muted">({rec.id})</span>
                  </div>
                  <div className="flex items-center space-x-3 text-xs text-foreground-muted font-mono">
                    <span className="flex items-center space-x-1">
                      <Clock className="w-3 h-3" />
                      <span>{new Date(rec.created_at).toLocaleString()}</span>
                    </span>
                    <span>&middot;</span>
                    <span>{rec.clauses_count} clauses</span>
                    <span>&middot;</span>
                    <span>{rec.findings_count} findings</span>
                  </div>
                </div>
              </div>

              <div className="flex items-center space-x-4">
                {/* Risk score badge */}
                <div className={cn(
                  'px-2.5 py-1 rounded-lg border font-mono font-bold text-xs',
                  rec.risk_score > 50
                    ? 'bg-rose-500/10 text-rose-600 border-rose-500/20'
                    : rec.risk_score > 20
                    ? 'bg-amber-500/10 text-amber-600 border-amber-500/20'
                    : 'bg-emerald-500/10 text-emerald-600 border-emerald-500/20'
                )}>
                  Risk: {rec.risk_score}/100
                </div>

                <button
                  onClick={() => {
                    if (onLoadAnalysis) onLoadAnalysis(rec.id);
                    navigate('/');
                  }}
                  className="flex items-center space-x-1 px-3 py-1.5 rounded-lg bg-surface-elevated border border-border hover:bg-border text-foreground text-xs font-semibold transition-colors"
                >
                  <span>Open Audit</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
