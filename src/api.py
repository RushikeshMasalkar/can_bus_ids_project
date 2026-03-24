# src/api.py
# Phase 9: FastAPI Backend for Real-Time CAN Bus Intrusion Detection
# ==============================================================================
# This module provides a production-ready REST and WebSocket API for real-time
# anomaly detection in CAN bus traffic using a trained DistilBERT model.
# ==============================================================================

import os
import sys
import json
import gc
import asyncio
from pathlib import Path
from datetime import datetime
from collections import deque
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager

import numpy as np
import torch
import torch.nn.functional as F
from transformers import DistilBertConfig, DistilBertForMaskedLM

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator
import uvicorn

# ==============================================================================
# CONFIGURATION
# ==============================================================================

# Paths
BASE_DIR       = Path(__file__).resolve().parent.parent
DATA_DIR       = BASE_DIR / "data"
MODELS_DIR     = BASE_DIR / "models"

VOCAB_PATH     = DATA_DIR / "vocab.json"
MODEL_PATH     = MODELS_DIR / "best_model.pt"
THRESHOLD_PATH = MODELS_DIR / "threshold.json"

# Model hyperparameters (must match training configuration)
WINDOW_SIZE = 64       # Sliding window size for sequences
MASK_RATIO  = 0.15     # MLM mask ratio for anomaly scoring

# Special token IDs
PAD_ID  = 0
MASK_ID = 1
UNK_ID  = 2

# Device configuration
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Default threshold (will be overwritten by threshold.json if available)
DEFAULT_THRESHOLD = 3.2565


# ==============================================================================
# PYDANTIC MODELS (Request/Response Schemas)
# ==============================================================================

class CANFrame(BaseModel):
    """
    Schema for a single CAN bus frame received via WebSocket.

    Attributes:
        can_id: The CAN arbitration ID (hex string like "0x250" or "250")
        timestamp: Optional Unix timestamp of the frame
        dlc: Optional Data Length Code (0-8)
        data: Optional data bytes as hex strings
    """
    can_id: str = Field(..., description="CAN ID in hex format (e.g., '0x250' or '0250')")
    timestamp: Optional[float] = Field(None, description="Unix timestamp of the frame")
    dlc: Optional[int] = Field(None, ge=0, le=8, description="Data Length Code")
    data: Optional[List[str]] = Field(None, description="Data bytes as hex strings")

    @field_validator('can_id')
    @classmethod
    def validate_can_id(cls, v: str) -> str:
        """Normalize CAN ID to lowercase hex without '0x' prefix."""
        v = v.strip().lower()
        if v.startswith('0x'):
            v = v[2:]
        return v.zfill(4)  # Pad to 4 characters


class PredictionResponse(BaseModel):
    """
    Schema for the prediction response sent back via WebSocket.

    Attributes:
        anomaly_score: The reconstruction loss (higher = more anomalous)
        is_attack: Boolean flag indicating if score exceeds threshold
        threshold: The current threshold value used for classification
        buffer_size: Current number of frames in the sliding window
        timestamp: Server timestamp of the prediction
        can_id: The CAN ID that triggered this prediction
    """
    anomaly_score: float = Field(..., description="Reconstruction loss score")
    is_attack: bool = Field(..., description="True if anomaly_score > threshold")
    threshold: float = Field(..., description="Current detection threshold")
    buffer_size: int = Field(..., description="Frames in sliding window")
    timestamp: str = Field(..., description="ISO format timestamp")
    can_id: str = Field(..., description="CAN ID that triggered prediction")
    confidence: float = Field(..., description="Confidence level (0-1)")


class HealthResponse(BaseModel):
    """Schema for the health check endpoint response."""
    status: str = Field(..., description="Service status")
    model_loaded: bool = Field(..., description="Whether model is loaded")
    vocab_loaded: bool = Field(..., description="Whether vocabulary is loaded")
    device: str = Field(..., description="Compute device (cuda/cpu)")
    vocab_size: int = Field(..., description="Number of tokens in vocabulary")
    threshold: float = Field(..., description="Current anomaly threshold")
    window_size: int = Field(..., description="Sliding window size")
    uptime_seconds: float = Field(..., description="API uptime in seconds")
    version: str = Field(..., description="API version")


class ThresholdUpdate(BaseModel):
    """Schema for updating the detection threshold."""
    threshold: float = Field(..., gt=0, description="New threshold value")


