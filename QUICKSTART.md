# 🚀 Quick Start Guide - Dashboard

Simple steps to run your CAN Bus IDS Dashboard with automatic test data.

## Start in 2 Minutes

### Step 1: Start Backend (Terminal 1)

```bash
cd <path-to-your-cloned-repo>/can_bus_ids_project
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

**Or double-click**: `start_backend.bat`

Wait for:
```
[API] Ready to accept connections!
```

### Step 2: Start Frontend (Terminal 2)

```bash
cd <path-to-your-cloned-repo>/can_bus_ids_project/frontend
npm run dev
```
# Terminal 1
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000

# Terminal 2
cd frontend && npm run dev

**Or double-click**: `start_frontend.bat`

Wait for:
```
Local: http://localhost:3000/
```

### Step 3: Open Dashboard

Navigate to: **http://localhost:3000**

---

## What to Expect ✅

### Immediate (0-5 seconds)
- ✅ Dashboard loads
- ✅ "Connected" status appears
- ✅ **Test data generator starts automatically**

### After 10 seconds
- ✅ Messages Processed counter increments
- ✅ Buffer fills to 64/64
- ✅ Real-time chart starts plotting
- ✅ Anomaly scores appear

### After 30-60 seconds
- ✅ First attacks detected (random, ~8% probability)
- ✅ Threat log populates
- ✅ Red dots appear on chart at attack points

---

## The Fix Applied

### Previous Issue
Dashboard showed "Connected" but no data flowed because the backend expected YOU to send CAN frames.

### Solution
Created **automatic test data generator** that:
- Sends 10 frames/second automatically
- Uses real CAN IDs from your vocabulary
- Generates 8% attack traffic (unknown IDs)
- Starts automatically when WebSocket connects

### Files Modified
- `frontend/src/utils/testDataGenerator.ts` - New test generator
- `frontend/src/hooks/useWebSocket.ts` - Auto-starts generator on connect

---

## Customization

Want to adjust the test data? Edit `frontend/src/hooks/useWebSocket.ts`:

```typescript
// Line ~25
const TEST_DATA_INTERVAL = 100;    // 100ms = 10 frames/sec
const ATTACK_PROBABILITY = 0.08;   // 8% attack rate
```

**Increase speed**: Lower interval (50ms = 20 FPS)
**More attacks**: Increase probability (0.15 = 15%)

---

## Troubleshooting

### Backend won't start
```bash
# Check if port 8000 is in use
taskkill /F /IM python.exe

# Try again
python -m uvicorn backend.main:app --port 8000
```

### Frontend won't start
```bash
cd frontend
rm -rf node_modules
npm install
npm run dev
```

### Still no data?
1. Open browser console (F12)
2. Check for WebSocket errors
3. Ensure backend started BEFORE frontend
4. Try refreshing the page

---

## Next Steps

Once working, explore:
- **Real data**: Send your own CAN frames via WebSocket
- **Threshold tuning**: Adjust detection sensitivity via API
- **Production build**: `npm run build` in frontend folder
- **API docs**: http://localhost:8000/docs

---

**Need more details?** See `frontend/SETUP.md` or main `README.md`
