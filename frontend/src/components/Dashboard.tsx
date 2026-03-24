// =============================================================================
// Dashboard.tsx - Main Dashboard Layout Component
// =============================================================================

import React from 'react';
import { RefreshCw, Power, Wifi, WifiOff } from 'lucide-react';
import { Header } from './Header';
import { MetricCards } from './MetricCards';
import { LiveChart } from './LiveChart';
import { ThreatLog } from './ThreatLog';
import { useWebSocket } from '../hooks/useWebSocket';

/**
 * Main dashboard component that orchestrates all sub-components
 * and manages the WebSocket connection state.
 */
export const Dashboard: React.FC = () => {
  const {
    connectionState,
    stats,
    chartData,
    threatLog,
    connect,
    disconnect,
    clearLog,
  } = useWebSocket();

  const isConnected = connectionState === 'connected';
  const isConnecting = connectionState === 'connecting';

  return (
    <div className="min-h-screen flex flex-col p-4 lg:p-6 gap-4 lg:gap-6">
      {/* Header */}
      <Header connectionState={connectionState} stats={stats} />

      {/* Main Content */}
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-3 gap-4 lg:gap-6">
        {/* Left Column: Chart + Metrics */}
        <div className="lg:col-span-2 flex flex-col gap-4 lg:gap-6">
          {/* Metric Cards */}
          <MetricCards stats={stats} connectionState={connectionState} />

          {/* Live Chart */}
          <div className="flex-1 min-h-[400px]">
            <LiveChart data={chartData} threshold={stats.threshold} />
          </div>
        </div>

        {/* Right Column: Threat Log + Controls */}
        <div className="flex flex-col gap-4 lg:gap-6">
          {/* Connection Controls */}
          <div className="glass-card p-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-semibold text-white uppercase tracking-wider">
                Connection Control
              </h3>
              <div className="flex items-center gap-2">
                {isConnected ? (
                  <Wifi className="w-4 h-4 text-threat-safe" />
                ) : (
                  <WifiOff className="w-4 h-4 text-gray-500" />
                )}
                <span
                  className={`text-xs font-medium ${
                    isConnected
                      ? 'text-threat-safe'
                      : isConnecting
                        ? 'text-yellow-500'
                        : 'text-gray-500'
                  }`}
                >
                  {isConnecting
                    ? 'Connecting...'
                    : isConnected
                      ? 'Connected'
                      : 'Disconnected'}
                </span>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              {/* Connect Button */}
              <button
                onClick={connect}
                disabled={isConnected || isConnecting}
                className={`
                  flex items-center justify-center gap-2 px-4 py-3 rounded-xl
                  font-medium text-sm transition-all duration-200
                  ${
                    isConnected || isConnecting
                      ? 'bg-cyber-surface text-cyber-muted cursor-not-allowed'
                      : 'bg-gradient-to-r from-neon-cyan/20 to-neon-blue/20 border border-neon-cyan/30 text-neon-cyan hover:border-neon-cyan/50 hover:shadow-neon-cyan'
                  }
                `}
              >
                {isConnecting ? (
                  <RefreshCw className="w-4 h-4 animate-spin" />
                ) : (
                  <Power className="w-4 h-4" />
                )}
                Connect
              </button>

              {/* Disconnect Button */}
              <button
                onClick={disconnect}
                disabled={!isConnected}
                className={`
                  flex items-center justify-center gap-2 px-4 py-3 rounded-xl
                  font-medium text-sm transition-all duration-200
                  ${
                    !isConnected
                      ? 'bg-cyber-surface text-cyber-muted cursor-not-allowed'
                      : 'bg-gradient-to-r from-threat-critical/20 to-threat-high/20 border border-threat-critical/30 text-threat-critical hover:border-threat-critical/50 hover:shadow-neon-red'
                  }
                `}
              >
                <Power className="w-4 h-4" />
                Disconnect
              </button>
            </div>

            {/* Connection Info */}
            <div className="mt-4 pt-4 border-t border-cyber-border">
              <div className="grid grid-cols-2 gap-3 text-xs">
                <div>
                  <span className="text-cyber-muted">Endpoint</span>
                  <p className="text-white font-mono mt-1">ws://localhost:8000</p>
                </div>
                <div>
                  <span className="text-cyber-muted">Window Size</span>
                  <p className="text-white font-mono mt-1">64 frames</p>
                </div>
              </div>
            </div>
          </div>

          {/* Threat Log */}
          <div className="flex-1 min-h-[300px]">
            <ThreatLog entries={threatLog} onClear={clearLog} />
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="glass-card px-6 py-3">
        <div className="flex items-center justify-between text-xs text-cyber-muted">
          <div className="flex items-center gap-4">
            <span>CAN Bus IDS v1.0.0</span>
            <span className="hidden sm:inline">|</span>
            <span className="hidden sm:inline">DistilBERT Transformer Model</span>
          </div>
          <div className="flex items-center gap-4">
            <span>Window: 64 frames</span>
            <span>|</span>
            <span className="font-mono">Threshold: {stats.threshold.toFixed(4)}</span>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Dashboard;
