import { FormEvent, useMemo, useState } from 'react';
import { apiClient, type PredictionResponse } from '../api/client';
import { useLiveStreamContext } from '../context/LiveStreamContext';
import { ConsoleLayout } from '../layout/ConsoleLayout';

function parseSequenceInput(text: string): string[] {
  return text
    .split(/[\n,\s]+/)
    .map((item) => item.trim())
    .filter(Boolean);
}

export function AnalyzePage() {
  const [sequenceText, setSequenceText] = useState('');
  const [analysisMode, setAnalysisMode] = useState<'fast' | 'detailed'>('fast');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<PredictionResponse | null>(null);

  const { points } = useLiveStreamContext();
  const tokens = useMemo(() => parseSequenceInput(sequenceText), [sequenceText]);

  const feedRows = useMemo(() => {
    const latest = [...points].slice(-5).reverse();
    return latest.map((entry) => {
      const label = entry.label === 'ATTACK' ? 'ATTACK' : 'BENIGN';
      return {
        timestamp: new Date().toISOString(),
        score: entry.score,
        label,
        type: entry.attackType,
      };
    });
  }, [points]);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();

    if (tokens.length !== 64) {
      setError(`Exactly 64 CAN arbitration identifiers are required for a valid sequence window. Current token count: ${tokens.length}`);
      return;
    }

    setError(null);
    setLoading(true);

    try {
      const prediction = await apiClient.predict(tokens, analysisMode === 'detailed');
      setResult(prediction);
    } catch (submitError) {
      const message = submitError instanceof Error ? submitError.message : 'Inference pipeline execution failed.';
      setError(message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <ConsoleLayout activeNav="integration">
      <div className="mx-auto max-w-[1200px] space-y-12 p-8">
        <header className="relative overflow-hidden rounded-xl bg-primary-container p-10 text-white">
          <div className="relative z-10">
            <h1 className="mb-2 font-headline text-4xl font-bold tracking-tight">Production-Grade Inference API Architecture</h1>
            <p className="font-medium text-on-primary-container">RESTful and WebSocket endpoint specifications for automotive intrusion telemetry integration and real-time anomaly classification.</p>
          </div>
          <div className="absolute right-0 top-0 flex h-full w-64 items-center justify-center opacity-10">
            <span className="material-symbols-outlined text-[120px]" style={{ fontVariationSettings: "'FILL' 1" }}>
              terminal
            </span>
          </div>
        </header>

        {/* Section 1: Abstract */}
        <section className="rounded-xl border border-outline-variant/10 bg-surface-container-low p-8">
          <div className="mb-2 font-mono text-[10px] font-bold uppercase tracking-widest text-secondary">Section 1</div>
          <h2 className="mb-4 font-headline text-xl font-bold text-primary">Abstract</h2>
          <p className="leading-relaxed text-on-surface-variant">
            The IDS Sentinel inference backend exposes a production-grade API surface designed for seamless integration with automotive telematics platforms, fleet management consoles, and SOC operator dashboards. The architecture provides both synchronous RESTful endpoints for on-demand sequence analysis and persistent WebSocket channels for continuous real-time telemetry streaming. All endpoints accept and emit structured JSON payloads conforming to the established data contract specification.
          </p>
        </section>

        <div className="grid grid-cols-12 gap-8">
          <div className="col-span-12 space-y-8 lg:col-span-8">
            {/* Section 2: Methodology — Endpoint Catalog */}
            <section>
              <div className="mb-2 font-mono text-[10px] font-bold uppercase tracking-widest text-secondary">Section 2</div>
              <h2 className="mb-6 flex items-center gap-2 font-headline text-xl font-bold text-primary">
                <span className="material-symbols-outlined text-secondary">database</span>
                Methodology — Endpoint Architecture
              </h2>
              <div className="overflow-hidden rounded-xl bg-surface-container-low shadow-sm">
                <table className="w-full border-collapse text-left">
                  <thead>
                    <tr className="bg-surface-container-high">
                      <th className="px-6 py-4 font-headline text-sm font-bold text-primary">Method</th>
                      <th className="px-6 py-4 font-headline text-sm font-bold text-primary">Endpoint</th>
                      <th className="px-6 py-4 font-headline text-sm font-bold text-primary">Description</th>
                      <th className="px-6 py-4 font-headline text-sm font-bold text-primary">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-surface-container-highest">
                    <tr className="bg-surface-container-lowest">
                      <td className="px-6 py-4">
                        <span className="rounded bg-secondary-container px-3 py-1 font-mono text-xs font-bold text-on-secondary-container">POST</span>
                      </td>
                      <td className="px-6 py-4 font-mono text-xs text-primary">/predict</td>
                      <td className="px-6 py-4 text-sm text-on-surface-variant">Single 64-frame CAN sequence anomaly scoring and multiclass classification</td>
                      <td className="px-6 py-4">
                        <span className="flex items-center gap-1.5 text-xs font-bold text-tertiary-container">
                          <span className="h-2 w-2 rounded-full bg-tertiary-fixed-dim" />
                          Operational
                        </span>
                      </td>
                    </tr>
                    <tr className="bg-surface-container-lowest">
                      <td className="px-6 py-4">
                        <span className="rounded bg-surface-container-highest px-3 py-1 font-mono text-xs font-bold text-primary">GET</span>
                      </td>
                      <td className="px-6 py-4 font-mono text-xs text-primary">/ws/live</td>
                      <td className="px-6 py-4 text-sm text-on-surface-variant">Persistent WebSocket channel for continuous real-time anomaly telemetry streaming</td>
                      <td className="px-6 py-4">
                        <span className="flex items-center gap-1.5 text-xs font-bold text-tertiary-container">
                          <span className="h-2 w-2 rounded-full bg-tertiary-fixed-dim" />
                          Operational
                        </span>
                      </td>
                    </tr>
                    <tr className="bg-surface-container-lowest">
                      <td className="px-6 py-4">
                        <span className="rounded bg-surface-container-highest px-3 py-1 font-mono text-xs font-bold text-primary">GET</span>
                      </td>
                      <td className="px-6 py-4 font-mono text-xs text-primary">/reports/manifest</td>
                      <td className="px-6 py-4 text-sm text-on-surface-variant">Retrieval of available report artifacts, evaluation metrics, and analysis figures</td>
                      <td className="px-6 py-4">
                        <span className="flex items-center gap-1.5 text-xs font-bold text-on-surface-variant opacity-70">
                          <span className="h-2 w-2 rounded-full bg-outline-variant" />
                          Stable
                        </span>
                      </td>
                    </tr>
                    <tr className="bg-surface-container-lowest">
                      <td className="px-6 py-4">
                        <span className="rounded bg-secondary-container px-3 py-1 font-mono text-xs font-bold text-on-secondary-container">POST</span>
                      </td>
                      <td className="px-6 py-4 font-mono text-xs text-primary">/predict/batch</td>
                      <td className="px-6 py-4 text-sm text-on-surface-variant">Batch inference for parallel processing of multiple CAN sequence windows</td>
                      <td className="px-6 py-4">
                        <span className="flex items-center gap-1.5 text-xs font-bold text-tertiary-container">
                          <span className="h-2 w-2 rounded-full bg-tertiary-fixed-dim" />
                          Operational
                        </span>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </section>

            {/* Section 3: Experimental Setup — Sequence Analyzer */}
            <section className="space-y-6 rounded-xl bg-surface-container-low p-8 shadow-sm">
              <div className="mb-2 font-mono text-[10px] font-bold uppercase tracking-widest text-secondary">Section 3</div>
              <div className="flex items-end justify-between">
                <div>
                  <h2 className="font-headline text-xl font-bold text-primary">Experimental Setup — Interactive Sequence Analyzer</h2>
                  <p className="text-sm text-on-surface-variant">Submit a single 64-frame CAN bus arbitration ID sequence for real-time dual-stage threat analysis through the inference pipeline.</p>
                </div>
                <div className="flex items-center gap-3">
                  <span className="rounded bg-secondary-fixed px-2 py-1 font-mono text-[10px] font-bold uppercase tracking-widest text-secondary">Experimental</span>
                  <div className="flex overflow-hidden rounded-lg border border-outline-variant bg-surface">
                    <button
                      type="button"
                      onClick={() => setAnalysisMode('fast')}
                      className={`px-3 py-1.5 text-[10px] font-bold uppercase tracking-wide transition-colors ${
                        analysisMode === 'fast' ? 'bg-primary text-white' : 'text-on-surface-variant hover:bg-surface-container-low'
                      }`}
                    >
                      Fast
                    </button>
                    <button
                      type="button"
                      onClick={() => setAnalysisMode('detailed')}
                      className={`px-3 py-1.5 text-[10px] font-bold uppercase tracking-wide transition-colors ${
                        analysisMode === 'detailed' ? 'bg-primary text-white' : 'text-on-surface-variant hover:bg-surface-container-low'
                      }`}
                    >
                      Detailed
                    </button>
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-1 gap-8 md:grid-cols-2">
                <form className="space-y-4" onSubmit={onSubmit}>
                  <label className="block text-xs font-bold uppercase tracking-wider text-on-surface-variant">64-Frame CAN Arbitration ID Sequence</label>
                  <textarea
                    className="w-full rounded-xl border-none bg-surface-container-lowest p-4 font-mono text-xs leading-relaxed ring-1 ring-outline-variant focus:ring-2 focus:ring-secondary"
                    placeholder="0x18F, 0x0C9, 0x111, 0x0AF... (Provide exactly 64 hexadecimal CAN arbitration identifiers)"
                    rows={6}
                    value={sequenceText}
                    onChange={(event) => setSequenceText(event.target.value)}
                  />
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-[11px] text-on-surface-variant">{tokens.length}/64 identifiers</span>
                    <button
                      type="submit"
                      disabled={loading}
                      className="flex items-center justify-center gap-2 rounded-xl bg-secondary px-6 py-3 font-headline font-bold text-white transition-all hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-70"
                    >
                      <span className="material-symbols-outlined text-sm">bolt</span>
                      {loading ? 'Executing Inference...' : 'Execute Prediction'}
                    </button>
                  </div>
                  <p className="text-[11px] text-on-surface-variant">
                    Mode: <span className="font-semibold text-primary">{analysisMode === 'fast' ? 'Fast — Reduced response overhead, anomaly score only' : 'Detailed — Full diagnostic output with per-token analysis'}</span>
                  </p>
                  {error ? <p className="text-sm font-medium text-error">{error}</p> : null}
                </form>

                <div
                  className={`relative overflow-hidden rounded-xl border p-6 ${
                    result?.is_attack
                      ? 'border-error/10 bg-error-container/30'
                      : 'border-secondary/10 bg-secondary-container/20'
                  }`}
                >
                  <div className="absolute right-0 top-0 p-4 opacity-20">
                    <span className="material-symbols-outlined text-6xl text-error">dangerous</span>
                  </div>

                  <div className="mb-6 flex items-start justify-between">
                    <div
                      className={`rounded-full px-3 py-1 text-[10px] font-bold uppercase tracking-widest ${
                        result?.is_attack ? 'bg-error text-white' : 'bg-tertiary-container text-tertiary-fixed-dim'
                      }`}
                    >
                      {result ? (result.is_attack ? 'Intrusion Detected — Attack Classification Active' : 'Nominal Traffic — No Anomaly Detected') : 'Awaiting Inference Execution'}
                    </div>
                    <div className="text-right">
                      <div className={`font-headline text-3xl font-bold ${result?.is_attack ? 'text-error' : 'text-primary'}`}>
                        {result ? result.anomaly_score.toFixed(2) : '0.00'}
                      </div>
                      <div className="text-[10px] font-bold uppercase opacity-70">Reconstruction Loss Score</div>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-x-6 gap-y-4">
                    <div>
                      <p className="text-[10px] font-bold uppercase opacity-60">Decision Threshold (τ)</p>
                      <p className="font-mono text-sm font-bold text-primary">{result ? result.threshold.toFixed(2) : '0.00'}</p>
                    </div>
                    <div>
                      <p className="text-[10px] font-bold uppercase opacity-60">Attack Category (Stage-2)</p>
                      <p className="font-mono text-sm font-bold text-error">{result?.attack_type ?? 'N/A'}</p>
                    </div>
                    <div>
                      <p className="text-[10px] font-bold uppercase opacity-60">Classifier Confidence</p>
                      <p className="font-mono text-sm font-bold text-primary">{result ? `${(result.confidence * 100).toFixed(1)}%` : '0.0%'}</p>
                    </div>
                    <div>
                      <p className="text-[10px] font-bold uppercase opacity-60">Pipeline Execution Latency</p>
                      <p className="font-mono text-sm font-bold text-primary">{result ? `${result.processing_time_ms.toFixed(1)}ms` : '0.0ms'}</p>
                    </div>
                  </div>
                </div>
              </div>
            </section>
          </div>

          <div className="col-span-12 space-y-8 lg:col-span-4">
            <section className="space-y-4">
              <div className="flex items-center justify-between">
                <h2 className="font-headline text-sm font-bold uppercase tracking-widest text-primary">Reference Implementation</h2>
                <div className="flex gap-2">
                  <button type="button" className="rounded bg-surface-container-high px-2 py-1 text-[10px] font-bold text-primary">
                    Python
                  </button>
                  <button type="button" className="px-2 py-1 text-[10px] font-bold text-on-surface-variant transition-all hover:text-primary">
                    Node.js
                  </button>
                </div>
              </div>

              <div className="code-block overflow-x-auto rounded-xl p-5 text-xs font-mono shadow-lg">
                <div className="mb-4 flex gap-1.5 opacity-30">
                  <div className="h-2 w-2 rounded-full bg-red-400" />
                  <div className="h-2 w-2 rounded-full bg-amber-400" />
                  <div className="h-2 w-2 rounded-full bg-emerald-400" />
                </div>
                <pre>
                  <code>{`import requests

payload = {
    "sequence": ["0x18F", "0x0C9", ...],
    "device_id": "sentinel-04"
}

response = requests.post(
    "http://localhost:8000/predict",
    json=payload
)

print(response.json())`}</code>
                </pre>
              </div>
            </section>

            <section className="space-y-4">
              <h2 className="flex items-center justify-between font-headline text-sm font-bold uppercase tracking-widest text-primary">
                Live Telemetry Feed
                <span className="relative flex h-2 w-2">
                  <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-secondary-container opacity-75" />
                  <span className="relative inline-flex h-2 w-2 rounded-full bg-secondary" />
                </span>
              </h2>

              <div className="h-80 space-y-3 overflow-y-auto rounded-xl bg-surface-container-highest p-4 font-mono text-[10px] leading-relaxed shadow-inner">
                {feedRows.length === 0 ? (
                  <div className="rounded-lg border-l-4 border-tertiary-fixed-dim bg-surface-container-lowest p-3">
                    <p className="text-on-surface-variant opacity-50">Establishing connection to the inference telemetry stream...</p>
                  </div>
                ) : (
                  feedRows.map((row, index) => (
                    <div
                      key={`feed-${row.timestamp}-${index}`}
                      className={`rounded-lg border-l-4 bg-surface-container-lowest p-3 ${
                        row.label === 'ATTACK' ? 'border-error' : 'border-tertiary-fixed-dim'
                      }`}
                    >
                      <p className="text-on-surface-variant">{`{ "timestamp": "${row.timestamp}",`}</p>
                      <p className="ml-2 text-on-surface-variant">
                        {row.label === 'ATTACK'
                          ? `"score": ${row.score.toFixed(3)}, "label": "ATTACK", "type": "${row.type ?? 'Unknown'}" }`
                          : `"score": ${row.score.toFixed(3)}, "label": "BENIGN" }`}
                      </p>
                    </div>
                  ))
                )}
              </div>
            </section>
          </div>
        </div>
      </div>
    </ConsoleLayout>
  );
}
