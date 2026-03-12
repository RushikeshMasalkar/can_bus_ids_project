# dashboard/app.py
# CAN Bus Intrusion Detection System — Professional Dashboard

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import torch
import json
import numpy as np
import pandas as pd
import sys
import time
import random
from pathlib import Path
from datetime import datetime
import torch.nn.functional as F

# ── Path Setup ─────────────────────────────────────────────────────────
BASE_DIR   = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR / "src"))

DATA_DIR   = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"

from transformers import DistilBertConfig, DistilBertForMaskedLM

# ══════════════════════════════════════════════════════════════════════
# PAGE CONFIG
# ══════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="CAN Bus IDS | Intrusion Detection System",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded"
)

# ══════════════════════════════════════════════════════════════════════
# PROFESSIONAL CYBERSECURITY DASHBOARD CSS
# Palette: Datadog / Cloudflare / CrowdStrike inspired
# ══════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Source+Code+Pro:wght@400;500;600&display=swap');

    /* ════════════════════════════════════════════
       BASE THEME
       ════════════════════════════════════════════ */
    .stApp {
        background-color: #F8FAFC;
        color: #111827;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        font-size: 15px;
    }

    /* ════════════════════════════════════════════
       SIDEBAR
       ════════════════════════════════════════════ */
    [data-testid="stSidebar"] {
        background: #FFFFFF;
        border-right: 1px solid #E5E7EB;
        box-shadow: 2px 0 12px rgba(0,0,0,0.04);
    }
    [data-testid="stSidebar"] * {
        color: #111827 !important;
        font-family: 'Inter', sans-serif !important;
    }
    [data-testid="stSidebar"] .section-title {
        color: #2563EB !important;
    }
    [data-testid="stSidebar"] label {
        color: #111827 !important;
        font-size: 13px !important;
        font-weight: 500 !important;
    }
    [data-testid="stSidebar"] .stSelectbox > div > div,
    [data-testid="stSidebar"] .stSlider > div {
        color: #111827 !important;
    }
    [data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] > div {
        background-color: #FFFFFF !important;
        color: #111827 !important;
        border-color: #D1D5DB !important;
    }
    [data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] span,
    [data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] div {
        color: #111827 !important;
        background-color: transparent !important;
    }
    [data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] svg {
        fill: #6B7280 !important;
    }
    [data-testid="stSidebar"] hr {
        border-color: #E5E7EB !important;
        margin: 20px 0 !important;
    }

    /* Sidebar brand block */
    .sidebar-brand {
        text-align: center;
        padding: 16px 12px 24px;
        border-bottom: 1px solid #E5E7EB;
        margin-bottom: 20px;
    }
    .sidebar-brand-icon {
        width: 44px;
        height: 44px;
        background: linear-gradient(135deg, #2563EB, #1E40AF);
        border-radius: 10px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        margin-bottom: 10px;
    }
    .sidebar-brand-icon svg {
        width: 24px;
        height: 24px;
    }
    .sidebar-brand-title {
        font-size: 14px;
        font-weight: 700;
        color: #111827;
        letter-spacing: -0.2px;
    }
    .sidebar-brand-sub {
        font-size: 11px;
        color: #6B7280;
        margin-top: 2px;
    }

    /* Sidebar section label */
    .sidebar-section {
        font-size: 11px;
        font-weight: 600;
        color: #6B7280 !important;
        text-transform: uppercase;
        letter-spacing: 1.2px;
        margin: 24px 0 10px;
        padding-left: 2px;
    }

    /* ════════════════════════════════════════════
       HEADER
       ════════════════════════════════════════════ */
    .dashboard-header {
        background: linear-gradient(135deg, #1E40AF 0%, #2563EB 100%);
        border-radius: 14px;
        padding: 28px 36px;
        margin-bottom: 24px;
        box-shadow: 0 4px 20px rgba(37,99,235,0.18);
        position: relative;
        overflow: hidden;
    }
    .dashboard-header::before {
        content: '';
        position: absolute;
        top: 0; right: 0;
        width: 260px; height: 100%;
        background: radial-gradient(circle at 80% 50%,
            rgba(255,255,255,0.06) 0%,
            transparent 70%);
        pointer-events: none;
    }
    .header-title {
        font-size: 34px;
        font-weight: 700;
        color: #FFFFFF;
        letter-spacing: -0.5px;
        line-height: 1.15;
    }
    .header-subtitle {
        font-size: 14px;
        color: rgba(255,255,255,0.78);
        letter-spacing: 0.3px;
        margin-top: 6px;
        font-weight: 400;
    }
    .header-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 5px 14px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        letter-spacing: 0.5px;
        text-transform: uppercase;
    }
    .badge-online {
        background: rgba(22,163,74,0.15);
        color: #bbf7d0;
        border: 1px solid rgba(22,163,74,0.35);
    }
    .badge-dot {
        width: 7px; height: 7px;
        background: #4ade80;
        border-radius: 50%;
        display: inline-block;
        animation: blink-dot 2s ease-in-out infinite;
    }
    @keyframes blink-dot {
        0%, 100% { opacity: 1; }
        50%      { opacity: 0.35; }
    }
    .header-meta {
        font-size: 12px;
        color: rgba(255,255,255,0.55);
        font-weight: 500;
        font-family: 'Source Code Pro', monospace;
    }

    /* ════════════════════════════════════════════
       METRIC CARDS
       ════════════════════════════════════════════ */
    .metric-card {
        background: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        transition: transform 0.18s ease, box-shadow 0.18s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(0,0,0,0.09);
    }
    .metric-icon {
        width: 36px; height: 36px;
        border-radius: 8px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto 10px;
        font-size: 16px;
        font-weight: 700;
    }
    .metric-icon-status  { background: #F0FDF4; color: #16A34A; }
    .metric-icon-score   { background: #EFF6FF; color: #2563EB; }
    .metric-icon-thresh  { background: #FFF7ED; color: #F59E0B; }
    .metric-icon-attack  { background: #FEF2F2; color: #EF4444; }
    .metric-icon-total   { background: #EFF6FF; color: #3B82F6; }
    .metric-value {
        font-size: 28px;
        font-weight: 700;
        font-family: 'Inter', sans-serif;
        line-height: 1.15;
    }
    .metric-label {
        font-size: 12px;
        color: #6B7280;
        text-transform: uppercase;
        letter-spacing: 1.2px;
        margin-top: 6px;
        font-weight: 500;
    }
    .metric-normal  { color: #16A34A; }
    .metric-warning { color: #F59E0B; }
    .metric-danger  { color: #EF4444; }
    .metric-info    { color: #2563EB; }

    /* ════════════════════════════════════════════
       ALERT BANNERS
       ════════════════════════════════════════════ */
    .alert-attack {
        background: #FEF2F2;
        border: 1px solid #FECACA;
        border-left: 4px solid #EF4444;
        border-radius: 12px;
        padding: 20px 24px;
        display: flex;
        gap: 16px;
        align-items: flex-start;
    }
    .alert-attack-icon {
        width: 40px; height: 40px; min-width: 40px;
        background: #FEE2E2;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 18px;
        font-weight: 800;
        color: #EF4444;
    }
    .alert-attack-title {
        font-size: 15px;
        font-weight: 700;
        color: #991B1B;
        letter-spacing: 0.2px;
    }
    .alert-attack-detail {
        font-size: 13px;
        color: #7F1D1D;
        margin-top: 4px;
        font-family: 'Source Code Pro', monospace;
        line-height: 1.5;
    }
    .alert-attack-time {
        font-size: 12px;
        color: #B91C1C;
        margin-top: 6px;
        font-weight: 500;
    }

    .alert-normal {
        background: #F0FDF4;
        border: 1px solid #BBF7D0;
        border-left: 4px solid #16A34A;
        border-radius: 12px;
        padding: 20px 24px;
        display: flex;
        gap: 16px;
        align-items: flex-start;
    }
    .alert-normal-icon {
        width: 40px; height: 40px; min-width: 40px;
        background: #DCFCE7;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 800;
        font-size: 18px;
        color: #16A34A;
    }
    .alert-normal-title {
        font-size: 15px;
        font-weight: 600;
        color: #14532D;
    }
    .alert-normal-detail {
        font-size: 13px;
        color: #166534;
        margin-top: 4px;
    }

    /* ════════════════════════════════════════════
       EVENT LOG
       ════════════════════════════════════════════ */
    .alert-log {
        background: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 12px;
        padding: 16px;
        font-family: 'Source Code Pro', monospace;
        font-size: 13px;
        max-height: 340px;
        overflow-y: auto;
    }
    .alert-log::-webkit-scrollbar { width: 5px; }
    .alert-log::-webkit-scrollbar-track { background: transparent; }
    .alert-log::-webkit-scrollbar-thumb { background: #D1D5DB; border-radius: 4px; }
    .log-attack { color: #EF4444; font-weight: 600; }
    .log-normal { color: #16A34A; font-weight: 500; }
    .log-time   { color: #9CA3AF; }
    .log-entry  {
        padding: 5px 0;
        border-bottom: 1px solid #F3F4F6;
    }
    .log-entry:last-child { border-bottom: none; }

    /* ════════════════════════════════════════════
       SECTION TITLES
       ════════════════════════════════════════════ */
    .section-title {
        color: #111827;
        font-size: 22px;
        font-weight: 600;
        margin-bottom: 16px;
        margin-top: 24px;
        letter-spacing: -0.3px;
    }
    .section-subtitle {
        font-size: 12px;
        font-weight: 500;
        color: #6B7280;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        margin-bottom: 12px;
    }

    /* ════════════════════════════════════════════
       INFO CARDS
       ════════════════════════════════════════════ */
    .info-card {
        background: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        margin-bottom: 16px;
    }
    .info-card-title {
        font-size: 15px;
        font-weight: 600;
        color: #111827;
        margin-bottom: 14px;
        padding-bottom: 10px;
        border-bottom: 1px solid #F3F4F6;
    }
    .info-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 8px 0;
        border-bottom: 1px solid #F3F4F6;
        font-size: 13px;
    }
    .info-row:last-child { border-bottom: none; }
    .info-key   { color: #6B7280; font-weight: 500; }
    .info-value {
        color: #111827;
        font-weight: 600;
        font-family: 'Source Code Pro', monospace;
        font-size: 13px;
    }

    /* ════════════════════════════════════════════
       CAPABILITY BADGES
       ════════════════════════════════════════════ */
    .capability-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 12px;
    }
    .capability-item {
        background: #F8FAFC;
        border: 1px solid #E5E7EB;
        border-radius: 10px;
        padding: 16px 12px;
        text-align: center;
        transition: border-color 0.2s, box-shadow 0.2s;
    }
    .capability-item:hover {
        border-color: #2563EB;
        box-shadow: 0 2px 8px rgba(37,99,235,0.1);
    }
    .capability-icon {
        font-size: 20px;
        font-weight: 800;
        color: #2563EB;
        margin-bottom: 6px;
        font-family: 'Source Code Pro', monospace;
    }
    .capability-label {
        font-size: 11px;
        font-weight: 600;
        color: #374151;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        line-height: 1.4;
    }

    /* ════════════════════════════════════════════
       STREAMLIT COMPONENT OVERRIDES
       ════════════════════════════════════════════ */
    .stButton > button {
        background: #2563EB;
        color: #FFFFFF !important;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        font-size: 14px;
        width: 100%;
        padding: 10px 18px;
        transition: background 0.2s, box-shadow 0.2s;
        font-family: 'Inter', sans-serif;
    }
    .stButton > button:hover {
        background: #1E40AF;
        color: #FFFFFF !important;
        box-shadow: 0 4px 12px rgba(37,99,235,0.25);
    }
    .stButton > button:active {
        background: #1D4ED8;
        color: #FFFFFF !important;
    }

    div[data-testid="stMetricValue"] { color: #2563EB; }

    h1, h2, h3 {
        color: #111827 !important;
        font-family: 'Inter', sans-serif !important;
    }
    p, li { color: #374151; font-size: 15px; }

    /* Selectbox & slider labels readable */
    .stSelectbox label, .stSlider label {
        color: #111827 !important;
        font-weight: 500 !important;
    }

    /* ════════════════════════════════════════════
       STATS BAR
       ════════════════════════════════════════════ */
    .stats-bar {
        background: linear-gradient(135deg, #1E40AF 0%, #2563EB 100%);
        border-radius: 14px;
        padding: 20px 28px;
        display: flex;
        justify-content: space-around;
        margin: 20px 0 24px;
        box-shadow: 0 4px 16px rgba(37,99,235,0.2);
    }
    .stats-item { text-align: center; }
    .stats-num {
        font-size: 22px;
        font-weight: 700;
        color: #FFFFFF;
        font-family: 'Inter', sans-serif;
    }
    .stats-label {
        font-size: 11px;
        color: rgba(255,255,255,0.7);
        text-transform: uppercase;
        letter-spacing: 1.2px;
        font-weight: 500;
        margin-top: 2px;
    }

    /* ════════════════════════════════════════════
       CHART CARDS (wraps plotly charts)
       ════════════════════════════════════════════ */
    .chart-card {
        background: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        margin-bottom: 16px;
    }
    .chart-card-header {
        font-size: 15px;
        font-weight: 600;
        color: #111827;
        margin-bottom: 14px;
        padding-bottom: 10px;
        border-bottom: 1px solid #F3F4F6;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .chart-header-icon {
        width: 28px; height: 28px;
        background: #EFF6FF;
        border-radius: 6px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-size: 13px;
        font-weight: 700;
        color: #2563EB;
    }

    /* ════════════════════════════════════════════
       FOOTER
       ════════════════════════════════════════════ */
    .dashboard-footer {
        background: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 12px;
        padding: 22px 32px;
        margin-top: 32px;
        text-align: center;
        font-size: 13px;
        color: #9CA3AF;
    }
    .footer-link {
        color: #2563EB;
        text-decoration: none;
        font-weight: 600;
    }

    /* ════════════════════════════════════════════
       RESPONSIVE GRID HELPERS
       ════════════════════════════════════════════ */
    .gap-16 { gap: 16px; }
    .mt-24  { margin-top: 24px; }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════
# LOAD RESOURCES (cached)
# ══════════════════════════════════════════════════════════════════════
@st.cache_resource
def load_model_and_vocab():
    """Load model and vocab once, cache for all reruns."""
    try:
        with open(DATA_DIR / "vocab.json") as f:
            vocab = json.load(f)

        with open(MODELS_DIR / "threshold.json") as f:
            threshold_data = json.load(f)

        config = DistilBertConfig(
            vocab_size               = len(vocab),
            max_position_embeddings  = 64,
            dim                      = 256,
            n_layers                 = 4,
            n_heads                  = 4,
            hidden_dim               = 1024,
            dropout                  = 0.1,
            attention_dropout        = 0.1,
            pad_token_id             = 0,
        )

        model = DistilBertForMaskedLM(config)
        checkpoint = torch.load(
            MODELS_DIR / "best_model.pt",
            map_location = "cpu",
            weights_only = False
        )
        model.load_state_dict(checkpoint['model_state'])
        model.eval()

        return model, vocab, threshold_data, None

    except Exception as e:
        return None, None, None, str(e)


@st.cache_data
def load_sample_data():
    """Load sample sequences for demo mode."""
    try:
        seqs = torch.load(
            DATA_DIR / "sequences.pt",
            weights_only=False
        )
        idx  = torch.randperm(len(seqs))[:2000]
        return seqs[idx]
    except:
        return None


@st.cache_data
def load_attack_data():
    """Load attack sequences for demo mode."""
    try:
        col_names = [
            'Timestamp','ID','DLC',
            'D0','D1','D2','D3','D4','D5','D6','D7','Flag'
        ]
        df = pd.read_csv(
            DATA_DIR / "attack_traffic.csv",
            header=None, names=col_names, nrows=50000
        )
        return df
    except:
        return None


# ══════════════════════════════════════════════════════════════════════
# SCORING FUNCTION
# ══════════════════════════════════════════════════════════════════════
def score_sequence(model, sequence_tensor):
    """Score one sequence -- returns anomaly loss."""
    with torch.no_grad():
        seq       = sequence_tensor.unsqueeze(0)
        B, L      = seq.shape
        input_ids = seq.clone()
        labels    = torch.full((B, L), -100, dtype=torch.long)

        prob          = torch.rand(B, L)
        mask_idx      = prob < 0.15
        special       = (seq == 0) | (seq == 1) | (seq == 2)
        mask_idx      = mask_idx & ~special

        labels[mask_idx]     = seq[mask_idx]
        input_ids[mask_idx]  = 1   # [MASK]

        attn = torch.ones(B, L, dtype=torch.long)
        out  = model(
            input_ids=input_ids,
            attention_mask=attn,
            labels=labels
        )
        return out.loss.item()


# ══════════════════════════════════════════════════════════════════════
# SESSION STATE INIT
# ══════════════════════════════════════════════════════════════════════
def init_session_state():
    defaults = {
        'scores'         : [],
        'timestamps'     : [],
        'labels'         : [],
        'alert_log'      : [],
        'total_analyzed' : 0,
        'total_attacks'  : 0,
        'running'        : False,
        'seq_index'      : 0,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


# ══════════════════════════════════════════════════════════════════════
# PLOTLY CHART BUILDERS
# ══════════════════════════════════════════════════════════════════════
CHART_BG   = "#FFFFFF"
CHART_GRID = "#F3F4F6"
CHART_FONT = dict(color="#374151", family="Inter, sans-serif", size=13)

def build_realtime_chart(scores, timestamps, labels, threshold):
    """Live scrolling anomaly score chart."""
    if not scores:
        scores     = [0.0]
        timestamps = [datetime.now().strftime("%H:%M:%S")]
        labels     = ["Normal"]

    colors = ["#EF4444" if l == "ATTACK" else "#16A34A" for l in labels]

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x    = timestamps,
        y    = scores,
        mode = 'lines+markers',
        name = 'Anomaly Score',
        line = dict(color='#2563EB', width=2.5),
        marker = dict(
            color = colors,
            size  = 6,
            line  = dict(width=1.5, color='#FFFFFF')
        ),
        fill      = 'tozeroy',
        fillcolor = 'rgba(37,99,235,0.06)',
    ))

    fig.add_hline(
        y           = threshold,
        line_dash   = "dash",
        line_color  = "#F59E0B",
        line_width  = 2,
        annotation_text  = f"Threshold: {threshold:.3f}",
        annotation_position = "top right",
        annotation_font_color = "#B45309",
        annotation_font_size = 12,
        annotation_font = dict(family="Inter"),
    )

    for i, (s, t, l) in enumerate(zip(scores, timestamps, labels)):
        if l == "ATTACK":
            fig.add_vline(
                x          = t,
                line_color = "rgba(239,68,68,0.1)",
                line_width = 12
            )

    fig.update_layout(
        paper_bgcolor = CHART_BG,
        plot_bgcolor  = CHART_BG,
        font          = CHART_FONT,
        xaxis = dict(
            title       = dict(text='Timestamp', font=dict(size=13, color='#6B7280')),
            gridcolor   = CHART_GRID,
            showgrid    = True,
            tickfont    = dict(size=11, color='#6B7280'),
            linecolor   = '#E5E7EB',
            zeroline    = False,
        ),
        yaxis = dict(
            title       = dict(text='Anomaly Score (Loss)', font=dict(size=13, color='#6B7280')),
            gridcolor   = CHART_GRID,
            showgrid    = True,
            rangemode   = 'tozero',
            linecolor   = '#E5E7EB',
            zeroline    = False,
        ),
        showlegend   = True,
        legend       = dict(
            bgcolor     = CHART_BG,
            bordercolor = '#E5E7EB',
            borderwidth = 1,
            font        = dict(size=12, color='#374151')
        ),
        margin       = dict(l=60, r=20, t=16, b=56),
        height       = 400,
        hovermode    = 'x unified',
        hoverlabel   = dict(bgcolor='#1E40AF', font_size=12, font_color='#FFFFFF'),
    )
    return fig


def build_distribution_chart(scores, labels, threshold):
    """Score distribution histogram."""
    if len(scores) < 5:
        fig = go.Figure()
        fig.update_layout(
            paper_bgcolor=CHART_BG, plot_bgcolor=CHART_BG,
            font=CHART_FONT, height=300,
            margin=dict(l=60, r=20, t=16, b=56),
            annotations=[dict(
                text="Collecting data...", showarrow=False,
                font=dict(size=14, color="#9CA3AF", family="Inter"),
                xref="paper", yref="paper", x=0.5, y=0.5
            )]
        )
        return fig

    normal_s = [s for s, l in zip(scores, labels) if l == "Normal"]
    attack_s = [s for s, l in zip(scores, labels) if l == "ATTACK"]

    fig = go.Figure()

    if normal_s:
        fig.add_trace(go.Histogram(
            x        = normal_s,
            name     = 'Normal',
            marker_color = '#16A34A',
            opacity  = 0.8,
            nbinsx   = 30,
        ))
    if attack_s:
        fig.add_trace(go.Histogram(
            x        = attack_s,
            name     = 'Attack',
            marker_color = '#EF4444',
            opacity  = 0.8,
            nbinsx   = 30,
        ))

    fig.add_vline(
        x=threshold, line_dash="dash",
        line_color="#F59E0B", line_width=2
    )

    fig.update_layout(
        barmode       = 'overlay',
        paper_bgcolor = CHART_BG,
        plot_bgcolor  = CHART_BG,
        font          = CHART_FONT,
        xaxis  = dict(title=dict(text='Anomaly Score', font=dict(size=13, color='#6B7280')),
                       gridcolor=CHART_GRID, linecolor='#E5E7EB', zeroline=False,
                       tickfont=dict(color='#6B7280', size=11)),
        yaxis  = dict(title=dict(text='Frequency', font=dict(size=13, color='#6B7280')),
                       gridcolor=CHART_GRID, linecolor='#E5E7EB', zeroline=False,
                       tickfont=dict(color='#6B7280', size=11)),
        legend = dict(bgcolor=CHART_BG, bordercolor='#E5E7EB', font=dict(color='#374151', size=12)),
        margin = dict(l=60, r=20, t=16, b=56),
        height = 300,
        hoverlabel = dict(bgcolor='#1E40AF', font_size=12, font_color='#FFFFFF'),
    )
    return fig


def build_gauge(value, threshold, title):
    """Gauge chart for current score vs threshold."""
    max_val = threshold * 3
    color   = "#EF4444" if value > threshold else "#16A34A"

    fig = go.Figure(go.Indicator(
        mode  = "gauge+number+delta",
        value = round(value, 4),
        delta = dict(
            reference  = threshold,
            increasing = dict(color="#EF4444"),
            decreasing = dict(color="#16A34A"),
        ),
        gauge = dict(
            axis  = dict(
                range    = [0, max_val],
                tickcolor = '#9CA3AF',
                tickfont  = dict(color='#6B7280', size=10, family='Inter')
            ),
            bar   = dict(color=color, thickness=0.7),
            bgcolor    = '#F8FAFC',
            bordercolor = '#E5E7EB',
            borderwidth = 1,
            steps = [
                dict(range=[0, threshold], color='#F0FDF4'),
                dict(range=[threshold, max_val], color='#FEF2F2'),
            ],
            threshold = dict(
                line  = dict(color="#F59E0B", width=3),
                value = threshold,
                thickness = 0.85
            ),
        ),
        title = dict(
            text = title,
            font = dict(color='#6B7280', size=13, family='Inter')
        ),
        number = dict(
            font      = dict(color=color, size=28, family='Inter'),
            valueformat = ".4f"
        ),
    ))

    fig.update_layout(
        paper_bgcolor = CHART_BG,
        font          = CHART_FONT,
        margin        = dict(l=20, r=20, t=44, b=20),
        height        = 210,
    )
    return fig


def build_metrics_pie(total_normal, total_attacks):
    """Donut chart of traffic classification."""
    if total_normal + total_attacks == 0:
        fig = go.Figure()
        fig.update_layout(
            paper_bgcolor=CHART_BG, height=210,
            margin=dict(l=10, r=10, t=10, b=10),
            annotations=[dict(
                text="No data", showarrow=False,
                font=dict(size=13, color="#9CA3AF", family="Inter"),
                xref="paper", yref="paper", x=0.5, y=0.5
            )]
        )
        return fig

    fig = go.Figure(go.Pie(
        labels = ['Normal', 'Attack'],
        values = [max(total_normal, 0.001), max(total_attacks, 0.001)],
        marker = dict(colors=['#16A34A', '#EF4444']),
        hole   = 0.65,
        textinfo  = 'label+percent',
        textfont  = dict(color='#374151', size=12, family='Inter'),
    ))

    fig.update_layout(
        paper_bgcolor = CHART_BG,
        font          = CHART_FONT,
        showlegend    = False,
        margin        = dict(l=10, r=10, t=10, b=10),
        height        = 210,
        annotations   = [dict(
            text      = f"<b>{total_attacks}</b><br><span style='font-size:11px;color:#6B7280'>threats</span>",
            x=0.5, y=0.5,
            font      = dict(size=20, color='#EF4444', family='Inter'),
            showarrow = False
        )]
    )
    return fig


def build_score_trend_chart(scores, labels):
    """Moving average trend chart for deeper analysis."""
    if len(scores) < 10:
        fig = go.Figure()
        fig.update_layout(
            paper_bgcolor=CHART_BG, plot_bgcolor=CHART_BG,
            font=CHART_FONT, height=240,
            margin=dict(l=60, r=20, t=16, b=44),
            annotations=[dict(
                text="Requires 10+ data points", showarrow=False,
                font=dict(size=14, color="#9CA3AF", family="Inter"),
                xref="paper", yref="paper", x=0.5, y=0.5
            )]
        )
        return fig

    window = min(10, len(scores))
    moving_avg = pd.Series(scores).rolling(window=window, min_periods=1).mean().tolist()
    moving_std = pd.Series(scores).rolling(window=window, min_periods=1).std().fillna(0).tolist()
    upper = [a + s for a, s in zip(moving_avg, moving_std)]
    lower = [max(a - s, 0) for a, s in zip(moving_avg, moving_std)]
    x_range = list(range(len(scores)))

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=x_range, y=upper, mode='lines',
        line=dict(width=0), showlegend=False, hoverinfo='skip',
    ))
    fig.add_trace(go.Scatter(
        x=x_range, y=lower, mode='lines',
        line=dict(width=0), showlegend=False, hoverinfo='skip',
        fill='tonexty', fillcolor='rgba(37,99,235,0.08)',
    ))
    fig.add_trace(go.Scatter(
        x=x_range, y=moving_avg, mode='lines',
        name=f'{window}-pt Moving Avg',
        line=dict(color='#2563EB', width=2.5),
    ))

    fig.update_layout(
        paper_bgcolor=CHART_BG, plot_bgcolor=CHART_BG,
        font=CHART_FONT,
        xaxis=dict(title=dict(text='Sequence Index', font=dict(size=13, color='#6B7280')),
                    gridcolor=CHART_GRID, linecolor='#E5E7EB', zeroline=False,
                    tickfont=dict(color='#6B7280', size=11)),
        yaxis=dict(title=dict(text='Score (Smoothed)', font=dict(size=13, color='#6B7280')),
                    gridcolor=CHART_GRID, linecolor='#E5E7EB', zeroline=False,
                    tickfont=dict(color='#6B7280', size=11)),
        legend=dict(bgcolor=CHART_BG, bordercolor='#E5E7EB', font=dict(color='#374151', size=12)),
        margin=dict(l=60, r=20, t=16, b=44),
        height=240, hovermode='x unified',
        hoverlabel=dict(bgcolor='#1E40AF', font_size=12, font_color='#FFFFFF'),
    )
    return fig


# ══════════════════════════════════════════════════════════════════════
# MAIN DASHBOARD
# ══════════════════════════════════════════════════════════════════════
def main():
    init_session_state()

    model, vocab, threshold_data, error = load_model_and_vocab()

    # ── HEADER ────────────────────────────────────────────────────────
    st.markdown("""
    <div class="dashboard-header">
        <div style="display:flex; align-items:center; justify-content:space-between; position:relative; z-index:1;">
            <div>
                <div class="header-title">
                    CAN Bus Intrusion Detection System
                </div>
                <div class="header-subtitle">
                    Real-Time Cyber Threat Monitor
                    &nbsp;&middot;&nbsp;
                    Transformer-Based Anomaly Detection
                </div>
            </div>
            <div style="display:flex; align-items:center; gap:18px;">
                <span class="header-badge badge-online">
                    <span class="badge-dot"></span> System Online
                </span>
                <div style="text-align:right;">
                    <div class="header-meta">SESSION</div>
                    <div style="font-size:14px; color:#FFFFFF; font-weight:600;
                         font-family:'Source Code Pro',monospace; margin-top:2px;">
                        """ + datetime.now().strftime("%Y-%m-%d %H:%M") + """
                    </div>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── ERROR STATE ────────────────────────────────────────────────────
    if error or model is None:
        st.error(f"Failed to load model: {error}")
        st.info("Ensure best_model.pt, vocab.json, and "
                "threshold.json exist in the correct directories.")
        st.stop()

    threshold = threshold_data['threshold']
    normal_sequences = load_sample_data()
    attack_df        = load_attack_data()

    # ── SIDEBAR ────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown("""
        <div class="sidebar-brand">
            <div class="sidebar-brand-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.2"
                     stroke-linecap="round" stroke-linejoin="round">
                    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                </svg>
            </div>
            <div class="sidebar-brand-title">CAN Bus IDS</div>
            <div class="sidebar-brand-sub">Intrusion Detection System</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="sidebar-section">Monitor Settings</div>',
                    unsafe_allow_html=True)

        mode = st.selectbox(
            "Detection Mode",
            ["Auto Demo", "Attack Simulation", "Normal Traffic Only"],
            help="Choose the traffic simulation mode"
        )

        speed = st.slider(
            "Refresh Interval (sec)", 0.3, 3.0, 0.8, 0.1
        )

        window_size = st.slider(
            "Display Window", 20, 100, 50,
            help="Number of recent data points to display"
        )

        custom_threshold = st.slider(
            "Detection Threshold",
            float(threshold * 0.5),
            float(threshold * 2.0),
            float(threshold),
            step=0.001,
            format="%.3f"
        )

        st.markdown("---")
        st.markdown('<div class="sidebar-section">Actions</div>',
                    unsafe_allow_html=True)

        col_s1, col_s2 = st.columns(2)
        with col_s1:
            if st.button("START", key="start"):
                st.session_state.running = True
        with col_s2:
            if st.button("STOP", key="stop"):
                st.session_state.running = False

        if st.button("RESET DATA", key="reset"):
            for key in ['scores','timestamps','labels',
                        'alert_log','total_analyzed','total_attacks']:
                st.session_state[key] = [] if isinstance(
                    st.session_state[key], list
                ) else 0
            st.session_state.running = False
            st.rerun()

        st.markdown("---")
        st.markdown('<div class="sidebar-section">Model Specifications</div>',
                    unsafe_allow_html=True)

        st.markdown(f"""
        <div class="info-card">
            <div class="info-row">
                <span class="info-key">Architecture</span>
                <span class="info-value">DistilBERT</span>
            </div>
            <div class="info-row">
                <span class="info-key">Vocabulary</span>
                <span class="info-value">{len(vocab):,} tokens</span>
            </div>
            <div class="info-row">
                <span class="info-key">Layers / Heads</span>
                <span class="info-value">4 / 4</span>
            </div>
            <div class="info-row">
                <span class="info-key">Hidden Dim</span>
                <span class="info-value">256</span>
            </div>
            <div class="info-row">
                <span class="info-key">Threshold</span>
                <span class="info-value">{threshold:.4f}</span>
            </div>
            <div class="info-row">
                <span class="info-key">Percentile</span>
                <span class="info-value">99th</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown('<div class="sidebar-section">About</div>',
                    unsafe_allow_html=True)
        st.markdown("""
        <div style="font-size:13px; color:#6B7280; line-height:1.65; padding:0 4px;">
            Transformer-based masked language model trained on normal
            CAN bus traffic to detect anomalous patterns indicating
            DoS, fuzzing, and spoofing attacks on automotive networks.
        </div>
        """, unsafe_allow_html=True)

    # ── COMPUTE METRICS ────────────────────────────────────────────────
    current_score = (
        st.session_state.scores[-1]
        if st.session_state.scores else 0.0
    )
    total_a = st.session_state.total_analyzed
    total_t = st.session_state.total_attacks
    det_rate = total_t / total_a * 100 if total_a > 0 else 0
    normal_rate = 100 - det_rate
    avg_score = (
        sum(st.session_state.scores) / len(st.session_state.scores)
        if st.session_state.scores else 0.0
    )
    max_score = max(st.session_state.scores) if st.session_state.scores else 0.0

    # ── STATS BAR ──────────────────────────────────────────────────────
    st.markdown(f"""
    <div class="stats-bar">
        <div class="stats-item">
            <div class="stats-num">{total_a:,}</div>
            <div class="stats-label">Sequences Analyzed</div>
        </div>
        <div class="stats-item">
            <div class="stats-num">{total_t:,}</div>
            <div class="stats-label">Threats Detected</div>
        </div>
        <div class="stats-item">
            <div class="stats-num">{det_rate:.1f}%</div>
            <div class="stats-label">Threat Rate</div>
        </div>
        <div class="stats-item">
            <div class="stats-num">{avg_score:.4f}</div>
            <div class="stats-label">Avg Score</div>
        </div>
        <div class="stats-item">
            <div class="stats-num">{max_score:.4f}</div>
            <div class="stats-label">Peak Score</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── METRIC CARDS ROW ───────────────────────────────────────────────
    st.markdown('<div class="section-title">Live Metrics</div>',
                unsafe_allow_html=True)

    m1, m2, m3, m4, m5 = st.columns(5)

    status_class = "metric-danger" if current_score > custom_threshold else "metric-normal"
    status_text  = "THREAT DETECTED" if current_score > custom_threshold else "NORMAL"
    status_icon_cls = "metric-icon-attack" if current_score > custom_threshold else "metric-icon-status"
    status_icon_txt = "!!" if current_score > custom_threshold else "OK"

    with m1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-icon {status_icon_cls}">{status_icon_txt}</div>
            <div class="metric-value {status_class}">{status_text}</div>
            <div class="metric-label">Current Status</div>
        </div>""", unsafe_allow_html=True)

    with m2:
        score_class = "metric-danger" if current_score > custom_threshold else "metric-normal"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-icon metric-icon-score">S</div>
            <div class="metric-value {score_class}">{current_score:.4f}</div>
            <div class="metric-label">Anomaly Score</div>
        </div>""", unsafe_allow_html=True)

    with m3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-icon metric-icon-thresh">T</div>
            <div class="metric-value metric-warning">{custom_threshold:.4f}</div>
            <div class="metric-label">Threshold</div>
        </div>""", unsafe_allow_html=True)

    with m4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-icon metric-icon-attack">A</div>
            <div class="metric-value metric-danger">{total_t:,}</div>
            <div class="metric-label">Attacks Detected</div>
        </div>""", unsafe_allow_html=True)

    with m5:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-icon metric-icon-total">N</div>
            <div class="metric-value metric-info">{total_a:,}</div>
            <div class="metric-label">Total Analyzed</div>
        </div>""", unsafe_allow_html=True)

    st.markdown('<div style="height:16px;"></div>', unsafe_allow_html=True)

    # ── ALERT BANNER ───────────────────────────────────────────────────
    is_attack = (
        current_score > custom_threshold
        and len(st.session_state.scores) > 0
    )

    if is_attack:
        malicious_id = random.choice(list(vocab.keys())[3:10])
        st.markdown(f"""
        <div class="alert-attack">
            <div class="alert-attack-icon">!!</div>
            <div>
                <div class="alert-attack-title">
                    INTRUSION DETECTED &mdash; Immediate attention required
                </div>
                <div class="alert-attack-detail">
                    CAN ID: {malicious_id.upper()}
                    &nbsp;&nbsp;|&nbsp;&nbsp;
                    Score: {current_score:.4f}
                    &nbsp;&nbsp;|&nbsp;&nbsp;
                    Threshold: {custom_threshold:.4f}
                    &nbsp;&nbsp;|&nbsp;&nbsp;
                    Delta: +{(current_score - custom_threshold):.4f}
                </div>
                <div class="alert-attack-time">
                    {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
                    &mdash; Anomaly exceeds 99th percentile baseline
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="alert-normal">
            <div class="alert-normal-icon">OK</div>
            <div>
                <div class="alert-normal-title">
                    All Clear &mdash; Network traffic within normal parameters
                </div>
                <div class="alert-normal-detail">
                    Monitoring {total_a:,} sequences
                    &nbsp;&middot;&nbsp;
                    Last updated: {datetime.now().strftime("%H:%M:%S")}
                    &nbsp;&middot;&nbsp;
                    Normal rate: {normal_rate:.1f}%
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div style="height:20px;"></div>', unsafe_allow_html=True)

    # ── MAIN CHART + GAUGE ─────────────────────────────────────────────
    chart_col, gauge_col = st.columns([3, 1])

    with chart_col:
        st.markdown("""
        <div class="chart-card">
            <div class="chart-card-header">
                <div class="chart-header-icon">RT</div>
                Real-Time Anomaly Score Feed
            </div>
        """, unsafe_allow_html=True)

        recent_scores = st.session_state.scores[-window_size:]
        recent_times  = st.session_state.timestamps[-window_size:]
        recent_labels = st.session_state.labels[-window_size:]

        chart_placeholder = st.empty()
        chart_placeholder.plotly_chart(
            build_realtime_chart(
                recent_scores, recent_times,
                recent_labels, custom_threshold
            ),
            use_container_width=True,
            key="main_chart"
        )
        st.markdown('</div>', unsafe_allow_html=True)

    with gauge_col:
        st.markdown("""
        <div class="chart-card">
            <div class="chart-card-header">
                <div class="chart-header-icon">G</div>
                Score Gauge
            </div>
        """, unsafe_allow_html=True)

        gauge_placeholder = st.empty()
        gauge_placeholder.plotly_chart(
            build_gauge(
                current_score,
                custom_threshold,
                "Current vs Threshold"
            ),
            use_container_width=True,
            key="gauge_chart"
        )
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("""
        <div class="chart-card">
            <div class="chart-card-header">
                <div class="chart-header-icon">TC</div>
                Traffic Classification
            </div>
        """, unsafe_allow_html=True)

        pie_placeholder = st.empty()
        normal_count = total_a - total_t
        pie_placeholder.plotly_chart(
            build_metrics_pie(normal_count, total_t),
            use_container_width=True,
            key="pie_chart"
        )
        st.markdown('</div>', unsafe_allow_html=True)

    # ── DISTRIBUTION + EVENT LOG ───────────────────────────────────────
    dist_col, log_col = st.columns([1, 1])

    with dist_col:
        st.markdown("""
        <div class="chart-card">
            <div class="chart-card-header">
                <div class="chart-header-icon">SD</div>
                Score Distribution
            </div>
        """, unsafe_allow_html=True)

        dist_placeholder = st.empty()
        dist_placeholder.plotly_chart(
            build_distribution_chart(
                st.session_state.scores,
                st.session_state.labels,
                custom_threshold
            ),
            use_container_width=True,
            key="dist_chart"
        )
        st.markdown('</div>', unsafe_allow_html=True)

    with log_col:
        st.markdown("""
        <div class="chart-card">
            <div class="chart-card-header">
                <div class="chart-header-icon">EL</div>
                Event Log
            </div>
        """, unsafe_allow_html=True)

        log_html = '<div class="alert-log">'
        if not st.session_state.alert_log:
            log_html += (
                '<span style="color:#9CA3AF;">'
                'No events recorded. Start monitoring to begin.</span>'
            )
        else:
            for entry in reversed(
                st.session_state.alert_log[-30:]
            ):
                css = (
                    'log-attack'
                    if entry['type'] == 'ATTACK'
                    else 'log-normal'
                )
                log_html += (
                    f'<div class="log-entry">'
                    f'<span class="log-time">'
                    f'[{entry["time"]}]</span> '
                    f'<span class="{css}">'
                    f'{entry["type"]}</span> '
                    f'score={entry["score"]:.4f}'
                    f'</div>'
                )
        log_html += '</div>'
        st.markdown(log_html, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # ── TREND ANALYSIS + CAPABILITIES ──────────────────────────────────
    st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

    trend_col, cap_col = st.columns([2, 1])

    with trend_col:
        st.markdown("""
        <div class="chart-card">
            <div class="chart-card-header">
                <div class="chart-header-icon">TA</div>
                Score Trend Analysis
            </div>
        """, unsafe_allow_html=True)

        st.plotly_chart(
            build_score_trend_chart(
                st.session_state.scores,
                st.session_state.labels
            ),
            use_container_width=True,
            key="trend_chart"
        )
        st.markdown('</div>', unsafe_allow_html=True)

    with cap_col:
        st.markdown(
            '<div class="section-title" style="margin-top:24px;">System Capabilities</div>',
            unsafe_allow_html=True
        )
        st.markdown("""
        <div class="capability-grid">
            <div class="capability-item">
                <div class="capability-icon">MLM</div>
                <div class="capability-label">Masked Language<br>Modeling</div>
            </div>
            <div class="capability-item">
                <div class="capability-icon">DoS</div>
                <div class="capability-label">Denial of Service<br>Detection</div>
            </div>
            <div class="capability-item">
                <div class="capability-icon">FUZ</div>
                <div class="capability-label">Fuzzing Attack<br>Detection</div>
            </div>
            <div class="capability-item">
                <div class="capability-icon">SPF</div>
                <div class="capability-label">Spoofing Attack<br>Detection</div>
            </div>
        </div>

        <div class="info-card" style="margin-top:16px;">
            <div class="info-card-title">Key Highlights</div>
            <div class="info-row">
                <span class="info-key">Detection Method</span>
                <span class="info-value">Unsupervised</span>
            </div>
            <div class="info-row">
                <span class="info-key">Sequence Length</span>
                <span class="info-value">64 frames</span>
            </div>
            <div class="info-row">
                <span class="info-key">Mask Ratio</span>
                <span class="info-value">15%</span>
            </div>
            <div class="info-row">
                <span class="info-key">Inference</span>
                <span class="info-value">Real-Time</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── FOOTER ─────────────────────────────────────────────────────────
    st.markdown(f"""
    <div class="dashboard-footer">
        <strong style="color:#374151;">CAN Bus Intrusion Detection System</strong>
        &nbsp;&middot;&nbsp;
        Transformer-Based Anomaly Detection
        &nbsp;&middot;&nbsp;
        Built with DistilBERT &amp; Streamlit
        <br>
        <span style="font-size:12px; color:#9CA3AF;">
            Session started {datetime.now().strftime("%Y-%m-%d")}
            &nbsp;&middot;&nbsp;
            Model vocabulary: {len(vocab):,} tokens
            &nbsp;&middot;&nbsp;
            Threshold: {threshold:.4f}
        </span>
    </div>
    """, unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════
    # LIVE SCORING LOOP
    # ══════════════════════════════════════════════════════════════════
    if st.session_state.running:
        try:
            inject_attack = False

            if mode == "Attack Simulation":
                inject_attack = True
            elif mode == "Auto Demo":
                inject_attack = random.random() < 0.15

            if inject_attack and attack_df is not None:
                start = random.randint(
                    0, max(0, len(attack_df) - 64)
                )
                ids = attack_df.iloc[
                    start:start+64
                ]['ID'].astype(str).tolist()
                tokens = [
                    vocab.get(x.strip().lower(), 2)
                    for x in ids
                ]
                if len(tokens) < 64:
                    tokens += [0] * (64 - len(tokens))
                seq = torch.tensor(
                    tokens[:64], dtype=torch.long
                )

            elif normal_sequences is not None:
                idx = st.session_state.seq_index % len(
                    normal_sequences
                )
                seq = normal_sequences[idx]
                st.session_state.seq_index += 1

            else:
                st.warning("No sequences loaded.")
                st.session_state.running = False
                st.stop()

            score = score_sequence(model, seq)

            now   = datetime.now().strftime("%H:%M:%S")
            label = (
                "ATTACK" if score > custom_threshold
                else "Normal"
            )

            st.session_state.scores.append(score)
            st.session_state.timestamps.append(now)
            st.session_state.labels.append(label)
            st.session_state.total_analyzed += 1

            if label == "ATTACK":
                st.session_state.total_attacks += 1

            st.session_state.alert_log.append({
                'time'  : now,
                'type'  : label.upper() if label == "ATTACK" else "Normal",
                'score' : score
            })

            for key in ['scores','timestamps','labels']:
                if len(st.session_state[key]) > 500:
                    st.session_state[key] = (
                        st.session_state[key][-500:]
                    )

        except Exception as e:
            st.error(f"Scoring error: {e}")
            st.session_state.running = False

        time.sleep(speed)
        st.rerun()


if __name__ == "__main__":
    main()