import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { AboutPage } from './pages/AboutPage';
import { AnalyzePage } from './pages/AnalyzePage';
import { DashboardPage } from './pages/DashboardPage';
import { HomePage } from './pages/HomePage';
import { PipelinePage } from './pages/PipelinePage';
import { ReportsPage } from './pages/ReportsPage';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/pipeline" element={<PipelinePage />} />
        <Route path="/integration" element={<AnalyzePage />} />
        <Route path="/reports" element={<ReportsPage />} />
        <Route path="/security" element={<AboutPage />} />

        <Route path="/analyze" element={<Navigate to="/integration" replace />} />
        <Route path="/about" element={<Navigate to="/security" replace />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
