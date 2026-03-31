# CAN Bus IDS Dashboard - Setup Guide

Complete instructions for running your CAN Bus Intrusion Detection System dashboard.

## Prerequisites

✅ Backend API running on `http://localhost:8000`
✅ Node.js and npm installed
✅ Frontend dependencies installed

## Quick Start

### Terminal 1: Start Backend API

```bash
cd E:/PROJECTS/can_bus_ids_project
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

Wait for:
```
[API] Ready to accept connections!
```

### Terminal 2: Start Frontend Dashboard

```bash
cd E:/PROJECTS/can_bus_ids_project/frontend
npm run dev
```

### Terminal 3 (Optional): Test the API Endpoints

```bash
# Check health
curl http://localhost:8000/health

# Check docs
# Open http://localhost:8000/docs in browser
```

## Open the Dashboard

Navigate to: **http://localhost:3000**

## What to Expect

### Automatic Test Data Generation

The dashboard now **automatically generates simulated CAN bus traffic** when you connect!

- **10 frames per second** (adjustable)
- **8% attack probability** (realistic mix)
- Uses real CAN IDs from your vocabulary
- Unknown IDs trigger anomaly detection

### Dashboard Features

1. **Header**: Connection status, uptime, system secure/threat indicator
2. **Metric Cards**:
   - Current anomaly score (updates in real-time)
   - Messages processed (increments every frame)
   - Threats detected (counts attacks)
   - Network status with buffer progress
3. **Real-Time Chart**: Smooth-scrolling line graph with threshold
4. **Threat Log**: Terminal-style log of detected attacks

### Expected Behavior

✅ Within 10 seconds:
- Messages Processed should start incrementing
- Real-time chart starts plotting points
- Buffer fills to 64/64

✅ Within 30-60 seconds:
- First threats detected (if random generates attacks)
- Threat log populates with attack details
- Anomaly scores fluctuate

## Troubleshooting

### "Connected but no data"
✅ **FIXED!** Test data generator now runs automatically.

### "Connection failed"
- Check backend is running: `curl http://localhost:8000/health`
- Check port 8000 is not in use
- Review backend logs for errors

### "Build errors"
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run build
```

### "WebSocket errors in console"
- Ensure backend started before frontend
- Check firewall isn't blocking WebSocket
- Try: `ws://127.0.0.1:8000/ws/predict`

## Manual Testing (Optional)

If you want to send your own CAN frames:

1. Open browser console (F12)
2. Paste this code:

```javascript
// Test normal traffic
const testNormal = () => {
  const ws = new WebSocket('ws://localhost:8000/ws/predict');

  ws.onopen = () => {
    // Send normal CAN IDs
    const normalIds = ['0316', '018f', '0260', '02a0'];
    normalIds.forEach(id => {
      ws.send(JSON.stringify({
        can_id: id,
        timestamp: Date.now() / 1000
      }));
    });
  };
};

// Test attack traffic
const testAttack = () => {
  const ws = new WebSocket('ws://localhost:8000/ws/predict');

  ws.onopen = () => {
    // Send unknown CAN IDs (triggers UNK -> high anomaly)
    const attackIds = ['0000', 'ffff', 'aaaa'];
    attackIds.forEach(id => {
      ws.send(JSON.stringify({
        can_id: id,
        timestamp: Date.now() / 1000
      }));
    });
  };
};
```

## Production Build

```bash
cd frontend
npm run build

# Output in: frontend/dist/
# Serve with: npx serve dist
```

## Features Overview

| Feature | Status | Notes |
|---------|--------|-------|
| Automatic test data | ✅ | 10 FPS, 8% attack rate |
| Real-time WebSocket | ✅ | Auto-reconnect |
| Anomaly detection | ✅ | DistilBERT model |
| Threshold calibration | ✅ | 99th percentile |
| Dark mode UI | ✅ | Cybersecurity aesthetic |
| Glassmorphism | ✅ | Professional design |
| Attack logging | ✅ | Terminal-style |
| Live telemetry chart | ✅ | Recharts |

## Configuration

Edit `frontend/src/hooks/useWebSocket.ts`:

```typescript
const TEST_DATA_INTERVAL = 100;    // ms between frames (100 = 10 FPS)
const ATTACK_PROBABILITY = 0.08;   // 0.08 = 8% chance of attack
```

## Architecture

```
┌─────────────┐     WebSocket      ┌──────────────┐
│   React     │ ←──────────────→  │  FastAPI     │
│  Dashboard  │  CAN Frames       │   Backend    │
│  (Port 3000)│  Predictions      │  (Port 8000) │
└─────────────┘                    └──────────────┘
      ↓                                    ↓
Test Data Generator            DistilBERT Model
(Simulated Traffic)          (Anomaly Detection)
```

## Credits

Built with:
- React + TypeScript + Vite
- Tailwind CSS
- Recharts
- Lucide React Icons
- FastAPI + WebSocket
- PyTorch + Transformers

---

**Need help?** Check the API docs at http://localhost:8000/docs
