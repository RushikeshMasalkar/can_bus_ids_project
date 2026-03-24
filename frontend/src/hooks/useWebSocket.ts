// =============================================================================
// useWebSocket.ts - Custom React Hook for WebSocket Connection
// Handles real-time streaming, reconnection logic, and state management
// =============================================================================

import { useState, useCallback, useRef, useEffect } from 'react';
import type {
  ConnectionState,
  DashboardStats,
  ChartDataPoint,
  ThreatLogEntry,
  PredictionMessage,
  WebSocketMessage,
  UseWebSocketReturn,
  CANFrame,
} from '../types';
import { testDataGenerator } from '../utils/testDataGenerator';

// Configuration
const WS_URL = 'ws://localhost:8000/ws/predict';
const MAX_CHART_POINTS = 100;      // Maximum data points to display
const MAX_LOG_ENTRIES = 50;        // Maximum threat log entries
const RECONNECT_DELAY = 3000;      // Reconnection delay in ms
const MAX_RECONNECT_ATTEMPTS = 10; // Maximum reconnection attempts
const TEST_DATA_INTERVAL = 100;    // Send frame every 100ms (10 frames/sec)
const ATTACK_PROBABILITY = 0.08;   // 8% chance of attack frame

/**
 * Custom hook for managing WebSocket connection to the CAN Bus IDS backend.
 * Provides real-time anomaly detection data, statistics, and automatic reconnection.
 */
