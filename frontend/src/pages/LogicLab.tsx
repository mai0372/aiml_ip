import { useState } from 'react';
import { 
  FlaskConical, 
  Sparkles, 
  Cpu, 
  Layers 
} from 'lucide-react';
import { convertLogicWff, proveLogicFormulas } from '../lib/api';
import type { LogicConvertResponse, ProofTree } from '../types';
import { ProofTreeViewer } from '../components/ProofTreeViewer';
import { cn } from '../lib/utils';

interface Preset {
  id: string;
  name: string;
  description: string;
  formulaToConvert: string;
  premises: string[];
  goal: string;
}

const PRESETS: Preset[] = [
  {
    id: 'socrates',
    name: '1. Socrates Syllogism',
    description: 'Textbook Greek syllogism: All men are mortal; Socrates is a man; therefore Socrates is mortal.',
    formulaToConvert: 'forall x: (Man(x) -> Mortal(x))',
    premises: [
      'Man(Socrates)',
      'forall x: (Man(x) -> Mortal(x))'
    ],
    goal: 'Mortal(Socrates)'
  },
  {
    id: 'rental_contradiction',
    name: '2. Rental Contradiction (Clause 3 vs Clause 12)',
    description: 'Worked example: Clause 3 allows 30-day notice; Clause 12 forbids early termination with notice under 90 days. Procedural arithmetic LessThan(30, 90) refutes consistency.',
    formulaToConvert: 'forall n: (LessThan(n, 90) -> Forb(tenant, Terminate(n)))',
    premises: [
      'Perm(tenant, Terminate(30))',
      'forall n: (LessThan(n, 90) -> Forb(tenant, Terminate(n)))',
      'forall p: forall a: ~(Perm(p, a) & Forb(p, a))'
    ],
    goal: ''
  },
  {
    id: 'curiosity_cat',
    name: '3. Curiosity Killed the Cat',
    description: 'Classic Russell & Norvig theorem proving puzzle: Who killed the cat Tuna?',
    formulaToConvert: 'forall x: (Cat(x) -> Animal(x))',
    premises: [
      'forall x: (forall y: (Animal(y) -> Loves(x, y)) -> exists z: Loves(z, x))',
      'forall x: (exists y: (Animal(y) & Kills(x, y)) -> forall z: ~Loves(z, x))',
      'forall x: (Cat(x) -> Animal(x))',
      'Cat(Tuna)',
      'Kills(Curiosity, Tuna)'
    ],
    goal: 'exists x: Kills(x, Tuna)'
  },
  {
    id: 'custom',
    name: '4. Custom WFF Formula',
    description: 'Enter any valid First-Order Predicate Logic WFF to convert and resolve.',
    formulaToConvert: 'forall x: (Bird(x) & ~Penguin(x) -> Flies(x))',
    premises: [
      'Bird(Tweety)',
      'forall x: (Bird(x) & ~Penguin(x) -> Flies(x))',
      '~Penguin(Tweety)'
    ],
    goal: 'Flies(Tweety)'
  }
];

