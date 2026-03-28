<p align="center">
  <h1 align="center">Transformer-Based Intrusion Detection System (IDS)<br>for CAN Bus Networks</h1>
  <p align="center">
    <em>Teaching AI the "Language of Cars" — detecting cyber attacks by learning the grammar of normal vehicle communication.</em>
  </p>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/PyTorch-2.x-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white" />
  <img src="https://img.shields.io/badge/HuggingFace-Transformers-FFD21E?style=for-the-badge&logo=huggingface&logoColor=black" />
  <img src="https://img.shields.io/badge/FastAPI-Backend-009688?style=for-the-badge&logo=fastapi&logoColor=white" />
  <img src="https://img.shields.io/badge/React-Frontend-61DAFB?style=for-the-badge&logo=react&logoColor=0A192F" />
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" />
</p>

---

## Table of Contents

- [Project Overview](#project-overview)
- [Core Concept — The Language of Cars](#core-concept--the-language-of-cars)
- [Tech Stack](#tech-stack)
- [Hardware Workflow](#hardware-workflow)
- [Directory Structure](#directory-structure)
- [Setup Instructions](#setup-instructions)
- [Execution Guide (Phase-by-Phase)](#execution-guide-phase-by-phase)
- [Future Scope](#future-scope)
- [License](#license)

---

## Project Overview

Modern vehicles rely on the **Controller Area Network (CAN) bus** protocol for internal communication between Electronic Control Units (ECUs) — steering, brakes, engine, transmission, and more. However, CAN was designed in the 1980s and **lacks authentication, encryption, or any form of sender verification**. This makes it highly vulnerable to cyber attacks.

This project builds an **AI-powered Intrusion Detection System** that detects three categories of CAN bus attacks:

| Attack Type | Description |
|:---|:---|
| **DoS (Denial of Service)** | Flooding the bus with high-priority frames to starve legitimate messages |
| **Fuzzy Attack** | Injecting random/spoofed CAN IDs and data payloads |
| **Spoofing (RPM/Gear)** | Forging specific ECU messages to manipulate vehicle behavior |

We use the **Car-Hacking Dataset** containing ~14 million normal frames and ~4.6 million attack frames captured from a real vehicle's OBD-II port.

---

## Core Concept — The Language of Cars

> **"If a CAN bus speaks a language, a hacker speaks broken grammar."**

We treat the CAN bus as a **natural language problem**:

| NLP Analogy | CAN Bus Equivalent |
|:---|:---|
| Word | CAN ID (hex → integer token) |
| Sentence | Sequence of CAN frames in a time window |
| Vocabulary | Set of all unique CAN IDs observed in normal traffic |
| Grammar | Temporal patterns and ordering rules of CAN IDs |
| Typo / Anomaly | Injected/spoofed frame that breaks the learned pattern |

### How It Works

```
Normal CAN Traffic → Hex IDs → Integer Tokens → Sequences (window=64)
                                                        |
                                              DistilBERT (MLM Training)
                                              Learns "baseline grammar"
                                                        |
                                              New Traffic → Reconstruct
                                                        |
                                              High Loss? → ANOMALY
```

1. **Tokenization** — Convert hex CAN IDs (`0x0A0`, `0x316`, ...) to integer tokens and build a vocabulary
2. **Sequence Construction** — Use an overlapping sliding window (size 64, stride 1) to create input sequences
3. **Pre-training** — Train a **DistilBERT** model using **Masked Language Modeling (MLM)** with a 15% mask rate on **normal traffic only**
4. **Inference** — Feed new traffic through the model and compute the **Cross-Entropy Reconstruction Loss**
5. **Detection** — If the loss exceeds the **99th-percentile threshold** of normal traffic losses → flag as **anomaly**

---

## Tech Stack

| Category | Tools |
|:---|:---|
| **Language** | Python 3.10+ |
| **Deep Learning** | PyTorch, HuggingFace Transformers, DistilBERT |
| **Data Science** | Pandas, NumPy, Scikit-learn, SciPy |
| **Visualization** | Matplotlib, Seaborn, Plotly |
| **Application Layer** | FastAPI backend + React frontend (Vite) |
| **Notebook** | JupyterLab |
| **Dataset** | [Car-Hacking Dataset](https://ocslab.hksecurity.net/Datasets/car-hacking-dataset) |

---

## Hardware Workflow

This project uses a **dual-machine workflow** to balance development speed with training power:

```
+------------------------------+      +------------------------------+
|   Development Machine        |      |   Training Machine           |
|   Intel Core Ultra 5         |      |   Lenovo LOQ                 |
|                              | ---> |   NVIDIA RTX 3050 GPU        |
|   - Data exploration         |      |   PyTorch CUDA (cu126)       |
|   - Preprocessing            |      |                              |
|   - Tokenization             |      |   - MLM Training (Batch 64)  |
|   - Backend/frontend dev     |      |   - LR: 2e-5                 |
|   - Inference testing        |      |   - Full epoch training      |
+------------------------------+      +------------------------------+
```

---

## Directory Structure

```
can_bus_ids_project/
|
+-- README.md                  <- You are here
+-- requirements.txt           <- Clean direct dependencies
+-- .gitignore                 <- Root ignore rules
|
+-- data/                      <- Datasets (git-ignored, download separately)
|   +-- DoS_dataset.csv
|   +-- Fuzzy_dataset.csv
|   +-- RPM_dataset.csv
|   +-- gear_dataset.csv
|   +-- normal_run_data.csv
|   +-- normal_traffic.csv     <- Extracted normal frames
|   +-- normal_traffic_augmented.csv  <- Augmented training data
|   +-- attack_traffic.csv     <- Extracted attack frames
|   +-- .gitignore
|
+-- notebooks/                 <- Jupyter notebooks (step-by-step)
|   +-- 01_data_exploration.ipynb  <- EDA, cleaning, augmentation
|   +-- .gitignore
|
+-- src/                       <- Python source modules
|   +-- .gitignore
|
+-- backend/                   <- Production FastAPI backend
|   +-- main.py
|   +-- config.py
|   +-- requirements.txt
|
+-- frontend/                  <- React + TypeScript web client
|   +-- src/
|   +-- package.json
|
+-- models/                    <- Trained model weights (git-ignored)
|   +-- .gitignore
|
+-- venv/                      <- Virtual environment (git-ignored)
```

---

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/<your-username>/can_bus_ids_project.git
cd can_bus_ids_project
```

### 2. Create a Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / macOS
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Install PyTorch (GPU)

> **Note:** Do NOT rely on `requirements.txt` for PyTorch — install it manually to match your hardware.

Visit [https://pytorch.org/get-started/locally/](https://pytorch.org/get-started/locally/) and select your config.

Example for **CUDA 12.6**:

```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu126
```

Example for **CPU only**:

```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
```

### 5. Download the Dataset

Download the **Car-Hacking Dataset** and place the CSV files in the `data/` folder:

```
data/
+-- DoS_dataset.csv
+-- Fuzzy_dataset.csv
+-- RPM_dataset.csv
+-- gear_dataset.csv
+-- normal_run_data.csv
```

---

## Execution Guide (Phase-by-Phase)

### Phase 1 — Data Exploration & Preprocessing

> `notebooks/01_data_exploration.ipynb`

- Load all raw CSV files (~18.6M rows across 5 files)
- Inspect columns: `Timestamp`, `ID`, `DLC`, `D0–D7`, `Flag`
- Clean data: strip whitespace, handle missing values, coerce types
- Separate **normal traffic** (`Flag = R`) and **attack traffic** (`Flag = T`)
- Visualize label distribution and top CAN ID frequencies
- Export: `normal_traffic.csv`, `attack_traffic.csv`

### Phase 2 — Data Augmentation

> `notebooks/01_data_exploration.ipynb` (cells 8–9)

- Apply **4-round chunk-based augmentation** on normal traffic:
  - Round 1: Original data pass-through
  - Rounds 2–4: Timestamp noise injection + rare ID upsampling + shuffle
- Result: ~14M → ~56M+ augmented rows for robust training
- Export: `normal_traffic_augmented.csv`

### Phase 3 — Tokenization & Sequence Building

- Convert hex CAN IDs to integer tokens
- Build a CAN ID vocabulary mapping
- Apply **Overlapping Sliding Window** (window size = 64, stride = 1)
- Generate MLM-ready input sequences

### Phase 4 — MLM Training (DistilBERT)

- Model: `distilbert-base-uncased` (custom vocab)
- Task: **Masked Language Modeling** — randomly mask 15% of tokens, predict them
- Train on **normal traffic only** — the model learns what "normal" looks like
- Hyperparameters:

| Parameter | Value |
|:---|:---|
| Batch Size | 64 |
| Learning Rate | 2e-5 |
| Mask Rate | 15% |
| Optimizer | AdamW |
| Hardware | NVIDIA RTX 3050 (CUDA 12.6) |

### Phase 5 — Anomaly Detection (Inference)

- Feed normal + attack sequences through the trained model
- Compute **Cross-Entropy Reconstruction Loss** per sequence
- Calculate the **99th-percentile threshold** from normal traffic losses
- Sequences with loss > threshold → flagged as **anomalies**

### Phase 6 — Production Runtime (FastAPI + React)

- Backend API is served from `backend/main.py`
- Frontend UI is the React app in `frontend/`

```bash
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

```bash
cd frontend
npm install
npm run dev
```

---

## Future Scope

| Area | Plan |
|:---|:---|
| **Multi-attack classification** | Extend from binary (normal/attack) to multi-class (DoS, Fuzzy, Spoofing) |
| **Real-time edge deployment** | Optimize model with ONNX/TensorRT for Raspberry Pi or NVIDIA Jetson |
| **Online learning** | Continuously retrain on new CAN traffic patterns without full retraining |
| **CAN FD support** | Adapt tokenization for CAN FD frames (64-byte payloads) |
| **Ensemble models** | Combine Transformer with Autoencoder or LSTM for hybrid detection |
| **OBD-II live capture** | Integrate with real-time CAN sniffing tools (python-can, SocketCAN) |

---

## License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

<p align="center">
  <em>Built for automotive cybersecurity research</em>
</p>
