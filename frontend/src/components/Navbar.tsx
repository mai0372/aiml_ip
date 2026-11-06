import { Link, useLocation } from 'react-router-dom';
import { 
  Scale, 
  BookOpen, 
  History as HistoryIcon, 
  FlaskConical, 
  Sun, 
  Moon, 
  Command, 
  ShieldCheck,
  FileText
} from 'lucide-react';
import { cn } from '../lib/utils';

interface NavbarProps {
  darkMode: boolean;
  onToggleDarkMode: () => void;
  onOpenCommandPalette: () => void;
  llmMode?: string;
  hasActiveAnalysis?: boolean;
}

export const Navbar = ({
  darkMode,
  onToggleDarkMode,
  onOpenCommandPalette,
  llmMode = 'offline',
}: NavbarProps) => {
  const location = useLocation();

  const navLinks = [
    { to: '/', label: 'Analysis', icon: FileText },
    { to: '/logic-lab', label: 'Logic Lab', icon: FlaskConical, badge: 'Syllabus' },
    { to: '/rules', label: 'Rulebook & Sources', icon: BookOpen },
    { to: '/history', label: 'History', icon: HistoryIcon },
  ];

  return (
    <header className="sticky top-0 z-40 w-full border-b border-border bg-surface/90 backdrop-blur-md transition-colors">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 h-14 flex items-center justify-between">
        {/* Brand */}
        <div className="flex items-center space-x-3">
          <Link to="/" className="flex items-center space-x-2.5 group">
            <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center text-primary-fg shadow-sm group-hover:scale-105 transition-transform">
              <Scale className="w-4 h-4" />
            </div>
            <div>
              <span className="font-bold text-base tracking-tight text-foreground flex items-center gap-1.5">
                ClauseLens
                <span className="text-[10px] uppercase font-semibold px-1.5 py-0.5 rounded bg-primary/10 text-primary border border-primary/20">
                  v1.0
                </span>
              </span>
            </div>
          </Link>

          <div className="hidden lg:flex items-center pl-3 border-l border-border text-xs text-foreground-muted">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-600 mr-1.5" />
            <span className="font-mono text-[11px]">Logic-Based Contract Compliance Engine</span>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex items-center space-x-1">
          {navLinks.map((item) => {
            const isActive = location.pathname === item.to;
            const Icon = item.icon;
            return (
              <Link
                key={item.to}
                to={item.to}
                className={cn(
                  'flex items-center space-x-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-colors',
                  isActive
                    ? 'bg-primary/10 text-primary font-semibold'
                    : 'text-foreground-muted hover:text-foreground hover:bg-surface-elevated'
                )}
              >
                <Icon className="w-3.5 h-3.5" />
                <span>{item.label}</span>
                {item.badge && (
                  <span className="ml-1 text-[9px] uppercase px-1 py-0.2 rounded bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20 font-mono">
                    {item.badge}
                  </span>
                )}
              </Link>
            );
          })}
        </nav>

        {/* Right Actions */}
        <div className="flex items-center space-x-2">
          {/* Mode Pill */}
          <div className="hidden sm:flex items-center space-x-1.5 px-2.5 py-1 rounded-full border border-border bg-surface-elevated text-xs font-mono">
            <span className={cn(
              "w-2 h-2 rounded-full",
              llmMode.toLowerCase().includes('offline') ? 'bg-emerald-500' : 'bg-primary animate-pulse'
            )} />
            <span className="text-[11px] text-foreground-muted">
              {llmMode.toLowerCase().includes('offline') ? 'Offline Rule Engine (100% Deterministic)' : 'Gemini 2.5 Pro'}
            </span>
          </div>

          {/* Quick Command Palette Button */}
          <button
            onClick={onOpenCommandPalette}
            className="flex items-center space-x-1.5 px-2.5 py-1 rounded-md border border-border bg-surface-elevated hover:bg-border text-foreground-muted hover:text-foreground text-xs transition-colors"
            title="Open Command Palette (Ctrl+K / Cmd+K)"
          >
            <Command className="w-3.5 h-3.5" />
            <span className="hidden md:inline font-mono text-[11px]">Cmd+K</span>
          </button>

          {/* Theme Toggle */}
          <button
            onClick={onToggleDarkMode}
            className="p-1.5 rounded-md border border-border text-foreground-muted hover:text-foreground hover:bg-surface-elevated transition-colors"
            title={darkMode ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
          >
            {darkMode ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4" />}
          </button>
        </div>
      </div>
    </header>
  );
};
