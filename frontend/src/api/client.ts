export const API_BASE =
  import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, '') || 'http://localhost:8000';

export type PredictionResponse = {
  anomaly_score: number;
  threshold: number;
  label: 'ATTACK' | 'NORMAL';
  attack_type: string | null;
  confidence: number;
  is_attack: boolean;
  processing_time_ms: number;
  details?: Record<string, unknown> | null;
};

export type LivePayload = {
  score: number;
  label: 'ATTACK' | 'NORMAL';
  attack_type?: string | null;
  confidence?: number;
  threshold: number;
  timestamp: string;
};

export type HealthResponse = {
  status: string;
  model: string;
  device: string;
};

export type StatsResponse = {
  total_analyzed: number;
  attacks_detected: number;
  normals_detected: number;
  detection_rate: number;
  average_anomaly_score: number;
  attack_type_breakdown: Record<string, number>;
  last_prediction: {
    timestamp?: string;
    label?: string;
    attack_type?: string | null;
    score?: number;
    confidence?: number;
  };
  uptime_seconds: number;
};

export type ReportsManifest = {
  available_files: Array<{ name: string; url: string; size_bytes: number }>;
  metrics?: {
    metrics?: {
      accuracy?: number;
      precision?: number;
      recall?: number;
      f1?: number;
      auc?: number;
      ap?: number;
    };
  };
};

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers ?? {}),
    },
    ...init,
  });

  if (!response.ok) {
    const fallback = `Request failed with status ${response.status}`;
    try {
      const err = (await response.json()) as { detail?: string };
      throw new Error(err.detail ?? fallback);
    } catch {
      throw new Error(fallback);
    }
  }

  return (await response.json()) as T;
}

export const apiClient = {
  getHealth: () => requestJson<HealthResponse>('/health'),
  getStats: () => requestJson<StatsResponse>('/stats'),
  getThreshold: () => requestJson<Record<string, unknown>>('/threshold'),
  getVocabSize: () => requestJson<{ vocab_size: number }>('/vocab/size'),
  getReportsManifest: () => requestJson<ReportsManifest>('/reports/manifest'),
  predict: (sequence: string[], returnDetails = true) =>
    requestJson<PredictionResponse>('/predict', {
      method: 'POST',
      body: JSON.stringify({ sequence, return_details: returnDetails }),
    }),
  predictBatch: (sequences: string[][], returnDetails = false) =>
    requestJson<{
      total: number;
      attacks: number;
      normals: number;
      average_score: number;
      predictions: PredictionResponse[];
    }>('/predict/batch', {
      method: 'POST',
      body: JSON.stringify({ sequences, return_details: returnDetails }),
    }),
  getReportAssetUrl: (fileName: string) => `${API_BASE}/static/reports/${fileName}`,
  getWebSocketUrl: () => API_BASE.replace(/^http/, 'ws') + '/ws/live',
};
