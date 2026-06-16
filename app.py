import streamlit as st
import pandas as pd
import numpy as np

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="WSL Stats Hub",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global CSS (FiveThirtyEight-inspired) ────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Atlas+Grotesk:wght@400;500;700&display=swap');

  html, body, [class*="css"] {
    font-family: 'Atlas Grotesk', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  }

  /* ── Sidebar ── */
  [data-testid="stSidebar"] {
    background-color: #1a1a2e;
    border-right: 3px solid #e63946;
  }
  [data-testid="stSidebar"] * { color: #f0f0f0 !important; }
  [data-testid="stSidebar"] .stSelectbox label,
  [data-testid="stSidebar"] .stMultiSelect label { color: #aaa !important; font-size: 0.75rem; }

  /* ── Main background ── */
  .main { background-color: #f5f5f0; }

  /* ── Header band ── */
  .page-header {
    background: #1a1a2e;
    color: #ffffff;
    padding: 1.2rem 1.8rem;
    border-bottom: 4px solid #e63946;
    margin: -1rem -1rem 1.5rem -1rem;
  }
  .page-header h1 { margin: 0; font-size: 1.9rem; font-weight: 700; letter-spacing: -0.5px; }
  .page-header p  { margin: 0.25rem 0 0; font-size: 0.85rem; color: #aaaacc; }

  /* ── Section label (538-style pill) ── */
  .section-label {
    background: #e63946;
    color: white;
    font-size: 0.65rem;
    font-weight: 700;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    padding: 3px 10px;
    border-radius: 2px;
    display: inline-block;
    margin-bottom: 0.5rem;
  }

  /* ── Metric cards ── */
  .metric-row { display: flex; gap: 0.75rem; margin-bottom: 1.25rem; flex-wrap: wrap; }
  .metric-card {
    background: white;
    border-top: 4px solid #1a1a2e;
    padding: 0.9rem 1.1rem;
    flex: 1;
    min-width: 130px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.08);
  }
  .metric-card .label { font-size: 0.7rem; text-transform: uppercase; letter-spacing: 1px; color: #888; }
  .metric-card .value { font-size: 1.9rem; font-weight: 700; color: #1a1a2e; line-height: 1.1; }
  .metric-card .delta { font-size: 0.78rem; color: #4caf50; }
  .metric-card .delta.neg { color: #e63946; }

  /* ── Tables ── */
  .styled-table-wrapper {
    background: white;
    border: 1px solid #e0e0da;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    overflow-x: auto;
    margin-bottom: 1.5rem;
  }
  .styled-table-wrapper table {
    border-collapse: collapse;
    width: 100%;
    font-size: 0.82rem;
  }
  .styled-table-wrapper thead tr {
    background: #1a1a2e;
    color: white;
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.8px;
  }
  .styled-table-wrapper thead th {
    padding: 9px 12px;
    text-align: right;
    white-space: nowrap;
    border-right: 1px solid #2e2e4e;
  }
  .styled-table-wrapper thead th:first-child,
  .styled-table-wrapper thead th:nth-child(2) { text-align: left; }
  .styled-table-wrapper tbody tr { border-bottom: 1px solid #ebebeb; }
  .styled-table-wrapper tbody tr:hover { background: #f0f4ff; }
  .styled-table-wrapper tbody tr:nth-child(even) { background: #fafaf8; }
  .styled-table-wrapper tbody tr:nth-child(even):hover { background: #f0f4ff; }
  .styled-table-wrapper tbody td {
    padding: 7px 12px;
    text-align: right;
    color: #222;
  }
  .styled-table-wrapper tbody td:first-child { text-align: center; color: #888; font-weight: 500; }
  .styled-table-wrapper tbody td:nth-child(2) { text-align: left; font-weight: 600; color: #1a1a2e; }

  /* heat-map cell shading done via inline style */

  /* ── Tab styling ── */
  [data-testid="stTabs"] [role="tab"] {
    font-size: 0.8rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: #555;
    padding: 6px 16px;
  }
  [data-testid="stTabs"] [aria-selected="true"] {
    color: #e63946 !important;
    border-bottom: 3px solid #e63946 !important;
  }

  /* ── Footer note ── */
  .footnote { font-size: 0.72rem; color: #999; margin-top: -0.5rem; margin-bottom: 1rem; }
</style>
""", unsafe_allow_html=True)

# ── Sample data ──────────────────────────────────────────────────────────────
np.random.seed(42)

TEAMS = [
    "Chelsea", "Manchester City", "Arsenal", "Liverpool", "Manchester United",
    "Tottenham", "Brighton", "West Ham", "Aston Villa", "Everton",
    "Crystal Palace", "Brentford", "Wolves", "Newcastle", "Fulham",
    "Bournemouth", "Nottm Forest", "Burnley", "Luton", "Sheffield Utd",
]

def make_table_data():
    n = len(TEAMS)
    gp = np.random.randint(20, 38, n)
    w  = np.random.randint(5, 25, n)
    d  = np.random.randint(2, 10, n)
    l  = gp - w - d
    l  = np.clip(l, 0, gp)
    pts = w * 3 + d
    gf  = np.round(np.random.uniform(0.8, 2.8, n) * gp).astype(int)
    ga  = np.round(np.random.uniform(0.6, 2.2, n) * gp).astype(int)
    gd  = gf - ga
    xg  = np.round(np.random.uniform(0.7, 2.6, n) * (gp / 38), 2) * 38
    xga = np.round(np.random.uniform(0.6, 2.1, n) * (gp / 38), 2) * 38
    poss = np.round(np.random.uniform(38, 68, n), 1)
    standing = np.argsort(-pts) + 1

    df = pd.DataFrame({
        "Rank":    standing[np.argsort(np.argsort(-pts))],
        "Team":    TEAMS,
        "GP":      gp,
        "W":       w,
        "D":       d,
        "L":       l,
        "GF":      gf,
        "GA":      ga,
        "GD":      gd,
        "Pts":     pts,
        "xG":      np.round(xg, 1),
        "xGA":     np.round(xga, 1),
        "xGD":     np.round(xg - xga, 1),
        "Poss%":   poss,
    }).sort_values("Pts", ascending=False).reset_index(drop=True)
    df["Rank"] = df.index + 1
    return df

def make_attack_data():
    n = len(TEAMS)
    shots   = np.random.randint(8, 20, n)
    sot     = np.round(shots * np.random.uniform(0.28, 0.45, n)).astype(int)
    goals   = np.round(sot * np.random.uniform(0.22, 0.38, n)).astype(int)
    xg      = np.round(np.random.uniform(0.7, 2.5, n), 2)
    npxg    = np.round(xg * np.random.uniform(0.82, 0.95, n), 2)
    xa      = np.round(np.random.uniform(0.3, 1.2, n), 2)
    key_passes = np.random.randint(5, 16, n)
    dribbles   = np.random.randint(4, 15, n)
    df = pd.DataFrame({
        "Team":         TEAMS,
        "Sh/90":        shots,
        "SoT/90":       sot,
        "Goals/90":     np.round(goals / 38, 2),
        "xG/90":        xg,
        "npxG/90":      npxg,
        "xA/90":        xa,
        "Key Passes":   key_passes,
        "Dribbles":     dribbles,
        "G-xG":         np.round(goals - xg * 38, 1),
    })
    return df.sort_values("xG/90", ascending=False).reset_index(drop=True)

def make_defense_data():
    n = len(TEAMS)
    tackles   = np.random.randint(12, 28, n)
    tkl_won   = np.round(tackles * np.random.uniform(0.5, 0.75, n)).astype(int)
    pressures = np.random.randint(90, 220, n)
    blocks    = np.random.randint(6, 18, n)
    interceptions = np.random.randint(8, 22, n)
    clears    = np.random.randint(12, 35, n)
    ga90      = np.round(np.random.uniform(0.7, 2.2, n), 2)
    xga90     = np.round(np.random.uniform(0.65, 2.0, n), 2)
    df = pd.DataFrame({
        "Team":           TEAMS,
        "GA/90":          ga90,
        "xGA/90":         xga90,
        "GA-xGA":         np.round(ga90 - xga90, 2),
        "Tackles":        tackles,
        "Tkl Won":        tkl_won,
        "Tkl%":           np.round(tkl_won / tackles * 100, 1),
        "Pressures":      pressures,
        "Blocks":         blocks,
        "Interceptions":  interceptions,
        "Clearances":     clears,
    })
    return df.sort_values("xGA/90").reset_index(drop=True)

def make_possession_data():
    n = len(TEAMS)
    poss     = np.round(np.random.uniform(38, 68, n), 1)
    pass_att = np.random.randint(350, 750, n)
    pass_cmp = np.round(pass_att * np.random.uniform(0.72, 0.90, n)).astype(int)
    pass_pct = np.round(pass_cmp / pass_att * 100, 1)
    prog_passes = np.random.randint(60, 200, n)
    prog_carries = np.random.randint(40, 160, n)
    touches  = np.random.randint(900, 1600, n)
    df = pd.DataFrame({
        "Team":           TEAMS,
        "Poss%":          poss,
        "Pass Att":       pass_att,
        "Pass Cmp":       pass_cmp,
        "Pass%":          pass_pct,
        "Prog Passes":    prog_passes,
        "Prog Carries":   prog_carries,
        "Touches":        touches,
        "Touch/Pass":     np.round(touches / pass_att, 2),
    })
    return df.sort_values("Poss%", ascending=False).reset_index(drop=True)

def make_advanced_data():
    n = len(TEAMS)
    ppda     = np.round(np.random.uniform(6, 14, n), 2)
    obppda   = np.round(np.random.uniform(8, 18, n), 2)
    deep     = np.random.randint(6, 24, n)
    deep_all = np.random.randint(5, 20, n)
    xpts     = np.round(np.random.uniform(20, 80, n), 1)
    pts      = np.random.randint(18, 82, n)
    df = pd.DataFrame({
        "Team":        TEAMS,
        "PPDA":        ppda,
        "Opp PPDA":    obppda,
        "Deep":        deep,
        "Deep Allowed":deep_all,
        "xPts":        xpts,
        "Actual Pts":  pts,
        "Pts-xPts":    np.round(pts - xpts, 1),
        "Luck Index":  np.round((pts - xpts) / xpts * 100, 1),
    })
    return df.sort_values("xPts", ascending=False).reset_index(drop=True)

# ── Colour helpers ────────────────────────────────────────────────────────────
def heatmap_bg(val, vmin, vmax, palette="blue", invert=False):
    if pd.isna(val):
        return ""
    ratio = (val - vmin) / (vmax - vmin + 1e-9)
    if invert:
        ratio = 1 - ratio
    ratio = np.clip(ratio, 0, 1)
    if palette == "red":
        r = int(255 * (0.95 - 0.55 * ratio))
        g = int(255 * (0.95 - 0.70 * ratio))
        b = int(255 * (0.95 - 0.70 * ratio))
    elif palette == "green":
        r = int(255 * (0.95 - 0.70 * ratio))
        g = int(255 * (0.75 + 0.10 * ratio))
        b = int(255 * (0.95 - 0.70 * ratio))
    else:  # blue
        r = int(255 * (0.95 - 0.65 * ratio))
        g = int(255 * (0.95 - 0.55 * ratio))
        b = int(255 * (0.95 - 0.10 * ratio))
    text = "white" if ratio > 0.65 else "#1a1a2e"
    return f"background-color:rgb({r},{g},{b});color:{text};"

def rank_badge(rank):
    if rank <= 4:
        color = "#2196f3"
    elif rank <= 6:
        color = "#ff9800"
    elif rank >= 18:
        color = "#e63946"
    else:
        color = "#666"
    return f'<span style="background:{color};color:white;border-radius:3px;padding:1px 6px;font-size:0.75rem;font-weight:700;">{rank}</span>'

def render_table(df, heatmap_cols=None, invert_cols=None, palette_map=None, show_rank=True):
    """Render a styled HTML table."""
    heatmap_cols  = heatmap_cols  or []
    invert_cols   = invert_cols   or []
    palette_map   = palette_map   or {}

    # pre-compute min/max
    col_stats = {}
    for col in heatmap_cols:
        if col in df.columns:
            col_stats[col] = (df[col].min(), df[col].max())

    rows = []
    for i, row in df.iterrows():
        cells = []
        for j, col in enumerate(df.columns):
            val = row[col]
            style = ""

            if col == "Rank" and show_rank:
                cell = rank_badge(int(val))
            elif col == "Team":
                cell = f'<strong>{val}</strong>'
            else:
                if col in heatmap_cols and col in col_stats:
                    vmin, vmax = col_stats[col]
                    pal = palette_map.get(col, "blue")
                    inv = col in invert_cols
                    style = heatmap_bg(val, vmin, vmax, pal, inv)

                # format numbers
                if isinstance(val, float):
                    cell = f"{val:+.1f}" if col in ("GD", "xGD", "G-xG", "GA-xGA", "Pts-xPts", "Luck Index") else f"{val:.2f}" if abs(val) < 10 else f"{val:.1f}"
                else:
                    cell = str(val)

            cells.append(f'<td style="{style}">{cell}</td>')

        rows.append("<tr>" + "".join(cells) + "</tr>")

    headers = "".join(f"<th>{c}</th>" for c in df.columns)
    table_html = f"""
    <div class="styled-table-wrapper">
      <table>
        <thead><tr>{headers}</tr></thead>
        <tbody>{"".join(rows)}</tbody>
      </table>
    </div>
    """
    st.markdown(table_html, unsafe_allow_html=True)


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚽ WSL Stats Hub")
    st.markdown("---")
    season = st.selectbox("Season", ["2023/24", "2022/23", "2021/22"], index=0)
    competition = st.selectbox("Competition", ["WSL", "FA Cup", "Champions League"], index=0)
    st.markdown("---")
    st.markdown("**Per-90 or Totals?**")
    stat_mode = st.radio("", ["Per 90", "Season Totals"], horizontal=True)
    st.markdown("---")
    teams_filter = st.multiselect("Filter Teams", TEAMS, default=[])
    st.markdown("---")
    st.markdown('<p style="font-size:0.7rem;color:#666;">Data: FBRef / StatsBomb<br>Design: FiveThirtyEight-inspired</p>', unsafe_allow_html=True)


# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="page-header">
  <h1>WSL Stats Hub</h1>
  <p>{season} &nbsp;·&nbsp; {competition} &nbsp;·&nbsp; Matchweek 28 of 38</p>
</div>
""", unsafe_allow_html=True)


# ── Load & filter data ────────────────────────────────────────────────────────
df_table   = make_table_data()
df_attack  = make_attack_data()
df_defense = make_defense_data()
df_poss    = make_possession_data()
df_adv     = make_advanced_data()

if teams_filter:
    df_table   = df_table[df_table["Team"].isin(teams_filter)].reset_index(drop=True)
    df_attack  = df_attack[df_attack["Team"].isin(teams_filter)].reset_index(drop=True)
    df_defense = df_defense[df_defense["Team"].isin(teams_filter)].reset_index(drop=True)
    df_poss    = df_poss[df_poss["Team"].isin(teams_filter)].reset_index(drop=True)
    df_adv     = df_adv[df_adv["Team"].isin(teams_filter)].reset_index(drop=True)


# ── Summary metric cards ──────────────────────────────────────────────────────
top = df_table.iloc[0]
best_xg  = df_attack.sort_values("xG/90", ascending=False).iloc[0]
best_def = df_defense.sort_values("xGA/90").iloc[0]
most_poss = df_poss.sort_values("Poss%", ascending=False).iloc[0]

st.markdown("""
<div class="metric-row">
  <div class="metric-card">
    <div class="label">League Leader</div>
    <div class="value" style="font-size:1.3rem;">{team}</div>
    <div class="delta">{pts} pts &nbsp;·&nbsp; {gd:+d} GD</div>
  </div>
  <div class="metric-card">
    <div class="label">Best Attack (xG/90)</div>
    <div class="value" style="font-size:1.3rem;">{atk}</div>
    <div class="delta">{xg} xG per 90</div>
  </div>
  <div class="metric-card">
    <div class="label">Best Defence (xGA/90)</div>
    <div class="value" style="font-size:1.3rem;">{def_}</div>
    <div class="delta">{xga} xGA per 90</div>
  </div>
  <div class="metric-card">
    <div class="label">Possession King</div>
    <div class="value" style="font-size:1.3rem;">{poss_team}</div>
    <div class="delta">{poss}% avg possession</div>
  </div>
</div>
""".format(
    team=top["Team"], pts=top["Pts"], gd=int(top["GD"]),
    atk=best_xg["Team"], xg=best_xg["xG/90"],
    def_=best_def["Team"], xga=best_def["xGA/90"],
    poss_team=most_poss["Team"], poss=most_poss["Poss%"],
), unsafe_allow_html=True)


# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📋  Standings", "⚡  Attack", "🛡  Defence", "🎯  Possession", "📐  Advanced"
])

# ── TAB 1 — Standings ─────────────────────────────────────────────────────────
with tab1:
    st.markdown('<span class="section-label">League Table</span>', unsafe_allow_html=True)

    col_sort = st.selectbox("Sort by", ["Pts", "GD", "GF", "xGD", "xG", "Poss%"], key="sort_table")
    asc = col_sort in ("GA", "xGA")
    df_sorted = df_table.sort_values(col_sort, ascending=asc).reset_index(drop=True)
    df_sorted["Rank"] = df_sorted.index + 1

    render_table(
        df_sorted,
        heatmap_cols=["Pts", "GF", "GA", "GD", "xG", "xGA", "xGD"],
        invert_cols=["GA", "xGA"],
        palette_map={"Pts": "blue", "GF": "green", "GA": "red",
                     "GD": "blue", "xG": "green", "xGA": "red", "xGD": "blue"},
    )
    st.markdown('<p class="footnote">xG = expected goals. xGD = xG differential. Poss% = average possession.</p>', unsafe_allow_html=True)

# ── TAB 2 — Attack ────────────────────────────────────────────────────────────
with tab2:
    st.markdown('<span class="section-label">Attacking Statistics</span>', unsafe_allow_html=True)

    col_sort2 = st.selectbox("Sort by", ["xG/90", "Goals/90", "npxG/90", "xA/90", "Sh/90", "SoT/90"], key="sort_atk")
    df_atk_s = df_attack.sort_values(col_sort2, ascending=False).reset_index(drop=True)
    df_atk_s.insert(0, "Rank", df_atk_s.index + 1)

    render_table(
        df_atk_s,
        heatmap_cols=["xG/90", "Goals/90", "npxG/90", "xA/90", "SoT/90", "Sh/90"],
        palette_map={"xG/90": "blue", "Goals/90": "green", "npxG/90": "blue",
                     "xA/90": "green", "SoT/90": "green", "Sh/90": "blue"},
    )
    st.markdown('<p class="footnote">npxG = non-penalty expected goals. xA = expected assists. G-xG = goals vs expected (overperformance).</p>', unsafe_allow_html=True)

# ── TAB 3 — Defence ───────────────────────────────────────────────────────────
with tab3:
    st.markdown('<span class="section-label">Defensive Statistics</span>', unsafe_allow_html=True)

    col_sort3 = st.selectbox("Sort by", ["xGA/90", "GA/90", "Tkl%", "Pressures", "Interceptions"], key="sort_def")
    asc3 = col_sort3 in ("xGA/90", "GA/90", "GA-xGA")
    df_def_s = df_defense.sort_values(col_sort3, ascending=asc3).reset_index(drop=True)
    df_def_s.insert(0, "Rank", df_def_s.index + 1)

    render_table(
        df_def_s,
        heatmap_cols=["GA/90", "xGA/90", "Tkl%", "Pressures", "Blocks", "Interceptions"],
        invert_cols=["GA/90", "xGA/90"],
        palette_map={"GA/90": "red", "xGA/90": "red", "Tkl%": "green",
                     "Pressures": "blue", "Blocks": "blue", "Interceptions": "blue"},
    )
    st.markdown('<p class="footnote">PPDA (passes allowed per defensive action) used in Advanced tab. Lower GA/90 and xGA/90 = better.</p>', unsafe_allow_html=True)

# ── TAB 4 — Possession ────────────────────────────────────────────────────────
with tab4:
    st.markdown('<span class="section-label">Possession & Passing</span>', unsafe_allow_html=True)

    col_sort4 = st.selectbox("Sort by", ["Poss%", "Pass%", "Prog Passes", "Prog Carries", "Touches"], key="sort_poss")
    df_poss_s = df_poss.sort_values(col_sort4, ascending=False).reset_index(drop=True)
    df_poss_s.insert(0, "Rank", df_poss_s.index + 1)

    render_table(
        df_poss_s,
        heatmap_cols=["Poss%", "Pass%", "Prog Passes", "Prog Carries", "Touches"],
        palette_map={"Poss%": "blue", "Pass%": "green",
                     "Prog Passes": "blue", "Prog Carries": "blue", "Touches": "blue"},
    )
    st.markdown('<p class="footnote">Prog = progressive (advances ball ≥10 yards toward goal). Touch/Pass = carrying intensity.</p>', unsafe_allow_html=True)

# ── TAB 5 — Advanced ──────────────────────────────────────────────────────────
with tab5:
    st.markdown('<span class="section-label">Advanced Metrics</span>', unsafe_allow_html=True)

    col_sort5 = st.selectbox("Sort by", ["xPts", "Actual Pts", "PPDA", "Opp PPDA", "Luck Index"], key="sort_adv")
    asc5 = col_sort5 in ("PPDA",)
    df_adv_s = df_adv.sort_values(col_sort5, ascending=asc5).reset_index(drop=True)
    df_adv_s.insert(0, "Rank", df_adv_s.index + 1)

    render_table(
        df_adv_s,
        heatmap_cols=["xPts", "Actual Pts", "PPDA", "Opp PPDA", "Luck Index"],
        invert_cols=["PPDA"],
        palette_map={"xPts": "blue", "Actual Pts": "green", "PPDA": "green",
                     "Opp PPDA": "red", "Luck Index": "blue"},
    )

    st.markdown("---")
    st.markdown('<span class="section-label">Glossary</span>', unsafe_allow_html=True)
    with st.expander("What do these metrics mean?"):
        st.markdown("""
| Metric | Definition |
|--------|-----------|
| **PPDA** | Passes Per Defensive Action — lower = higher pressing intensity |
| **Opp PPDA** | Opposition PPDA — how much the opponent is allowed to pass before pressure |
| **Deep** | Completed passes into the opposition's 18-yard box |
| **xPts** | Expected points based on xG for and against |
| **Pts-xPts** | Actual points minus expected — positive = overperforming |
| **Luck Index** | (Pts-xPts)/xPts × 100 — how much variance has helped/hurt |
        """)
