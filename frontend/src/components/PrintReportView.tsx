import type { ClauseIR, Finding, SeverityCounts } from '../types';
import { Scale, Printer, ArrowLeft } from 'lucide-react';

interface PrintReportViewProps {
  filename: string;
  clauses: ClauseIR[];
  findings: Finding[];
  riskScore: number;
  severityCounts: SeverityCounts;
  onBack: () => void;
}

export const PrintReportView = ({
  filename,
  clauses,
  findings,
  riskScore,
  severityCounts,
  onBack,
}: PrintReportViewProps) => {
  return (
    <div className="bg-white text-black min-h-screen p-8 max-w-4xl mx-auto select-none print:p-0">
      {/* Top Action Bar (hidden on print) */}
      <div className="no-print flex items-center justify-between pb-6 mb-8 border-b border-gray-200">
        <button
          onClick={onBack}
          className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg border border-gray-300 hover:bg-gray-100 text-xs font-semibold"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Analysis</span>
        </button>

        <button
          onClick={() => window.print()}
          className="flex items-center space-x-1.5 px-4 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700 text-xs font-bold shadow"
        >
          <Printer className="w-4 h-4" />
          <span>Print / Save as PDF</span>
        </button>
      </div>

      {/* COVER / HEADER PAGE */}
      <div className="border-b-2 border-black pb-6 mb-8 space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Scale className="w-6 h-6 text-black" />
            <span className="text-2xl font-black tracking-tight uppercase font-serif">ClauseLens</span>
          </div>
          <span className="font-mono text-xs text-gray-600">
            AUDIT DATE: {new Date().toLocaleDateString('en-IN', { dateStyle: 'long' })}
          </span>
        </div>

        <h1 className="text-3xl font-serif font-bold text-gray-900 pt-4">
          Residential Tenancy Compliance & Verification Audit Report
        </h1>
        <p className="text-sm text-gray-600">
          Document Audited: <b>{filename}</b> &middot; Formal Verification Engine: Logic-Based Contract Compliance Engine
        </p>

        {/* Executive Score Card */}
        <div className="grid grid-cols-4 gap-4 pt-4 text-center font-mono text-xs">
          <div className="p-3 border border-gray-300 rounded">
            <div className="text-2xl font-bold">{riskScore}/100</div>
            <div className="text-gray-500 text-[10px] uppercase">Overall Risk Index</div>
          </div>
          <div className="p-3 border border-gray-300 rounded">
            <div className="text-2xl font-bold text-red-600">{severityCounts.conflict}</div>
            <div className="text-gray-500 text-[10px] uppercase">Contradictions Proved</div>
          </div>
          <div className="p-3 border border-gray-300 rounded">
            <div className="text-2xl font-bold text-amber-600">{severityCounts.high + severityCounts.medium}</div>
            <div className="text-gray-500 text-[10px] uppercase">Statutory Risks</div>
          </div>
          <div className="p-3 border border-gray-300 rounded">
            <div className="text-2xl font-bold">{clauses.length}</div>
            <div className="text-gray-500 text-[10px] uppercase">Clauses Evaluated</div>
          </div>
        </div>
      </div>

      {/* SECTION 1: EXECUTIVE SUMMARY */}
      <div className="space-y-4 mb-8">
        <h2 className="text-lg font-bold font-serif uppercase tracking-wide border-b border-gray-300 pb-1">
          1. Executive Summary & Key Advice
        </h2>
        <p className="text-sm leading-relaxed text-gray-800">
          This report presents an automated compliance audit of the residential lease agreement using the First-Order Logic Contract Compliance Engine. Logical contradictions were evaluated via resolution refutation over closed deontic axioms. Statutory risks were evaluated against the Model Tenancy Act 2021, Transfer of Property Act 1882, and Registration Act 1908.
        </p>
      </div>

      {/* SECTION 2: AUDIT FINDINGS */}
      <div className="space-y-4 mb-8">
        <h2 className="text-lg font-bold font-serif uppercase tracking-wide border-b border-gray-300 pb-1">
          2. Identified Risks & Negotiation Points
        </h2>
        {findings.length === 0 ? (
          <p className="text-sm text-gray-600 italic">No violations or contradictions found. Agreement appears fair.</p>
        ) : (
          <div className="space-y-4">
            {findings.map((f, idx) => (
              <div key={f.id} className="border border-gray-200 p-4 rounded space-y-2 text-xs">
                <div className="flex items-center justify-between font-bold text-sm">
                  <span>{idx + 1}. {f.title}</span>
                  <span className="font-mono text-[10px] uppercase px-1.5 py-0.5 border border-black rounded">
                    {f.kind} &middot; {f.severity}
                  </span>
                </div>
                <p className="text-gray-800">{f.plain_explanation}</p>
                {f.evidence_quote && (
                  <div className="pl-3 border-l-2 border-gray-400 italic text-gray-700 font-serif">
                    "{f.evidence_quote}"
                  </div>
                )}
                {f.source && (
                  <div className="text-[11px] text-gray-600 font-mono">
                    Statutory Authority: {f.source.statute_name}, {f.source.section} ({f.source.jurisdiction_note})
                  </div>
                )}
                <div className="p-2 bg-gray-50 rounded text-gray-800 font-medium">
                  Recommendation: {f.suggestion}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* SECTION 3: FORMAL LOGIC PROOFS APPENDIX */}
      <div className="page-break space-y-4 pt-6">
        <h2 className="text-lg font-bold font-serif uppercase tracking-wide border-b border-gray-300 pb-1">
          3. Appendix: Formal Logic Resolution Proofs
        </h2>
        <p className="text-xs text-gray-600">
          The following resolution refutation proofs mathematically demonstrate internal contradictions using pure first-order resolution with occurs check and procedural arithmetic.
        </p>

        {findings.filter(f => f.proof).map((f) => (
          <div key={f.id} className="border border-gray-300 p-4 rounded space-y-2 text-xs font-mono">
            <div className="font-bold text-black text-sm">
              Refutation Proof for: {f.title}
            </div>
            <div>Outcome: {f.proof?.outcome} (Refutation Achieved: {f.proof?.empty_clause_id || 'BOX'})</div>
            <div className="space-y-1 pt-2">
              <div className="font-semibold text-gray-700">Derivation Steps:</div>
              {f.proof?.steps.map((st) => (
                <div key={st.clause_id} className="pl-2 border-l border-gray-400">
                  <span className="font-bold">{st.clause_id}:</span> {st.literals.join(' ∨ ') || '□ (Empty clause)'}{' '}
                  {st.parents && <span className="text-gray-500">from {st.parents.join(' & ')} on {st.resolved_on}</span>}{' '}
                  {st.unifier && <span className="text-blue-700">[σ: {JSON.stringify(st.unifier)}]</span>}
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* FOOTER */}
      <div className="border-t border-gray-300 pt-4 mt-12 text-center text-[10px] text-gray-500 font-mono">
        ClauseLens v1.0 &middot; Generated deterministically with zero artificial hallucination &middot; Not Legal Advice
      </div>
    </div>
  );
};
