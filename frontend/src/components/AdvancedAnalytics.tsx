import { useMemo, useState } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';

// Simulated byte-level delta data for heatmap visualization
function generateByteDeltas(): { row: number; col: number; value: number }[] {
  const data: { row: number; col: number; value: number }[] = [];
  for (let row = 0; row < 8; row++) {
    for (let col = 0; col < 8; col++) {
      data.push({
        row,
        col,
        value: Math.random() * 255,
      });
    }
  }
  return data;
}

// Simulated IAT histogram data
function generateIATData(timeframe: string): { bin: string; count: number }[] {
  const bins: { bin: string; count: number }[] = [];
  const multiplier = timeframe === '1m' ? 1 : timeframe === '5m' ? 5 : 60;
  const labels = ['0-1ms', '1-2ms', '2-5ms', '5-10ms', '10-20ms', '20-50ms', '50-100ms', '100ms+'];
  const baseCounts = [420, 380, 290, 85, 42, 18, 7, 3];

  for (let i = 0; i < labels.length; i++) {
    bins.push({
      bin: labels[i],
      count: Math.round(baseCounts[i] * multiplier * (0.8 + Math.random() * 0.4)),
    });
  }
  return bins;
}

function getHeatColor(value: number): string {
  const normalized = value / 255;
  if (normalized < 0.2) return '#dbeaff';
  if (normalized < 0.4) return '#9fc4f4';
  if (normalized < 0.6) return '#4E89D6';
  if (normalized < 0.8) return '#2a73cc';
  return '#1f5fa8';
}

const TIMEFRAME_OPTIONS = ['1m', '5m', '1h'] as const;

