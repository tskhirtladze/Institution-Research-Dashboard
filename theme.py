"""
theme.py
--------
Visual system for the dashboard: a "scholarly ledger" theme (white paper
background, ink-navy for structure, a brass/gold accent for emphasis, and
a monospace face for figures). Kept separate from app.py so presentation
concerns don't clutter the data/layout logic, and so the color palette is
in one place if it ever needs to change.

Native Streamlit widgets (buttons, sliders, checkboxes) still take their
base colors from .streamlit/config.toml's [theme] section - this file only
covers the custom CSS classes and fine-grained styling config.toml can't
express (fonts, per-element borders, tabs, expanders, metric cards, etc).
"""

import streamlit as st

INK = "#1B1E24"
INK_SOFT = "#5B6270"
NAVY = "#1E3A5F"
GOLD = "#AD8A3E"
RULE = "#E5E1D8"
PAPER = "#FFFFFF"
PAPER_SUBTLE = "#F8F7F3"

CHART_PALETTE = ["#1E3A5F", "#AD8A3E", "#2F6F62", "#B5533C", "#6B5B7B", "#4E7A94"]


def inject_css():
    """Apply the dashboard's scholarly-ledger CSS theme. Call once, near the top of app.py."""
    st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,400;8..60,600;8..60,700&family=Inter:wght@400;500;600&family=IBM+Plex+Mono:wght@500;600&display=swap');

html, body, [class*="css"] {{
    font-family: 'Inter', -apple-system, sans-serif;
    color: {INK};
}}

.stApp {{
    background-color: {PAPER};
}}

section[data-testid="stSidebar"] {{
    background-color: {PAPER_SUBTLE};
    border-right: 1px solid {RULE};
}}

h1, h2, h3 {{
    font-family: 'Source Serif 4', Georgia, serif !important;
    color: {NAVY} !important;
    letter-spacing: -0.01em;
}}

h1 {{ font-weight: 700 !important; }}
h2, h3 {{ font-weight: 600 !important; }}

/* Masthead */
.masthead-title {{
    font-family: 'Source Serif 4', Georgia, serif;
    font-weight: 700;
    font-size: 2.6rem;
    text-align: center;
    color: {NAVY};
    margin-bottom: 0.15rem;
    line-height: 1.15;
}}
.masthead-rule {{
    width: 64px;
    height: 3px;
    background: {GOLD};
    margin: 0.6rem auto 0.9rem auto;
}}
.masthead-sub {{
    text-align: center;
    color: {INK_SOFT};
    font-size: 1rem;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    margin-bottom: 2.2rem;
}}

/* Section eyebrow used before subheaders */
.eyebrow {{
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.72rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: {GOLD};
    margin-bottom: -0.4rem;
}}

/* Metrics */
div[data-testid="stMetric"] {{
    background-color: {PAPER_SUBTLE};
    border: 1px solid {RULE};
    border-bottom: 2px solid {GOLD};
    border-radius: 4px;
    padding: 0.9rem 1rem 0.7rem 1rem;
}}
div[data-testid="stMetricValue"] {{
    font-family: 'IBM Plex Mono', monospace;
    color: {NAVY};
    font-weight: 600;
    font-size: 1.5rem;
}}
div[data-testid="stMetricLabel"] {{
    color: {INK_SOFT};
    font-size: 0.8rem;
    letter-spacing: 0.03em;
}}
label[data-testid="stWidgetLabel"] p {{
    color: {INK_SOFT};
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.8rem;
    letter-spacing: 0.03em;
}}

/* Tabs styled like index-card dividers */
.stTabs [data-baseweb="tab-list"] {{
    gap: 4px;
    border-bottom: 1px solid {RULE};
}}
.stTabs [data-baseweb="tab"] {{
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.82rem;
    letter-spacing: 0.02em;
    color: {INK_SOFT};
    background-color: transparent;
    border-radius: 4px 4px 0 0;
    padding: 0.5rem 1rem;
}}
.stTabs [aria-selected="true"] {{
    color: {NAVY} !important;
    background-color: {PAPER_SUBTLE} !important;
    border-bottom: 2px solid {GOLD} !important;
    font-weight: 600;
}}

/* Buttons / inputs */
.stButton > button, .stDownloadButton > button {{
    font-family: 'Inter', sans-serif;
    background-color: {NAVY};
    color: {PAPER};
    border: none;
    border-radius: 3px;
}}
.stButton > button:hover {{
    background-color: {GOLD};
}}
div[data-baseweb="select"] > div, .stTextInput input {{
    border-color: {RULE} !important;
    border-radius: 3px !important;
}}

/* Dividers */
hr {{
    border: none;
    border-top: 1px solid {RULE};
    margin: 1.4rem 0;
}}

/* Expanders */
.streamlit-expanderHeader {{
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.85rem;
    color: {NAVY};
    background-color: {PAPER_SUBTLE};
    border: 1px solid {RULE};
    border-radius: 4px;
}}

/* Dataframes */
/* Dataframe styling */
div[data-testid="stDataFrame"] {{
    border: 1px solid {RULE};
    border-radius: 4px;
    overflow: hidden;
}}

/* Dataframe text */
div[data-testid="stDataFrame"] [data-testid="glideDataEditor"] {{
    background-color: {PAPER} !important;
}}


/* Footer */
.dashboard-footer {{
    text-align: center;
    color: {INK_SOFT};
    font-size: 0.82rem;
    padding: 1.4rem 0 0.6rem 0;
    border-top: 1px solid {RULE};
    margin-top: 1rem;
}}
.dashboard-footer strong {{
    color: {NAVY};
    font-family: 'Source Serif 4', Georgia, serif;
}}

/* Tab content */
.stTabs [data-baseweb="tab-panel"] {{
    background-color: {PAPER} !important;
    color: {INK} !important;
}}

.stTabs .stMarkdown {{
    color: {INK} !important;
}}

.stTabs .stMarkdown strong {{
    color: {INK} !important;
}}

#MainMenu, footer {{visibility: hidden;}}
</style>
""", unsafe_allow_html=True)


def styled_chart(fig, height=None):
    """Apply the dashboard's paper-and-ink chart styling consistently."""
    fig.update_layout(
        template="plotly_white",
        colorway=CHART_PALETTE,
        font=dict(family="Inter, sans-serif", color=INK, size=12),
        title_font=dict(family="Source Serif 4, Georgia, serif", color=NAVY, size=18),
        paper_bgcolor=PAPER,
        plot_bgcolor=PAPER,
        margin=dict(t=60, l=10, r=10, b=10),
    )
    fig.update_xaxes(gridcolor=RULE, zerolinecolor=RULE)
    fig.update_yaxes(gridcolor=RULE, zerolinecolor=RULE)
    if height:
        fig.update_layout(height=height)
    return fig


def eyebrow(text):
    st.markdown(f'<div class="eyebrow">{text}</div>', unsafe_allow_html=True)