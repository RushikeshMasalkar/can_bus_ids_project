import { FormEvent, useMemo, useState } from 'react';
import { apiClient, type PredictionResponse } from '../api/client';

function parseSequenceInput(text: string): string[] {
  return text
    .split(/[\n,\s]+/)
    .map((item) => item.trim())
    .filter(Boolean);
}

export function AnalyzePage() {
  const [sequenceText, setSequenceText] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<PredictionResponse | null>(null);

  const tokens = useMemo(() => parseSequenceInput(sequenceText), [sequenceText]);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();

    if (tokens.length !== 64) {
      setError(`Exactly 64 CAN IDs are required. Current count: ${tokens.length}`);
      return;
    }

    setError(null);
    setLoading(true);

    try {
      const prediction = await apiClient.predict(tokens, true);
      setResult(prediction);
    } catch (submitError) {
      const message = submitError instanceof Error ? submitError.message : 'Prediction failed.';
      setError(message);
    } finally {
      setLoading(false);
    }
  }

  const scoreProgress = result
    ? Math.min(100, (result.anomaly_score / Math.max(result.threshold * 1.7, 0.0001)) * 100)
    : 0;

  return (
    <div className="analyze-layout">
      <section className="card form-card">
        <div className="panel-head">
          <h2>Manual Sequence Analysis</h2>
          <span>Paste one ID per line or comma separated</span>
        </div>

        <form onSubmit={onSubmit} className="analyze-form">
          <textarea
            value={sequenceText}
            onChange={(event) => setSequenceText(event.target.value)}
            placeholder="0316\n018f\n0260\n..."
            rows={14}
          />
          <div className="form-foot">
            <small>{tokens.length}/64 CAN IDs</small>
            <button type="submit" disabled={loading}>
              {loading ? 'Analyzing...' : 'Analyze Sequence'}
            </button>
          </div>
        </form>

        {error ? <p className="error-text">{error}</p> : null}
      </section>

      <section className={`card result-card ${result?.is_attack ? 'attack' : result ? 'normal' : ''}`}>
        <div className="panel-head">
          <h2>Results</h2>
          <span>{result ? 'Latest prediction' : 'Submit a sequence to view results'}</span>
        </div>

        {result ? (
          <>
            <div className="result-grid">
              <article>
                <h4>Anomaly Score</h4>
                <p>{result.anomaly_score.toFixed(4)}</p>
              </article>
              <article>
                <h4>Label</h4>
                <p>{result.label}</p>
              </article>
              <article>
                <h4>Attack Type</h4>
                <p>{result.attack_type ?? 'Normal traffic'}</p>
              </article>
              <article>
                <h4>Confidence</h4>
                <p>{(result.confidence * 100).toFixed(1)}%</p>
              </article>
              <article>
                <h4>Processing Time</h4>
                <p>{result.processing_time_ms.toFixed(2)} ms</p>
              </article>
              <article>
                <h4>Threshold</h4>
                <p>{result.threshold.toFixed(4)}</p>
              </article>
            </div>

            <div className="progress-block">
              <div className="progress-header">
                <strong>Score vs Threshold</strong>
                <span>{scoreProgress.toFixed(1)}%</span>
              </div>
              <div className="progress-track">
                <div
                  className={`progress-fill ${result.is_attack ? 'attack' : 'normal'}`}
                  style={{ width: `${scoreProgress}%` }}
                />
              </div>
            </div>
          </>
        ) : (
          <p className="empty-state">No analysis result yet.</p>
        )}
      </section>
    </div>
  );
}