export function AdvancedAnalytics() {
  const [iatTimeframe, setIatTimeframe] = useState<(typeof TIMEFRAME_OPTIONS)[number]>('5m');

  const byteDeltas = useMemo(() => generateByteDeltas(), []);
  const iatData = useMemo(() => generateIATData(iatTimeframe), [iatTimeframe]);

  const maxIAT = useMemo(() => Math.max(1, ...iatData.map((d) => d.count)), [iatData]);

  return (
    <section className="mt-8">
      <div className="mb-6 flex items-center gap-3">
        <span className="material-symbols-outlined text-secondary">insights</span>
        <h2 className="font-headline text-xl font-bold text-primary">Advanced Network Analysis Tools</h2>
      </div>
      <p className="mb-8 max-w-3xl text-sm text-on-surface-variant">
        Supplementary analytical instruments are provided to facilitate granular inspection of CAN bus frame characteristics beyond the primary anomaly scoring pipeline. These visualizations enable SOC operators to identify subtle byte-level anomalies and temporal injection patterns that may precede or accompany classified attack sequences.
      </p>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Chart A: Byte-Level Delta Map */}
        <div className="rounded-xl bg-surface-container-lowest p-6">
          <div className="mb-2 flex items-center justify-between">
            <h3 className="font-headline text-sm font-bold text-primary">Byte-Level Delta Map</h3>
            <span className="rounded bg-secondary-fixed px-2 py-1 font-mono text-[10px] font-bold uppercase tracking-widest text-secondary">
              64-Frame Window
            </span>
          </div>
          <p className="mb-6 text-xs text-on-surface-variant">
            Heatmap visualization displaying byte-value deltas across the active 64-frame sequence window. Each cell represents the magnitude of byte-level deviation between consecutive frames, enabling rapid identification of anomalous payload mutations indicative of fuzzy injection or replay attack vectors.
          </p>

          <div className="overflow-hidden rounded-lg border border-outline-variant/20">
            <div className="bg-surface-container-low px-3 py-2">
              <div className="grid grid-cols-8 gap-0 text-center font-mono text-[9px] text-on-surface-variant">
                {Array.from({ length: 8 }, (_, i) => (
                  <div key={`col-header-${i}`}>B{i}</div>
                ))}
              </div>
            </div>
            <div className="grid grid-cols-8 gap-[1px] bg-surface-container-low p-[1px]">
              {byteDeltas.map((cell) => (
                <div
                  key={`cell-${cell.row}-${cell.col}`}
                  className="flex aspect-square items-center justify-center font-mono text-[9px] font-bold text-white"
                  style={{ backgroundColor: getHeatColor(cell.value) }}
                  title={`Byte ${cell.col}, Frame ${cell.row}: Δ${Math.round(cell.value)}`}
                >
                  {Math.round(cell.value)}
                </div>
              ))}
            </div>
            <div className="flex items-center justify-between bg-surface-container-low px-3 py-2">
              <span className="font-mono text-[9px] text-on-surface-variant">Low Δ</span>
              <div className="flex gap-0.5">
                {['#dbeaff', '#9fc4f4', '#4E89D6', '#2a73cc', '#1f5fa8'].map((color) => (
                  <div key={color} className="h-2 w-6 rounded-sm" style={{ backgroundColor: color }} />
                ))}
              </div>
              <span className="font-mono text-[9px] text-on-surface-variant">High Δ</span>
            </div>
          </div>

          <div className="mt-4 rounded-lg bg-surface-container-low p-3">
            <p className="font-mono text-[10px] text-on-surface-variant">
              Interpretation: Elevated delta concentrations in specific byte positions may indicate targeted payload manipulation. Uniform high-delta patterns across all bytes are characteristic of Denial-of-Service flooding (0xFF saturation).
            </p>
          </div>
        </div>

        {/* Chart B: Message Rate Interval Histogram */}
        <div className="rounded-xl bg-surface-container-lowest p-6">
          <div className="mb-2 flex items-center justify-between">
            <h3 className="font-headline text-sm font-bold text-primary">Inter-Frame Arrival Time (IAT) Distribution</h3>
          </div>
          <p className="mb-4 text-xs text-on-surface-variant">
            Histogram of inter-frame arrival time intervals plotted to detect potential message injection or bus flooding attacks. Anomalous temporal clustering at sub-millisecond intervals is indicative of high-priority DoS flooding, while irregular gaps may suggest selective frame suppression.
          </p>

          <div className="mb-4 flex items-center gap-2">
            <span className="text-xs text-on-surface-variant">Observation Window:</span>
            <div className="flex overflow-hidden rounded-lg border border-outline-variant bg-surface">
              {TIMEFRAME_OPTIONS.map((option) => (
                <button
                  key={option}
                  type="button"
                  onClick={() => setIatTimeframe(option)}
                  className={`px-3 py-1.5 text-[10px] font-bold uppercase tracking-wide transition-colors ${
                    iatTimeframe === option
                      ? 'bg-primary text-white'
                      : 'text-on-surface-variant hover:bg-surface-container-low'
                  }`}
                >
                  {option}
                </button>
              ))}
            </div>
          </div>

          <div className="h-56 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={iatData} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#d7dee8" vertical={false} />
                <XAxis
                  dataKey="bin"
                  tick={{ fontSize: 10, fill: '#5f6773' }}
                  stroke="#d7dee8"
                  axisLine={{ stroke: '#d7dee8' }}
                />
                <YAxis
                  tick={{ fontSize: 10, fill: '#5f6773' }}
                  stroke="#d7dee8"
                  axisLine={{ stroke: '#d7dee8' }}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#fff',
                    border: '1px solid #d7dee8',
                    borderRadius: '8px',
                    fontSize: '12px',
                  }}
                  formatter={(value: number) => [`${value.toLocaleString()} frames`, 'Count']}
                />
                <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                  {iatData.map((entry, index) => {
                    const ratio = entry.count / maxIAT;
                    const color = ratio > 0.7 ? '#2a73cc' : ratio > 0.3 ? '#4E89D6' : '#9fc4f4';
                    return <Cell key={`iat-bar-${index}`} fill={color} />;
                  })}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="mt-4 rounded-lg bg-surface-container-low p-3">
            <p className="font-mono text-[10px] text-on-surface-variant">
              Statistical baseline: Normal CAN 2.0B traffic exhibits a predictable IAT distribution centered at 1–5ms for high-priority safety frames. Significant deviation from this profile warrants further forensic investigation.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
