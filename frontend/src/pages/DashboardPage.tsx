// FILE: frontend/src/pages/DashboardPage.tsx - FIXES: FIX 1, FIX 2
import { useEffect, useMemo, useRef, useState, type CSSProperties } from 'react';
import { CartesianGrid, Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { Activity, AlertTriangle, Shield, Sigma, ShieldCheck } from 'lucide-react';
import { apiClient } from '../api/client';
import { useLiveStreamContext } from '../context/LiveStreamContext';
import { AppLayout, useAnalysisControl } from '../layout/AppLayout';
import { AdvancedAnalytics } from '../components/AdvancedAnalytics';

const DONUT_COLORS = ['#1A6FD4', '#3A80DA', '#5B8FD9', '#7EA8E3', '#AAC4ED'];
const FALLBACK_TYPES = ['DoS', 'Fuzzy', 'Gear', 'RPM'];
const MAX_RENDERED_POINTS = 90;
const MAX_RENDERED_ALERTS = 14;

const CARD_STYLE: CSSProperties = {
  background: 'var(--color-bg-card)',
  border: '1px solid var(--color-border)',
  borderRadius: '10px',
  boxShadow: 'var(--shadow-card)',
};

const SECTION_LABEL_STYLE: CSSProperties = {
  fontSize: '0.68rem',
  fontWeight: 600,
  textTransform: 'uppercase',
  letterSpacing: '0.09em',
  color: 'var(--color-text-muted)',
  paddingLeft: '8px',
  borderLeft: '3px solid var(--color-primary)',
  marginBottom: '12px',
  lineHeight: 1,
};

export function DashboardPage() {
  return (
    <AppLayout>
      <DashboardContent />
    </AppLayout>
  );
}

function DashboardContent() {
  const { points, alerts, connected, threshold } = useLiveStreamContext();
  const { isAnalysisRunning } = useAnalysisControl();

  const [renderedPoints, setRenderedPoints] = useState<typeof points>([]);
  const [renderedAlerts, setRenderedAlerts] = useState<typeof alerts>([]);
  const [renderedTotalAnalyzed, setRenderedTotalAnalyzed] = useState(0);
  const [renderedAttacksDetected, setRenderedAttacksDetected] = useState(0);

  const lastProcessedPointIdRef = useRef(0);
  const lastProcessedAlertIdRef = useRef(0);
  const ignoreUntilPointIdRef = useRef(0);
  const ignoreUntilAlertIdRef = useRef(0);

  const [thresholdInput, setThresholdInput] = useState(0);
  const [thresholdEdited, setThresholdEdited] = useState(false);
  const [streamIntervalMs, setStreamIntervalMs] = useState(650);
  const [controlBusy, setControlBusy] = useState<'threshold' | 'speed' | null>(null);
  const [controlNotice, setControlNotice] = useState<string | null>(null);
  const [controlError, setControlError] = useState<string | null>(null);

  useEffect(() => {
    if (!thresholdEdited && threshold > 0) {
      setThresholdInput(Number(threshold.toFixed(3)));
    }
  }, [threshold, thresholdEdited]);

  useEffect(() => {
    let active = true;

    apiClient
      .getStreamConfig()
      .then((config) => {
        if (active) {
          setStreamIntervalMs(config.interval_ms);
        }
      })
      .catch(() => undefined);

    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    if (!isAnalysisRunning) {
      const latestPointId = points.length > 0 ? points[points.length - 1].id : 0;
      ignoreUntilPointIdRef.current = Math.max(ignoreUntilPointIdRef.current, latestPointId);
      return;
    }

    const cutoff = Math.max(lastProcessedPointIdRef.current, ignoreUntilPointIdRef.current);
    const incomingPoints = points.filter((point) => point.id > cutoff);

    if (incomingPoints.length === 0) {
      return;
    }

    lastProcessedPointIdRef.current = incomingPoints[incomingPoints.length - 1].id;

    setRenderedPoints((prev) => {
      const merged = [...prev, ...incomingPoints];
      return merged.slice(Math.max(0, merged.length - MAX_RENDERED_POINTS));
    });

    setRenderedTotalAnalyzed((prev) => prev + incomingPoints.length);
    const newAttackCount = incomingPoints.filter((point) => point.label === 'ATTACK').length;
    if (newAttackCount > 0) {
      setRenderedAttacksDetected((prev) => prev + newAttackCount);
    }
  }, [points, isAnalysisRunning]);

  useEffect(() => {
    if (!isAnalysisRunning) {
      const latestAlertId = alerts.length > 0 ? alerts[0].id : 0;
      ignoreUntilAlertIdRef.current = Math.max(ignoreUntilAlertIdRef.current, latestAlertId);
      return;
    }

    const cutoff = Math.max(lastProcessedAlertIdRef.current, ignoreUntilAlertIdRef.current);
    const incomingAlerts = alerts.filter((alert) => alert.id > cutoff);

    if (incomingAlerts.length === 0) {
      return;
    }

    lastProcessedAlertIdRef.current = Math.max(...incomingAlerts.map((alert) => alert.id));

    setRenderedAlerts((prev) => {
      const unique = new Map<number, (typeof alerts)[number]>();
      [...incomingAlerts, ...prev].forEach((alert) => {
        if (!unique.has(alert.id)) {
          unique.set(alert.id, alert);
        }
      });
      return Array.from(unique.values()).slice(0, MAX_RENDERED_ALERTS);
    });
  }, [alerts, isAnalysisRunning]);

  async function handleThresholdUpdate() {
    setControlBusy('threshold');
    setControlError(null);
    setControlNotice(null);

    try {
      const safeThreshold = Number(thresholdInput.toFixed(6));
      await apiClient.updateThreshold(safeThreshold, true);
      setThresholdEdited(false);
      setControlNotice('Threshold updated successfully.');
    } catch {
      setControlError('Unable to update threshold.');
    } finally {
      setControlBusy(null);
    }
  }

  async function handleSpeedUpdate() {
    setControlBusy('speed');
    setControlError(null);
    setControlNotice(null);

    try {
      const config = await apiClient.updateStreamConfig(streamIntervalMs);
      setStreamIntervalMs(config.interval_ms);
      setControlNotice(`Live sequence speed set to ${config.frames_per_second.toFixed(2)} fps.`);
    } catch {
      setControlError('Unable to update stream speed.');
    } finally {
      setControlBusy(null);
    }
  }

  const averageScore = useMemo(() => {
    if (renderedPoints.length === 0) {
      return 0;
    }
    const total = renderedPoints.reduce((acc, point) => acc + point.score, 0);
    return total / renderedPoints.length;
  }, [renderedPoints]);

  const detectionRate = useMemo(() => {
    if (!renderedTotalAnalyzed) {
      return 0;
    }
    return (renderedAttacksDetected / renderedTotalAnalyzed) * 100;
  }, [renderedAttacksDetected, renderedTotalAnalyzed]);

  const attackBreakdown = useMemo(() => {
    const map = new Map<string, number>();
    renderedAlerts.forEach((item) => {
      map.set(item.attackType, (map.get(item.attackType) ?? 0) + 1);
    });
    return Array.from(map.entries()).map(([name, value]) => ({ name, value }));
  }, [renderedAlerts]);

  const donutData = useMemo(() => {
    if (attackBreakdown.length === 0) {
      return FALLBACK_TYPES.map((name) => ({ name, value: 0 }));
    }
    return attackBreakdown;
  }, [attackBreakdown]);

  const donutTotal = useMemo(() => donutData.reduce((acc, item) => acc + item.value, 0), [donutData]);

  const donutGradient = useMemo(() => {
    if (donutTotal === 0) {
      return 'conic-gradient(#ECEFF5 0deg 360deg)';
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

  const scoreDistribution = useMemo(() => {
    if (renderedPoints.length === 0) {
      return [] as Array<{ bin: string; count: number }>;
    }

    const min = Math.min(...renderedPoints.map((item) => item.score));
    const max = Math.max(...renderedPoints.map((item) => item.score));
    const bins = 8;
    const width = (max - min) / bins || 0.1;
    const counts = new Array<number>(bins).fill(0);

    renderedPoints.forEach((item) => {
      const idx = Math.min(bins - 1, Math.floor((item.score - min) / width));
      counts[idx] += 1;
    });

    return counts.map((count, idx) => {
      const start = min + idx * width;
      const end = start + width;
      return {
        bin: `${start.toFixed(2)}-${end.toFixed(2)}`,
        count,
      };
    });
  }, [renderedPoints]);

  const maxHistogramCount = useMemo(() => {
    const counts = scoreDistribution.map((item) => item.count);
    return counts.length > 0 ? Math.max(1, ...counts) : 1;
  }, [scoreDistribution]);

  const eventFeed = useMemo(() => {
    const alertsById = new Map(renderedAlerts.map((item) => [item.id, item]));
    return [...renderedPoints]
      .slice(-MAX_RENDERED_ALERTS)
      .reverse()
      .map((point) => {
        const matchingAlert = alertsById.get(point.id);
        return {
          id: point.id,
          time: point.time,
          label: point.label,
          score: point.score,
          attackType: point.attackType ?? 'Normal',
          confidence: matchingAlert?.confidence ?? 0,
        };
      });
  }, [renderedPoints, renderedAlerts]);

  const statusBadge = useMemo(() => {
    if (!isAnalysisRunning) {
      return {
        label: 'PAUSED',
        style: {
          border: '1px solid var(--color-border)',
          background: 'var(--color-bg-hover)',
          color: 'var(--color-text-muted)',
        },
      };
    }

    if (connected) {
      return {
        label: 'LIVE',
        style: {
          border: '1px solid rgba(15,123,85,0.2)',
          background: 'var(--color-success-bg)',
          color: 'var(--color-success)',
        },
      };
    }

    return {
      label: 'OFFLINE',
      style: {
        border: '1px solid var(--color-border)',
        background: 'var(--color-bg-hover)',
        color: 'var(--color-text-muted)',
      },
    };
  }, [connected, isAnalysisRunning]);

  const chartData =
    renderedPoints.length > 0
      ? renderedPoints
      : [{ time: '--:--:--', score: 0, attackScore: null, threshold: 0, id: 0, label: 'NORMAL', attackType: null }];

  const activeThreshold = threshold > 0 ? threshold : thresholdInput || 0.75;
  const cpuLoad = Math.min(95, Math.max(10, Math.round((detectionRate + (connected ? 8 : 0)) / 4)));

  return (
    <div style={{ width: '100%', maxWidth: '100%', boxSizing: 'border-box' }}>
      <header
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '10px',
          minHeight: '52px',
          maxHeight: '60px',
          marginBottom: '20px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', minWidth: 0 }}>
          <ShieldCheck
            style={{
              width: '32px',
              height: '32px',
              color: 'var(--color-primary)',
              maxHeight: '48px',
              maxWidth: '48px',
              objectFit: 'contain',
              flexShrink: 0,
            }}
          />
          <div style={{ minWidth: 0 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <h1
                style={{
                  fontSize: '1.1rem',
                  fontWeight: 700,
                  color: 'var(--color-text-primary)',
                  letterSpacing: '-0.01em',
                }}
              >
                Network Monitor
              </h1>
              <span
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '0.6rem',
                  fontWeight: 600,
                  padding: '2px 7px',
                  height: '18px',
                  letterSpacing: '0.08em',
                  borderRadius: '999px',
                  lineHeight: 1,
                  textTransform: 'uppercase',
                  ...statusBadge.style,
                }}
              >
                {statusBadge.label}
              </span>
            </div>
            <p style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', marginTop: '3px' }}>
              Real-time CAN bus anomaly detection
            </p>
          </div>
        </div>

        <div style={{ textAlign: 'right' }}>
          <div
            style={{
              fontSize: '0.68rem',
              fontWeight: 600,
              textTransform: 'uppercase',
              letterSpacing: '0.09em',
              color: 'var(--color-text-muted)',
              lineHeight: 1,
            }}
          >
            Threshold
          </div>
          <div style={{ marginTop: '3px', fontSize: '0.72rem', fontFamily: 'JetBrains Mono, monospace', color: 'var(--color-text-secondary)' }}>
            {activeThreshold.toFixed(3)}
          </div>
        </div>
      </header>

      <section className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4" style={{ gap: '12px' }}>
        {[
          {
            icon: <Activity size={14} color="var(--color-primary)" />,
            value: renderedTotalAnalyzed.toLocaleString(),
            label: 'Messages Analyzed',
            trend: `+${Math.max(1, Math.round((1000 / streamIntervalMs) * 60)).toLocaleString()}/min`,
            trendColor: 'var(--color-success)',
          },
          {
            icon: <AlertTriangle size={14} color="var(--color-primary)" />,
            value: renderedAttacksDetected.toLocaleString(),
            label: 'Alerts Triggered',
            trend: `${renderedAlerts.length} active`,
            trendColor: 'var(--color-danger)',
          },
          {
            icon: <Shield size={14} color="var(--color-primary)" />,
            value: `${detectionRate.toFixed(2)}%`,
            label: 'Detection Rate',
            trend: 'runtime precision',
            trendColor: 'var(--color-success)',
          },
          {
            icon: <Sigma size={14} color="var(--color-primary)" />,
            value: averageScore.toFixed(3),
            label: 'Mean Score',
            trend: `threshold ${activeThreshold.toFixed(3)}`,
            trendColor: 'var(--color-warning)',
          },
        ].map((metric) => (
          <article key={metric.label} style={{ ...CARD_STYLE, padding: '14px 16px', borderRadius: '10px' }}>
            <div
              style={{
                width: '28px',
                height: '28px',
                borderRadius: '7px',
                background: 'var(--color-primary-light)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              {metric.icon}
            </div>

            <div
              style={{
                fontSize: '1.3rem',
                fontWeight: 700,
                fontFamily: 'JetBrains Mono, monospace',
                color: 'var(--color-text-primary)',
                marginTop: '8px',
                lineHeight: 1.1,
              }}
            >
              {metric.value}
            </div>

            <div
              style={{
                fontSize: '0.68rem',
                fontWeight: 500,
                textTransform: 'uppercase',
                letterSpacing: '0.09em',
                color: 'var(--color-text-muted)',
                marginTop: '2px',
                lineHeight: 1,
              }}
            >
              {metric.label}
            </div>

            <div style={{ fontSize: '0.8rem', color: metric.trendColor, marginTop: '6px' }}>{metric.trend}</div>
          </article>
        ))}
      </section>

      <section className="grid grid-cols-1 xl:grid-cols-12" style={{ gap: '16px', marginTop: '16px' }}>
        <article className="xl:col-span-8" style={{ ...CARD_STYLE, padding: '20px 24px' }}>
          <div style={SECTION_LABEL_STYLE}>Anomaly Score Feed</div>
          <h2 style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--color-text-primary)' }}>Real-time reconstruction loss</h2>
          <p style={{ fontSize: '0.72rem', color: 'var(--color-text-muted)', marginTop: '2px' }}>
            Attack spikes are plotted against the calibrated threshold.
          </p>

          <div style={{ marginTop: '12px', height: '280px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F4" />
                <XAxis dataKey="time" tick={{ fontSize: 10, fill: '#8896A8' }} minTickGap={20} stroke="#E2E8F4" />
                <YAxis tick={{ fontSize: 10, fill: '#8896A8' }} stroke="#E2E8F4" domain={[0, 1.2]} />
                <Tooltip
                  contentStyle={{
                    borderRadius: '10px',
                    border: '1px solid #E2E8F4',
                    boxShadow: 'var(--shadow-sm)',
                    fontSize: '0.75rem',
                  }}
                />
                <ReferenceLine
                  y={activeThreshold}
                  stroke="#C41E3A"
                  strokeDasharray="6 4"
                  label={{ value: 'Threshold', position: 'right', fill: '#8896A8', fontSize: '0.7rem' }}
                />
                <Line type="monotone" dataKey="score" stroke="#1A6FD4" strokeWidth={2} dot={false} isAnimationActive />
                <Line
                  type="monotone"
                  dataKey="attackScore"
                  stroke="transparent"
                  dot={{ fill: '#C41E3A', stroke: '#C41E3A', r: 3 }}
                  connectNulls={false}
                  isAnimationActive
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </article>

        <article className="xl:col-span-4" style={{ ...CARD_STYLE, padding: '20px 24px' }}>
          <div style={SECTION_LABEL_STYLE}>Attack Breakdown</div>
          <h2 style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--color-text-primary)' }}>Stage-2 class distribution</h2>
          <p style={{ fontSize: '0.72rem', color: 'var(--color-text-muted)', marginTop: '2px' }}>Recent attack class proportions.</p>

          <div style={{ marginTop: '12px', display: 'flex', justifyContent: 'center', position: 'relative' }}>
            <div style={{ width: '142px', height: '142px', borderRadius: '999px', background: donutGradient }} />
            <div
              style={{
                position: 'absolute',
                top: '50%',
                left: '50%',
                transform: 'translate(-50%, -50%)',
                width: '84px',
                height: '84px',
                borderRadius: '999px',
                background: 'var(--color-bg-card)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexDirection: 'column',
              }}
            >
              <span
                style={{
                  fontSize: '1.3rem',
                  fontWeight: 700,
                  fontFamily: 'JetBrains Mono, monospace',
                  color: 'var(--color-text-primary)',
                  lineHeight: 1.1,
                }}
              >
                {renderedAttacksDetected}
              </span>
              <span style={{ fontSize: '0.68rem', color: 'var(--color-text-muted)', letterSpacing: '0.09em', textTransform: 'uppercase' }}>Alerts</span>
            </div>
          </div>

          <div style={{ marginTop: '12px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {donutData.map((item, index) => {
              const pct = donutTotal > 0 ? (item.value / donutTotal) * 100 : 0;
              return (
                <div key={item.name} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.75rem', color: 'var(--color-text-secondary)' }}>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ width: '9px', height: '9px', borderRadius: '2px', background: DONUT_COLORS[index % DONUT_COLORS.length] }} />
                    <span style={{ fontSize: '0.75rem' }}>{item.name}</span>
                  </span>
                  <span style={{ fontSize: '0.75rem', fontFamily: 'JetBrains Mono, monospace', color: 'var(--color-text-secondary)' }}>{pct.toFixed(0)}%</span>
                </div>
              );
            })}
          </div>
        </article>

        <article className="xl:col-span-8" style={{ ...CARD_STYLE, padding: '20px 24px' }}>
          <div style={SECTION_LABEL_STYLE}>Threat Feed</div>
          <h2 style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--color-text-primary)' }}>Latest sequence decisions</h2>
          <p style={{ fontSize: '0.72rem', color: 'var(--color-text-muted)', marginTop: '2px' }}>Incoming frames are ignored while analysis is paused.</p>

          <div style={{ marginTop: '12px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {eventFeed.length === 0 ? (
              <div style={{ border: '1px solid var(--color-border)', borderRadius: '8px', background: 'var(--color-bg-base)', padding: '10px 14px', fontSize: '0.78rem', color: 'var(--color-text-muted)' }}>
                No alerts yet.
              </div>
            ) : (
              eventFeed.map((item) => {
                const isAttack = item.label === 'ATTACK';
                return (
                  <div
                    key={item.id}
                    style={{
                      padding: '10px 14px',
                      borderRadius: '8px',
                      borderLeft: isAttack ? '3px solid var(--color-danger)' : '3px solid var(--color-success)',
                      background: isAttack ? 'var(--color-danger-bg)' : 'var(--color-success-bg)',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '10px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', minWidth: 0 }}>
                        <span style={{ fontSize: '0.76rem', color: 'var(--color-text-primary)', fontWeight: 500 }}>{isAttack ? item.attackType.toUpperCase() : 'NORMAL'}</span>
                        <span
                          style={{
                            fontSize: '0.6rem',
                            fontWeight: 600,
                            padding: '1px 6px',
                            borderRadius: '4px',
                            letterSpacing: '0.08em',
                            textTransform: 'uppercase',
                            background: isAttack ? 'rgba(196,30,58,0.18)' : 'rgba(15,123,85,0.16)',
                            color: isAttack ? 'var(--color-danger)' : 'var(--color-success)',
                          }}
                        >
                          {isAttack ? 'Attack' : 'Normal'}
                        </span>
                        <span style={{ fontSize: '0.72rem', fontFamily: 'JetBrains Mono, monospace', color: 'var(--color-text-secondary)' }}>
                          Score {item.score.toFixed(3)}
                        </span>
                      </div>
                      <span style={{ fontSize: '0.68rem', fontFamily: 'JetBrains Mono, monospace', color: 'var(--color-text-muted)' }}>{item.time}</span>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </article>

        <div className="xl:col-span-4" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <article style={{ ...CARD_STYLE, padding: '20px 24px' }}>
            <div style={SECTION_LABEL_STYLE}>Controls</div>
            <h2 style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--color-text-primary)' }}>Operator settings</h2>
            <p style={{ fontSize: '0.72rem', color: 'var(--color-text-muted)', marginTop: '2px' }}>Threshold and stream speed.</p>

            <div style={{ marginTop: '12px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: 'var(--color-text-secondary)' }}>
                  <span>Threshold</span>
                  <span style={{ fontSize: '0.72rem', fontFamily: 'JetBrains Mono, monospace', color: 'var(--color-text-secondary)' }}>{thresholdInput.toFixed(3)}</span>
                </div>
                <input
                  type="range"
                  min={0.5}
                  max={8}
                  step={0.01}
                  value={thresholdInput || threshold || 0.5}
                  onChange={(event) => {
                    setThresholdEdited(true);
                    setThresholdInput(Number(event.target.value));
                  }}
                  className="w-full accent-primary"
                />
                <button
                  type="button"
                  onClick={handleThresholdUpdate}
                  disabled={controlBusy !== null || thresholdInput <= 0}
                  className="mt-3 w-full rounded-btn bg-primary px-3 py-2 text-[0.8rem] font-semibold text-white transition-colors hover:bg-primary-hover disabled:cursor-not-allowed disabled:opacity-70"
                >
                  {controlBusy === 'threshold' ? 'Updating...' : 'Apply Threshold'}
                </button>
              </div>

              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: 'var(--color-text-secondary)' }}>
                  <span>Stream Speed</span>
                  <span style={{ fontSize: '0.72rem', fontFamily: 'JetBrains Mono, monospace', color: 'var(--color-text-secondary)' }}>
                    {(1000 / streamIntervalMs).toFixed(2)} fps
                  </span>
                </div>
                <input
                  type="range"
                  min={200}
                  max={2000}
                  step={50}
                  value={streamIntervalMs}
                  onChange={(event) => setStreamIntervalMs(Number(event.target.value))}
                  className="w-full accent-primary"
                />
                <button
                  type="button"
                  onClick={handleSpeedUpdate}
                  disabled={controlBusy !== null}
                  className="mt-3 w-full rounded-btn border border-[rgba(26,111,212,0.2)] bg-primary-light px-3 py-2 text-[0.8rem] font-semibold text-primary transition-colors hover:bg-[#dcecff] disabled:cursor-not-allowed disabled:opacity-70"
                >
                  {controlBusy === 'speed' ? 'Applying...' : 'Apply Speed'}
                </button>
              </div>

              {controlNotice ? <p style={{ fontSize: '0.8rem', color: 'var(--color-success)' }}>{controlNotice}</p> : null}
              {controlError ? <p style={{ fontSize: '0.8rem', color: 'var(--color-danger)' }}>{controlError}</p> : null}
            </div>
          </article>

          <article style={{ ...CARD_STYLE, padding: '20px 24px' }}>
            <div style={SECTION_LABEL_STYLE}>Score Distribution</div>
            <h2 style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--color-text-primary)' }}>Histogram</h2>
            <p style={{ fontSize: '0.72rem', color: 'var(--color-text-muted)', marginTop: '2px' }}>Recent anomaly score bins.</p>

            <div style={{ marginTop: '12px', display: 'flex', alignItems: 'end', gap: '4px', height: '108px' }}>
              {(scoreDistribution.length > 0
                ? scoreDistribution
                : new Array(8).fill(null).map((_, idx) => ({ bin: `${idx}`, count: 0 }))).map((bar, idx) => {
                const height = Math.max(5, (bar.count / maxHistogramCount) * 100);
                const color = idx >= 5 ? 'rgba(196,30,58,0.45)' : 'rgba(26,111,212,0.45)';
                return (
                  <div
                    key={`${bar.bin}-${idx}`}
                    style={{
                      flex: 1,
                      height: `${height}%`,
                      borderTopLeftRadius: '3px',
                      borderTopRightRadius: '3px',
                      background: color,
                    }}
                  />
                );
              })}
            </div>
            <div style={{ marginTop: '8px', display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>
              <span style={{ fontSize: '0.72rem', fontFamily: 'JetBrains Mono, monospace' }}>0.0</span>
              <span style={{ fontSize: '0.72rem', fontFamily: 'JetBrains Mono, monospace' }}>1.0+</span>
            </div>
          </article>

          <article style={{ ...CARD_STYLE, padding: '20px 24px' }}>
            <div style={SECTION_LABEL_STYLE}>System Health</div>
            <h2 style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--color-text-primary)' }}>Runtime status</h2>
            <p style={{ fontSize: '0.72rem', color: 'var(--color-text-muted)', marginTop: '2px' }}>Connectivity and load indicator.</p>

            <div style={{ marginTop: '12px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ fontSize: '0.72rem', color: 'var(--color-text-muted)' }}>WebSocket status</span>
                <span style={{ fontSize: '0.8rem', color: connected ? 'var(--color-success)' : 'var(--color-danger)', fontWeight: 600 }}>
                  {connected ? 'Online' : 'Offline'}
                </span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ fontSize: '0.72rem', color: 'var(--color-text-muted)' }}>Analysis mode</span>
                <span style={{ fontSize: '0.8rem', color: isAnalysisRunning ? 'var(--color-success)' : 'var(--color-warning)', fontWeight: 600 }}>
                  {isAnalysisRunning ? 'Running' : 'Paused'}
                </span>
              </div>

              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                  <span style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)' }}>CPU Load</span>
                  <span style={{ fontSize: '0.72rem', fontFamily: 'JetBrains Mono, monospace', color: 'var(--color-text-secondary)' }}>{cpuLoad}%</span>
                </div>
                <div style={{ height: '6px', borderRadius: '999px', background: 'var(--color-bg-hover)', overflow: 'hidden' }}>
                  <div style={{ height: '100%', width: `${cpuLoad}%`, background: 'var(--color-primary)' }} />
                </div>
              </div>
            </div>
          </article>
        </div>
      </section>

      <div style={{ marginTop: '16px' }}>
        <AdvancedAnalytics />
      </div>
    </div>
  );
}