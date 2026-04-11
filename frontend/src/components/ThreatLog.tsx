// =============================================================================
// ThreatLog.tsx - Terminal-style Threat Detection Log
// =============================================================================

import React, { useRef, useEffect } from 'react';
import {
  AlertTriangle,
  Terminal,
  Trash2,
  Clock,
  Hash,
  Gauge,
} from 'lucide-react';
import type { ThreatLogEntry } from '../types';

interface ThreatLogProps {
  entries: ThreatLogEntry[];
  onClear: () => void;
}

/**
 * Terminal-style scrolling log for threat detection events
 */
export const ThreatLog: React.FC<ThreatLogProps> = ({ entries, onClear }) => {
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to latest entry
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = 0;
    }
  }, [entries]);

  return (
    <div className="glass-card h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-cyber-border">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-threat-critical/10 flex items-center justify-center">
            <Terminal className="w-5 h-5 text-threat-critical" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-white flex items-center gap-2">
              Threat Log
              {entries.length > 0 && (
                <span className="px-2 py-0.5 rounded-full bg-threat-critical/20 text-threat-critical text-xs font-mono">
                  {entries.length}
                </span>
              )}
            </h3>
            <p className="text-sm text-cyber-muted">
              Security events above threshold
            </p>
          </div>
        </div>

        {/* Clear button */}
        <button
          onClick={onClear}
          disabled={entries.length === 0}
          className={`
            flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium
            transition-all duration-200
            ${entries.length > 0
              ? 'bg-cyber-surface hover:bg-cyber-border text-white'
              : 'bg-cyber-surface/50 text-cyber-muted cursor-not-allowed'
            }
          `}
        >
          <Trash2 className="w-4 h-4" />
          Clear
        </button>
      </div>

      {/* Log Entries */}
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto p-4 space-y-2 font-mono text-sm"
        style={{ maxHeight: '300px' }}
      >
        {entries.length === 0 ? (
          <div className="h-full flex items-center justify-center text-cyber-muted">
            <div className="text-center">
              
              <p>No threats detected</p>
              <p className="text-xs mt-1">System is operating normally</p>
            </div>
          </div>
        ) : (
          entries.map((entry, index) => (
            <div
              key={entry.id}
              className="log-entry log-entry-threat rounded-lg animate-slide-in"
              style={{ animationDelay: `${index * 50}ms` }}
            >
              {/* Entry Header */}
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 text-threat-critical animate-pulse" />
                  <span className="text-threat-critical font-semibold">
                    INTRUSION DETECTED
                  </span>
                </div>
                <div className="flex items-center gap-2 text-cyber-muted text-xs">
                  <Clock className="w-3 h-3" />
                  <span>{entry.localTime}</span>
                </div>
              </div>

              {/* Entry Details */}
              <div className="grid grid-cols-3 gap-4 text-xs">
                <div className="flex items-center gap-2">
                  <Hash className="w-3 h-3 text-cyber-muted" />
                  <span className="text-cyber-muted">CAN ID:</span>
                  <span className="text-white font-bold">{entry.canId}</span>
                </div>
                <div className="flex items-center gap-2">
                  <Gauge className="w-3 h-3 text-cyber-muted" />
                  <span className="text-cyber-muted">Score:</span>
                  <span className="text-threat-critical font-bold">
                    {entry.anomalyScore.toFixed(4)}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <Shield className="w-3 h-3 text-cyber-muted" />
                  <span className="text-cyber-muted">Confidence:</span>
                  <span className="text-white">
                    {(entry.confidence * 100).toFixed(1)}%
                  </span>
                </div>
              </div>

              {/* Timestamp */}
              <div className="mt-2 pt-2 border-t border-threat-critical/20 text-xs text-cyber-muted">
                <span className="opacity-70">{entry.timestamp}</span>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Footer with statistics */}
      {entries.length > 0 && (
        <div className="p-3 border-t border-cyber-border bg-cyber-darker/50">
          <div className="flex items-center justify-between text-xs text-cyber-muted">
            <span>
              Latest: {entries[0]?.localTime || 'N/A'}
            </span>
            <span>
              Total threats: {entries.length}
            </span>
            <span>
              Avg score:{' '}
              {(
                entries.reduce((sum, e) => sum + e.anomalyScore, 0) / entries.length
              ).toFixed(2)}
            </span>
          </div>
        </div>
      )}
    </div>
  );
};

export default ThreatLog;