class BatchPredictionRequest(BaseModel):
    """Schema for batch prediction endpoint."""
    frames: List[CANFrame] = Field(..., min_length=1, description="List of CAN frames")


class BatchPredictionResponse(BaseModel):
    """Schema for batch prediction response."""
    anomaly_score: float
    is_attack: bool
    threshold: float
    num_frames: int
    timestamp: str


# ==============================================================================
# GLOBAL STATE (Populated during lifespan startup)
# ==============================================================================

class ModelState:
    """
    Global container for the loaded model and vocabulary.
    Initialized during FastAPI lifespan startup event.
    """
    model: Optional[DistilBertForMaskedLM] = None
    vocab: Optional[Dict[str, int]] = None
    vocab_size: int = 0
    threshold: float = DEFAULT_THRESHOLD
    startup_time: Optional[datetime] = None
    is_ready: bool = False


# Global state instance
state = ModelState()


# ==============================================================================
# MODEL LOADING FUNCTIONS
# ==============================================================================

def load_vocabulary(vocab_path: Path) -> Dict[str, int]:
    """
    Load the vocabulary mapping from hex CAN IDs to integer tokens.

    Args:
        vocab_path: Path to vocab.json file

    Returns:
        Dictionary mapping hex CAN ID strings to integer token IDs

    Raises:
        FileNotFoundError: If vocab file doesn't exist
    """
    if not vocab_path.exists():
        raise FileNotFoundError(f"Vocabulary file not found: {vocab_path}")

    with open(vocab_path, 'r') as f:
        vocab = json.load(f)

    print(f"[API] Vocabulary loaded: {len(vocab)} tokens")
    return vocab


def load_model(model_path: Path, vocab_size: int) -> DistilBertForMaskedLM:
    """
    Load the trained DistilBERT model for inference.

    Args:
        model_path: Path to best_model.pt checkpoint
        vocab_size: Size of vocabulary for model configuration

    Returns:
        Loaded model in evaluation mode on the appropriate device

    Raises:
        FileNotFoundError: If model file doesn't exist
    """
    if not model_path.exists():
        raise FileNotFoundError(f"Model checkpoint not found: {model_path}")

    # Load checkpoint
    checkpoint = torch.load(model_path, map_location=DEVICE, weights_only=False)
    print(f"[API] Checkpoint loaded (epoch {checkpoint.get('epoch', 'N/A')})")

    # Reconstruct model architecture
    config = DistilBertConfig(
        vocab_size              = vocab_size,
        max_position_embeddings = WINDOW_SIZE,
        dim                     = 256,
        n_layers                = 4,
        n_heads                 = 4,
        hidden_dim              = 1024,
        dropout                 = 0.1,
        attention_dropout       = 0.1,
        pad_token_id            = PAD_ID,
    )

    model = DistilBertForMaskedLM(config)
    model.load_state_dict(checkpoint['model_state'])
    model = model.to(DEVICE)
    model.eval()  # Set to evaluation mode

    print(f"[API] Model loaded on {DEVICE}")
    return model


def load_threshold(threshold_path: Path) -> float:
    """
    Load the calibrated threshold from threshold.json.

    Args:
        threshold_path: Path to threshold.json

    Returns:
        Calibrated threshold value
    """
    if threshold_path.exists():
        with open(threshold_path, 'r') as f:
            data = json.load(f)
        threshold = data.get('threshold', DEFAULT_THRESHOLD)
        print(f"[API] Threshold loaded: {threshold:.6f}")
        return threshold
    else:
        print(f"[API] Using default threshold: {DEFAULT_THRESHOLD}")
        return DEFAULT_THRESHOLD


# ==============================================================================
# INFERENCE FUNCTIONS
# ==============================================================================

def tokenize_can_id(can_id: str) -> int:
    """
    Convert a hex CAN ID to its integer token.

    Args:
        can_id: Normalized CAN ID string (e.g., "0250")

    Returns:
        Integer token ID, or UNK_ID if not in vocabulary
    """
    return state.vocab.get(can_id, UNK_ID)


