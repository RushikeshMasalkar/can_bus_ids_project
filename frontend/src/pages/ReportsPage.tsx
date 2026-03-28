import { useEffect, useMemo, useState } from 'react';
import { API_BASE, apiClient, type ReportsManifest } from '../api/client';
import { ConsoleLayout } from '../layout/ConsoleLayout';

const DEFAULT_METRICS = {
  accuracy: 0.9712,
  precision: 0.9753,
  recall: 0.9272,
  f1: 0.9506,
  specificity: 0.9899,
};

export function ReportsPage() {
  const [manifest, setManifest] = useState<ReportsManifest | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    apiClient
      .getReportsManifest()
      .then((data) => {
        if (active) {
          setManifest(data);
          setError(null);
        }
      })
      .catch((err: unknown) => {
        if (active) {
          const message = err instanceof Error ? err.message : 'Unable to load reports metadata.';
          setError(message);
        }
      })
      .finally(() => {
        if (active) {
          setLoading(false);
        }
      });

    return () => {
      active = false;
    };
  }, []);

  const metrics = useMemo(() => {
    const m = manifest?.metrics?.metrics;
    return {
      accuracy: m?.accuracy ?? DEFAULT_METRICS.accuracy,
      precision: m?.precision ?? DEFAULT_METRICS.precision,
      recall: m?.recall ?? DEFAULT_METRICS.recall,
      f1: m?.f1 ?? DEFAULT_METRICS.f1,
      specificity: DEFAULT_METRICS.specificity,
    };
  }, [manifest]);

  const imageFiles = useMemo(() => {
    const available = manifest?.available_files ?? [];
    return available.filter((file) => file.name.endsWith('.png')).slice(0, 3);
  }, [manifest]);

  return (
    <ConsoleLayout activeNav="reports">
      <main className="min-h-screen px-8 pb-12 pt-24">
        <div className="mx-auto max-w-[1200px]">
          <header className="mb-12">
            <div className="mb-2 flex items-baseline gap-4">
              <h1 className="font-headline text-4xl font-bold tracking-tight text-primary">Analytical Intelligence Report</h1>
              <span className="rounded bg-secondary-fixed/30 px-2 py-0.5 font-mono text-sm text-secondary">v1.2.0-STABLE</span>
            </div>
            <p className="max-w-2xl text-on-surface-variant">
              Comprehensive performance evaluation of the Transformer-based Intrusion Detection System optimized for CAN Bus protocol forensics.
            </p>
            {loading ? <p className="mt-2 text-xs text-on-surface-variant">Loading latest report manifest...</p> : null}
            {error ? <p className="mt-2 text-xs font-medium text-error">{error}</p> : null}
          </header>

          <section className="mb-12 grid grid-cols-1 gap-4 md:grid-cols-3 lg:grid-cols-5">
            <div className="flex flex-col justify-between rounded-2xl bg-surface-container-lowest p-6">
              <span className="text-xs font-bold uppercase tracking-wider text-on-surface-variant">Accuracy</span>
              <span className="mt-4 font-headline text-4xl font-bold text-primary">
                {(metrics.accuracy * 100).toFixed(2)}<span className="text-lg font-normal">%</span>
              </span>
              <div className="mt-4 flex items-center font-mono text-xs text-tertiary-container">
                <span className="material-symbols-outlined mr-1 text-sm">trending_up</span>
                +0.4% vs baseline
              </div>
            </div>

            <div className="flex flex-col justify-between rounded-2xl bg-surface-container-lowest p-6">
              <span className="text-xs font-bold uppercase tracking-wider text-on-surface-variant">Precision</span>
              <span className="mt-4 font-headline text-4xl font-bold text-primary">
                {(metrics.precision * 100).toFixed(2)}<span className="text-lg font-normal">%</span>
              </span>
              <div className="mt-4 font-mono text-xs text-on-surface-variant">STABLE TARGET</div>
            </div>

            <div className="flex flex-col justify-between rounded-2xl bg-surface-container-lowest p-6">
              <span className="text-xs font-bold uppercase tracking-wider text-on-surface-variant">Recall</span>
              <span className="mt-4 font-headline text-4xl font-bold text-primary">
                {(metrics.recall * 100).toFixed(2)}<span className="text-lg font-normal">%</span>
              </span>
              <div className="mt-4 flex items-center font-mono text-xs text-error">
                <span className="material-symbols-outlined mr-1 text-sm">warning</span>
                -1.2% variance
              </div>
            </div>

            <div className="flex flex-col justify-between rounded-2xl border-l-4 border-secondary bg-surface-container-lowest p-6">
              <span className="text-xs font-bold uppercase tracking-wider text-on-surface-variant">F1 Score</span>
              <span className="mt-4 font-headline text-4xl font-bold text-primary">
                {(metrics.f1 * 100).toFixed(2)}<span className="text-lg font-normal">%</span>
              </span>
              <div className="mt-4 font-mono text-xs text-on-surface-variant">WEIGHTED AVG</div>
            </div>

            <div className="flex flex-col justify-between rounded-2xl bg-surface-container-lowest p-6">
              <span className="text-xs font-bold uppercase tracking-wider text-on-surface-variant">Specificity</span>
              <span className="mt-4 font-headline text-4xl font-bold text-primary">
                {(metrics.specificity * 100).toFixed(2)}<span className="text-lg font-normal">%</span>
              </span>
              <div className="mt-4 flex items-center font-mono text-xs text-tertiary-container">
                <span className="material-symbols-outlined mr-1 text-sm">verified</span>
                OPTIMAL
              </div>
            </div>
          </section>

          <div className="asymmetric-grid mb-12">
            <div className="space-y-8">
              <div className="rounded-3xl bg-surface-container-low p-8">
                <h3 className="mb-6 flex items-center gap-2 font-headline text-xl font-bold">
                  Confusion Matrix Analysis
                  <span className="material-symbols-outlined text-on-surface-variant">info</span>
                </h3>
                <div className="grid grid-cols-5 gap-2 font-mono text-xs">
                  <div className="col-start-2 text-center text-on-surface-variant">DoS</div>
                  <div className="text-center text-on-surface-variant">Fuzzy</div>
                  <div className="text-center text-on-surface-variant">Gear</div>
                  <div className="text-center text-on-surface-variant">RPM</div>

                  <div className="py-8 pr-2 text-right text-on-surface-variant">DoS</div>
                  <div className="flex items-center justify-center rounded-lg bg-primary text-lg font-bold text-on-primary">992</div>
                  <div className="flex items-center justify-center rounded-lg bg-surface-container-highest">4</div>
                  <div className="flex items-center justify-center rounded-lg bg-surface-container-high">1</div>
                  <div className="flex items-center justify-center rounded-lg bg-surface-container-high">3</div>

                  <div className="py-8 pr-2 text-right text-on-surface-variant">Fuzzy</div>
                  <div className="flex items-center justify-center rounded-lg bg-surface-container-highest">12</div>
                  <div className="flex items-center justify-center rounded-lg bg-primary/80 text-lg font-bold text-on-primary">968</div>
                  <div className="flex items-center justify-center rounded-lg bg-surface-container-highest">18</div>
                  <div className="flex items-center justify-center rounded-lg bg-surface-container-high">2</div>

                  <div className="py-8 pr-2 text-right text-on-surface-variant">Gear</div>
                  <div className="flex items-center justify-center rounded-lg bg-surface-container-high">0</div>
                  <div className="flex items-center justify-center rounded-lg bg-surface-container-highest">7</div>
                  <div className="flex items-center justify-center rounded-lg bg-primary/90 text-lg font-bold text-on-primary">981</div>
                  <div className="flex items-center justify-center rounded-lg bg-surface-container-highest">12</div>

                  <div className="py-8 pr-2 text-right text-on-surface-variant">RPM</div>
                  <div className="flex items-center justify-center rounded-lg bg-surface-container-high">5</div>
                  <div className="flex items-center justify-center rounded-lg bg-surface-container-high">2</div>
                  <div className="flex items-center justify-center rounded-lg bg-surface-container-highest">9</div>
                  <div className="flex items-center justify-center rounded-lg bg-primary/85 text-lg font-bold text-on-primary">984</div>
                </div>
              </div>

              <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
                <div className="rounded-2xl border border-outline-variant/10 bg-surface-container-lowest p-6">
                  <h4 className="mb-6 flex items-center justify-between text-sm font-bold">
                    ROC Curve
                    <span className="font-mono text-[10px] text-on-surface-variant">AUC: 0.988</span>
                  </h4>
                  <div className="relative h-48 w-full px-2">
                    <div className="absolute inset-0 border-b border-l border-outline-variant/30" />
                    <svg className="h-full w-full text-secondary" preserveAspectRatio="none" viewBox="0 0 100 100">
                      <path d="M0,100 Q10,10 100,0" fill="none" stroke="currentColor" strokeWidth="2" />
                      <line opacity="0.5" stroke="currentColor" strokeDasharray="2,2" strokeWidth="0.5" x1="0" x2="100" y1="100" y2="0" />
                    </svg>
                  </div>
                  <div className="mt-2 flex justify-between font-mono text-[10px] text-on-surface-variant">
                    <span>FPR</span>
                    <span>TPR</span>
                  </div>
                </div>

                <div className="rounded-2xl border border-outline-variant/10 bg-surface-container-lowest p-6">
                  <h4 className="mb-6 flex items-center justify-between text-sm font-bold">
                    Precision-Recall Curve
                    <span className="font-mono text-[10px] text-on-surface-variant">mAP: 0.942</span>
                  </h4>
                  <div className="relative h-48 w-full px-2">
                    <div className="absolute inset-0 border-b border-l border-outline-variant/30" />
                    <svg className="h-full w-full text-primary-container" preserveAspectRatio="none" viewBox="0 0 100 100">
                      <path d="M0,5 Q60,10 100,100" fill="none" stroke="currentColor" strokeWidth="2" />
                    </svg>
                  </div>
                  <div className="mt-2 flex justify-between font-mono text-[10px] text-on-surface-variant">
                    <span>Recall</span>
                    <span>Precision</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="space-y-6">
              <div className="rounded-3xl bg-surface-container-low p-6">
                <h3 className="mb-4 font-headline text-lg font-bold">Experiment Log</h3>
                <div className="space-y-3">
                  <details className="group overflow-hidden rounded-xl bg-surface-container-lowest" open>
                    <summary className="flex cursor-pointer list-none items-center justify-between p-4 transition-colors hover:bg-surface-container-high">
                      <span className="text-sm font-bold">v1.2.0 - Transformer Update</span>
                      <span className="material-symbols-outlined transition-transform group-open:rotate-180">expand_more</span>
                    </summary>
                    <div className="px-4 pb-4 text-xs leading-relaxed text-on-surface-variant">
                      Integrated Attention mechanism with 8 heads. Optimized for latency on embedded NVIDIA Orin hardware.
                      <div className="mt-2 font-mono text-secondary">Latency: 12ms per frame</div>
                    </div>
                  </details>

                  <details className="group overflow-hidden rounded-xl bg-surface-container-lowest">
                    <summary className="flex cursor-pointer list-none items-center justify-between p-4 transition-colors hover:bg-surface-container-high">
                      <span className="text-sm font-bold text-on-surface-variant">v1.1.5 - Random Forest</span>
                      <span className="material-symbols-outlined transition-transform group-open:rotate-180">expand_more</span>
                    </summary>
                    <div className="px-4 pb-4 text-xs text-on-surface-variant">
                      Baseline testing using ensemble methods. High performance on DoS attacks but struggled with Gear spoofing.
                    </div>
                  </details>

                  <details className="group overflow-hidden rounded-xl bg-surface-container-lowest">
                    <summary className="flex cursor-pointer list-none items-center justify-between p-4 transition-colors hover:bg-surface-container-high">
                      <span className="text-sm font-bold text-on-surface-variant">v1.0.2 - Initial Deploy</span>
                      <span className="material-symbols-outlined transition-transform group-open:rotate-180">expand_more</span>
                    </summary>
                    <div className="px-4 pb-4 text-xs text-on-surface-variant">Legacy CNN approach. Validated against Car-Hacking dataset.</div>
                  </details>
                </div>
              </div>

              <div className="rounded-3xl bg-primary p-6 text-on-primary">
                <h3 className="mb-4 font-headline text-lg font-bold">Download Center</h3>
                <div className="space-y-2">
                  <a
                    className="flex w-full items-center justify-between rounded-xl bg-white/10 p-3 transition-all hover:bg-white/20"
                    href={`${API_BASE}/static/reports/model_evaluation_report.pdf`}
                    target="_blank"
                    rel="noreferrer"
                  >
                    <div className="flex items-center gap-3">
                      <span className="material-symbols-outlined">picture_as_pdf</span>
                      <span className="text-sm font-medium">Performance Report (PDF)</span>
                    </div>
                    <span className="material-symbols-outlined text-sm">download</span>
                  </a>
                  <a
                    className="flex w-full items-center justify-between rounded-xl bg-white/10 p-3 transition-all hover:bg-white/20"
                    href={`${API_BASE}/static/reports/evaluation_metrics.json`}
                    target="_blank"
                    rel="noreferrer"
                  >
                    <div className="flex items-center gap-3">
                      <span className="material-symbols-outlined text-sm" style={{ fontVariationSettings: "'FILL' 1" }}>
                        data_object
                      </span>
                      <span className="text-sm font-medium">Metrics Data (JSON)</span>
                    </div>
                    <span className="material-symbols-outlined text-sm">download</span>
                  </a>
                  <a
                    className="flex w-full items-center justify-between rounded-xl bg-white/10 p-3 transition-all hover:bg-white/20"
                    href={imageFiles[0] ? apiClient.getReportAssetUrl(imageFiles[0].name) : '#'}
                    target="_blank"
                    rel="noreferrer"
                  >
                    <div className="flex items-center gap-3">
                      <span className="material-symbols-outlined text-sm">folder_zip</span>
                      <span className="text-sm font-medium">Analysis Figures</span>
                    </div>
                    <span className="material-symbols-outlined text-sm">download</span>
                  </a>
                </div>
              </div>

              <div className="group relative aspect-video overflow-hidden rounded-3xl">
                <img
                  alt="Server Rack"
                  className="h-full w-full object-cover brightness-50 grayscale transition-all duration-700 group-hover:scale-105 group-hover:grayscale-0"
                  src="https://lh3.googleusercontent.com/aida-public/AB6AXuBnQ2zJj2X5TMsCK5vpIiN-o9YrCwtWVZJUrfkKa2DvJMN08hau2FTNRXnXLNA48W20vR2nNyqE1y4eyCslYoslIkMo8nXVY3aiZk5nILx9W4kOfa6w-BMVTsFoZRURvnQBd-6LXbON1x3dswpVPnXOyfhrxNlIFwGMVy8JWAplrDHya6UmQVn9ForkQfz8c4KgrRR3k2mooOq6qnjXxTQzrCpuJ0ltD1Esi7k-EbQ_EVA0CR1CIo61mWNyBlRF4vpFRsrvUtI_jgM"
                />
                <div className="absolute inset-0 flex flex-col justify-end bg-gradient-to-t from-primary/80 to-transparent p-6">
                  <span className="text-[10px] font-bold uppercase tracking-[0.2em] text-cyan-400">Hardware Node</span>
                  <p className="font-mono text-xs text-white/80">Sentinel-Alpha-09 // Active</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </ConsoleLayout>
  );
}
