"""Global visual identity: one CSS injection called at the top of every
page (via lib.state.render_user_picker, so it's guaranteed everywhere),
plus small reusable render helpers (page header, footer, pills) so all 10
pages share one consistent, animated look instead of ad-hoc
st.title/st.caption calls. Pure presentation — no data logic lives here.
"""

import streamlit as st

from lib import theme

_CSS = f"""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&family=Inter:wght@400;500;600&display=swap');

  :root {{
    --resona-accent: {theme.ACCENT};
    --resona-accent-2: {theme.SERIES[7]};
    --resona-accent-3: {theme.SERIES[3]};
  }}

  /* ---- Typography & layout ---- */
  html, body, [class*="css"] {{
    font-family: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  }}
  .block-container {{
    padding-top: 2rem;
    padding-bottom: 4rem;
    max-width: 1200px;
    animation: resona-fade-up 0.5s cubic-bezier(0.16, 1, 0.3, 1) both;
  }}
  h1, h2, h3, h4, h5 {{
    font-family: "Manrope", "Inter", sans-serif;
    letter-spacing: -0.02em;
    font-weight: 700;
  }}
  ::selection {{
    background: color-mix(in srgb, var(--resona-accent) 30%, transparent);
  }}

  /* ---- Scrollbar ---- */
  ::-webkit-scrollbar {{ width: 10px; height: 10px; }}
  ::-webkit-scrollbar-track {{ background: transparent; }}
  ::-webkit-scrollbar-thumb {{
    background: color-mix(in srgb, {theme.TEXT_MUTED} 40%, transparent);
    border-radius: 999px;
  }}
  ::-webkit-scrollbar-thumb:hover {{
    background: var(--resona-accent);
  }}

  /* ---- Keyframes ---- */
  @keyframes resona-fade-up {{
    from {{ opacity: 0; transform: translateY(14px); }}
    to   {{ opacity: 1; transform: translateY(0); }}
  }}
  @keyframes resona-fade-in {{
    from {{ opacity: 0; }}
    to   {{ opacity: 1; }}
  }}
  @keyframes resona-float {{
    0%, 100% {{ transform: translate(0, 0) scale(1); }}
    50%      {{ transform: translate(-2%, 3%) scale(1.05); }}
  }}
  @keyframes resona-glow {{
    0%, 100% {{ box-shadow: 0 0 0 0 color-mix(in srgb, var(--resona-accent) 35%, transparent); }}
    50%      {{ box-shadow: 0 0 0 8px color-mix(in srgb, var(--resona-accent) 0%, transparent); }}
  }}
  @keyframes resona-shimmer {{
    0%   {{ background-position: -400px 0; }}
    100% {{ background-position: 400px 0; }}
  }}
  @keyframes resona-gradient-x {{
    0%, 100% {{ background-position: 0% 50%; }}
    50%      {{ background-position: 100% 50%; }}
  }}

  /* ---- Hide default Streamlit chrome for a product feel ---- */
  #MainMenu {{visibility: hidden;}}
  footer {{visibility: hidden;}}
  header[data-testid="stHeader"] {{background: transparent;}}

  /* ---- Ambient background blobs ---- */
  .stApp {{
    background:
      radial-gradient(circle at 12% 8%, color-mix(in srgb, var(--resona-accent) 7%, transparent) 0%, transparent 38%),
      radial-gradient(circle at 88% 18%, color-mix(in srgb, var(--resona-accent-2) 6%, transparent) 0%, transparent 40%),
      radial-gradient(circle at 50% 100%, color-mix(in srgb, var(--resona-accent-3) 5%, transparent) 0%, transparent 45%),
      {theme.BACKGROUND};
    background-attachment: fixed;
  }}

  /* ---- Sidebar ---- */
  section[data-testid="stSidebar"] {{
    background: linear-gradient(180deg, color-mix(in srgb, var(--resona-accent) 5%, {theme.SURFACE}) 0%, {theme.SURFACE} 220px);
    border-right: 1px solid {theme.BORDER};
  }}
  section[data-testid="stSidebar"] .stSelectbox > div > div {{
    border-radius: 10px !important;
    transition: border-color 0.15s ease, box-shadow 0.15s ease;
  }}
  section[data-testid="stSidebar"] .stSelectbox > div > div:focus-within {{
    border-color: var(--resona-accent) !important;
    box-shadow: 0 0 0 3px color-mix(in srgb, var(--resona-accent) 15%, transparent);
  }}

  /* ---- Cards (st.container(border=True)) ---- */
  div[data-testid="stVerticalBlockBorderWrapper"] {{
    border-radius: 16px !important;
    border-color: {theme.BORDER} !important;
    background: color-mix(in srgb, {theme.SURFACE} 92%, transparent);
    backdrop-filter: blur(6px);
    box-shadow: 0 1px 2px rgba(11,11,11,0.04);
    transition: box-shadow 0.25s cubic-bezier(0.16, 1, 0.3, 1),
                transform 0.25s cubic-bezier(0.16, 1, 0.3, 1),
                border-color 0.25s ease;
    animation: resona-fade-up 0.5s cubic-bezier(0.16, 1, 0.3, 1) both;
  }}
  div[data-testid="stVerticalBlockBorderWrapper"]:hover {{
    box-shadow: 0 12px 28px -8px rgba(11,11,11,0.14), 0 0 0 1px color-mix(in srgb, var(--resona-accent) 18%, transparent);
    transform: translateY(-3px);
    border-color: color-mix(in srgb, var(--resona-accent) 35%, {theme.BORDER}) !important;
  }}

  /* ---- Metrics ---- */
  div[data-testid="stMetric"] {{
    background: linear-gradient(155deg, color-mix(in srgb, var(--resona-accent) 4%, {theme.SURFACE}), {theme.SURFACE});
    border: 1px solid {theme.BORDER};
    border-radius: 14px;
    padding: 1rem 1.1rem 0.8rem;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
  }}
  div[data-testid="stMetric"]:hover {{
    transform: translateY(-2px);
    box-shadow: 0 8px 20px -8px rgba(11,11,11,0.14);
  }}
  div[data-testid="stMetricValue"] {{
    font-family: "Manrope", sans-serif;
    font-size: 1.7rem;
    font-weight: 800;
    background: linear-gradient(135deg, {theme.TEXT_PRIMARY}, var(--resona-accent));
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent;
  }}
  div[data-testid="stMetricLabel"] {{
    color: {theme.TEXT_MUTED};
    text-transform: uppercase;
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.05em;
  }}

  /* ---- Buttons ---- */
  .stButton > button, .stDownloadButton > button {{
    border-radius: 999px;
    border: 1px solid {theme.BORDER};
    font-weight: 600;
    transition: all 0.15s cubic-bezier(0.16, 1, 0.3, 1);
  }}
  .stButton > button:hover {{
    border-color: var(--resona-accent);
    color: var(--resona-accent);
    transform: translateY(-1px) scale(1.02);
    box-shadow: 0 4px 14px -4px color-mix(in srgb, var(--resona-accent) 40%, transparent);
  }}
  .stButton > button:active {{
    transform: translateY(0) scale(0.98);
  }}
  .stButton > button[kind="primary"] {{
    background: linear-gradient(135deg, var(--resona-accent), color-mix(in srgb, var(--resona-accent) 70%, var(--resona-accent-2)));
    border-color: var(--resona-accent);
    color: white;
    background-size: 200% 200%;
  }}
  .stButton > button[kind="primary"]:hover {{
    animation: resona-gradient-x 1.6s ease infinite;
    color: white;
  }}

  /* ---- Progress bars (used as ratio/score bars) ---- */
  div[data-testid="stProgress"] > div {{
    background: {theme.GRIDLINE};
    border-radius: 999px;
    overflow: hidden;
  }}
  div[data-testid="stProgress"] > div > div {{
    background: linear-gradient(90deg, var(--resona-accent), var(--resona-accent-3));
    border-radius: 999px;
    background-size: 40px 100%;
  }}

  /* ---- Tabs / selects / expanders ---- */
  .streamlit-expanderHeader {{
    border-radius: 10px;
    font-weight: 600;
    transition: background 0.15s ease;
  }}
  div[data-testid="stExpander"] {{
    border-radius: 14px !important;
    border-color: {theme.BORDER} !important;
  }}

  /* ---- Alerts (info/success/warning/error) ---- */
  div[data-testid="stAlert"] {{
    border-radius: 12px;
    animation: resona-fade-up 0.4s cubic-bezier(0.16, 1, 0.3, 1) both;
  }}

  /* ---- Tabs underline ---- */
  .stTabs [data-baseweb="tab-highlight"] {{
    background-color: var(--resona-accent) !important;
  }}

  /* ---- Custom classes used by render_* helpers below ---- */
  .resona-eyebrow {{
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--resona-accent);
    background: color-mix(in srgb, var(--resona-accent) 10%, transparent);
    border: 1px solid color-mix(in srgb, var(--resona-accent) 28%, transparent);
    border-radius: 999px;
    padding: 0.25rem 0.8rem;
    margin-bottom: 0.7rem;
    animation: resona-fade-up 0.45s cubic-bezier(0.16, 1, 0.3, 1) both;
  }}
  .resona-eyebrow::before {{
    content: "";
    width: 6px; height: 6px;
    border-radius: 50%;
    background: var(--resona-accent);
    animation: resona-glow 2s ease-in-out infinite;
  }}
  .resona-page-title {{
    font-family: "Manrope", sans-serif;
    font-size: 2.15rem;
    font-weight: 800;
    letter-spacing: -0.03em;
    margin: 0 0 0.3rem 0;
    display: flex;
    align-items: center;
    gap: 0.55rem;
    animation: resona-fade-up 0.5s cubic-bezier(0.16, 1, 0.3, 1) 0.05s both;
  }}
  .resona-page-subtitle {{
    color: {theme.TEXT_SECONDARY};
    font-size: 0.97rem;
    max-width: 46rem;
    margin-bottom: 1.6rem;
    line-height: 1.55;
    animation: resona-fade-up 0.5s cubic-bezier(0.16, 1, 0.3, 1) 0.1s both;
  }}
  .resona-footer {{
    margin-top: 3rem;
    padding-top: 1.2rem;
    border-top: 1px solid {theme.BORDER};
    color: {theme.TEXT_MUTED};
    font-size: 0.78rem;
    line-height: 1.6;
  }}
  .resona-pill {{
    display: inline-flex;
    align-items: center;
    border-radius: 999px;
    border: 1px solid {theme.BORDER};
    padding: 0.2rem 0.7rem;
    font-size: 0.75rem;
    font-weight: 600;
    color: {theme.TEXT_SECONDARY};
    margin: 0 0.35rem 0.35rem 0;
    transition: transform 0.15s ease, box-shadow 0.15s ease;
  }}
  .resona-pill:hover {{
    transform: translateY(-1px);
  }}
  .resona-pill-accent {{
    color: var(--resona-accent);
    border-color: color-mix(in srgb, var(--resona-accent) 40%, transparent);
    background: linear-gradient(135deg, color-mix(in srgb, var(--resona-accent) 12%, transparent), color-mix(in srgb, var(--resona-accent-2) 8%, transparent));
  }}
  .resona-brand {{
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-family: "Manrope", sans-serif;
    font-weight: 800;
    font-size: 1.15rem;
    letter-spacing: -0.02em;
    margin-bottom: 1rem;
    background: linear-gradient(135deg, {theme.TEXT_PRIMARY}, var(--resona-accent));
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent;
  }}
  .resona-caption {{
    color: {theme.TEXT_MUTED};
    font-size: 0.8rem;
  }}
  .resona-hero-title {{
    font-family: "Manrope", sans-serif;
    font-size: 3.4rem;
    font-weight: 800;
    letter-spacing: -0.04em;
    margin: 0.3rem 0 0.7rem;
    background: linear-gradient(120deg, {theme.TEXT_PRIMARY} 30%, var(--resona-accent) 65%, var(--resona-accent-2) 100%);
    background-size: 200% auto;
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent;
    animation: resona-fade-up 0.6s cubic-bezier(0.16, 1, 0.3, 1) 0.1s both,
               resona-gradient-x 6s ease-in-out infinite 0.6s;
  }}
  .resona-glass {{
    background: color-mix(in srgb, {theme.SURFACE} 85%, transparent);
    backdrop-filter: blur(10px);
    border: 1px solid {theme.BORDER};
    border-radius: 20px;
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
