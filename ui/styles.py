import streamlit as st

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@500;700&family=JetBrains+Mono:wght@400;600&display=swap');

h1, h2, h3, h4, h5, h6 { color: #a7f3d0 !important; }
[data-testid="stMetricValue"] { color: #10b981 !important; }
[data-testid="stMetricLabel"] { color: #94a3b8 !important; }
[data-testid="stDataFrame"]   { border: 1px solid #334155; }
[data-testid="stSidebar"]     { border-right: 1px solid #334155; }
div.stButton > button       { background-color: #059669; color: white; border: none; font-weight: bold; }
div.stButton > button:hover { background-color: #10b981; border-color: #10b981; }
.stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
    background-color: #1e293b;
    border-top: 2px solid #10b981;
}

/* ── Карточка техники ── */
.vc-card    { background: linear-gradient(135deg, #0f172a 0%, #1a2744 50%, #0f172a 100%);
              border: 1px solid #1e3a5f; border-radius: 12px; overflow: hidden;
              box-shadow: 0 0 40px rgba(16,185,129,0.08), 0 4px 24px rgba(0,0,0,0.5);
              font-family: 'JetBrains Mono', monospace; }
.vc-header  { background: linear-gradient(90deg, #064e3b, #065f46, #1e3a5f);
              padding: 18px 24px 14px; border-bottom: 1px solid #10b981;
              position: relative; overflow: hidden; }
.vc-header::before { content: ''; position: absolute; top: -20px; right: -20px;
                     width: 120px; height: 120px;
                     background: radial-gradient(circle, rgba(16,185,129,0.15) 0%, transparent 70%);
                     border-radius: 50%; }
.vc-title    { font-family: 'Rajdhani', sans-serif; font-size: 1.6rem; font-weight: 700;
               color: #ecfdf5; letter-spacing: 0.05em;
               text-shadow: 0 0 20px rgba(16,185,129,0.4); margin: 0 0 4px 0; }
.vc-subtitle { font-size: 0.75rem; color: #6ee7b7; letter-spacing: 0.12em; text-transform: uppercase; }

/* ── Бейджи ── */
.vc-badge       { display: inline-block; padding: 2px 10px; border-radius: 4px;
                  font-size: 0.7rem; font-weight: 600; letter-spacing: 0.1em;
                  text-transform: uppercase; margin-right: 6px; vertical-align: middle; }
.vc-badge-prem  { background:#78350f; color:#fde68a; border:1px solid #d97706; }
.vc-badge-pack  { background:#312e81; color:#c7d2fe; border:1px solid #6366f1; }
.vc-badge-squad { background:#1e3a5f; color:#93c5fd; border:1px solid #3b82f6; }
.vc-badge-mkt   { background:#4a044e; color:#f0abfc; border:1px solid #a855f7; }

/* ── Тело карточки ── */
.vc-body          { padding: 20px 24px; }
.vc-section-title { font-family: 'Rajdhani', sans-serif; font-size: 0.7rem; font-weight: 700;
                    letter-spacing: 0.2em; text-transform: uppercase; color: #10b981;
                    border-bottom: 1px solid #1e3a5f; padding-bottom: 4px; margin: 16px 0 10px 0; }
.vc-row   { display: flex; justify-content: space-between; align-items: center;
            padding: 3px 0; font-size: 0.78rem; }
.vc-label { color: #64748b; }
.vc-value        { color: #e2e8f0; font-weight: 600; }
.vc-value-green  { color: #34d399; font-weight: 700; }
.vc-value-yellow { color: #fbbf24; font-weight: 700; }
.vc-value-red    { color: #f87171; font-weight: 700; }
.vc-value-blue   { color: #60a5fa; font-weight: 700; }

/* ── Броня ── */
.vc-armor-bar   { display: flex; align-items: center; gap: 6px; margin: 3px 0; font-size: 0.73rem; }
.vc-armor-label { color: #64748b; width: 110px; flex-shrink: 0; }
.vc-armor-track { flex: 1; height: 6px; background: #1e293b; border-radius: 3px; overflow: hidden; }
.vc-armor-fill  { height: 100%; border-radius: 3px; }
.vc-armor-num   { color: #e2e8f0; font-weight: 600; width: 46px; text-align: right; flex-shrink: 0; }

/* ── Снаряды ── */
.vc-ammo-chip { display: inline-block; padding: 2px 7px; margin: 2px 2px;
                border-radius: 3px; font-size: 0.65rem; font-weight: 600;
                letter-spacing: 0.05em; text-transform: uppercase; }
.chip-aphe  { background:#7f1d1d; color:#fca5a5; border:1px solid #ef4444; }
.chip-heat  { background:#78350f; color:#fed7aa; border:1px solid #f97316; }
.chip-atgm  { background:#14532d; color:#86efac; border:1px solid #22c55e; }
.chip-apds  { background:#1e3a5f; color:#93c5fd; border:1px solid #3b82f6; }
.chip-he    { background:#4a044e; color:#f0abfc; border:1px solid #a855f7; }
.chip-smoke { background:#1c1917; color:#a8a29e; border:1px solid #57534e; }
.chip-other { background:#1e293b; color:#94a3b8; border:1px solid #475569; }

/* ── Сетка статов (2 колонки) ── */
.vc-stat-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0 16px; }

/* ── Футер карточки ── */
.vc-footer { background: #0b1120; border-top: 1px solid #1e293b; padding: 10px 24px;
             font-size: 0.67rem; color: #334155;
             display: flex; justify-content: space-between; font-family: monospace; }
</style>
"""


def inject_css() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)
