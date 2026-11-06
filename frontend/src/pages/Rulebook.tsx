import { useState, useEffect } from 'react';
import type { RuleCatalogItem } from '../types';
import { fetchRules } from '../lib/api';
import { BookOpen, ExternalLink, Copy, Search } from 'lucide-react';
import { cn, copyToClipboard } from '../lib/utils';

export const Rulebook = () => {
  const [rules, setRules] = useState<RuleCatalogItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [filterReviewed, setFilterReviewed] = useState<'all' | 'reviewed' | 'unreviewed'>('all');
  const [search, setSearch] = useState('');
  const [copiedId, setCopiedId] = useState<string | null>(null);

  useEffect(() => {
    fetchRules()
      .then(res => setRules(res))
      .catch(err => console.error('Failed to load rules:', err))
      .finally(() => setIsLoading(false));
  }, []);

  const handleCopyCitation = async (rule: RuleCatalogItem) => {
    const citation = `${rule.statute_name}, ${rule.section} (Cited under ClauseLens Rule ${rule.id}: "${rule.title}"). Available at: ${rule.source_url}`;
    const ok = await copyToClipboard(citation);
    if (ok) {
      setCopiedId(rule.id);
      setTimeout(() => setCopiedId(null), 2000);
    }
  };

  const filteredRules = rules.filter(r => {
    if (filterReviewed === 'reviewed' && !r.reviewed) return false;
    if (filterReviewed === 'unreviewed' && r.reviewed) return false;
    if (search.trim()) {
      const q = search.toLowerCase();
      return r.id.toLowerCase().includes(q) ||
             r.title.toLowerCase().includes(q) ||
             r.statute_name.toLowerCase().includes(q) ||
             r.plain_explanation.toLowerCase().includes(q);
    }
    return true;
  });

  return (
    <div className="flex-1 overflow-y-auto p-6 sm:p-10 max-w-7xl mx-auto w-full space-y-8 select-none">
      {/* Header */}
      <div className="space-y-2">
        <div className="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-600 dark:text-blue-400 text-xs font-semibold">
          <BookOpen className="w-3.5 h-3.5" />
          <span>Statutory Rule Pack: Indian Residential Tenancy (R01–R10)</span>
        </div>
        <h1 className="text-3xl font-extrabold tracking-tight text-foreground">
          Indian Tenancy Rulebook & Primary Sources
        </h1>
        <p className="text-sm text-foreground-muted max-w-3xl leading-relaxed">
          ClauseLens evaluates residential leases against vetted provisions of the Model Tenancy Act 2021, Transfer of Property Act 1882, and Registration Act 1908. Every rule carries official government links (India Code / MoHUA) and strict review status gating.
        </p>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3 p-3 rounded-xl border border-border bg-surface">
        <div className="relative w-full sm:w-80">
          <Search className="w-4 h-4 text-foreground-muted absolute left-3 top-2.5" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search rules, statutes, sections..."
            className="w-full bg-surface-elevated border border-border rounded-lg pl-9 pr-3 py-1.5 text-xs focus:outline-none focus:border-primary text-foreground placeholder:text-foreground-muted"
          />
        </div>

        <div className="flex items-center space-x-1 self-start sm:self-auto text-xs">
          {(['all', 'unreviewed', 'reviewed'] as const).map(tab => (
            <button
              key={tab}
              onClick={() => setFilterReviewed(tab)}
              className={cn(
                'px-3 py-1 rounded-lg text-xs font-medium capitalize transition-colors',
                filterReviewed === tab
                  ? 'bg-primary text-primary-fg'
                  : 'text-foreground-muted hover:bg-surface-elevated hover:text-foreground'
              )}
            >
              {tab === 'all' ? 'All (10)' : tab === 'unreviewed' ? 'Pending Review (10)' : 'Reviewed (0)'}
            </button>
          ))}
        </div>
      </div>

      {/* Rules Table */}
      <div className="border border-border rounded-2xl bg-surface overflow-hidden shadow-sm">
        {isLoading ? (
          <div className="p-12 text-center text-xs text-foreground-muted font-mono animate-pulse">
            Loading Indian statutory rules from rule pack...
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="border-b border-border bg-surface-elevated/70 text-foreground-muted font-semibold">
                  <th className="p-3.5 pl-5 font-mono">Rule ID</th>
                  <th className="p-3.5">Title & Plain-English Description</th>
                  <th className="p-3.5">Statutory Basis</th>
                  <th className="p-3.5">Review Status</th>
                  <th className="p-3.5 pr-5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/50">
                {filteredRules.map((rule) => (
                  <tr key={rule.id} className="hover:bg-surface-elevated/40 transition-colors">
                    {/* Rule ID */}
                    <td className="p-3.5 pl-5 align-top font-mono font-bold text-primary">
                      {rule.id}
                    </td>

                    {/* Title & Desc */}
                    <td className="p-3.5 align-top max-w-sm space-y-1">
                      <div className="font-bold text-foreground">{rule.title}</div>
                      <div className="text-foreground-muted text-[11px] leading-relaxed">
                        {rule.plain_explanation}
                      </div>
                      <div className="pt-1 text-[10px] text-primary/80 font-mono">
                        Target Clauses: {rule.target_clause_types.join(', ')}
                      </div>
                    </td>

                    {/* Statutory Basis */}
                    <td className="p-3.5 align-top max-w-xs space-y-1">
                      <div className="font-semibold text-foreground flex items-center space-x-1">
                        <span>{rule.statute_name}</span>
                        {rule.source_url && (
                          <a
                            href={rule.source_url}
                            target="_blank"
                            rel="noreferrer"
                            className="text-primary hover:underline"
                            title="Open official India Code / MoHUA PDF"
                          >
                            <ExternalLink className="w-3 h-3 inline" />
                          </a>
                        )}
                      </div>
                      <div className="text-[11px] font-mono text-foreground-muted">
                        {rule.section}
                      </div>
                      <div className="text-[10px] text-foreground-muted italic">
                        {rule.jurisdiction_note}
                      </div>
                    </td>

                    {/* Review Status */}
                    <td className="p-3.5 align-top">
                      <div className="space-y-1">
                        <span className={cn(
                          'inline-flex items-center space-x-1 px-2 py-0.5 rounded border text-[10px] font-mono font-semibold',
                          rule.reviewed
                            ? 'bg-emerald-500/10 text-emerald-600 border-emerald-500/20'
                            : 'bg-amber-500/10 text-amber-600 border-amber-500/20'
                        )}>
                          <span>{rule.reviewed ? 'Verified by Counsel' : 'reviewed: false'}</span>
                        </span>
                        <div className="text-[10px] text-foreground-muted">
                          {rule.reviewed ? 'Certified' : 'Needs advocate verification'}
                        </div>
                      </div>
                    </td>

                    {/* Actions */}
                    <td className="p-3.5 pr-5 align-top text-right">
                      <button
                        onClick={() => handleCopyCitation(rule)}
                        className="inline-flex items-center space-x-1 px-2.5 py-1 rounded bg-surface border border-border hover:bg-border text-foreground text-[11px] transition-colors"
                      >
                        <Copy className="w-3 h-3" />
                        <span>{copiedId === rule.id ? 'Copied' : 'Copy Citation'}</span>
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