def calculate_anomaly_score(sequence: List[int]) -> float:
    """
    Calculate the reconstruction loss (anomaly score) for a sequence.

    Uses MLM-style masking: masks 15% of tokens randomly, predicts them,
    and calculates cross-entropy loss. Higher loss indicates anomaly.

    Args:
        sequence: List of 64 integer token IDs

    Returns:
        Anomaly score (reconstruction loss)
    """
    if state.model is None:
        raise RuntimeError("Model not loaded")

    state.model.eval()

    with torch.no_grad():
        # Convert to tensor: (1, 64)
        input_tensor = torch.tensor([sequence], dtype=torch.long, device=DEVICE)
        B, L = input_tensor.shape

        # Clone for masking
        input_ids = input_tensor.clone()
        labels = torch.full((B, L), -100, dtype=torch.long, device=DEVICE)

        # Create random mask (15% of tokens)
        prob_matrix = torch.rand(B, L, device=DEVICE)
        masked_indices = prob_matrix < MASK_RATIO

        # Never mask special tokens
        special_mask = (
            (input_tensor == PAD_ID) |
            (input_tensor == MASK_ID) |
            (input_tensor == UNK_ID)
        )
        masked_indices = masked_indices & ~special_mask

        # Ensure at least one token is masked
        if not masked_indices.any():
            # Randomly select one position to mask
            valid_positions = ~special_mask
            if valid_positions.any():
                valid_indices = valid_positions.nonzero(as_tuple=True)
                random_idx = torch.randint(0, len(valid_indices[1]), (1,))
                masked_indices[0, valid_indices[1][random_idx]] = True

        # Set labels at masked positions
        labels[masked_indices] = input_tensor[masked_indices]

        # Replace masked positions with [MASK] token
        input_ids[masked_indices] = MASK_ID

        # Create attention mask
        attention_mask = torch.ones(B, L, dtype=torch.long, device=DEVICE)

        # Forward pass
        outputs = state.model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            labels=labels
        )

        # Get the loss
        if outputs.loss is not None:
            return float(outputs.loss.item())
        else:
            # Manual loss calculation if needed
            logits = outputs.logits
            loss_per_pos = F.cross_entropy(
                logits.view(-1, logits.size(-1)),
                labels.view(-1),
                reduction='none',
                ignore_index=-100
            ).view(B, L)

            mask_counts = (labels != -100).sum(dim=1).float().clamp(min=1)
            seq_scores = loss_per_pos.sum(dim=1) / mask_counts

            return float(seq_scores[0].item())


def calculate_confidence(anomaly_score: float, threshold: float) -> float:
    """
    Calculate confidence level for the prediction.

    For attacks: how far above threshold (capped at 1.0)
    For normal: how far below threshold (capped at 1.0)

    Args:
        anomaly_score: The computed anomaly score
        threshold: Current detection threshold

    Returns:
        Confidence value between 0 and 1
    """
    if anomaly_score > threshold:
        # Attack: confidence based on how much above threshold
        distance = (anomaly_score - threshold) / threshold
        return min(1.0, 0.5 + distance * 0.5)
    else:
        # Normal: confidence based on how much below threshold
        distance = (threshold - anomaly_score) / threshold
        return min(1.0, 0.5 + distance * 0.5)


# ==============================================================================
# FASTAPI LIFESPAN (Startup/Shutdown Events)
# ==============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan context manager for startup and shutdown events.

    On startup:
        - Load vocabulary from vocab.json
        - Load trained model from best_model.pt
        - Load threshold from threshold.json
        - Initialize global state

    On shutdown:
        - Clean up model from memory
        - Clear CUDA cache if applicable
    """
    # ─────────────────────────────────────────────────────────────────────────
    # STARTUP
    # ─────────────────────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("[API] Starting CAN Bus IDS Backend...")
    print("=" * 60)

    try:
        # Load vocabulary
        state.vocab = load_vocabulary(VOCAB_PATH)
        state.vocab_size = len(state.vocab)

        # Load model
        state.model = load_model(MODEL_PATH, state.vocab_size)

        # Load threshold
        state.threshold = load_threshold(THRESHOLD_PATH)

        # Mark as ready
        state.startup_time = datetime.now()
        state.is_ready = True

        print(f"[API] Device: {DEVICE}")
        print(f"[API] Vocab size: {state.vocab_size}")
        print(f"[API] Threshold: {state.threshold:.6f}")
        print(f"[API] Ready to accept connections!")
        print("=" * 60 + "\n")

    except Exception as e:
        print(f"[API] FATAL: Failed to initialize - {e}")
        raise

    yield  # Application runs here

    # ─────────────────────────────────────────────────────────────────────────
    # SHUTDOWN
    # ─────────────────────────────────────────────────────────────────────────
    print("\n[API] Shutting down...")

    # Clean up model
    if state.model is not None:
        del state.model
        state.model = None

    # Clear CUDA cache
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    gc.collect()
    print("[API] Shutdown complete.")


# ==============================================================================
# FASTAPI APPLICATION
# ==============================================================================

app = FastAPI(
    title="CAN Bus Intrusion Detection System API",
    description="""
    Real-time intrusion detection for CAN bus networks using a Transformer-based
    anomaly detection model. This API provides both REST and WebSocket endpoints
    for detecting cyber attacks in automotive CAN bus traffic.

    ## Features
    - Real-time streaming inference via WebSocket
    - Sliding window analysis (64-frame windows)
    - Configurable detection threshold
    - GPU acceleration support

    ## Model
    - Architecture: DistilBERT for Masked Language Modeling
    - Anomaly Detection: Reconstruction loss (Cross-Entropy)
    - Higher loss = More anomalous = Likely attack
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware for cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==============================================================================
# REST ENDPOINTS
# ==============================================================================

