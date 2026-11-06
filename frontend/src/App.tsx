import { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Navbar } from './components/Navbar';
import { CommandPalette } from './components/CommandPalette';
import { AnalysisWorkspace } from './pages/AnalysisWorkspace';
import { LogicLab } from './pages/LogicLab';
import { Rulebook } from './pages/Rulebook';
import { HistoryPage } from './pages/HistoryPage';
import { fetchHealth } from './lib/api';

export function App() {
  const [darkMode, setDarkMode] = useState<boolean>(() => {
    return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
  });
  const [cmdOpen, setCmdOpen] = useState(false);
  const [runtimeMode, setRuntimeMode] = useState('offline');

  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [darkMode]);

  useEffect(() => {
    fetchHealth()
      .then(res => setRuntimeMode(res.mode))
      .catch(() => setRuntimeMode('offline'));
  }, []);

  return (
    <BrowserRouter>
      <div className="min-h-screen bg-background text-foreground flex flex-col font-sans transition-colors">
        <Navbar
          darkMode={darkMode}
          onToggleDarkMode={() => setDarkMode(!darkMode)}
          onOpenCommandPalette={() => setCmdOpen(true)}
          llmMode={runtimeMode}
        />

        <main className="flex-1 flex flex-col">
          <Routes>
            <Route path="/" element={<AnalysisWorkspace />} />
            <Route path="/logic-lab" element={<LogicLab />} />
            <Route path="/rules" element={<Rulebook />} />
            <Route path="/sources" element={<Rulebook />} />
            <Route path="/history" element={<HistoryPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>

        <CommandPalette
          isOpen={cmdOpen}
          onClose={() => setCmdOpen(false)}
        />
      </div>
    </BrowserRouter>
  );
}

export default App;
