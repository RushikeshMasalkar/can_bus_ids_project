// =============================================================================
// Header.tsx - Dashboard Header with Status Indicator
// =============================================================================

import React from 'react';
import {
  Shield,
  Wifi,
  WifiOff,
  AlertTriangle,
  Activity,
  Zap,
} from 'lucide-react';
import type { ConnectionState, DashboardStats } from '../types';

interface HeaderProps {
  connectionState: ConnectionState;
  stats: DashboardStats;
}

/**
 * Dashboard header component with project title and live system status indicator.
 * Shows connection state and threat detection status with animated indicators.
 */
export const Header: React.FC<HeaderProps> = ({ connectionState, stats }) => {
  // Determine status indicator properties
  const getStatusConfig = () => {
    if (connectionState !== 'connected') {
      return {
        label: 'DISCONNECTED',
        color: 'text-gray-500',
        bgColor: 'bg-gray-500/20',
        borderColor: 'border-gray-500/50',
        dotClass: 'bg-gray-500',
        icon: WifiOff,
        pulse: false,
      };
    }

    switch (stats.networkStatus) {
      case 'threat':
        return {
          label: 'THREAT DETECTED',
          color: 'text-threat-critical',
          bgColor: 'bg-threat-critical/20',
          borderColor: 'border-threat-critical/50',
          dotClass: 'status-dot-threat',
          icon: AlertTriangle,
          pulse: true,
        };
      case 'buffering':
        return {
          label: 'INITIALIZING',
          color: 'text-yellow-500',
          bgColor: 'bg-yellow-500/20',
          borderColor: 'border-yellow-500/50',
          dotClass: 'bg-yellow-500',
          icon: Activity,
          pulse: true,
        };
      case 'secure':
      default:
        return {
          label: 'SYSTEM SECURE',
          color: 'text-threat-safe',
          bgColor: 'bg-threat-safe/20',
          borderColor: 'border-threat-safe/50',
          dotClass: 'status-dot-safe',
          icon: Shield,
          pulse: false,
        };
    }
  };

  const statusConfig = getStatusConfig();
  const StatusIcon = statusConfig.icon;

  // Format uptime
  const formatUptime = (seconds: number): string => {
    const hrs = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    return `${hrs.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <header className="glass-card px-6 py-4">
      <div className="flex items-center justify-between">
        {/* Left: Logo and Title */}
        <div className="flex items-center space-x-4">
          {/* Logo */}
          <div className="relative">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-neon-cyan/20 to-neon-blue/20 border border-neon-cyan/30 flex items-center justify-center">
              <Shield className="w-6 h-6 text-neon-cyan" />
            </div>
            {connectionState === 'connected' && (
              <div className="absolute -top-1 -right-1 w-3 h-3 rounded-full bg-threat-safe animate-pulse" />
            )}
          </div>

          {/* Title */}
          <div>
            <h1 className="text-xl font-bold text-white flex items-center gap-2">
              CAN Bus IDS
              <Zap className="w-5 h-5 text-neon-cyan" />
            </h1>
            <p className="text-sm text-cyber-muted">
              Transformer-Based Intrusion Detection
            </p>
          </div>
        </div>

        {/* Center: Connection Info */}
        <div className="hidden md:flex items-center space-x-6 text-sm">
          <div className="flex items-center gap-2 text-cyber-muted">
            <Wifi className={`w-4 h-4 ${connectionState === 'connected' ? 'text-threat-safe' : 'text-gray-500'}`} />
            <span className="font-mono">
              {connectionState === 'connected' ? 'ws://localhost:8000' : 'Offline'}
            </span>
          </div>
          <div className="h-4 w-px bg-cyber-border" />
          <div className="flex items-center gap-2 text-cyber-muted">
            <Activity className="w-4 h-4 text-neon-cyan" />
            <span className="font-mono">Uptime: {formatUptime(stats.uptime)}</span>
          </div>
        </div>

        {/* Right: Status Indicator */}
        <div
          className={`
            flex items-center gap-3 px-4 py-2 rounded-xl border
            ${statusConfig.bgColor} ${statusConfig.borderColor}
            transition-all duration-300
            ${statusConfig.pulse ? 'animate-pulse' : ''}
          `}
        >
          <div className={`w-3 h-3 rounded-full ${statusConfig.dotClass}`} />
          <StatusIcon className={`w-5 h-5 ${statusConfig.color}`} />
          <span className={`font-semibold text-sm tracking-wide ${statusConfig.color}`}>
            {statusConfig.label}
          </span>
        </div>
      </div>

      {/* Scan Line Effect */}
      {connectionState === 'connected' && stats.networkStatus === 'secure' && (
        <div className="scan-line" />
      )}
    </header>
  );
};

export default Header;