@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": "CAN Bus IDS API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "websocket": "ws://host:port/ws/predict"
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Health check endpoint to verify API and model status.

    Returns:
        HealthResponse with detailed system status

    Raises:
        HTTPException: If model or vocabulary is not loaded
    """
    if not state.is_ready:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not ready. Model or vocabulary not loaded."
        )

    uptime = (datetime.now() - state.startup_time).total_seconds() if state.startup_time else 0

    return HealthResponse(
        status="healthy",
        model_loaded=state.model is not None,
        vocab_loaded=state.vocab is not None,
        device=str(DEVICE),
        vocab_size=state.vocab_size,
        threshold=state.threshold,
        window_size=WINDOW_SIZE,
        uptime_seconds=round(uptime, 2),
        version="1.0.0"
    )


@app.get("/threshold", tags=["Configuration"])
async def get_threshold():
    """Get the current anomaly detection threshold."""
    return {"threshold": state.threshold}


@app.put("/threshold", tags=["Configuration"])
async def update_threshold(update: ThresholdUpdate):
    """
    Update the anomaly detection threshold.

    Args:
        update: ThresholdUpdate with new threshold value

    Returns:
        Confirmation with old and new threshold values
    """
    old_threshold = state.threshold
    state.threshold = update.threshold

    return {
        "message": "Threshold updated successfully",
        "old_threshold": old_threshold,
        "new_threshold": state.threshold
    }


@app.get("/vocab/stats", tags=["Vocabulary"])
async def vocab_stats():
    """Get vocabulary statistics."""
    if state.vocab is None:
        raise HTTPException(status_code=503, detail="Vocabulary not loaded")

    special_tokens = sum(1 for k in state.vocab.keys() if k.startswith('['))

    return {
        "total_tokens": state.vocab_size,
        "special_tokens": special_tokens,
        "can_id_tokens": state.vocab_size - special_tokens,
        "special_token_ids": {
            "[PAD]": PAD_ID,
            "[MASK]": MASK_ID,
            "[UNK]": UNK_ID
        }
    }


@app.post("/predict/batch", response_model=BatchPredictionResponse, tags=["Prediction"])
async def batch_predict(request: BatchPredictionRequest):
    """
    Batch prediction endpoint for non-streaming use cases.

    Accepts a list of CAN frames and returns the anomaly score.
    Requires exactly 64 frames for a complete prediction.

    Args:
        request: BatchPredictionRequest with list of CAN frames

    Returns:
        BatchPredictionResponse with anomaly score and classification
    """
    if not state.is_ready:
        raise HTTPException(status_code=503, detail="Service not ready")

    frames = request.frames

    if len(frames) < WINDOW_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"Requires at least {WINDOW_SIZE} frames. Got {len(frames)}."
        )

    # Take the last 64 frames
    recent_frames = frames[-WINDOW_SIZE:]

    # Tokenize
    tokens = [tokenize_can_id(frame.can_id) for frame in recent_frames]

    # Calculate anomaly score
    try:
        anomaly_score = calculate_anomaly_score(tokens)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inference error: {str(e)}")

    is_attack = anomaly_score > state.threshold

    return BatchPredictionResponse(
        anomaly_score=round(anomaly_score, 6),
        is_attack=is_attack,
        threshold=state.threshold,
        num_frames=len(recent_frames),
        timestamp=datetime.now().isoformat()
    )


# ==============================================================================
# WEBSOCKET ENDPOINT FOR REAL-TIME STREAMING
# ==============================================================================

@app.websocket("/ws/predict")
async def websocket_predict(websocket: WebSocket):
    """
    WebSocket endpoint for real-time streaming CAN bus intrusion detection.

    Protocol:
        1. Client connects to ws://host:port/ws/predict
        2. Client sends JSON frames: {"can_id": "0x250", "timestamp": 123456}
        3. Server maintains a sliding window buffer (64 frames)
        4. Once buffer is full, each new frame triggers inference
        5. Server responds with prediction: {"anomaly_score": 0.5, "is_attack": false, ...}

    The sliding window uses collections.deque with maxlen=64 for efficient
    FIFO behavior - oldest frame is automatically removed when a new one arrives.
    """
    await websocket.accept()

    # Create sliding window buffer for this connection
    # deque with maxlen=64 automatically removes oldest when full
    window_buffer: deque = deque(maxlen=WINDOW_SIZE)

    client_id = f"{websocket.client.host}:{websocket.client.port}" if websocket.client else "unknown"
    print(f"[WS] Client connected: {client_id}")

    # Send welcome message
    await websocket.send_json({
        "type": "connection",
        "status": "connected",
        "message": f"Connected to CAN Bus IDS. Send CAN frames to begin. Buffer needs {WINDOW_SIZE} frames.",
        "threshold": state.threshold,
        "window_size": WINDOW_SIZE
    })

    try:
        while True:
            # Receive incoming frame data
            data = await websocket.receive_json()

            try:
                # Parse and validate the incoming frame
                frame = CANFrame(**data)

                # Tokenize the CAN ID
                token = tokenize_can_id(frame.can_id)

                # Check if it's an unknown CAN ID
                is_unknown = (token == UNK_ID)

                # Add to sliding window buffer
                window_buffer.append(token)

                current_buffer_size = len(window_buffer)

                # Check if buffer is full (64 frames)
                if current_buffer_size < WINDOW_SIZE:
                    # Buffer not yet full - send status update
                    await websocket.send_json({
                        "type": "buffering",
                        "buffer_size": current_buffer_size,
                        "frames_needed": WINDOW_SIZE - current_buffer_size,
                        "can_id": frame.can_id,
                        "is_unknown_id": is_unknown,
                        "message": f"Buffering... {current_buffer_size}/{WINDOW_SIZE} frames"
                    })
                else:
                    # Buffer is full - perform inference
                    sequence = list(window_buffer)

                    # Calculate anomaly score
                    anomaly_score = calculate_anomaly_score(sequence)
                    is_attack = anomaly_score > state.threshold
                    confidence = calculate_confidence(anomaly_score, state.threshold)

                    # Create and send response
                    response = PredictionResponse(
                        anomaly_score=round(anomaly_score, 6),
                        is_attack=is_attack,
                        threshold=state.threshold,
                        buffer_size=current_buffer_size,
                        timestamp=datetime.now().isoformat(),
                        can_id=frame.can_id,
                        confidence=round(confidence, 4)
                    )

                    await websocket.send_json({
                        "type": "prediction",
                        **response.model_dump(),
                        "is_unknown_id": is_unknown
                    })

                    # Log attack detections
                    if is_attack:
                        print(f"[WS] ATTACK DETECTED! Score: {anomaly_score:.4f} | "
                              f"CAN ID: {frame.can_id} | Client: {client_id}")

            except ValueError as e:
                # Invalid frame format
                await websocket.send_json({
                    "type": "error",
                    "error": "Invalid frame format",
                    "details": str(e),
                    "expected_format": {
                        "can_id": "string (hex, e.g., '0x250' or '0250')",
                        "timestamp": "number (optional)",
                        "dlc": "number 0-8 (optional)",
                        "data": "array of hex strings (optional)"
                    }
                })

            except Exception as e:
                # Inference or other error
                await websocket.send_json({
                    "type": "error",
                    "error": "Processing error",
                    "details": str(e)
                })

    except WebSocketDisconnect:
        print(f"[WS] Client disconnected: {client_id}")

    except Exception as e:
        print(f"[WS] Error with client {client_id}: {e}")
        try:
            await websocket.close(code=1011, reason=str(e))
        except:
            pass


# ==============================================================================
# WEBSOCKET ENDPOINT FOR BATCH STREAMING
# ==============================================================================

@app.websocket("/ws/predict/batch")
async def websocket_predict_batch(websocket: WebSocket):
    """
    WebSocket endpoint for batch frame processing.

    Unlike the single-frame endpoint, this accepts arrays of frames
    and processes them in one go. Useful for replaying captured traffic.

    Protocol:
        1. Client sends: {"frames": [{"can_id": "0x250"}, {"can_id": "0x251"}, ...]}
        2. Server accumulates frames into sliding window
        3. Server responds with prediction for each complete window
    """
    await websocket.accept()

    window_buffer: deque = deque(maxlen=WINDOW_SIZE)
    client_id = f"{websocket.client.host}:{websocket.client.port}" if websocket.client else "unknown"

    print(f"[WS-Batch] Client connected: {client_id}")

    await websocket.send_json({
        "type": "connection",
        "status": "connected",
        "mode": "batch",
        "message": "Send batches of frames as arrays"
    })

    try:
        while True:
            data = await websocket.receive_json()

            frames = data.get("frames", [])
            if not frames:
                await websocket.send_json({
                    "type": "error",
                    "error": "No frames provided",
                    "expected_format": {"frames": [{"can_id": "0x250"}, ...]}
                })
                continue

            predictions = []

            for frame_data in frames:
                try:
                    frame = CANFrame(**frame_data)
                    token = tokenize_can_id(frame.can_id)
                    window_buffer.append(token)

                    if len(window_buffer) >= WINDOW_SIZE:
                        sequence = list(window_buffer)
                        anomaly_score = calculate_anomaly_score(sequence)
                        is_attack = anomaly_score > state.threshold

                        predictions.append({
                            "can_id": frame.can_id,
                            "anomaly_score": round(anomaly_score, 6),
                            "is_attack": is_attack
                        })

                except Exception as e:
                    predictions.append({
                        "can_id": frame_data.get("can_id", "unknown"),
                        "error": str(e)
                    })

            await websocket.send_json({
                "type": "batch_result",
                "num_frames_processed": len(frames),
                "num_predictions": len(predictions),
                "predictions": predictions,
                "timestamp": datetime.now().isoformat()
            })

    except WebSocketDisconnect:
        print(f"[WS-Batch] Client disconnected: {client_id}")
    except Exception as e:
        print(f"[WS-Batch] Error: {e}")


# ==============================================================================
# ERROR HANDLERS
# ==============================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled errors."""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc),
            "type": type(exc).__name__
        }
    )


