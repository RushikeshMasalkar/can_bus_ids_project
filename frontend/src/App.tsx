// =============================================================================
// App.tsx - Main Application Component
// =============================================================================

import React from 'react';
import { Dashboard } from './components/Dashboard';

/**
 * Root application component.
 * Renders the main dashboard for the CAN Bus IDS.
 */
const App: React.FC = () => {
  return (
    <div className="min-h-screen bg-cyber-darker">
      <Dashboard />
    </div>
  );
};

export default App;
