import { useEffect, useMemo, useRef, useState } from 'react';
import { apiClient, type LivePayload } from '../api/client';

export type LivePoint = {
  id: number;
  time: string;
  score: number;
  threshold: number;
  label: 'ATTACK' | 'NORMAL';
  attackType: string | null;
  attackScore: number | null;
};

export type AlertItem = {
  id: number;
  time: string;
  score: number;
  attackType: string;
  confidence: number;
};

const MAX_POINTS = 90;
const MAX_ALERTS = 10;

export function useLiveStream() {
  const [points, setPoints] = useState<LivePoint[]>([]);
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [totalAnalyzed, setTotalAnalyzed] = useState(0);
  const [attacksDetected, setAttacksDetected] = useState(0);
  const [threshold, setThreshold] = useState(0);

  const idCounter = useRef(0);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    const ws = new WebSocket(apiClient.getWebSocketUrl());
    wsRef.current = ws;

    ws.onopen = () => {
      setConnected(true);
      setError(null);
    };

    ws.onclose = () => {
      setConnected(false);
    };

    ws.onerror = () => {
      setError('Live stream connection failed. Check backend availability.');
    };

    ws.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data) as LivePayload;

        if (typeof payload.score !== 'number') {
          return;
        }

        idCounter.current += 1;
        const time = new Date(payload.timestamp).toLocaleTimeString([], {
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit',
        });

        const point: LivePoint = {
          id: idCounter.current,
          time,
          score: payload.score,
          threshold: payload.threshold,
          label: payload.label,
          attackType: payload.attack_type ?? null,
          attackScore: payload.label === 'ATTACK' ? payload.score : null,
        };

        setThreshold(payload.threshold);
        setTotalAnalyzed((prev) => prev + 1);
        if (payload.label === 'ATTACK') {
          setAttacksDetected((prev) => prev + 1);
        }

        setPoints((prev) => {
          const updated = [...prev, point];
          return updated.slice(Math.max(0, updated.length - MAX_POINTS));
        });

        if (payload.label === 'ATTACK') {
          const alert: AlertItem = {
            id: point.id,
            time,
            score: payload.score,
            attackType: payload.attack_type ?? 'Unknown',
            confidence: payload.confidence ?? 0,
          };

          setAlerts((prev) => [alert, ...prev].slice(0, MAX_ALERTS));
        }
      } catch {
        setError('Received malformed live stream message.');
      }
    };

    return () => {
      ws.close();
    };
  }, []);

  const detectionRate = useMemo(() => {
    if (!totalAnalyzed) return 0;
    return (attacksDetected / totalAnalyzed) * 100;
  }, [attacksDetected, totalAnalyzed]);

  const attackBreakdown = useMemo(() => {
    const map = new Map<string, number>();
    alerts.forEach((item) => {
      map.set(item.attackType, (map.get(item.attackType) ?? 0) + 1);
    });
    return Array.from(map.entries()).map(([name, value]) => ({ name, value }));
  }, [alerts]);

  const scoreDistribution = useMemo(() => {
    if (points.length === 0) {
      return [] as Array<{ bin: string; count: number }>;
    }

    const min = Math.min(...points.map((item) => item.score));
    const max = Math.max(...points.map((item) => item.score));
    const bins = 8;
    const width = (max - min) / bins || 0.1;

    const counts = new Array<number>(bins).fill(0);

    points.forEach((item) => {
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
  }, [points]);

  return {
    points,
    alerts,
    connected,
    error,
    threshold,
    totalAnalyzed,
    attacksDetected,
    detectionRate,
    attackBreakdown,
    scoreDistribution,
  };
}
