import { useEffect, useMemo, useState } from 'react';
import { Line, LineChart, ResponsiveContainer } from 'recharts';
import { API_BASE, apiClient, type ReportsManifest } from '../api/client';

type MetricCardProps = {
  label: string;
  value: number;
};

function sparklineData(base: number) {
  const values = new Array(10).fill(0).map((_, idx) => ({
    x: idx,
    y: Math.max(0, Math.min(1, base + Math.sin(idx / 2) * 0.03 + (idx % 2 ? 0.01 : -0.01))),
  }));
  return values;
}

function MetricCard({ label, value }: MetricCardProps) {
  return (
    <article className="metric-card">
      <h4>{label}</h4>
      <p>{(value * 100).toFixed(2)}%</p>
      <div className="sparkline-wrap">
        <ResponsiveContainer width="100%" height={46}>
          <LineChart data={sparklineData(value)}>
            <Line type="monotone" dataKey="y" stroke="#0056D2" strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </article>
  );
}

const REPORT_IMAGE_FILES = [
  'confusion_matrix.png',
  'roc_curve.png',
  'pr_curve.png',
  'score_distribution.png',
  'metrics_summary.png',
];

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
      accuracy: m?.accuracy ?? 0,
      f1: m?.f1 ?? 0,
      auc: m?.auc ?? 0,
      precision: m?.precision ?? 0,
      recall: m?.recall ?? 0,
    };
  }, [manifest]);

  const imageFiles = useMemo(() => {
    const available = new Set(manifest?.available_files.map((file) => file.name) ?? []);
    return REPORT_IMAGE_FILES.filter((name) => available.has(name));
  }, [manifest]);

  return (
    <div className="reports-layout">
      <section className="card">
        <div className="panel-head">
          <h2>Model Information</h2>
          <span>DistilBERT IDS profile</span>
        </div>

        <div className="model-grid">
          <article>
            <h4>Architecture</h4>
            <p>DistilBERT (4 layers, 4 heads, dim=256)</p>
          </article>
          <article>
            <h4>Detection Method</h4>
            <p>Cross-Entropy anomaly score with 99th percentile thresholding</p>
          </article>
          <article>
            <h4>Training Corpus</h4>
            <p>56M CAN sequences from normal traffic augmentation</p>
          </article>
          <article>
            <h4>Attack Classes</h4>
            <p>DoS, Fuzzy, Gear spoofing, RPM spoofing</p>
          </article>
        </div>
      </section>

      <section className="metrics-row">
        <MetricCard label="F1" value={metrics.f1} />
        <MetricCard label="Accuracy" value={metrics.accuracy} />
        <MetricCard label="AUC" value={metrics.auc} />
        <MetricCard label="Precision" value={metrics.precision} />
        <MetricCard label="Recall" value={metrics.recall} />
      </section>

      <section className="card">
        <div className="panel-head">
          <h2>Evaluation Charts</h2>
          <a className="download-btn" href={`${API_BASE}/static/reports/model_evaluation_report.pdf`} target="_blank" rel="noreferrer">
            Download PDF Report
          </a>
        </div>

        {loading ? <p className="empty-state">Loading report assets...</p> : null}
        {error ? <p className="error-text">{error}</p> : null}

        <div className="report-images">
          {imageFiles.length === 0 && !loading ? (
            <p className="empty-state">
              No report images found. Run the evaluation script to generate assets in reports/.png.
            </p>
          ) : null}

          {imageFiles.map((name) => (
            <figure key={name} className="report-image-card">
              <img src={apiClient.getReportAssetUrl(name)} alt={name} />
              <figcaption>{name.replace('.png', '').split('_').join(' ')}</figcaption>
            </figure>
          ))}
        </div>
      </section>
    </div>
  );
}
