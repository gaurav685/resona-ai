"""Global visual polish: one CSS injection called at the top of every page,
plus small reusable render helpers (page header, footer, section label,
pill/badge) so all 10 pages share one consistent look instead of ad-hoc
st.title/st.caption calls. Pure presentation — no data logic lives here.
"""

import streamlit as st

from lib import theme

_CSS = f"""
<style>
  /* ---- Typography & layout ---- */
  html, body, [class*="css"] {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Inter, Roboto, sans-serif;
  }}
  .block-container {{
    padding-top: 2rem;
    padding-bottom: 3rem;
    max-width: 1200px;
  }}
  h1, h2, h3 {{
    letter-spacing: -0.01em;
    font-weight: 650;
  }}

  /* ---- Hide default Streamlit chrome for a product feel ---- */
  #MainMenu {{visibility: hidden;}}
  footer {{visibility: hidden;}}
  header[data-testid="stHeader"] {{background: transparent;}}

  /* ---- Sidebar ---- */
  section[data-testid="stSidebar"] {{
    background: {theme.SURFACE};
    border-right: 1px solid {theme.BORDER};
  }}

  /* ---- Cards (st.container(border=True)) ---- */
  div[data-testid="stVerticalBlockBorderWrapper"] {{
    border-radius: 14px !important;
    border-color: {theme.BORDER} !important;
    background: {theme.SURFACE};
    transition: box-shadow 0.15s ease, transform 0.15s ease;
  }}
  div[data-testid="stVerticalBlockBorderWrapper"]:hover {{
    box-shadow: 0 4px 16px rgba(11,11,11,0.06);
  }}

  /* ---- Metrics ---- */
  div[data-testid="stMetric"] {{
    background: {theme.SURFACE};
    border: 1px solid {theme.BORDER};
    border-radius: 12px;
    padding: 0.9rem 1rem 0.7rem;
  }}
  div[data-testid="stMetricValue"] {{
    font-size: 1.6rem;
    font-weight: 650;
  }}
  div[data-testid="stMetricLabel"] {{
    color: {theme.TEXT_MUTED};
    text-transform: uppercase;
    font-size: 0.72rem;
    letter-spacing: 0.04em;
  }}

  /* ---- Buttons ---- */
  .stButton > button, .stDownloadButton > button {{
    border-radius: 999px;
    border: 1px solid {theme.BORDER};
    font-weight: 500;
    transition: all 0.12s ease;
  }}
  .stButton > button:hover {{
    border-color: {theme.ACCENT};
    color: {theme.ACCENT};
  }}
  .stButton > button[kind="primary"] {{
    background: {theme.ACCENT};
    border-color: {theme.ACCENT};
  }}

  /* ---- Progress bars (used as ratio/score bars) ---- */
  div[data-testid="stProgress"] > div > div {{
    background: {theme.ACCENT};
    border-radius: 999px;
  }}

  /* ---- Tabs / selects / expanders ---- */
  .streamlit-expanderHeader {{
    border-radius: 10px;
    font-weight: 500;
  }}

  /* ---- Custom classes used by render_* helpers below ---- */
  .resona-eyebrow {{
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: {theme.ACCENT};
    background: color-mix(in srgb, {theme.ACCENT} 10%, transparent);
    border: 1px solid color-mix(in srgb, {theme.ACCENT} 25%, transparent);
    border-radius: 999px;
    padding: 0.2rem 0.7rem;
    margin-bottom: 0.6rem;
  }}
  .resona-page-title {{
    font-size: 2rem;
    font-weight: 700;
    letter-spacing: -0.02em;
    margin: 0 0 0.25rem 0;
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }}
  .resona-page-subtitle {{
    color: {theme.TEXT_SECONDARY};
    font-size: 0.95rem;
    max-width: 46rem;
    margin-bottom: 1.5rem;
  }}
  .resona-footer {{
    margin-top: 3rem;
    padding-top: 1.2rem;
    border-top: 1px solid {theme.BORDER};
    color: {theme.TEXT_MUTED};
    font-size: 0.78rem;
    line-height: 1.5;
  }}
  .resona-pill {{
    display: inline-flex;
    align-items: center;
    border-radius: 999px;
    border: 1px solid {theme.BORDER};
    padding: 0.15rem 0.6rem;
    font-size: 0.75rem;
    font-weight: 500;
    color: {theme.TEXT_SECONDARY};
    margin: 0 0.3rem 0.3rem 0;
  }}
  .resona-pill-accent {{
    color: {theme.ACCENT};
    border-color: color-mix(in srgb, {theme.ACCENT} 40%, transparent);
    background: color-mix(in srgb, {theme.ACCENT} 8%, transparent);
  }}
  .resona-brand {{
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-weight: 700;
    font-size: 1.05rem;
    letter-spacing: -0.01em;
    margin-bottom: 0.75rem;
  }}
  .resona-caption {{
    color: {theme.TEXT_MUTED};
    font-size: 0.8rem;
  }}
</style>
"""


def inject_css() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)


def render_header(title: str, subtitle: str | None = None, icon: str = "", eyebrow: str | None = None) -> None:
    if eyebrow:
        st.markdown(f'<span class="resona-eyebrow">{eyebrow}</span>', unsafe_allow_html=True)
    st.markdown(f'<div class="resona-page-title">{icon} {title}</div>', unsafe_allow_html=True)
    if subtitle:
        st.markdown(f'<div class="resona-page-subtitle">{subtitle}</div>', unsafe_allow_html=True)


def render_footer() -> None:
    st.markdown(
        """
        <div class="resona-footer">
          Personality outputs are <strong>model-estimated associations</strong> from a research
          dataset of music-listening preferences — not psychological diagnoses, and not derived
          from any individual listener's real listening history.<br />
          Resona AI — college research project. All metrics shown come from real, locally-run models.
        </div>
        """,
        unsafe_allow_html=True,
    )


def pill(text: str, accent: bool = False) -> str:
    cls = "resona-pill resona-pill-accent" if accent else "resona-pill"
    return f'<span class="{cls}">{text}</span>'


def render_pills(items: list[str], accent: bool = False) -> None:
    st.markdown("".join(pill(i, accent) for i in items), unsafe_allow_html=True)
