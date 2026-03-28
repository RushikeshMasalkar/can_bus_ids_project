<div align="center">

# 🚗 CAN Bus Intrusion Detection System

### *Transformer-Based Anomaly Detection & Attack Classification for In-Vehicle Networks*

> **"If a CAN bus speaks a language, a hacker speaks broken grammar."**  
> We teach a Transformer to learn that language — and catch every typo.

<br>

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.x-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white)](https://pytorch.org)
[![HuggingFace](https://img.shields.io/badge/HuggingFace-Transformers-FFD21E?style=for-the-badge&logo=huggingface&logoColor=black)](https://huggingface.co)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-ML-F7931E?style=for-the-badge&logo=scikitlearn&logoColor=white)](https://scikit-learn.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-Frontend-61DAFB?style=for-the-badge&logo=react&logoColor=0A192F)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-Typed-3178C6?style=for-the-badge&logo=typescript&logoColor=white)](https://typescriptlang.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-22c55e?style=for-the-badge)](LICENSE)

<br>

**[Overview](#-project-overview) · [Architecture](#-system-architecture--the-2-stage-pipeline) · [Tech Stack](#-tech-stack) · [Quickstart](#-quickstart) · [API Reference](#-api-reference) · [Evaluation](#-evaluation--metrics) · [Roadmap](#-roadmap)**

</div>

---

## 📌 Table of Contents

- [Why This Matters](#-why-this-matters)
- [Project Overview](#-project-overview)
- [System Architecture — The 2-Stage Pipeline](#-system-architecture--the-2-stage-pipeline)
  - [Stage 1: Anomaly Detection via Reconstruction Loss](#stage-1-anomaly-detection-via-reconstruction-loss)
  - [Stage 2: Multiclass Attack Classification](#stage-2-multiclass-attack-classification)
  - [Pipeline Diagram](#pipeline-diagram)
- [Tech Stack](#-tech-stack)
- [Repository Structure](#-repository-structure)
- [Data Pipeline](#-data-pipeline)
- [Model Pipeline](#-model-pipeline)
- [Evaluation & Metrics](#-evaluation--metrics)
- [Quickstart](#-quickstart)
- [Full Execution Workflow](#-full-execution-workflow)
- [API Reference](#-api-reference)
- [Frontend Dashboard](#-frontend-dashboard)
- [Configuration](#-configuration)
- [Artifacts & Outputs](#-artifacts--outputs)
- [Security & Responsible Use](#-security--responsible-use)
- [Troubleshooting](#-troubleshooting)
- [Roadmap](#-roadmap)
- [Contributing](#-contributing)
- [License](#-license)
- [Acknowledgments & Citation](#-acknowledgments--citation)

---

## ⚠️ Why This Matters

Modern vehicles are rolling networks. Every time you brake, accelerate, or turn the wheel, dozens of **Electronic Control Units (ECUs)** exchange thousands of messages per second over the **Controller Area Network (CAN) bus** — a protocol designed in 1986 that ships with:

- ❌ No message authentication
- ❌ No sender verification
- ❌ No encryption of any kind

A single compromised ECU, a malicious OBD-II dongle, or a rogue Bluetooth module gives an attacker **unrestricted write access** to safety-critical systems including brakes, steering, throttle, and transmission. High-profile demonstrations by Miller & Valasek (Jeep Cherokee, 2015) proved this is not theoretical — they remotely disabled brakes and took control of steering at highway speed.

**This project builds a production-grade, real-time IDS that requires zero labeled attack data during training** — learning only what "normal" looks like, and flagging everything that deviates. When an anomaly is confirmed, a second-stage classifier identifies the exact attack type with fine-grained accuracy.

---

## 🧠 Project Overview

This repository implements a **two-stage AI pipeline** for CAN bus intrusion detection:

| Stage | Task | Model | Trigger |
|:------|:-----|:------|:--------|
| **Stage 1** | Binary: Normal vs. Attack | DistilBERT (MLM, reconstruction loss) | Always runs on every window |
| **Stage 2** | Multiclass: Exact attack type | RandomForest + TF-IDF + numeric features | Only when Stage 1 flags ATTACK |

The system is served through a **FastAPI backend** with REST and WebSocket endpoints, and visualized in a **React + TypeScript SOC-style dashboard** with live stream monitoring, manual sequence analysis, and downloadable evaluation reports.

The entire approach is grounded in a linguistic analogy:

| NLP Concept | CAN Bus Equivalent |
|:------------|:-------------------|
| Word | CAN ID (hex → integer token) |
| Sentence | Sequence of CAN frames (window = 64) |
| Vocabulary | All unique CAN IDs observed in normal traffic |
| Grammar | Temporal ordering patterns of CAN IDs |
| Anomaly | Frame sequence that violates the learned grammar |

The model **never sees attack data during training**. It learns the statistical "language" of a healthy CAN bus through Masked Language Modeling. Attack frames — with injected, out-of-distribution IDs — produce high reconstruction loss because the model has never learned to predict them.

---

## 🏗 System Architecture — The 2-Stage Pipeline

### Stage 1: Anomaly Detection via Reconstruction Loss

DistilBERT is fine-tuned on **normal CAN traffic only** using a Masked Language Modeling objective — randomly masking 15% of CAN ID tokens in each window and training the model to predict them from context.

At inference time:
1. A sliding window (size = 64, stride = 1) segments incoming CAN traffic into overlapping sequences
2. Each sequence passes through the trained model
3. **Cross-entropy reconstruction loss** is computed per sequence
4. If `loss > threshold` (the 99th percentile of normal traffic losses, stored in `threshold.json`) → flagged as **ATTACK**

This approach is entirely **unsupervised with respect to attack types** — it is inherently robust to zero-day attack variants never seen during training.

### Stage 2: Multiclass Attack Classification

When Stage 1 confirms an anomaly, Stage 2 activates:

1. The flagged sequence is featurized using:
   - **TF-IDF** over the string representation of the CAN ID sequence
   - **Numeric statistical features** (mean, variance, entropy of token distribution, unique token count)
2. A **RandomForest classifier** predicts one of four attack types:

| Label | Attack Description |
|:------|:-------------------|
| `DoS` | High-priority frame flooding to starve legitimate messages off the bus |
| `Fuzzy` | Injection of random/spoofed CAN IDs and data payloads |
| `RPM` | Forging engine RPM sensor messages to manipulate driver perception |
| `Gear` | Forging transmission gear position messages |

Stage 2 **only triggers on confirmed anomalies** — keeping inference overhead negligible on normal traffic.

### Pipeline Diagram

```mermaid
flowchart TD
    A[🚗 Raw CAN Traffic\nCSV Files · OBD-II Port] --> B

    subgraph DATA["📦 Data Pipeline"]
        B[preprocess.py\nClean · Normalize · Tokenize]
        B --> C[dataset.py\nSliding Window size=64 stride=1]
        C --> D[(sequences.pt\nvocab.json)]
    end

    D --> E

    subgraph STAGE1["🔍 Stage 1 — Anomaly Detection"]
        E[DistilBERT MLM\nbest_model.pt]
        E --> F{Reconstruction Loss\nvs threshold.json}
    end

    F -- "loss ≤ threshold" --> G[✅ NORMAL\nNo further action]
    F -- "loss > threshold" --> H

    subgraph STAGE2["🚨 Stage 2 — Attack Classification"]
        H[Feature Extraction\nTF-IDF + Numeric Stats]
        H --> I[RandomForest Classifier\nmulticlass_model.pkl · vectorizer.pkl]
        I --> J[Attack Label\nDoS · Fuzzy · RPM · Gear]
    end

    G & J --> K

    subgraph SERVING["⚡ Runtime — FastAPI"]
        K[backend/main.py]
        K --> L[REST Endpoints\n/predict · /predict/batch · /stats · /threshold]
        K --> M[WebSocket\n/ws/live]
    end

    M --> N

    subgraph UI["🖥 React Dashboard"]
        N[useLiveStream.ts\nWebSocket Hook]
        N --> O[DashboardPage\nLive Anomaly Feed]
        N --> P[AnalyzePage\nManual Sequence Analysis]
        N --> Q[ReportsPage\nEvaluation Reports]
    end
```

---

## 🛠 Tech Stack

### 🤖 Machine Learning & Data Science

| Library | Version | Role |
|:--------|:--------|:-----|
| **PyTorch** | 2.x | Deep learning framework for Stage 1 training and inference |
| **Hugging Face Transformers** | latest | DistilBERT model, tokenizer, and MLM training utilities |
| **scikit-learn** | latest | Stage 2 RandomForest classifier, TF-IDF vectorizer, evaluation metrics |
| **pandas** | latest | Data loading, cleaning, and manipulation of raw CAN CSV datasets |
| **NumPy** | latest | Numerical operations, threshold computation, sequence statistics |
| **SciPy** | latest | Statistical analysis for threshold percentile calibration |
| **Matplotlib / Seaborn / Plotly** | latest | Loss distribution plots, confusion matrices, ROC curves |

### ⚙️ Backend

| Library | Role |
|:--------|:-----|
| **FastAPI** | High-performance async REST API framework |
| **WebSockets** | Real-time bidirectional streaming via `/ws/live` |
| **pydantic-settings** | Environment-driven path and config management in `config.py` |
| **uvicorn** | ASGI server for production-grade async execution |

### 🖥 Frontend

| Library | Role |
|:--------|:-----|
| **React 18** | Component-driven UI framework |
| **TypeScript** | Full static typing across all frontend source files |
| **Vite** | Fast build tooling and dev server (port 3000) |
| **Tailwind CSS** | Utility-first styling system |
| **Recharts** | Real-time anomaly score and confidence visualizations |
| **lucide-react** | Consistent icon system |

---

## 📁 Repository Structure

```
can_bus_ids_project/
│
├── 📂 backend/                        # FastAPI production backend
│   ├── main.py                        # App entrypoint — all route definitions
│   ├── config.py                      # Pydantic-settings path and env config
│   └── requirements.txt               # Backend-specific Python dependencies
│
├── 📂 src/                            # Core ML pipeline scripts
│   ├── preprocess.py                  # Data cleaning, normalization, tokenization
│   ├── dataset.py                     # Sliding window sequence builder
│   ├── inference.py                   # Stage 1 scoring — loss computation per window
│   ├── evaluate.py                    # End-to-end evaluation and report generation
│   ├── train_multiclass.py            # Stage 2 RandomForest training
│   └── multiclass_inference.py        # Stage 2 inference helper
│
├── 📂 frontend/                       # React + TypeScript SOC dashboard
│   ├── src/
│   │   ├── App.tsx                    # Root component and route definitions
│   │   ├── layout/
│   │   │   └── AppLayout.tsx          # Shell: sidebar, nav, layout grid
│   │   ├── pages/
│   │   │   ├── DashboardPage.tsx      # Live WebSocket anomaly feed and charts
│   │   │   ├── AnalyzePage.tsx        # Manual sequence submission and results
│   │   │   ├── ReportsPage.tsx        # Evaluation report browser
│   │   │   └── AboutPage.tsx          # Architecture and model documentation
│   │   ├── api/
│   │   │   └── client.ts              # Typed REST API client (all endpoints)
│   │   └── hooks/
│   │       └── useLiveStream.ts       # WebSocket lifecycle, reconnection, state
│   ├── vite.config.ts                 # Dev server on port 3000; API proxy config
│   └── package.json
│
├── 📂 data/                           # Datasets and processed artifacts (git-ignored)
│   ├── DoS_dataset.csv
│   ├── Fuzzy_dataset.csv
│   ├── gear_dataset.csv
│   ├── RPM_dataset.csv
│   ├── normal_traffic_augmented.csv   # Augmented training data (~56M rows)
│   ├── attack_traffic.csv             # Extracted attack frames
│   ├── vocab.json                     # CAN ID → token index mapping
│   └── sequences.pt                   # Windowed sequence tensors
│
├── 📂 models/                         # Trained model artifacts (git-ignored)
│   ├── best_model.pt                  # Stage 1 DistilBERT weights
│   ├── threshold.json                 # 99th-percentile anomaly decision boundary
│   ├── multiclass_model.pkl           # Stage 2 RandomForest classifier
│   └── vectorizer.pkl                 # Stage 2 TF-IDF vectorizer
│
├── 📂 reports/                        # Evaluation outputs and metrics
│   ├── evaluation_metrics.json        # Full pipeline evaluation results
│   └── multiclass_training_metrics.json  # Stage 2 per-class training performance
│
├── 📂 notebooks/
│   └── 01_data_exploration.ipynb      # EDA, augmentation, CAN ID visualizations
│
├── start_backend.bat                  # Windows one-click backend launcher
├── start_frontend.bat                 # Windows one-click frontend launcher
├── requirements.txt                   # Root Python dependencies
└── README.md
```

---

## 📊 Data Pipeline

The dataset is the **Car-Hacking Dataset** from Korea University's OCSLab, captured via OBD-II port from a real production vehicle under controlled attack injection conditions.

### Dataset Summary

| File | Contents | Approx. Rows |
|:-----|:---------|:-------------|
| `DoS_dataset.csv` | Normal + DoS attack frames | ~3.6M |
| `Fuzzy_dataset.csv` | Normal + Fuzzy injection frames | ~3.7M |
| `RPM_dataset.csv` | Normal + RPM spoofing frames | ~4.0M |
| `gear_dataset.csv` | Normal + Gear spoofing frames | ~4.0M |
| `normal_run_data.csv` | Clean baseline traffic only | ~3.0M |

**Total raw dataset size:** ~18.3M rows across five files.

### Column Schema

| Column | Type | Description |
|:-------|:-----|:------------|
| `Timestamp` | float64 | Seconds since capture start |
| `ID` | string (hex) | CAN identifier — e.g., `0x316`, `0x0A0` |
| `DLC` | int | Data Length Code (0–8 bytes) |
| `D0`–`D7` | string (hex) | Data payload bytes |
| `Flag` | char | `R` = normal/received, `T` = injected/attack |

### Processing Steps

```
Raw CSV Files (~18.3M rows)
         │
         ▼
[preprocess.py]
    ├── Strip whitespace, coerce types, drop malformed rows
    ├── Separate by Flag:
    │     Flag = R  →  normal traffic
    │     Flag = T  →  attack_traffic.csv
    └── Hex CAN IDs → integer tokens → vocab.json
         │
         ▼
[Augmentation — notebooks/01_data_exploration.ipynb]
    ├── 4-round chunk-based augmentation on normal traffic
    ├── Round 1: Original passthrough
    └── Rounds 2–4: Timestamp jitter + rare-ID upsampling + shuffle
              ~14M rows  →  ~56M augmented rows
         │
         ▼
[dataset.py]
    ├── Overlapping sliding window: size=64, stride=1
    ├── Each window → one MLM training input sequence
    └── Output: sequences.pt (torch TensorDataset)
```

---

## 🤖 Model Pipeline

### Stage 1 — DistilBERT MLM Training

**Architecture:** `distilbert-base-uncased` backbone with custom embedding layer sized to the CAN vocabulary (replacing the default 30,522-token WordPiece vocabulary).

**Training objective:** Masked Language Modeling — 15% of CAN ID tokens per sequence are randomly masked, and the model is trained to predict the correct token from surrounding context.

**Core insight:** By training exclusively on normal traffic, the model internalizes a probability distribution over expected CAN ID co-occurrence patterns. Attack frames inject anomalous IDs that violate these patterns, producing high reconstruction loss — making loss a reliable anomaly signal with no attack labels required.

**Training Hyperparameters:**

| Parameter | Value |
|:----------|:------|
| Architecture | DistilBERT (6 layers, 768 hidden dim, 12 attention heads) |
| Custom vocabulary | All unique CAN IDs extracted from training data |
| Window size | 64 tokens |
| Mask rate | 15% |
| Batch size | 64 |
| Learning rate | 2e-5 |
| Optimizer | AdamW |
| Loss function | Cross-entropy (masked positions only) |
| Threshold calibration | 99th percentile of normal traffic losses |
| Hardware | NVIDIA RTX 3050, CUDA 12.6 |

**Stage 1 Artifacts:**

| Artifact | Path | Purpose |
|:---------|:-----|:--------|
| Model weights | `models/best_model.pt` | Loaded at backend startup for all inference |
| Decision threshold | `models/threshold.json` | Anomaly boundary — sequences above this are flagged |
| Vocabulary | `data/vocab.json` | CAN ID → integer token index mapping |

### Stage 2 — RandomForest Multiclass Training

**Training command:**
```bash
python -m src.train_multiclass
```

**Feature engineering:**
- **TF-IDF representation** over the space-separated string of CAN ID tokens in each flagged sequence window
- **Numeric statistical features:** mean token index, variance, entropy of token distribution, unique token count, sequence length

**Label space:**

| Class | Description |
|:------|:------------|
| `DoS` | High-frequency flooding of dominant-priority frames |
| `Fuzzy` | Random CAN ID and payload injection |
| `RPM` | Engine speed spoofing |
| `Gear` | Transmission position spoofing |

**Stage 2 Artifacts:**

| Artifact | Path | Purpose |
|:---------|:-----|:--------|
| Classifier | `models/multiclass_model.pkl` | Loaded by backend; called only on flagged sequences |
| TF-IDF vectorizer | `models/vectorizer.pkl` | Text feature extractor — must match training version |
| Training metrics | `reports/multiclass_training_metrics.json` | Per-class precision, recall, F1, support |

---

## 📈 Evaluation & Metrics

Full evaluation is run by:

```bash
python src/evaluate.py
```

This evaluates both stages end-to-end on a held-out test set and writes structured results to `reports/`.

### Stage 1 — Binary Detection Metrics

| Metric | Description |
|:-------|:------------|
| **ROC-AUC** | Area under the Receiver Operating Characteristic curve |
| **Precision** | Fraction of sequences flagged as attack that are true attacks |
| **Recall** | Fraction of true attacks that were successfully detected |
| **F1 Score** | Harmonic mean of precision and recall |
| **False Positive Rate** | Fraction of normal sequences incorrectly flagged as attack |
| **Threshold sensitivity** | Performance sweep across the 95th, 97th, 99th, 99.5th percentile thresholds |

### Stage 2 — Multiclass Attack Classification Metrics

| Metric | Reporting Level |
|:-------|:----------------|
| **Precision** | Per-class (DoS, Fuzzy, RPM, Gear) + weighted average |
| **Recall** | Per-class + weighted average |
| **F1 Score** | Per-class + macro and weighted averages |
| **Confusion Matrix** | 4×4 matrix showing inter-class prediction errors |
| **Support** | Sample count per class in held-out test set |

### Evaluation Report Artifacts

| File | Location | Contents |
|:-----|:---------|:---------|
| `evaluation_metrics.json` | `reports/` | Full Stage 1 + Stage 2 numeric metrics |
| `multiclass_training_metrics.json` | `reports/` | Stage 2 per-class training performance |
| Loss distribution plot | `reports/` | Histogram comparing normal vs. attack reconstruction losses |
| ROC curve | `reports/` | Stage 1 binary detection performance curve |
| Confusion matrix | `reports/` | Stage 2 attack type prediction heatmap |

> All report assets are browsable in the **Reports page** of the React dashboard and served via `/static/reports/{filename}`.

---

## 🚀 Quickstart

> **Assumes trained artifacts already exist** in `models/` and `data/`. If starting from raw data, follow the [Full Execution Workflow](#-full-execution-workflow) first.

### Prerequisites

| Requirement | Version |
|:------------|:--------|
| Python | 3.10+ |
| Node.js | 18+ |
| npm | 9+ |
| NVIDIA GPU + CUDA | 12.x *(optional, for faster inference)* |

### 1. Clone the Repository

```bash
git clone https://github.com/<your-username>/can_bus_ids_project.git
cd can_bus_ids_project
```

### 2. Create and Activate Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / macOS
source venv/bin/activate
```

### 3. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 4. Install PyTorch — Match Your Hardware

> **Do not install PyTorch via `requirements.txt`** — always install manually to match your CUDA version.

```bash
# CUDA 12.6 (RTX 30/40 series, recommended)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu126

# CPU only
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
```

Verify your installation:
```bash
python -c "import torch; print(torch.__version__, torch.cuda.is_available())"
```

### 5. Install Frontend Dependencies

```bash
cd frontend
npm install
cd ..
```

### 6. Start Backend

```bash
# From project root
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

**Windows shortcut:**
```bat
start_backend.bat
```

### 7. Start Frontend

```bash
cd frontend
npm run dev
```

**Windows shortcut:**
```bat
start_frontend.bat
```

### 8. Open the Dashboard

**http://localhost:3000**

### 9. Validate Backend Health

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "ok",
  "model_loaded": true,
  "stage2_loaded": true
}
```

---

## 🔁 Full Execution Workflow

Run these steps **in order** when starting from raw data with no pre-trained artifacts.

### Step 1 — Download the Dataset

Download the [Car-Hacking Dataset](https://ocslab.hksecurity.net/Datasets/car-hacking-dataset) and place all files in `data/`:

```
data/
├── DoS_dataset.csv
├── Fuzzy_dataset.csv
├── gear_dataset.csv
├── RPM_dataset.csv
└── normal_run_data.csv
```

### Step 2 — Data Exploration and Augmentation

Open and run all cells in `notebooks/01_data_exploration.ipynb`.

**Outputs:**
- `data/normal_traffic_augmented.csv` (~56M rows)
- `data/attack_traffic.csv`

### Step 3 — Preprocessing and Sequence Construction

```bash
python src/preprocess.py
python src/dataset.py
```

**Outputs:**
- `data/vocab.json`
- `data/sequences.pt`

### Step 4 — Stage 1 Training (DistilBERT MLM)

> Training is GPU-intensive. On an NVIDIA RTX 3050 with batch size 64, expect several hours per full epoch on the augmented dataset. Use the GPU training machine for this step; transfer `sequences.pt` and `vocab.json` before training and transfer back `best_model.pt` and `threshold.json` afterward.

**Outputs:**
- `models/best_model.pt`
- `models/threshold.json`

### Step 5 — Stage 2 Training (Multiclass RandomForest)

```bash
python -m src.train_multiclass
```

**Outputs:**
- `models/multiclass_model.pkl`
- `models/vectorizer.pkl`
- `reports/multiclass_training_metrics.json`

### Step 6 — Evaluation and Report Generation

```bash
python src/evaluate.py
```

**Outputs:**
- `reports/evaluation_metrics.json`
- Loss distribution plots, ROC curve, confusion matrix in `reports/`

### Step 7 — Start Backend and Frontend

```bash
# Terminal 1
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000

# Terminal 2
cd frontend && npm run dev
```

---

## 📡 API Reference

All endpoints are defined in [`backend/main.py`](backend/main.py). Base URL: `http://localhost:8000`

### REST Endpoints

| Method | Path | Purpose | Request | Response |
|:-------|:-----|:--------|:--------|:---------|
| `GET` | `/` | Root — project info and version | — | `{name, version, description}` |
| `GET` | `/health` | Liveness + artifact load status | — | `{status, model_loaded, stage2_loaded}` |
| `GET` | `/stats` | Detection counters since last backend start | — | `{total, attacks, normals, attack_types}` |
| `GET` | `/threshold` | Current Stage 1 decision boundary | — | `{threshold: float}` |
| `GET` | `/vocab/size` | Tokenizer vocabulary size | — | `{vocab_size: int}` |
| `POST` | `/predict` | Single sequence inference | `{"sequence": [int, ...]}` | See schema below |
| `POST` | `/predict/batch` | Batch sequence inference | `{"sequences": [[int,...], ...]}` | `{results: [...]}` |
| `GET` | `/reports/manifest` | List all available report assets | — | `{reports: [filename, ...]}` |
| `GET` | `/static/reports/{filename}` | Serve a report asset (PNG, JSON, HTML) | — | File response |

**`/predict` response schema:**

```json
{
  "score": 0.843,
  "is_attack": true,
  "label": "ATTACK",
  "attack_type": "DoS",
  "confidence": 0.91,
  "threshold": 0.612,
  "timestamp": "2025-01-15T10:23:41.003Z"
}
```

### WebSocket — `/ws/live`

Connect to `ws://localhost:8000/ws/live` for a continuous real-time inference event stream.

**Event payload fields:**

| Field | Type | Description |
|:------|:-----|:------------|
| `score` | `float` | Stage 1 reconstruction loss for this window |
| `is_attack` | `bool` | `true` if `score > threshold` |
| `label` | `string` | `"NORMAL"` or `"ATTACK"` |
| `attack_type` | `string \| null` | Stage 2 class label if attack; `null` if normal |
| `confidence` | `float \| null` | Stage 2 class probability if attack; `null` if normal |
| `threshold` | `float` | Decision threshold active at time of event |
| `timestamp` | `string` | ISO 8601 UTC timestamp |

**Example client connection (JavaScript):**

```javascript
const ws = new WebSocket("ws://localhost:8000/ws/live");

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.is_attack) {
    console.warn(`🚨 ATTACK: ${data.attack_type} — confidence ${data.confidence}`);
  }
};

ws.onerror = (err) => console.error("WebSocket error:", err);
ws.onclose = () => console.log("Stream closed");
```

---

## 🖥 Frontend Dashboard

The React dashboard is a single-page application with four views, all driven by the API client in `api/client.ts` and the live WebSocket hook in `hooks/useLiveStream.ts`.

| Page | File | Purpose |
|:-----|:-----|:--------|
| **Dashboard** | `DashboardPage.tsx` | Live anomaly event feed, real-time score chart, attack type distribution, session statistics |
| **Analyze** | `AnalyzePage.tsx` | Manual sequence submission to `/predict`, full result breakdown with Stage 1 loss and Stage 2 label |
| **Reports** | `ReportsPage.tsx` | Browse and view evaluation report assets from `/reports/manifest` |
| **About** | `AboutPage.tsx` | System architecture documentation and model methodology |

**Key frontend implementation modules:**

| File | Purpose |
|:-----|:--------|
| `api/client.ts` | Fully typed Fetch/Axios wrapper for every REST endpoint |
| `hooks/useLiveStream.ts` | Manages WebSocket connection lifecycle, automatic reconnection, and event state |
| `layout/AppLayout.tsx` | Sidebar navigation, header, responsive layout grid |
| `vite.config.ts` | Dev server on port 3000; reverse proxy to `localhost:8000` for API calls |

---

## ⚙️ Configuration

All runtime paths and environment settings are managed through [`backend/config.py`](backend/config.py) using `pydantic-settings`. Values are read from environment variables at startup with safe defaults pointing to standard project paths.

### Environment Variables

| Variable | Default | Description |
|:---------|:--------|:------------|
| `MODEL_PATH` | `models/best_model.pt` | Stage 1 DistilBERT checkpoint |
| `THRESHOLD_PATH` | `models/threshold.json` | Anomaly decision boundary |
| `VOCAB_PATH` | `data/vocab.json` | CAN ID tokenizer vocabulary |
| `MULTICLASS_MODEL_PATH` | `models/multiclass_model.pkl` | Stage 2 RandomForest classifier |
| `VECTORIZER_PATH` | `models/vectorizer.pkl` | Stage 2 TF-IDF vectorizer |
| `REPORTS_DIR` | `reports/` | Directory for evaluation report assets |
| `HOST` | `0.0.0.0` | Backend bind address |
| `PORT` | `8000` | Backend listen port |

**Override defaults by creating a `.env` file in the project root:**

```env
MODEL_PATH=models/best_model.pt
THRESHOLD_PATH=models/threshold.json
VOCAB_PATH=data/vocab.json
MULTICLASS_MODEL_PATH=models/multiclass_model.pkl
VECTORIZER_PATH=models/vectorizer.pkl
REPORTS_DIR=reports/
```

---

## 📦 Artifacts & Outputs

| Artifact | Path | Generated By | Consumed By | Purpose |
|:---------|:-----|:------------|:------------|:--------|
| CAN vocabulary | `data/vocab.json` | `preprocess.py` | `dataset.py`, backend | Hex CAN ID → integer token index |
| Sequence tensors | `data/sequences.pt` | `dataset.py` | Stage 1 training, `inference.py` | Windowed input sequences for training |
| Stage 1 weights | `models/best_model.pt` | Stage 1 training | `inference.py`, backend | Trained DistilBERT model state dict |
| Anomaly threshold | `models/threshold.json` | Stage 1 training | `inference.py`, backend | 99th-percentile loss decision boundary |
| Stage 2 classifier | `models/multiclass_model.pkl` | `train_multiclass.py` | `multiclass_inference.py`, backend | Trained RandomForest model |
| TF-IDF vectorizer | `models/vectorizer.pkl` | `train_multiclass.py` | `multiclass_inference.py`, backend | Text feature extractor for Stage 2 input |
| Eval metrics | `reports/evaluation_metrics.json` | `evaluate.py` | Backend `/reports`, frontend Reports page | Full pipeline evaluation results |
| Training metrics | `reports/multiclass_training_metrics.json` | `train_multiclass.py` | Frontend Reports page | Stage 2 per-class training performance |

---

## 🔐 Security & Responsible Use

> **This project is released strictly for academic research and automotive cybersecurity education.**

### Responsible Use Policy

- Do **not** deploy against live vehicle networks without explicit written authorization from the vehicle owner and relevant authorities
- Do **not** use this codebase to develop or enhance offensive automotive attack tools
- All datasets used were captured in **controlled laboratory environments** under institutional oversight — not from public roads or production vehicles in service

### Data Handling

- Raw CAN CSV files may contain temporal patterns that encode vehicle-specific ECU configuration — do not commit them to public repositories
- `data/` and `models/` are `.gitignore`d by default — verify this before any public push
- If sharing `vocab.json`, be aware it encodes information about the specific vehicle's ECU identifier space

### Production Hardening Checklist

Before deploying in any research or operational environment:

- [ ] Run the backend behind a reverse proxy (nginx, Caddy) with TLS termination
- [ ] Replace the default CORS wildcard (`*`) in `main.py` with explicit allowed origins
- [ ] Restrict WebSocket and API access to trusted internal network segments or VPN
- [ ] Add rate limiting to `/predict` and `/predict/batch` endpoints
- [ ] Externalize all secrets and paths via environment variables — never hardcode
- [ ] Enable structured logging with request/response audit trails
- [ ] Configure health check monitoring with automatic restart (systemd unit, Docker healthcheck)
- [ ] Disable debug mode and auto-reload in production uvicorn invocation

---

## 🔧 Troubleshooting

| Symptom | Likely Cause | Fix |
|:--------|:-------------|:----|
| Backend fails on startup — `FileNotFoundError` | `best_model.pt` or `threshold.json` missing | Verify `models/` contents; check `.env` overrides; run training pipeline if artifacts don't exist |
| `/health` returns `model_loaded: false` | Model file exists but failed to load — PyTorch or CUDA version mismatch | Align PyTorch version with training environment; try `map_location='cpu'` in load call |
| WebSocket disconnects immediately on connect | CORS policy blocking the frontend origin | Add `http://localhost:3000` to allowed origins list in `main.py` |
| Stage 2 returns `null` attack type on all anomalies | `multiclass_model.pkl` or `vectorizer.pkl` missing | Run `python -m src.train_multiclass` to generate Stage 2 artifacts |
| Frontend shows "Cannot connect to API" | Backend not running or wrong base URL in `client.ts` | Confirm backend is on port 8000; verify `vite.config.ts` proxy target |
| Port 8000 already in use | Another process holds the port | Pass `--port 8001` to uvicorn; update `client.ts` base URL and Vite proxy accordingly |
| CUDA out-of-memory during Stage 1 training | Batch size too large for available GPU VRAM | Reduce batch size; enable gradient accumulation steps |
| scikit-learn `InconsistentVersionWarning` on Stage 2 load | Version mismatch between training and inference environment | Pin scikit-learn version in `requirements.txt`; retrain Stage 2 if necessary |
| Sequences load slowly / OOM during dataset construction | `sequences.pt` too large for available RAM | Reduce sliding window stride; use chunked loading in `dataset.py` |

---

## 🗺 Roadmap

| Priority | Item | Status |
|:---------|:-----|:-------|
| 🔴 High | Finalize and document Stage 1 training script in `src/` with CLI args | In progress |
| 🔴 High | End-to-end integration tests for all backend REST endpoints | Planned |
| 🔴 High | Docker Compose setup for single-command deployment | Planned |
| 🟡 Medium | ONNX export of Stage 1 for edge deployment (Jetson Nano, Raspberry Pi 5) | Planned |
| 🟡 Medium | Online threshold recalibration from accumulated live traffic statistics | Planned |
| 🟡 Medium | CI/CD pipeline with automated model evaluation on PR | Planned |
| 🟢 Low | CAN FD protocol support — extend tokenizer for 64-byte payloads | Future |
| 🟢 Low | Ensemble Stage 1 with LSTM or Autoencoder for hybrid detection | Future |
| 🟢 Low | Live OBD-II capture integration via `python-can` / `SocketCAN` | Future |
| 🟢 Low | Multi-vehicle vocabulary transfer learning and domain adaptation | Future |

---

## 🤝 Contributing

Contributions are welcome from researchers, students, and automotive security practitioners.

### How to Contribute

**1. Fork and branch:**
```bash
git fork https://github.com/<your-username>/can_bus_ids_project.git
git checkout -b feat/your-feature-name
```

**2. Implement with tests** — any change to `src/` or `backend/` should include or update corresponding tests.

**3. Code standards:**
- **Python:** Follow PEP 8; use type hints throughout `src/` and `backend/`
- **TypeScript:** Maintain strict typing; avoid `any` unless unavoidable with a comment justifying it
- **Commits:** Use conventional commit format — `feat:`, `fix:`, `docs:`, `refactor:`, `test:`

**4. Open a Pull Request** with:
- A concise description of what changed and why
- Links to any relevant issues
- Updated documentation if any endpoint, artifact path, or config variable changed

### Priority Areas

The following areas would have the most impact:

- Training script documentation, CLI argument support, and config externalization
- Docker and containerization for reproducible deployment
- Additional evaluation visualizations and interactive report components
- CAN FD protocol extension and broader dataset support

---

## 📄 License

This project is licensed under the **MIT License** — see [`LICENSE`](LICENSE) for full terms.

---

## 📚 Acknowledgments & Citation

### Dataset

**Car-Hacking Dataset** — Provided by the OCSLab, School of Cybersecurity, Korea University.  
Captured via OBD-II port from a real vehicle under laboratory-controlled attack injection conditions.

🔗 [https://ocslab.hksecurity.net/Datasets/car-hacking-dataset](https://ocslab.hksecurity.net/Datasets/car-hacking-dataset)

### Citation

If you use this repository or the Car-Hacking dataset in your research, please cite:

```bibtex
@article{song2020vehicle,
  title     = {In-Vehicle Network Intrusion Detection Using Deep Convolutional Neural Network},
  author    = {Song, Hyun Min and Kim, Ha Rang and Kim, Huy Kang},
  journal   = {Vehicular Communications},
  volume    = {21},
  pages     = {100198},
  year      = {2020},
  publisher = {Elsevier},
  doi       = {10.1016/j.vehcom.2019.100198}
}
```

### Related Literature

| Reference | Relevance |
|:----------|:----------|
| Miller & Valasek (2015). *Remote Exploitation of an Unaltered Passenger Vehicle.* DEF CON 23. | Foundational motivation for CAN bus IDS research |
| Kang & Kang (2016). *Intrusion Detection System Using Deep Neural Network for In-Vehicle Network Security.* PLOS ONE. | Early deep learning approach to CAN IDS |
| Vaswani et al. (2017). *Attention Is All You Need.* NeurIPS. | Transformer architecture underpinning Stage 1 |
| Sanh et al. (2019). *DistilBERT, a distilled version of BERT.* arXiv:1910.01108. | Stage 1 base model |
| Devlin et al. (2018). *BERT: Pre-training of Deep Bidirectional Transformers.* arXiv:1810.04805. | MLM pre-training methodology |

---

<div align="center">

**Built for automotive cybersecurity research.**

*If this project helped your work, consider leaving a ⭐ on GitHub.*

</div>