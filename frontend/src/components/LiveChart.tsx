// =============================================================================
// LiveChart.tsx - Real-time Anomaly Score Line Chart
// =============================================================================

import React, { useMemo } from 'react';
import {
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
  ResponsiveContainer,
  Area,
  ComposedChart,
} from 'recharts';
import { Activity, AlertTriangle } from 'lucide-react';
import type { ChartDataPoint } from '../types';

interface LiveChartProps {
  data: ChartDataPoint[];
  threshold: number;
}

interface CustomTooltipProps {
  active?: boolean;
  payload?: Array<{
    value: number;
    payload: ChartDataPoint;
  }>;
  label?: string;
}

/**
 * Custom tooltip component for the chart
 */
const CustomTooltip: React.FC<CustomTooltipProps> = ({ active, payload }) => {
  if (!active || !payload || !payload.length) return null;

  const data = payload[0].payload;
  const isAttack = data.isAttack;

  return (
    <div
      className={`
        glass-card px-4 py-3 border
        ${isAttack ? 'border-threat-critical/50' : 'border-neon-cyan/30'}
      `}
    >
      <div className="flex items-center gap-2 mb-2">
        {isAttack ? (
          <AlertTriangle className="w-4 h-4 text-threat-critical" />
        ) : (
          <Activity className="w-4 h-4 text-neon-cyan" />
        )}
        <span
          className={`font-semibold ${isAttack ? 'text-threat-critical' : 'text-neon-cyan'}`}
        >
          {isAttack ? 'THREAT DETECTED' : 'Normal Traffic'}
        </span>
      </div>

      <div className="space-y-1 text-sm">
        <div className="flex justify-between gap-4">
          <span className="text-cyber-muted">Score:</span>
          <span className={`font-mono font-bold ${isAttack ? 'text-threat-critical' : 'text-white'}`}>
            {data.score.toFixed(4)}
          </span>
        </div>
        <div className="flex justify-between gap-4">
          <span className="text-cyber-muted">CAN ID:</span>
          <span className="font-mono text-white">{data.canId}</span>
        </div>
        <div className="flex justify-between gap-4">
          <span className="text-cyber-muted">Time:</span>
          <span className="font-mono text-white">{data.time}</span>
        </div>
      </div>
    </div>
  );
};

/**
 * Real-time line chart displaying anomaly scores over time
 */
export const LiveChart: React.FC<LiveChartProps> = ({ data, threshold }) => {
  // Calculate Y-axis domain
  const yDomain = useMemo(() => {
    if (data.length === 0) return [0, threshold * 1.5];
    const maxScore = Math.max(...data.map(d => d.score), threshold);
    return [0, Math.ceil(maxScore * 1.2)];
  }, [data, threshold]);

  // Count attacks in visible data
  const attackCount = useMemo(() => {
    return data.filter(d => d.isAttack).length;
  }, [data]);

  return (
    <div className="glass-card p-5 h-full">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-neon-cyan/10 flex items-center justify-center">
            <Activity className="w-5 h-5 text-neon-cyan" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-white">
              Real-Time Telemetry
            </h3>
            <p className="text-sm text-cyber-muted">
              Anomaly score over time
            </p>
          </div>
        </div>

        {/* Legend */}
        <div className="flex items-center gap-4 text-sm">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-neon-cyan" />
            <span className="text-cyber-muted">Normal</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-threat-critical" />
            <span className="text-cyber-muted">Threat ({attackCount})</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-8 h-0.5 bg-yellow-500 border-dashed" />
            <span className="text-cyber-muted">Threshold</span>
          </div>
        </div>
      </div>

      {/* Chart */}
      <div className="h-[300px]">
        {data.length === 0 ? (
          <div className="h-full flex items-center justify-center text-cyber-muted">
            <div className="text-center">
              <Activity className="w-12 h-12 mx-auto mb-3 opacity-30" />
              <p>Waiting for telemetry data...</p>
              <p className="text-sm mt-1">Connect to start monitoring</p>
            </div>
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart
              data={data}
              margin={{ top: 20, right: 30, left: 0, bottom: 0 }}
            >
              <defs>
                {/* Gradient for the area fill */}
                <linearGradient id="scoreGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#00f5ff" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#00f5ff" stopOpacity={0} />
                </linearGradient>

                {/* Gradient for threat areas */}
                <linearGradient id="threatGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#ff0040" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#ff0040" stopOpacity={0} />
                </linearGradient>

                {/* Glow filter for the line */}
                <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
                  <feGaussianBlur stdDeviation="2" result="coloredBlur" />
                  <feMerge>
                    <feMergeNode in="coloredBlur" />
                    <feMergeNode in="SourceGraphic" />
                  </feMerge>
                </filter>
              </defs>

              <CartesianGrid
                strokeDasharray="3 3"
                stroke="rgba(48, 54, 61, 0.5)"
                vertical={false}
              />

              <XAxis
                dataKey="time"
                stroke="#484f58"
                tick={{ fill: '#8b949e', fontSize: 11 }}
                tickLine={false}
                axisLine={{ stroke: '#30363d' }}
                interval="preserveStartEnd"
              />

              <YAxis
                domain={yDomain}
                stroke="#484f58"
                tick={{ fill: '#8b949e', fontSize: 11 }}
                tickLine={false}
                axisLine={{ stroke: '#30363d' }}
                tickFormatter={(value) => value.toFixed(1)}
              />

              <Tooltip content={<CustomTooltip />} />

              {/* Threshold reference line */}
              <ReferenceLine
                y={threshold}
                stroke="#eab308"
                strokeDasharray="8 4"
                strokeWidth={2}
                label={{
                  value: `Threshold: ${threshold.toFixed(2)}`,
                  position: 'right',
                  fill: '#eab308',
                  fontSize: 11,
                  fontFamily: 'JetBrains Mono',
                }}
              />

              {/* Area fill under the line */}
              <Area
                type="monotone"
                dataKey="score"
                stroke="none"
                fill="url(#scoreGradient)"
                isAnimationActive={false}
              />

              {/* Main line */}
              <Line
                type="monotone"
                dataKey="score"
                stroke="#00f5ff"
                strokeWidth={2}
                dot={(props) => {
                  const { cx, cy, payload } = props;
                  if (!payload || !payload.isAttack) return <></>;

                  return (
                    <circle
                      key={`dot-${cx}-${cy}`}
                      cx={cx}
                      cy={cy}
                      r={6}
                      fill="#ff0040"
                      stroke="#ff0040"
                      strokeWidth={2}
                      filter="url(#glow)"
                    />
                  );
                }}
                activeDot={{
                  r: 6,
                  fill: '#00f5ff',
                  stroke: '#00f5ff',
                  strokeWidth: 2,
                  filter: 'url(#glow)',
                }}
                isAnimationActive={false}
                filter="url(#glow)"
              />
            </ComposedChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
};

export default LiveChart;
