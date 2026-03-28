import { useMemo } from 'react';
import { CartesianGrid, Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { useLiveStream } from '../hooks/useLiveStream';
import { ConsoleLayout } from '../layout/ConsoleLayout';

const DONUT_COLORS = ['#162839', '#00677f', '#00ccf9', '#b7eaff', '#48b8ab'];
const FALLBACK_TYPES = ['DoS', 'Fuzzy', 'Gear', 'RPM'];

export function DashboardPage() {
  const {
    points,
    alerts,
    connected,
    totalAnalyzed,
    attacksDetected,
    detectionRate,
    threshold,
    scoreDistribution,
    attackBreakdown,
  } = useLiveStream();

  const averageScore = useMemo(() => {
    if (points.length === 0) {
      return 0;
    }
    const total = points.reduce((acc, point) => acc + point.score, 0);
    return total / points.length;
  }, [points]);

  const donutData = useMemo(() => {
    if (attackBreakdown.length === 0) {
      return FALLBACK_TYPES.map((name) => ({ name, value: 0 }));
    }
    return attackBreakdown;
  }, [attackBreakdown]);

  const donutTotal = useMemo(
    () => donutData.reduce((acc, item) => acc + item.value, 0),
    [donutData]
  );

  const donutGradient = useMemo(() => {
    if (donutTotal === 0) {
      return 'conic-gradient(#eceef0 0deg 360deg)';
    }

    let running = 0;
    const segments = donutData.map((item, index) => {
      const start = running;
      const span = (item.value / donutTotal) * 360;
      running += span;
      return `${DONUT_COLORS[index % DONUT_COLORS.length]} ${start.toFixed(2)}deg ${running.toFixed(2)}deg`;
    });

    return `conic-gradient(${segments.join(',')})`;
  }, [donutData, donutTotal]);

  const maxHistogramCount = useMemo(
    () => Math.max(1, ...scoreDistribution.map((item) => item.count)),
    [scoreDistribution]
  );

  const cpuLoad = Math.min(95, Math.max(10, Math.round((detectionRate + (connected ? 8 : 0)) / 4)));

  return (
    <ConsoleLayout activeNav="dashboard">
      <div className="mx-auto max-w-[1440px] p-8">
        <div className="mb-8 grid grid-cols-1 gap-4 md:grid-cols-5">
          <div className="flex flex-col justify-between rounded-xl bg-surface-container-lowest p-5">
            <span className="font-headline text-xs font-bold uppercase tracking-wider text-on-surface-variant/70">Total Analyzed</span>
            <div className="mt-2 flex items-end justify-between">
              <span className="font-headline text-2xl font-bold text-primary">{totalAnalyzed.toLocaleString()}</span>
              <div className="flex h-6 w-16 items-end gap-0.5 rounded-sm bg-tertiary-fixed-dim/20 px-1">
                {[30, 50, 40, 80, 60].map((height) => (
                  <div key={`ta-${height}`} className="w-1 bg-tertiary-fixed-dim" style={{ height: `${height}%` }} />
                ))}
              </div>
            </div>
          </div>

          <div className="flex flex-col justify-between rounded-xl border-l-4 border-error bg-surface-container-lowest p-5">
            <span className="font-headline text-xs font-bold uppercase tracking-wider text-on-surface-variant/70">Attacks Detected</span>
            <div className="mt-2 flex items-center justify-between">
              <span className="font-headline text-2xl font-bold text-error">{attacksDetected}</span>
              <div className={`h-3 w-3 rounded-full ${attacksDetected > 0 ? 'pulse-red bg-error' : 'bg-secondary'}`} />
            </div>
          </div>

          <div className="flex flex-col justify-between rounded-xl bg-surface-container-lowest p-5">
            <span className="font-headline text-xs font-bold uppercase tracking-wider text-on-surface-variant/70">Detection Rate</span>
            <div className="mt-2">
              <span className="font-headline text-2xl font-bold text-primary">{detectionRate.toFixed(2)}%</span>
              <div className="mt-2 h-1 w-full overflow-hidden rounded-full bg-surface-container-high">
                <div className="h-full bg-secondary" style={{ width: `${Math.min(100, detectionRate).toFixed(0)}%` }} />
              </div>
            </div>
          </div>

          <div className="flex flex-col justify-between rounded-xl bg-surface-container-lowest p-5">
            <span className="font-headline text-xs font-bold uppercase tracking-wider text-on-surface-variant/70">Avg. Anomaly Score</span>
            <div className="mt-2">
              <span className="font-mono text-2xl text-primary">{averageScore.toFixed(3)}</span>
              <p className="text-[10px] font-bold text-on-tertiary-container">Threshold {threshold.toFixed(3)}</p>
            </div>
          </div>

          <div className="relative flex flex-col justify-between overflow-hidden rounded-xl bg-primary p-5 text-on-primary">
            <div className="absolute -mr-12 -mt-12 h-24 w-24 rounded-full bg-white/5" />
            <span className="font-headline text-xs font-bold uppercase tracking-wider opacity-60">System Status</span>
            <div className="mt-2 flex items-center gap-2">
              <div
                className={`h-2.5 w-2.5 rounded-full ${connected ? 'bg-tertiary-fixed shadow-[0_0_10px_rgba(137,245,231,0.6)]' : 'bg-error'}`}
              />
              <span className="font-headline text-xl font-bold">{connected ? 'LIVE' : 'OFFLINE'}</span>
            </div>
          </div>
        </div>

        <div className="bento-grid">
          <div className="col-span-12 min-h-[400px] rounded-xl bg-surface-container-lowest p-6 lg:col-span-8">
            <div className="mb-6 flex items-center justify-between">
              <h3 className="font-headline text-lg font-bold text-primary">Real-time Anomaly Score</h3>
              <div className="flex gap-2">
                <span className="flex items-center gap-1.5 text-xs font-medium text-on-surface-variant">
                  <span className="h-2 w-2 rounded-full bg-secondary" />
                  Live Stream
                </span>
                <span className="flex items-center gap-1.5 text-xs font-medium text-on-surface-variant">
                  <span className="h-2 w-2 rounded-full bg-error" />
                  Attack Threshold
                </span>
              </div>
            </div>

            <div className="relative mt-4 h-72 w-full border-b border-l border-outline-variant/30">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={points.length > 0 ? points : [{ time: '--:--:--', score: 0, attackScore: null, threshold: 0, id: 0, label: 'NORMAL', attackType: null }]}> 
                  <CartesianGrid strokeDasharray="3 3" stroke="#dfe3e6" />
                  <XAxis dataKey="time" tick={{ fontSize: 10, fill: '#74777d' }} minTickGap={22} stroke="#c4c6cd" />
                  <YAxis tick={{ fontSize: 10, fill: '#74777d' }} stroke="#c4c6cd" domain={[0, 1]} />
                  <Tooltip />
                  <ReferenceLine y={threshold || 0.75} stroke="#ba1a1a" strokeDasharray="6 4" />
                  <Line type="monotone" dataKey="score" stroke="#00677f" strokeWidth={2.5} dot={false} isAnimationActive />
                  <Line
                    type="monotone"
                    dataKey="attackScore"
                    stroke="transparent"
                    dot={{ fill: '#ba1a1a', stroke: '#ba1a1a', r: 4 }}
                    connectNulls={false}
                    isAnimationActive
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="col-span-12 flex flex-col rounded-xl bg-surface-container-lowest p-6 lg:col-span-4">
            <h3 className="mb-6 font-headline text-lg font-bold text-primary">Attack Vector Distribution</h3>
            <div className="relative flex flex-grow items-center justify-center">
              <div className="relative h-48 w-48 rounded-full" style={{ background: donutGradient }}>
                <div className="absolute left-1/2 top-1/2 h-28 w-28 -translate-x-1/2 -translate-y-1/2 rounded-full bg-surface-container-lowest" />
              </div>
              <div className="absolute flex flex-col items-center">
                <span className="font-headline text-2xl font-bold text-primary">{attacksDetected}</span>
                <span className="text-[10px] font-bold uppercase text-on-surface-variant">Total</span>
              </div>
            </div>
            <div className="mt-6 grid grid-cols-2 gap-4">
              {donutData.slice(0, 4).map((item, index) => {
                const percent = donutTotal > 0 ? (item.value / donutTotal) * 100 : 0;
                return (
                  <div key={`legend-${item.name}`} className="flex items-center gap-2">
                    <div className="h-3 w-3 rounded-sm" style={{ backgroundColor: DONUT_COLORS[index % DONUT_COLORS.length] }} />
                    <span className="text-xs font-medium">{item.name} ({percent.toFixed(0)}%)</span>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="col-span-12 rounded-xl bg-surface-container-lowest p-6 lg:col-span-9">
            <div className="mb-6 flex items-center justify-between">
              <h3 className="font-headline text-lg font-bold text-primary">Recent Security Alerts</h3>
              <button className="text-xs font-bold uppercase tracking-widest text-secondary hover:underline" type="button">
                View All Logs
              </button>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left">
                <thead className="bg-surface-container-low">
                  <tr className="text-[10px] font-bold uppercase tracking-wider text-on-surface-variant/70">
                    <th className="px-4 py-3 first:rounded-l-lg">Time</th>
                    <th className="px-4 py-3">Score</th>
                    <th className="px-4 py-3">Attack Type</th>
                    <th className="px-4 py-3">Confidence</th>
                    <th className="px-4 py-3 last:rounded-r-lg">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-surface-container-low">
                  {alerts.length === 0 ? (
                    <tr>
                      <td className="px-4 py-6 text-sm text-on-surface-variant" colSpan={5}>
                        No alerts in the live stream yet.
                      </td>
                    </tr>
                  ) : (
                    alerts.map((alert, index) => (
                      <tr key={alert.id} className="transition-colors hover:bg-surface-container-high/20">
                        <td className="px-4 py-4 font-mono text-xs">{alert.time}</td>
                        <td className="px-4 py-4 font-mono text-xs font-bold text-error">{alert.score.toFixed(3)}</td>
                        <td className="px-4 py-4">
                          <span className="rounded bg-error-container px-2 py-1 text-[10px] font-bold text-on-error-container">
                            {alert.attackType.toUpperCase()}
                          </span>
                        </td>
                        <td className="px-4 py-4 font-mono text-xs">{(alert.confidence * 100).toFixed(1)}%</td>
                        <td className="px-4 py-4">
                          <span className="flex items-center gap-1.5 text-[10px] font-bold text-on-surface-variant">
                            <span className={`h-1.5 w-1.5 rounded-full ${index === 0 ? 'bg-error' : 'bg-secondary'}`} />
                            {index === 0 ? 'Investigating' : 'Resolved'}
                          </span>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>

          <div className="col-span-12 flex flex-col gap-6 lg:col-span-3">
            <div className="flex-grow rounded-xl bg-surface-container-lowest p-6">
              <h3 className="mb-4 font-headline text-sm font-bold text-primary">Score Distribution</h3>
              <div className="flex h-32 w-full items-end gap-1">
                {(scoreDistribution.length > 0 ? scoreDistribution : new Array(8).fill(null).map((_, idx) => ({ bin: `${idx}`, count: 0 }))).map((bar, idx) => {
                  const height = Math.max(5, (bar.count / maxHistogramCount) * 100);
                  const barTone = idx >= 5 ? 'bg-error/50' : 'bg-secondary/40';
                  return <div key={`hist-${bar.bin}-${idx}`} className={`flex-grow rounded-t-sm ${barTone}`} style={{ height: `${height}%` }} />;
                })}
              </div>
              <div className="mt-2 flex justify-between font-mono text-[9px] text-on-surface-variant">
                <span>0.0</span>
                <span>Normal Range</span>
                <span>1.0</span>
              </div>
            </div>

            <div className="rounded-xl bg-primary p-6 text-on-primary">
              <h3 className="mb-4 border-b border-white/10 pb-2 font-headline text-sm font-bold">System Health</h3>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-xs opacity-70">Backend</span>
                  <span className={`text-xs font-bold ${connected ? 'text-tertiary-fixed' : 'text-error-container'}`}>
                    {connected ? 'Online' : 'Offline'}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs opacity-70">Model</span>
                  <span className="text-xs font-bold">Loaded: v1.2.0</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs opacity-70">Device</span>
                  <span className="text-xs font-bold">OBD-II Interface</span>
                </div>
                <div className="pt-2">
                  <div className="mb-1.5 flex items-center justify-between">
                    <span className="text-xs opacity-70">CPU Load</span>
                    <span className="font-mono text-xs">{cpuLoad}%</span>
                  </div>
                  <div className="h-1 w-full overflow-hidden rounded-full bg-white/10">
                    <div className="h-full bg-secondary-container" style={{ width: `${cpuLoad}%` }} />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </ConsoleLayout>
  );
}