# ==============================================================================
# MAIN ENTRY POINT
# ==============================================================================

if __name__ == "__main__":
    """
    Run the FastAPI server using Uvicorn.

    Usage:
        # Development mode (with auto-reload):
        uvicorn src.api:app --reload --host 0.0.0.0 --port 8000

        # Production mode:
        uvicorn src.api:app --host 0.0.0.0 --port 8000 --workers 4

        # Or run this script directly:
        python src/api.py

    API Endpoints:
        GET  /           - Root endpoint with API info
        GET  /health     - Health check endpoint
        GET  /docs       - Swagger UI documentation
        GET  /redoc      - ReDoc documentation
        GET  /threshold  - Get current threshold
        PUT  /threshold  - Update threshold
        POST /predict/batch - Batch prediction
        WS   /ws/predict - WebSocket for real-time streaming
        WS   /ws/predict/batch - WebSocket for batch streaming

    WebSocket Usage Example (Python):
        import asyncio
        import websockets
        import json

        async def test_websocket():
            uri = "ws://localhost:8000/ws/predict"
            async with websockets.connect(uri) as ws:
                # Send CAN frames
                for i in range(100):
                    frame = {"can_id": "0x0316", "timestamp": i}
                    await ws.send(json.dumps(frame))
                    response = await ws.recv()
                    print(json.loads(response))

        asyncio.run(test_websocket())

    WebSocket Usage Example (JavaScript):
        const ws = new WebSocket('ws://localhost:8000/ws/predict');

        ws.onopen = () => {
            console.log('Connected');
            ws.send(JSON.stringify({can_id: '0x0316', timestamp: Date.now()}));
        };

        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            console.log('Prediction:', data);
        };
    """
    print("\n" + "=" * 60)
    print("  CAN BUS INTRUSION DETECTION SYSTEM - API SERVER")
    print("=" * 60)
    print(f"\n  Device: {DEVICE}")
    print(f"  Window Size: {WINDOW_SIZE}")
    print(f"  Default Threshold: {DEFAULT_THRESHOLD}")
    print("\n  Starting Uvicorn server...")
    print("  Documentation: http://localhost:8000/docs")
    print("  Health Check:  http://localhost:8000/health")
    print("  WebSocket:     ws://localhost:8000/ws/predict")
    print("=" * 60 + "\n")

    uvicorn.run(
        "src.api:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  # Set to True for development
        log_level="info"
    )