export function useWebSocket(): UseWebSocketReturn {
  // Connection state
  const [connectionState, setConnectionState] = useState<ConnectionState>('disconnected');
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttempts = useRef(0);
  const reconnectTimeout = useRef<ReturnType<typeof setTimeout> | null>(null);
  const startTime = useRef<number>(Date.now());

  // Dashboard statistics
  const [stats, setStats] = useState<DashboardStats>({
    messagesProcessed: 0,
    attacksDetected: 0,
    currentScore: 0,
    bufferSize: 0,
    isConnected: false,
    networkStatus: 'disconnected',
    threshold: 3.26,
    lastUpdate: new Date().toISOString(),
    uptime: 0,
  });

  // Chart data (rolling window)
  const [chartData, setChartData] = useState<ChartDataPoint[]>([]);

  // Threat log
  const [threatLog, setThreatLog] = useState<ThreatLogEntry[]>([]);

  // Last prediction for display
  const [lastPrediction, setLastPrediction] = useState<PredictionMessage | null>(null);

  /**
   * Generate unique ID for log entries
   */
  const generateId = useCallback(() => {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }, []);

  /**
   * Format timestamp for display
   */
  const formatTime = useCallback((isoString: string) => {
    const date = new Date(isoString);
    return date.toLocaleTimeString('en-US', {
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  }, []);

  /**
   * Handle incoming WebSocket messages
   */
  const handleMessage = useCallback((event: MessageEvent) => {
    try {
      const message: WebSocketMessage = JSON.parse(event.data);

      switch (message.type) {
        case 'connection':
          console.log('[WS] Connected:', message.message);
          setStats(prev => ({
            ...prev,
            threshold: message.threshold,
            isConnected: true,
            networkStatus: 'buffering',
          }));
          break;

        case 'buffering':
          setStats(prev => ({
            ...prev,
            bufferSize: message.buffer_size,
            networkStatus: 'buffering',
            messagesProcessed: prev.messagesProcessed + 1,
            lastUpdate: new Date().toISOString(),
          }));
          break;

        case 'prediction':
          const prediction = message as PredictionMessage;
          setLastPrediction(prediction);

          // Update stats
          setStats(prev => ({
            ...prev,
            messagesProcessed: prev.messagesProcessed + 1,
            currentScore: prediction.anomaly_score,
            bufferSize: prediction.buffer_size,
            threshold: prediction.threshold,
            attacksDetected: prediction.is_attack
              ? prev.attacksDetected + 1
              : prev.attacksDetected,
            networkStatus: prediction.is_attack ? 'threat' : 'secure',
            lastUpdate: prediction.timestamp,
            uptime: Math.floor((Date.now() - startTime.current) / 1000),
          }));

          // Add to chart data
          const chartPoint: ChartDataPoint = {
            timestamp: Date.now(),
            time: formatTime(prediction.timestamp),
            score: prediction.anomaly_score,
            isAttack: prediction.is_attack,
            canId: prediction.can_id,
          };

          setChartData(prev => {
            const newData = [...prev, chartPoint];
            return newData.slice(-MAX_CHART_POINTS);
          });

          // Add to threat log if it's an attack
          if (prediction.is_attack) {
            const logEntry: ThreatLogEntry = {
              id: generateId(),
              timestamp: prediction.timestamp,
              localTime: formatTime(prediction.timestamp),
              anomalyScore: prediction.anomaly_score,
              canId: prediction.can_id,
              isAttack: true,
              confidence: prediction.confidence,
            };

            setThreatLog(prev => {
              const newLog = [logEntry, ...prev];
              return newLog.slice(0, MAX_LOG_ENTRIES);
            });
          }
          break;

        case 'error':
          console.error('[WS] Error:', message.error, message.details);
          break;

        default:
          console.log('[WS] Unknown message type:', message);
      }
    } catch (error) {
      console.error('[WS] Failed to parse message:', error);
    }
  }, [formatTime, generateId]);

  /**
   * Send a CAN frame to the backend via WebSocket
   */
  const sendFrame = useCallback((frame: CANFrame) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      try {
        wsRef.current.send(JSON.stringify(frame));
      } catch (error) {
        console.error('[WS] Failed to send frame:', error);
      }
    }
  }, []);

  /**
   * Connect to WebSocket server
   */
  const connect = useCallback(() => {
    // Don't connect if already connected
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    // Clear any existing reconnection timeout
    if (reconnectTimeout.current) {
      clearTimeout(reconnectTimeout.current);
      reconnectTimeout.current = null;
    }

    setConnectionState('connecting');
    console.log('[WS] Connecting to', WS_URL);

    try {
      const ws = new WebSocket(WS_URL);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('[WS] Connection established');
        setConnectionState('connected');
        reconnectAttempts.current = 0;
        startTime.current = Date.now();

        // Start sending test CAN frames automatically
        console.log('[WS] Starting test data generator');
        testDataGenerator.start(sendFrame, TEST_DATA_INTERVAL, ATTACK_PROBABILITY);
      };

      ws.onmessage = handleMessage;

      ws.onerror = (error) => {
        console.error('[WS] Connection error:', error);
        setConnectionState('error');
      };

      ws.onclose = (event) => {
        console.log('[WS] Connection closed:', event.code, event.reason);
        setConnectionState('disconnected');
        setStats(prev => ({
          ...prev,
          isConnected: false,
          networkStatus: 'disconnected',
        }));

        // Stop test data generator
        testDataGenerator.stop();

        // Attempt to reconnect if not intentionally closed
        if (event.code !== 1000 && reconnectAttempts.current < MAX_RECONNECT_ATTEMPTS) {
          reconnectAttempts.current++;
          console.log(`[WS] Reconnecting in ${RECONNECT_DELAY}ms (attempt ${reconnectAttempts.current}/${MAX_RECONNECT_ATTEMPTS})`);

          reconnectTimeout.current = setTimeout(() => {
            connect();
          }, RECONNECT_DELAY);
        }
      };
    } catch (error) {
      console.error('[WS] Failed to create WebSocket:', error);
      setConnectionState('error');
    }
  }, [handleMessage, sendFrame]);

  /**
   * Disconnect from WebSocket server
   */
  const disconnect = useCallback(() => {
    // Stop test data generator
    testDataGenerator.stop();

    if (reconnectTimeout.current) {
      clearTimeout(reconnectTimeout.current);
      reconnectTimeout.current = null;
    }

    if (wsRef.current) {
      wsRef.current.close(1000, 'User initiated disconnect');
      wsRef.current = null;
    }

    setConnectionState('disconnected');
    reconnectAttempts.current = 0;
  }, []);

  /**
   * Clear threat log
   */
  const clearLog = useCallback(() => {
    setThreatLog([]);
  }, []);

  // Auto-connect on mount
  useEffect(() => {
    connect();

    // Cleanup on unmount
    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  // Update uptime periodically
  useEffect(() => {
    const interval = setInterval(() => {
      if (connectionState === 'connected') {
        setStats(prev => ({
          ...prev,
          uptime: Math.floor((Date.now() - startTime.current) / 1000),
        }));
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [connectionState]);

  return {
    connectionState,
    stats,
    chartData,
    threatLog,
    lastPrediction,
    connect,
    disconnect,
    clearLog,
  };
}

export default useWebSocket;
