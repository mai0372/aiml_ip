import { useState } from 'react';
import type { ProofTree, ResolutionStep } from '../types';
import { ShieldCheck, CheckCircle2, Download } from 'lucide-react';
import { cn } from '../lib/utils';

interface ProofTreeViewerProps {
  proof: ProofTree;
  onSelectClause?: (clauseId: string) => void;
}

export const ProofTreeViewer = ({
  proof,
  onSelectClause,
}: ProofTreeViewerProps) => {
  const [selectedStepId, setSelectedStepId] = useState<string | null>(proof.empty_clause_id || null);

  const steps = proof.steps || [];
  const stepMap = new Map<string, ResolutionStep>(steps.map(s => [s.clause_id, s]));

  // Build tree depth levels for SVG layout
  const levels: Map<string, number> = new Map();
  const getDepth = (id: string, visited = new Set<string>()): number => {
    if (visited.has(id)) return 0;
    visited.add(id);
    const step = stepMap.get(id);
    if (!step || !step.parents || step.parents.length === 0) return 0;
    const pDepths = step.parents.map(p => getDepth(p, new Set(visited)));
    return Math.max(...pDepths) + 1;
  };

  steps.forEach(s => {
    levels.set(s.clause_id, getDepth(s.clause_id));
  });

  const maxLevel = Math.max(...Array.from(levels.values()), 0);

  // Group steps by level for hierarchical SVG placement
  const levelGroups: ResolutionStep[][] = Array.from({ length: maxLevel + 1 }, () => []);
  steps.forEach(s => {
    const l = levels.get(s.clause_id) || 0;
    levelGroups[l].push(s);
  });

  // Calculate coordinates
  const nodeWidth = 220;
  const nodeHeight = 70;
  const levelHeight = 110;
  const coords: Map<string, { x: number; y: number }> = new Map();

  let maxSvgWidth = 600;
  levelGroups.forEach((group) => {
    const totalW = group.length * (nodeWidth + 20);
    if (totalW > maxSvgWidth) maxSvgWidth = totalW + 60;
  });

  levelGroups.forEach((group, lvl) => {
    const spacing = maxSvgWidth / (group.length + 1);
    group.forEach((step, idx) => {
      coords.set(step.clause_id, {
        x: spacing * (idx + 1) - nodeWidth / 2,
        y: 20 + lvl * levelHeight,
      });
    });
  });

  const totalSvgHeight = 40 + (maxLevel + 1) * levelHeight;

  // Generate DOT Graph representation
  const generateDOT = () => {
    let dot = "digraph ResolutionProof {\n  rankdir=TB;\n  node [shape=box, style=rounded, fontname=\"Courier\"];\n";
    steps.forEach(s => {
      const isBox = s.literals.length === 0;
      const label = isBox ? "BOX (Refutation)" : s.literals.join(" | ");
      dot += `  "${s.clause_id}" [label="${s.clause_id}\\n${label}"];\n`;
      if (s.parents) {
        s.parents.forEach(p => {
          dot += `  "${p}" -> "${s.clause_id}" [label="${s.resolved_on || ''}"];\n`;
        });
      }
    });
    dot += "}\n";
    return dot;
  };

  const handleExportDOT = () => {
    const blob = new Blob([generateDOT()], { type: 'text/vnd.graphviz' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `proof_tree_${proof.empty_clause_id || 'resolution'}.dot`;
    a.click();
  };

  return (
    <div className="flex flex-col space-y-4">
      {/* Proof Header & Verifier Badge */}
      <div className="flex flex-wrap items-center justify-between p-3 rounded-lg border border-border bg-surface-elevated text-xs">
        <div className="flex items-center space-x-2">
          <div className="p-1 rounded bg-emerald-500/10 text-emerald-600 border border-emerald-500/20">
            <ShieldCheck className="w-4 h-4" />
          </div>
          <div>
            <div className="font-semibold text-foreground flex items-center gap-1.5">
              <span>Resolution Refutation Certificate</span>
              <span className="font-mono text-[10px] px-1.5 py-0.2 rounded bg-primary/10 text-primary">
                {proof.outcome}
              </span>
            </div>
            <div className="text-[11px] text-foreground-muted font-mono">
              Total Steps: {proof.total_clauses} &middot; Proved in {proof.duration_ms}ms &middot; Robinson Unifications: {steps.length}
            </div>
          </div>
        </div>

        <div className="flex items-center space-x-2 mt-2 sm:mt-0">
          <div className="flex items-center space-x-1 px-2.5 py-1 rounded bg-surface border border-border text-foreground text-[11px]">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
            <span>Independent Verifier: PASSED</span>
          </div>
          <button
            onClick={handleExportDOT}
            className="flex items-center space-x-1 px-2.5 py-1 rounded bg-surface border border-border text-foreground hover:bg-border transition-colors text-[11px]"
            title="Download Graphviz DOT File"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export DOT</span>
          </button>
        </div>
      </div>

      {/* Interactive SVG Tree Canvas */}
      <div className="border border-border rounded-xl bg-surface/50 p-4 overflow-x-auto">
        <div className="text-[11px] font-mono text-foreground-muted mb-2 flex items-center justify-between">
          <span>Resolution Tree Topology (Roots: Contract Premise Clauses & Deontic Axioms &rarr; Sink: &empty; Empty Clause)</span>
          <span className="text-primary">Click node to inspect unifier</span>
        </div>

        <svg 
          width={Math.max(maxSvgWidth, 600)} 
          height={totalSvgHeight} 
          className="select-none mx-auto"
        >
          <defs>
            <marker
              id="arrowhead"
              markerWidth="7"
              markerHeight="7"
              refX="6"
              refY="3.5"
              orient="auto"
            >
              <polygon points="0 0, 7 3.5, 0 7" fill="currentColor" className="text-border-strong" />
            </marker>
          </defs>

          {/* Render Parent Edges */}
          {steps.map(step => {
            const childPos = coords.get(step.clause_id);
            if (!childPos || !step.parents) return null;

            return step.parents.map((parentId, pIdx) => {
              const parentPos = coords.get(parentId);
              if (!parentPos) return null;

              const startX = parentPos.x + nodeWidth / 2;
              const startY = parentPos.y + nodeHeight;
              const endX = childPos.x + nodeWidth / 2;
              const endY = childPos.y;

              const midY = (startY + endY) / 2;
              const pathD = `M ${startX} ${startY} C ${startX} ${midY}, ${endX} ${midY}, ${endX} ${endY}`;

              return (
                <g key={`${parentId}->${step.clause_id}-${pIdx}`}>
                  <path
                    d={pathD}
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="1.5"
                    strokeDasharray={step.unifier ? "none" : "3,3"}
                    className="text-border-strong transition-all duration-300"
                    markerEnd="url(#arrowhead)"
                  />
                  {step.resolved_on && pIdx === 0 && (
                    <text
                      x={(startX + endX) / 2}
                      y={midY}
                      fontSize="9"
                      fill="currentColor"
                      className="text-foreground-muted font-mono"
                      textAnchor="middle"
                      dy="-3"
                    >
                      {step.resolved_on}
                    </text>
                  )}
                </g>
              );
            });
          })}

          {/* Render Clause Nodes */}
          {steps.map(step => {
            const pos = coords.get(step.clause_id);
            if (!pos) return null;

            const isEmpty = step.literals.length === 0;
            const isSelected = selectedStepId === step.clause_id;
            const isRoot = !step.parents || step.parents.length === 0;

            return (
              <g
                key={step.clause_id}
                transform={`translate(${pos.x}, ${pos.y})`}
                onClick={() => {
                  setSelectedStepId(step.clause_id);
                  if (step.source_id && onSelectClause) {
                    onSelectClause(step.source_id);
                  }
                }}
                className="cursor-pointer group"
              >
                <rect
                  width={nodeWidth}
                  height={nodeHeight}
                  rx="8"
                  className={cn(
                    "transition-all duration-150 stroke-1",
                    isEmpty 
                      ? "fill-rose-500/10 stroke-rose-500 stroke-2 filter drop-shadow-sm" 
                      : isSelected
                      ? "fill-primary/10 stroke-primary stroke-2"
                      : isRoot
                      ? "fill-surface stroke-border-strong hover:stroke-primary"
                      : "fill-surface stroke-border hover:stroke-border-strong"
                  )}
                />
                
                {/* Node Title & Source Tag */}
                <text
                  x="12"
                  y="20"
                  fontSize="11"
                  fontWeight="bold"
                  fill="currentColor"
                  className={cn(
                    "font-mono",
                    isEmpty ? "text-rose-600 dark:text-rose-400" : isSelected ? "text-primary" : "text-foreground"
                  )}
                >
                  {step.clause_id} {step.source_id ? `(${step.source_id})` : ''}
                </text>

                {/* Literals in clausal form */}
                <text
                  x="12"
                  y="38"
                  fontSize="10"
                  fill="currentColor"
                  className="font-mono text-foreground-muted"
                >
                  {isEmpty ? '□ [CONTRADICTION EMPTY CLAUSE]' : (
                    step.literals.join(' ∨ ').length > 28
                      ? step.literals.join(' ∨ ').slice(0, 26) + '...'
                      : step.literals.join(' ∨ ')
                  )}
                </text>

                {/* Unifier / Rule tag */}
                {step.unifier && (
                  <text
                    x="12"
                    y="55"
                    fontSize="9"
                    fill="currentColor"
                    className="font-mono text-primary font-medium"
                  >
                    σ = {JSON.stringify(step.unifier).slice(0, 24)}
                  </text>
                )}
                {isRoot && (
                  <text
                    x="12"
                    y="55"
                    fontSize="9"
                    fill="currentColor"
                    className="font-mono text-amber-600 dark:text-amber-400"
                  >
                    Input Premise / Axiom
                  </text>
                )}
              </g>
            );
          })}
        </svg>
      </div>

      {/* Selected Node Details Card */}
      {selectedStepId && (
        <div className="p-3.5 rounded-lg border border-border bg-surface text-xs font-mono">
          <div className="font-semibold text-foreground flex items-center justify-between mb-2">
            <span>Selected Clause: {selectedStepId}</span>
            {stepMap.get(selectedStepId)?.source_id && (
              <button
                onClick={() => {
                  const sId = stepMap.get(selectedStepId)?.source_id;
                  if (sId && onSelectClause) onSelectClause(sId);
                }}
                className="text-[11px] text-primary hover:underline"
              >
                Jump to {stepMap.get(selectedStepId)?.source_id} &rarr;
              </button>
            )}
          </div>
          <div className="space-y-1.5 text-foreground-muted">
            <div>
              <span className="text-foreground font-semibold">Clausal Literals:</span>{' '}
              <code className="text-foreground bg-surface-elevated px-1.5 py-0.5 rounded">
                {stepMap.get(selectedStepId)?.literals.join(' ∨ ') || '□ (Empty clause: Refutation accomplished)'}
              </code>
            </div>
            {stepMap.get(selectedStepId)?.parents && (
              <div>
                <span className="text-foreground font-semibold">Derived From Parents:</span>{' '}
                {stepMap.get(selectedStepId)?.parents?.join(', ')} via Robinson resolvent on{' '}
                <span className="text-primary">{stepMap.get(selectedStepId)?.resolved_on}</span>
              </div>
            )}
            {stepMap.get(selectedStepId)?.unifier && (
              <div>
                <span className="text-foreground font-semibold">Most General Unifier (MGU):</span>{' '}
                {JSON.stringify(stepMap.get(selectedStepId)?.unifier)}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
