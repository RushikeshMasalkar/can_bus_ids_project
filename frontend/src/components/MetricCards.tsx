// =============================================================================
// MetricCards.tsx - KPI Metric Display Widgets
// =============================================================================

import React from 'react';
import {
  Activity,
  AlertOctagon,
  Gauge,
  Radio,
  TrendingUp,
  Cpu,
} from 'lucide-react';
import type { DashboardStats, ConnectionState } from '../types';

interface MetricCardsProps {
  stats: DashboardStats;
  connectionState: ConnectionState;
}

interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: React.ElementType;
  trend?: 'up' | 'down' | 'neutral';
  isThreat?: boolean;
  isLarge?: boolean;
  animate?: boolean;
}

/**
 * Individual metric card component
 */
const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  subtitle,
  icon: Icon,
  isThreat = false,
  isLarge = false,
  animate = false,
}) => {
  return (
    <div
      className={`
        glass-card p-5 transition-all duration-300 hover:scale-[1.02]
        ${isThreat ? 'border-threat-critical/50 shadow-neon-red' : 'hover:border-neon-cyan/30'}
        ${animate ? 'animate-pulse' : ''}
      `}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <span className="text-sm font-medium text-cyber-muted uppercase tracking-wider">
          {title}
        </span>
        <div
          className={`
            w-10 h-10 rounded-lg flex items-center justify-center
            ${isThreat
              ? 'bg-threat-critical/20 text-threat-critical'
              : 'bg-neon-cyan/10 text-neon-cyan'
            }
          `}
        >
          <Icon className="w-5 h-5" />
        </div>
      </div>

      {/* Value */}
      <div className="mb-2">
        <span
          className={`
            ${isLarge ? 'text-5xl' : 'text-4xl'}
            font-bold font-mono tracking-tight
            ${isThreat ? 'metric-value-threat' : 'metric-value'}
          `}
        >
          {value}
        </span>
      </div>

      {/* Subtitle */}
      {subtitle && (
        <p className="text-sm text-cyber-muted flex items-center gap-2">
          <TrendingUp className="w-4 h-4" />
          {subtitle}
        </p>
      )}
    </div>
  );
};

/**
 * Metric cards grid component displaying key performance indicators
 */
export const MetricCards: React.FC<MetricCardsProps> = ({
  stats,
  connectionState,
}) => {
  const isConnected = connectionState === 'connected';
  const isThreat = stats.networkStatus === 'threat';

  // Format large numbers
  const formatNumber = (num: number): string => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num.toString();
  };

  // Format anomaly score
  const formatScore = (score: number): string => {
    return score.toFixed(4);
  };

  // Determine network status label
  const getNetworkStatusLabel = (): string => {
    if (!isConnected) return 'OFFLINE';
    switch (stats.networkStatus) {
      case 'threat':
        return 'ATTACK';
      case 'buffering':
        return 'INIT';
      case 'secure':
      default:
        return 'SECURE';
    }
  };

  const getNetworkStatusColor = (): string => {
    if (!isConnected) return 'text-gray-500';
    switch (stats.networkStatus) {
      case 'threat':
        return 'text-threat-critical';
      case 'buffering':
        return 'text-yellow-500';
      case 'secure':
      default:
        return 'text-threat-safe';
    }
  };

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {/* Current Anomaly Score */}
      <MetricCard
        title="Anomaly Score"
        value={isConnected ? formatScore(stats.currentScore) : '---'}
        subtitle={`Threshold: ${stats.threshold.toFixed(2)}`}
        icon={Gauge}
        isThreat={isThreat}
        isLarge={true}
        animate={isThreat}
      />

      {/* Messages Processed */}
      <MetricCard
        title="Messages Processed"
        value={isConnected ? formatNumber(stats.messagesProcessed) : '---'}
        subtitle="Total CAN frames"
        icon={Activity}
      />

      {/* Attacks Detected */}
      <MetricCard
        title="Threats Detected"
        value={isConnected ? stats.attacksDetected : '---'}
        subtitle="Above threshold"
        icon={AlertOctagon}
        isThreat={stats.attacksDetected > 0}
      />

      {/* Network Status */}
      <div
        className={`
          glass-card p-5 transition-all duration-300
          ${isThreat ? 'border-threat-critical/50 animate-pulse' : ''}
        `}
      >
        <div className="flex items-center justify-between mb-4">
          <span className="text-sm font-medium text-cyber-muted uppercase tracking-wider">
            Network Status
          </span>
          <div className="w-10 h-10 rounded-lg flex items-center justify-center bg-neon-cyan/10">
            <Radio
              className={`w-5 h-5 ${isConnected ? 'text-neon-cyan animate-pulse' : 'text-gray-500'}`}
            />
          </div>
        </div>

        <div className="mb-2">
          <span
            className={`
              text-4xl font-bold font-mono tracking-tight
              ${getNetworkStatusColor()}
            `}
          >
            {getNetworkStatusLabel()}
          </span>
        </div>

        <div className="flex items-center gap-2 text-sm text-cyber-muted">
          <Cpu className="w-4 h-4" />
          <span>Buffer: {stats.bufferSize}/64</span>
          <div className="flex-1 h-1.5 bg-cyber-surface rounded-full overflow-hidden ml-2">
            <div
              className="h-full bg-gradient-to-r from-neon-cyan to-neon-blue transition-all duration-300"
              style={{ width: `${(stats.bufferSize / 64) * 100}%` }}
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default MetricCards;