export const LogicLab = () => {
  const [selectedPreset, setSelectedPreset] = useState<Preset>(PRESETS[1]); // Default to rental contradiction
  const [formulaInput, setFormulaInput] = useState(PRESETS[1].formulaToConvert);
  const [premisesInput, setPremisesInput] = useState(PRESETS[1].premises.join('\n'));
  const [goalInput, setGoalInput] = useState(PRESETS[1].goal);

  // Results
  const [cnfResult, setCnfResult] = useState<LogicConvertResponse | null>(null);
  const [proofResult, setProofResult] = useState<ProofTree | null>(null);
  const [activeTab, setActiveTab] = useState<'cnf' | 'resolution'>('resolution');
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleApplyPreset = (preset: Preset) => {
    setSelectedPreset(preset);
    setFormulaInput(preset.formulaToConvert);
    setPremisesInput(preset.premises.join('\n'));
    setGoalInput(preset.goal);
    setCnfResult(null);
    setProofResult(null);
    setErrorMsg(null);
  };

  const handleConvertCNF = async () => {
    if (!formulaInput.trim()) return;
    setIsLoading(true);
    setErrorMsg(null);
    try {
      const res = await convertLogicWff(formulaInput);
      setCnfResult(res);
      setActiveTab('cnf');
    } catch (err: any) {
      setErrorMsg(err.message || 'CNF conversion failed');
    } finally {
      setIsLoading(false);
    }
  };

  const handleExecuteProof = async () => {
    setIsLoading(true);
    setErrorMsg(null);
    try {
      const premises = premisesInput.split('\n').map(p => p.trim()).filter(Boolean);
      const res = await proveLogicFormulas(premises, goalInput);
      setProofResult(res);
      setActiveTab('resolution');
    } catch (err: any) {
      setErrorMsg(err.message || 'Resolution failed');
    } finally {
      setIsLoading(false);
    }
  };

  const insertSymbol = (sym: string) => {
    setFormulaInput(prev => prev + sym);
  };

  return (
    <div className="flex-1 overflow-y-auto p-6 sm:p-10 max-w-7xl mx-auto w-full space-y-8 select-none">
      {/* Header */}
      <div className="space-y-2">
        <div className="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-full bg-amber-500/10 border border-amber-500/20 text-amber-600 dark:text-amber-400 text-xs font-semibold">
          <FlaskConical className="w-3.5 h-3.5" />
          <span>Module II Syllabus Showcase: Logic-Based Contract Compliance Engine</span>
        </div>
        <h1 className="text-3xl font-extrabold tracking-tight text-foreground">
          Logic Lab & First-Order Resolution Workbench
        </h1>
        <p className="text-sm text-foreground-muted max-w-3xl leading-relaxed">
          Interactive formal reasoning environment implementing pure First-Order Predicate Logic (FOPL): recursive-descent AST parsing, 9-step conversion to Clausal Normal Form (CNF), Skolemization, Robinson unification with occurs check, and resolution refutation theorem proving.
        </p>
      </div>

      {/* Preset Selectors */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        {PRESETS.map((p) => (
          <button
            key={p.id}
            onClick={() => handleApplyPreset(p)}
            className={cn(
              'p-3.5 rounded-xl border text-left transition-all space-y-1.5 group',
              selectedPreset.id === p.id
                ? 'border-primary ring-2 ring-primary/20 bg-surface'
                : 'border-border bg-surface hover:border-primary/40 hover:bg-surface-elevated/40'
            )}
          >
            <div className="font-semibold text-xs text-foreground group-hover:text-primary transition-colors">
              {p.name}
            </div>
            <div className="text-[11px] text-foreground-muted line-clamp-2 leading-relaxed">
              {p.description}
            </div>
          </button>
        ))}
      </div>

      {/* Inputs Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Card: WFF to CNF Stepper */}
        <div className="p-5 rounded-2xl border border-border bg-surface space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Layers className="w-4 h-4 text-primary" />
              <h2 className="font-bold text-sm text-foreground">1. WFF to CNF 9-Step Converter</h2>
            </div>
            <span className="text-[10px] font-mono text-foreground-muted">Module II WFF &rarr; CNF</span>
          </div>

          {/* Logical Symbol Palette */}
          <div className="flex items-center space-x-1.5 flex-wrap gap-y-1">
            {['¬', '∧', '∨', '→', '↔', '∀', '∃', 'LessThan(x, y)', 'Equals(x, y)'].map(s => (
              <button
                key={s}
                onClick={() => insertSymbol(s)}
                className="px-2 py-0.5 rounded bg-surface-elevated border border-border hover:bg-border text-foreground font-mono text-xs transition-colors"
              >
                {s}
              </button>
            ))}
          </div>

          <textarea
            value={formulaInput}
            onChange={(e) => setFormulaInput(e.target.value)}
            rows={3}
            placeholder="Enter WFF formula e.g. forall x: (Man(x) -> Mortal(x))"
            className="w-full p-3 rounded-lg border border-border bg-surface-elevated font-mono text-xs text-foreground focus:outline-none focus:border-primary resize-none"
          />

          <button
            onClick={handleConvertCNF}
            disabled={isLoading || !formulaInput.trim()}
            className="w-full flex items-center justify-center space-x-2 py-2 rounded-lg bg-primary text-primary-fg hover:bg-primary-hover font-semibold text-xs transition-colors"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Generate 9-Step CNF Breakdown</span>
          </button>
        </div>

        {/* Right Card: Resolution Theorem Prover */}
        <div className="p-5 rounded-2xl border border-border bg-surface space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Cpu className="w-4 h-4 text-emerald-500" />
              <h2 className="font-bold text-sm text-foreground">2. Resolution Refutation Prover</h2>
            </div>
            <span className="text-[10px] font-mono text-foreground-muted">Robinson Refutation</span>
          </div>

          <div className="space-y-2">
            <label className="text-[11px] font-mono text-foreground-muted">Input Premises (one per line):</label>
            <textarea
              value={premisesInput}
              onChange={(e) => setPremisesInput(e.target.value)}
              rows={3}
              placeholder="Premises in FOPL..."
              className="w-full p-2.5 rounded-lg border border-border bg-surface-elevated font-mono text-xs text-foreground focus:outline-none focus:border-primary resize-none"
            />
          </div>

          <div className="space-y-1">
            <label className="text-[11px] font-mono text-foreground-muted">Negated Goal Q (optional, tests KB ⊨ Q):</label>
            <input
              type="text"
              value={goalInput}
              onChange={(e) => setGoalInput(e.target.value)}
              placeholder="Goal formula e.g. Mortal(Socrates)"
              className="w-full p-2 rounded-lg border border-border bg-surface-elevated font-mono text-xs text-foreground focus:outline-none focus:border-primary"
            />
          </div>

          <button
            onClick={handleExecuteProof}
            disabled={isLoading || !premisesInput.trim()}
            className="w-full flex items-center justify-center space-x-2 py-2 rounded-lg bg-emerald-600 text-white hover:bg-emerald-700 font-semibold text-xs transition-colors"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Execute Robinson Resolution Theorem Prover</span>
          </button>
        </div>
      </div>

      {/* Error message */}
      {errorMsg && (
        <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-600 text-xs font-mono">
          Error: {errorMsg}
        </div>
      )}

      {/* Results View Tabs */}
      <div className="border border-border rounded-2xl bg-surface p-6 space-y-6">
        <div className="flex items-center space-x-3 border-b border-border pb-3">
          <button
            onClick={() => setActiveTab('resolution')}
            className={cn(
              'flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors',
              activeTab === 'resolution'
                ? 'bg-primary text-primary-fg'
                : 'text-foreground-muted hover:bg-surface-elevated hover:text-foreground'
            )}
          >
            <Cpu className="w-3.5 h-3.5" />
            <span>Resolution Refutation Tree</span>
          </button>

          <button
            onClick={() => setActiveTab('cnf')}
            className={cn(
              'flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors',
              activeTab === 'cnf'
                ? 'bg-primary text-primary-fg'
                : 'text-foreground-muted hover:bg-surface-elevated hover:text-foreground'
            )}
          >
            <Layers className="w-3.5 h-3.5" />
            <span>CNF Conversion Steps</span>
          </button>
        </div>

        {/* Tab Content: Resolution */}
        {activeTab === 'resolution' && (
          <div>
            {proofResult ? (
              <ProofTreeViewer proof={proofResult} />
            ) : (
              <div className="p-12 text-center text-xs text-foreground-muted font-mono space-y-2">
                <div>Click "Execute Robinson Resolution Theorem Prover" above to prove theorems live.</div>
                <div className="text-[11px] opacity-75">
                  Preset 2 proves the conflict between Clause 3 (30-day notice) and Clause 12 (minimum 90-day notice) with arithmetic LessThan(30, 90).
                </div>
              </div>
            )}
          </div>
        )}

        {/* Tab Content: 9-Step CNF Stepper */}
        {activeTab === 'cnf' && (
          <div className="space-y-4">
            {cnfResult ? (
              <div className="space-y-3 font-mono text-xs">
                <div className="p-3 rounded-lg bg-surface-elevated border border-border flex items-center justify-between">
                  <span className="font-semibold text-foreground">Source WFF: {cnfResult.formula}</span>
                  <span className="text-primary">{cnfResult.clauses.length} Disjunctive Clause(s) Produced</span>
                </div>

                <div className="divide-y divide-border/40 border border-border rounded-xl overflow-hidden">
                  {cnfResult.steps.map((st) => (
                    <div key={st.step_number} className="p-3.5 bg-surface hover:bg-surface-elevated/40 transition-colors flex items-start space-x-4">
                      <div className="w-7 h-7 rounded-full bg-primary/10 text-primary flex items-center justify-center font-bold text-xs shrink-0">
                        {st.step_number}
                      </div>
                      <div className="flex-1 space-y-1">
                        <div className="flex items-center justify-between">
                          <span className="font-bold text-foreground text-xs">{st.step_name}</span>
                          <span className="text-[10px] text-foreground-muted">{st.description}</span>
                        </div>
                        <div className="p-2 rounded bg-surface-elevated text-foreground text-[11px] whitespace-pre-wrap">
                          {st.formula}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="p-12 text-center text-xs text-foreground-muted font-mono">
                Click "Generate 9-Step CNF Breakdown" above to view every algebraic simplification step.
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
