import { useState } from 'react';
import type { 
  ClauseIR, 
  Finding, 
  PipelineEventData, 
  AnalysisPayload, 
  SeverityCounts 
} from '../types';
import { SAMPLE_CONTRACTS } from '../data/sampleContracts';
import type { SampleContract } from '../data/sampleContracts';
import { createAnalysis, streamAnalysisEvents } from '../lib/api';
import { ClauseNavigator } from '../components/ClauseNavigator';
import { DocumentReader } from '../components/DocumentReader';
import { InspectorPane } from '../components/InspectorPane';
import { PrintReportView } from '../components/PrintReportView';
import { 
  Upload, 
  FileText, 
  Sparkles, 
  ShieldCheck, 
  CheckCircle2, 
  Cpu, 
  ArrowRight,
  RefreshCw
} from 'lucide-react';
import { cn } from '../lib/utils';

export const AnalysisWorkspace = () => {
  const [inputText, setInputText] = useState('');
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [filename, setFilename] = useState('agreement.txt');
  const [redactPii, setRedactPii] = useState(false);

  // Execution states
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [pipelineEvents, setPipelineEvents] = useState<PipelineEventData[]>([]);
  const [currentStage, setCurrentStage] = useState<string>('');

  // Result state
  const [analysisId, setAnalysisId] = useState<string | null>(null);
  const [clauses, setClauses] = useState<ClauseIR[]>([]);
  const [findings, setFindings] = useState<Finding[]>([]);
  const [severityCounts, setSeverityCounts] = useState<SeverityCounts>({ high: 0, medium: 0, low: 0, info: 0, conflict: 0 });
  const [riskScore, setRiskScore] = useState<number>(0);
  const [cleanText, setCleanText] = useState<string>('');
  const [selectedClauseId, setSelectedClauseId] = useState<string | null>(null);
  const [showPrintReport, setShowPrintReport] = useState(false);

  const handleSelectSample = (sample: SampleContract) => {
    setInputText(sample.text);
    setFilename(sample.filename);
    setUploadedFile(null);
  };

  const handleStartAnalysis = async () => {
    if (!inputText.trim() && !uploadedFile) return;

    setIsAnalyzing(true);
    setPipelineEvents([]);
    setCurrentStage('ingest');

    try {
      const initRes = await createAnalysis({
        text: inputText,
        file: uploadedFile || undefined,
        filename,
        redact_pii: redactPii,
      });

      setAnalysisId(initRes.id);

      streamAnalysisEvents(
        initRes.id,
        (event) => {
          setPipelineEvents(prev => [...prev.filter(e => e.stage !== event.stage), event]);
          setCurrentStage(event.stage);
        },
        (err) => {
          console.error('SSE Error:', err);
          setIsAnalyzing(false);
        },
        (payload: AnalysisPayload) => {
          setClauses(payload.clauses);
          setFindings(payload.findings);
          setSeverityCounts(payload.severity_counts);
          setRiskScore(payload.risk_score);
          setCleanText(payload.clean_text);
          if (payload.clauses.length > 0) {
            setSelectedClauseId(payload.clauses[0].id);
          }
          setIsAnalyzing(false);
        }
      );
    } catch (err: any) {
      alert(`Analysis failed: ${err.message || 'Unknown error'}`);
      setIsAnalyzing(false);
    }
  };

  const handleReset = () => {
    setAnalysisId(null);
    setClauses([]);
    setFindings([]);
    setInputText('');
    setUploadedFile(null);
    setPipelineEvents([]);
    setShowPrintReport(false);
  };

  // 0. PRINT REPORT VIEW
  if (showPrintReport && analysisId) {
    return (
      <PrintReportView
        filename={filename}
        clauses={clauses}
        findings={findings}
        riskScore={riskScore}
        severityCounts={severityCounts}
        onBack={() => setShowPrintReport(false)}
      />
    );
  }

  // 1. LIVE SSE PROCESSING VIEW
  if (isAnalyzing) {
    const stages = [
      { id: 'ingest', name: 'Document Ingestion & PII Redaction' },
      { id: 'segment', name: 'Clause Segmentation & Coordinate Mapping' },
      { id: 'extract', name: 'Ontological ClauseIR Extraction' },
      { id: 'verify_extraction', name: 'Decoupled Extraction Verification (Dual-Pass & Grounding)' },
      { id: 'translate', name: 'Deterministic FOPL Translation' },
      { id: 'reason', name: 'Logic-Based Compliance Engine (Resolution Refutation)' },
      { id: 'retrieve_rules', name: 'Indian Residential Tenancy Rule Evaluation' },
      { id: 'explain', name: 'Explanation & Citation Verification' }
    ];

    return (
      <div className="flex-1 flex items-center justify-center p-6 bg-surface">
        <div className="w-full max-w-xl bg-surface-elevated/40 border border-border rounded-2xl p-6 shadow-xl space-y-6">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-center text-primary animate-pulse">
              <Cpu className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-foreground">
                Analyzing Contract Compliance
              </h2>
              <p className="text-xs text-foreground-muted">
                Executing 10-stage symbolic reasoning pipeline & verifiers...
              </p>
            </div>
          </div>

          {/* Timeline Stages */}
          <div className="space-y-3">
            {stages.map((st) => {
              const ev = pipelineEvents.find(e => e.stage === st.id);
              const isCurrent = currentStage === st.id;
              const isDone = Boolean(ev && ev.status === 'completed');

              return (
                <div
                  key={st.id}
                  className={cn(
                    'flex items-center justify-between p-2.5 rounded-lg border text-xs transition-colors',
                    isDone
                      ? 'border-emerald-500/20 bg-emerald-500/[0.04] text-foreground'
                      : isCurrent
                      ? 'border-primary/40 bg-primary/[0.06] text-primary font-medium'
                      : 'border-border/40 bg-surface/50 text-foreground-muted'
                  )}
                >
                  <div className="flex items-center space-x-2.5">
                    {isDone ? (
                      <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />
                    ) : isCurrent ? (
                      <div className="w-4 h-4 rounded-full border-2 border-primary border-t-transparent animate-spin shrink-0" />
                    ) : (
                      <div className="w-4 h-4 rounded-full border border-border shrink-0" />
                    )}
                    <span>{st.name}</span>
                  </div>

                  {ev && isDone && (
                    <span className="font-mono text-[10px] text-foreground-muted">
                      {ev.duration_ms}ms
                    </span>
                  )}
                </div>
              );
            })}
          </div>

          <div className="text-center font-mono text-xs text-foreground-muted">
            Engine: Logic-Based Contract Compliance Engine (Module II Syllabus)
          </div>
        </div>
      </div>
    );
  }

  // 2. LOADED 3-PANE WORKSPACE VIEW
  if (analysisId && clauses.length > 0) {
    return (
      <div className="flex-1 flex flex-col h-[calc(100vh-3.5rem)] overflow-hidden">
        {/* Workspace Sub-header */}
        <div className="h-10 px-6 border-b border-border bg-surface-elevated/70 flex items-center justify-between text-xs select-none">
          <div className="flex items-center space-x-3">
            <span className="font-semibold text-foreground flex items-center space-x-1.5">
              <FileText className="w-3.5 h-3.5 text-primary" />
              <span>{filename}</span>
            </span>
            <span className="text-foreground-muted font-mono text-[11px]">
              ({clauses.length} clauses analyzed)
            </span>
            <span className={cn(
              'font-mono text-[10px] px-1.5 py-0.2 rounded border font-semibold',
              riskScore > 50 ? 'bg-rose-500/10 text-rose-600 border-rose-500/20' : 'bg-emerald-500/10 text-emerald-600 border-emerald-500/20'
            )}>
              Risk Score: {riskScore}/100
            </span>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={() => setShowPrintReport(true)}
              className="flex items-center space-x-1.5 px-2.5 py-1 rounded border border-border bg-surface hover:bg-border text-foreground transition-colors text-[11px] font-medium"
            >
              <span>Print Report</span>
            </button>
            <button
              onClick={handleReset}
              className="flex items-center space-x-1.5 px-2.5 py-1 rounded border border-border bg-surface hover:bg-border text-foreground-muted hover:text-foreground transition-colors text-[11px]"
            >
              <RefreshCw className="w-3 h-3" />
              <span>New Audit</span>
            </button>
          </div>
        </div>

        {/* 3-Pane Responsive Layout */}
        <div className="flex-1 flex overflow-hidden">
          <ClauseNavigator
            clauses={clauses}
            findings={findings}
            selectedClauseId={selectedClauseId}
            onSelectClause={setSelectedClauseId}
          />
          <DocumentReader
            clauses={clauses}
            findings={findings}
            selectedClauseId={selectedClauseId}
            onSelectClause={setSelectedClauseId}
            cleanText={cleanText}
          />
          <InspectorPane
            analysisId={analysisId}
            clauses={clauses}
            findings={findings}
            severityCounts={severityCounts}
            riskScore={riskScore}
            selectedClauseId={selectedClauseId}
            onSelectClause={setSelectedClauseId}
            onPrintReport={() => setShowPrintReport(true)}
          />
        </div>
      </div>
    );
  }

  // 3. EMPTY / INPUT STAGE
  return (
    <div className="flex-1 overflow-y-auto p-6 sm:p-10 max-w-5xl mx-auto w-full space-y-8">
      {/* Title Hero */}
      <div className="space-y-2">
        <div className="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-full bg-primary/10 border border-primary/20 text-primary text-xs font-semibold">
          <ShieldCheck className="w-3.5 h-3.5" />
          <span>Indian Residential Tenancy Compliance & First-Order Logic Verifier</span>
        </div>
        <h1 className="text-3xl font-extrabold tracking-tight text-foreground">
          Understand your rental agreement before you sign it.
        </h1>
        <p className="text-sm text-foreground-muted max-w-2xl leading-relaxed">
          Upload or paste any Indian residential lease. ClauseLens extracts contractual obligations, detects unfair statutory terms, and rigorously proves internal contradictions using a pure first-order-logic theorem prover.
        </p>
      </div>

      {/* 1-Click Preset Samples */}
      <div className="space-y-3">
        <div className="text-xs font-semibold uppercase tracking-wider text-foreground-muted flex items-center justify-between">
          <span>Or load a benchmark test agreement (1-Click)</span>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {SAMPLE_CONTRACTS.map((s) => (
            <button
              key={s.id}
              onClick={() => handleSelectSample(s)}
              className={cn(
                'text-left p-3.5 rounded-xl border bg-surface transition-all duration-150 space-y-1.5 group',
                filename === s.filename
                  ? 'border-primary ring-2 ring-primary/20'
                  : 'border-border hover:border-primary/50 hover:bg-surface-elevated/40'
              )}
            >
              <div className="flex items-center justify-between">
                <span className="font-semibold text-xs text-foreground group-hover:text-primary transition-colors">
                  {s.name}
                </span>
                <span className={cn('text-[10px] px-1.5 py-0.2 rounded border font-mono', s.tagColor)}>
                  {s.tag}
                </span>
              </div>
              <p className="text-[11px] text-foreground-muted leading-relaxed line-clamp-2">
                {s.subtitle}
              </p>
            </button>
          ))}
        </div>
      </div>

      {/* Contract Input Box & Drag Drop */}
      <div className="space-y-4">
        <div className="border border-border rounded-xl bg-surface overflow-hidden shadow-sm focus-within:border-primary transition-colors">
          <div className="p-3 border-b border-border bg-surface-elevated/40 flex items-center justify-between text-xs text-foreground-muted">
            <span className="font-medium text-foreground">Agreement Source Text</span>
            <div className="flex items-center space-x-3">
              <label className="flex items-center space-x-1.5 cursor-pointer text-xs text-foreground-muted hover:text-foreground">
                <input
                  type="checkbox"
                  checked={redactPii}
                  onChange={(e) => setRedactPii(e.target.checked)}
                  className="rounded border-border text-primary focus:ring-primary h-3.5 w-3.5"
                />
                <span>Redact Indian PII (Aadhaar, PAN, Phone)</span>
              </label>

              <label className="flex items-center space-x-1 px-2 py-0.5 rounded bg-surface border border-border hover:bg-border cursor-pointer transition-colors">
                <Upload className="w-3 h-3 text-foreground-muted" />
                <span className="text-[11px]">Upload PDF / Docx / TXT</span>
                <input
                  type="file"
                  accept=".pdf,.docx,.txt"
                  className="hidden"
                  onChange={(e) => {
                    const f = e.target.files?.[0];
                    if (f) {
                      setUploadedFile(f);
                      setFilename(f.name);
                    }
                  }}
                />
              </label>
            </div>
          </div>

          <textarea
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder="Paste your residential rental agreement text here or choose a test sample above..."
            rows={12}
            className="w-full p-4 bg-transparent font-serif text-sm leading-relaxed text-foreground placeholder:text-foreground-muted focus:outline-none resize-none"
          />
        </div>

        {/* Start Button */}
        <div className="flex items-center justify-between pt-2">
          <div className="text-xs text-foreground-muted">
            {uploadedFile ? `Selected file: ${uploadedFile.name}` : `${inputText.length} characters loaded`}
          </div>

          <button
            onClick={handleStartAnalysis}
            disabled={!inputText.trim() && !uploadedFile}
            className="flex items-center space-x-2 px-6 py-2.5 rounded-xl bg-primary text-primary-fg hover:bg-primary-hover disabled:opacity-50 font-semibold shadow-md transition-all text-xs"
          >
            <Sparkles className="w-4 h-4" />
            <span>Audit & Verify Contract</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};
