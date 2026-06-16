import streamlit as st
import pandas as pd
import numpy as np
import glob
import os

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="WSL Stats Hub",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  html, body, [class*="css"] {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  }
  [data-testid="stSidebar"] { background-color: #1a1a2e; border-right: 3px solid #e63946; }
  [data-testid="stSidebar"] * { color: #f0f0f0 !important; }
  .main { background-color: #f5f5f0; }
  .page-header {
    background: #1a1a2e; color: #fff;
    padding: 1.2rem 1.8rem;
    border-bottom: 4px solid #e63946;
    margin: -1rem -1rem 1.5rem -1rem;
  }
  .page-header h1 { margin: 0; font-size: 1.9rem; font-weight: 700; }
  .page-header p  { margin: 0.25rem 0 0; font-size: 0.85rem; color: #aaaacc; }
  .section-label {
    background: #e63946; color: white;
    font-size: 0.65rem; font-weight: 700; letter-spacing: 1.5px;
    text-transform: uppercase; padding: 3px 10px; border-radius: 2px;
    display: inline-block; margin-bottom: 0.5rem;
  }
  .metric-row { display: flex; gap: 0.75rem; margin-bottom: 1.25rem; flex-wrap: wrap; }
  .metric-card {
    background: white; border-top: 4px solid #1a1a2e;
    padding: 0.9rem 1.1rem; flex: 1; min-width: 130px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.08);
  }
  .metric-card .label { font-size: 0.7rem; text-transform: uppercase; letter-spacing: 1px; color: #888; }
  .metric-card .value { font-size: 1.4rem; font-weight: 700; color: #1a1a2e; line-height: 1.2; }
  .metric-card .sub   { font-size: 0.78rem; color: #4caf50; }
  .styled-table-wrapper {
    background: white; border: 1px solid #e0e0da;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    overflow-x: auto; margin-bottom: 1.5rem;
  }
  .styled-table-wrapper table { border-collapse: collapse; width: 100%; font-size: 0.82rem; }
  .styled-table-wrapper thead tr { background: #1a1a2e; color: white; font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.8px; }
  .styled-table-wrapper thead th { padding: 9px 12px; text-align: right; white-space: nowrap; border-right: 1px solid #2e2e4e; }
  .styled-table-wrapper thead th:first-child,
  .styled-table-wrapper thead th:nth-child(2) { text-align: left; }
  .styled-table-wrapper tbody tr { border-bottom: 1px solid #ebebeb; }
  .styled-table-wrapper tbody tr:hover { background: #f0f4ff !important; }
  .styled-table-wrapper tbody tr:nth-child(even) { background: #fafaf8; }
  .styled-table-wrapper tbody td { padding: 7px 12px; text-align: right; color: #222; }
  .styled-table-wrapper tbody td:first-child { text-align: center; color: #888; font-weight: 600; }
  .styled-table-wrapper tbody td:nth-child(2) { text-align: left; font-weight: 600; color: #1a1a2e; }
  [data-testid="stTabs"] [role="tab"] { font-size: 0.8rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }
  [data-testid="stTabs"] [aria-selected="true"] { color: #e63946 !important; border-bottom: 3px solid #e63946 !important; }
  .footnote { font-size: 0.72rem; color: #999; margin-top: -0.5rem; margin-bottom: 1rem; }
</style>
""", unsafe_allow_html=True)

# ── Data loading ──────────────────────────────────────────────────────────────
XG_DIR      = os.path.join(os.path.dirname(__file__), "WSL", "xgCSV")
MATCHES_CSV = os.path.join(os.path.dirname(__file__), "WSL Matches.csv")

@st.cache_data
def load_shots():
    files = glob.glob(os.path.join(XG_DIR, "*.csv"))
    dfs = []
    for f in files:
        try:
            df = pd.read_csv(f, index_col=0)
            dfs.append(df)
        except Exception:
            pass
    if not dfs:
        return pd.DataFrame()
    shots = pd.concat(dfs, ignore_index=True)
    shots["Date"] = pd.to_datetime(shots["Date"], utc=True, errors="coerce")
    shots["xG"]   = pd.to_numeric(shots["xG"], errors="coerce")
    shots["isGoal"] = shots["isGoal"].astype(str).str.upper().isin(["TRUE", "1", "YES"])
    return shots

@st.cache_data
def load_matches():
    df = pd.read_csv(MATCHES_CSV, encoding="utf-8-sig")
    df.columns = df.columns.str.strip()
    return df

shots   = load_shots()
matches = load_matches()

# ── Derive team list ──────────────────────────────────────────────────────────
ALL_TEAMS = sorted(shots["HomeTeam"].dropna().unique().tolist()) if not shots.empty else []

# ── Build league-level stats from shots ──────────────────────────────────────
@st.cache_data
def build_team_stats(shots_df):
    if shots_df.empty:
        return pd.DataFrame()

    home_teams = shots_df["HomeTeam"].dropna().unique()
    away_teams = shots_df["AwayTeam"].dropna().unique()
    teams = sorted(set(home_teams) | set(away_teams))

    rows = []
    for team in teams:
        team_shots = shots_df[shots_df["TeamId"] == team]
        opp_shots  = shots_df[(shots_df["HomeTeam"] == team) | (shots_df["AwayTeam"] == team)]
        opp_shots  = opp_shots[opp_shots["TeamId"] != team]

        xg    = team_shots["xG"].sum()
        xga   = opp_shots["xG"].sum()
        gf    = int(team_shots["isGoal"].sum())
        ga    = int(opp_shots["isGoal"].sum())

        # matches played = unique (HomeTeam+AwayTeam+Date) combos involving team
        m = shots_df[(shots_df["HomeTeam"] == team) | (shots_df["AwayTeam"] == team)]
        gp = m.groupby(["HomeTeam", "AwayTeam", shots_df.loc[m.index, "Date"].dt.date]).ngroups

        shots_for  = len(team_shots)
        shots_ag   = len(opp_shots)
        big_ch     = int(team_shots["isBigChance"].astype(str).str.upper().isin(["YES", "TRUE", "1"]).sum())

        rows.append({
            "Team":       team,
            "GP":         gp,
            "GF":         gf,
            "GA":         ga,
            "GD":         gf - ga,
            "xG":         round(xg, 1),
            "xGA":        round(xga, 1),
            "xGD":        round(xg - xga, 1),
            "Sh":         shots_for,
            "Sh Ag":      shots_ag,
            "Big Ch":     big_ch,
            "xG/90":      round(xg / max(gp, 1), 2),
            "xGA/90":     round(xga / max(gp, 1), 2),
            "G-xG":       round(gf - xg, 1),
            "GA-xGA":     round(ga - xga, 1),
        })

    df = pd.DataFrame(rows)

    # reconstruct W/D/L from match CSV if available
    return df.sort_values("xGD", ascending=False).reset_index(drop=True)

@st.cache_data
def build_match_results(matches_df):
    if matches_df.empty:
        return pd.DataFrame()
    cols_needed = {
        "matchInfo/date":                       "Date",
        "matchInfo/contestant/0/name":          "Home",
        "matchInfo/contestant/1/name":          "Away",
        "liveData/matchDetails/scores/ft/home": "HG",
        "liveData/matchDetails/scores/ft/away": "AG",
        "matchInfo/week":                       "Week",
    }
    present = {k: v for k, v in cols_needed.items() if k in matches_df.columns}
    res = matches_df[list(present.keys())].rename(columns=present).copy()
    res["Date"] = pd.to_datetime(res["Date"], utc=True, errors="coerce").dt.date
    res["HG"]   = pd.to_numeric(res.get("HG", np.nan), errors="coerce")
    res["AG"]   = pd.to_numeric(res.get("AG", np.nan), errors="coerce")
    res = res.dropna(subset=["HG", "AG"])
    res["HG"]   = res["HG"].astype(int)
    res["AG"]   = res["AG"].astype(int)
    res["Score"]= res["HG"].astype(str) + " – " + res["AG"].astype(str)
    res["Result"] = res.apply(
        lambda r: "H" if r["HG"] > r["AG"] else ("A" if r["AG"] > r["HG"] else "D"), axis=1
    )
    return res.sort_values("Date", ascending=False).reset_index(drop=True)

@st.cache_data
def build_standings(match_results):
    if match_results.empty:
        return pd.DataFrame()
    rows = []
    teams = pd.concat([match_results["Home"], match_results["Away"]]).unique()
    for team in teams:
        home = match_results[match_results["Home"] == team]
        away = match_results[match_results["Away"] == team]
        gp = len(home) + len(away)
        w  = (home["Result"] == "H").sum() + (away["Result"] == "A").sum()
        d  = (home["Result"] == "D").sum() + (away["Result"] == "D").sum()
        l  = gp - w - d
        gf = home["HG"].sum() + away["AG"].sum()
        ga = home["AG"].sum() + away["HG"].sum()
        pts = w * 3 + d
        rows.append({"Team": team, "GP": gp, "W": int(w), "D": int(d), "L": int(l),
                     "GF": int(gf), "GA": int(ga), "GD": int(gf - ga), "Pts": int(pts)})
    df = pd.DataFrame(rows).sort_values(["Pts", "GD"], ascending=False).reset_index(drop=True)
    df.insert(0, "Rank", df.index + 1)
    return df

team_stats   = build_team_stats(shots)
match_results = build_match_results(matches)
standings    = build_standings(match_results)

# Merge standings + xG stats
if not standings.empty and not team_stats.empty:
    standings = standings.merge(
        team_stats[["Team", "xG", "xGA", "xGD", "xG/90", "xGA/90", "G-xG", "GA-xGA", "Sh", "Big Ch"]],
        on="Team", how="left"
    )

# ── Helpers ───────────────────────────────────────────────────────────────────
def heatmap_style(val, vmin, vmax, palette="blue", invert=False):
    if pd.isna(val):
        return ""
    ratio = np.clip((val - vmin) / (vmax - vmin + 1e-9), 0, 1)
    if invert:
        ratio = 1 - ratio
    if palette == "red":
        r, g, b = int(255*(0.95-0.55*ratio)), int(255*(0.95-0.70*ratio)), int(255*(0.95-0.70*ratio))
    elif palette == "green":
        r, g, b = int(255*(0.95-0.70*ratio)), int(255*(0.75+0.10*ratio)), int(255*(0.95-0.70*ratio))
    else:
        r, g, b = int(255*(0.95-0.65*ratio)), int(255*(0.95-0.55*ratio)), int(255*(0.95-0.10*ratio))
    text = "white" if ratio > 0.65 else "#1a1a2e"
    return f"background-color:rgb({r},{g},{b});color:{text};"

def rank_badge(rank):
    color = "#2196f3" if rank <= 4 else "#ff9800" if rank <= 6 else "#e63946" if rank >= len(standings)-1 else "#555"
    return f'<span style="background:{color};color:white;border-radius:3px;padding:1px 7px;font-size:0.75rem;font-weight:700;">{rank}</span>'

def fmt(val, col):
    if pd.isna(val):
        return "—"
    sign_cols = {"GD", "xGD", "G-xG", "GA-xGA", "xPts diff"}
    if col in sign_cols:
        return f"{val:+.1f}" if isinstance(val, float) else f"{int(val):+d}"
    if isinstance(val, float):
        return f"{val:.2f}" if abs(val) < 10 else f"{val:.1f}"
    return str(val)

def render_table(df, heatmap_cols=None, invert_cols=None, palette_map=None):
    heatmap_cols = heatmap_cols or []
    invert_cols  = invert_cols  or []
    palette_map  = palette_map  or {}
    stats = {c: (df[c].min(), df[c].max()) for c in heatmap_cols if c in df.columns}

    rows_html = []
    for _, row in df.iterrows():
        cells = []
        for col in df.columns:
            val = row[col]
            style = ""
            if col == "Rank":
                cell = rank_badge(int(val))
            elif col == "Team":
                cell = f"<strong>{val}</strong>"
            else:
                if col in stats:
                    vmin, vmax = stats[col]
                    style = heatmap_style(val, vmin, vmax, palette_map.get(col, "blue"), col in invert_cols)
                cell = fmt(val, col)
            cells.append(f'<td style="{style}">{cell}</td>')
        rows_html.append("<tr>" + "".join(cells) + "</tr>")

    headers = "".join(f"<th>{c}</th>" for c in df.columns)
    st.markdown(f"""
    <div class="styled-table-wrapper">
      <table>
        <thead><tr>{headers}</tr></thead>
        <tbody>{"".join(rows_html)}</tbody>
      </table>
    </div>""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚽ WSL Stats Hub")
    st.markdown("**2025/26 Barclays WSL**")
    st.markdown("---")
    team_filter = st.multiselect("Filter Teams", ALL_TEAMS)
    st.markdown("---")
    if not shots.empty:
        min_d = shots["Date"].dt.date.min()
        max_d = shots["Date"].dt.date.max()
        date_range = st.date_input("Date range", value=(min_d, max_d), min_value=min_d, max_value=max_d)
    else:
        date_range = None
    st.markdown("---")
    st.markdown('<p style="font-size:0.7rem;color:#777;">Data: Opta / StatsBomb<br>Design: FBRef × FiveThirtyEight</p>', unsafe_allow_html=True)

# ── Filter shots by date ──────────────────────────────────────────────────────
shots_f = shots.copy()
if date_range and len(date_range) == 2:
    d0, d1 = pd.Timestamp(date_range[0], tz="UTC"), pd.Timestamp(date_range[1], tz="UTC")
    shots_f = shots_f[(shots_f["Date"] >= d0) & (shots_f["Date"] <= d1)]
if team_filter:
    shots_f = shots_f[(shots_f["HomeTeam"].isin(team_filter)) | (shots_f["AwayTeam"].isin(team_filter))]

# ── Header ────────────────────────────────────────────────────────────────────
n_matches = match_results["Home"].count() if not match_results.empty else 0
gp_done   = standings["GP"].max() if not standings.empty else "—"
st.markdown(f"""
<div class="page-header">
  <h1>WSL Stats Hub</h1>
  <p>2025/26 Barclays Women's Super League &nbsp;·&nbsp; {n_matches} matches · up to GW {gp_done}</p>
</div>
""", unsafe_allow_html=True)

# ── Summary cards ─────────────────────────────────────────────────────────────
if not standings.empty:
    leader = standings.iloc[0]
    top_atk = team_stats.sort_values("xG/90", ascending=False).iloc[0] if not team_stats.empty else None
    top_def = team_stats.sort_values("xGA/90").iloc[0] if not team_stats.empty else None
    total_goals = int(shots["isGoal"].sum()) if not shots.empty else 0
    total_xg    = round(shots["xG"].sum(), 1) if not shots.empty else 0

    atk_val  = f"{top_atk['xG/90']} xG/90" if top_atk is not None else "—"
    def_val  = f"{top_def['xGA/90']} xGA/90" if top_def is not None else "—"

    st.markdown(f"""
    <div class="metric-row">
      <div class="metric-card">
        <div class="label">League Leader</div>
        <div class="value">{leader['Team']}</div>
        <div class="sub">{leader['Pts']} pts · {leader['GD']:+d} GD</div>
      </div>
      <div class="metric-card">
        <div class="label">Best Attack</div>
        <div class="value">{top_atk['Team'] if top_atk is not None else '—'}</div>
        <div class="sub">{atk_val}</div>
      </div>
      <div class="metric-card">
        <div class="label">Best Defence</div>
        <div class="value">{top_def['Team'] if top_def is not None else '—'}</div>
        <div class="sub">{def_val}</div>
      </div>
      <div class="metric-card">
        <div class="label">Total Goals</div>
        <div class="value">{total_goals}</div>
        <div class="sub">{total_xg} total xG</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📋  Standings", "⚡  xG Table", "🎯  Shot Map", "📅  Results", "🔍  Team Deep Dive"
])

# ── TAB 1 — Standings ─────────────────────────────────────────────────────────
with tab1:
    st.markdown('<span class="section-label">League Standings</span>', unsafe_allow_html=True)
    if not standings.empty:
        sort_col = st.selectbox("Sort by", ["Pts", "GD", "GF", "xGD", "xG", "xGA"], key="s1")
        asc = sort_col in ("xGA", "GA")
        df_s = standings.sort_values(sort_col, ascending=asc).reset_index(drop=True)
        df_s["Rank"] = df_s.index + 1
        show_cols = ["Rank", "Team", "GP", "W", "D", "L", "GF", "GA", "GD", "Pts", "xG", "xGA", "xGD", "G-xG"]
        show_cols = [c for c in show_cols if c in df_s.columns]
        render_table(
            df_s[show_cols],
            heatmap_cols=["Pts", "GF", "xG", "xGD", "G-xG"],
            invert_cols=["xGA", "GA"],
            palette_map={"Pts": "blue", "GF": "green", "xG": "green", "xGD": "blue", "G-xG": "green"},
        )
        st.markdown('<p class="footnote">xG = expected goals. G-xG = goals scored minus xG (positive = overperforming).</p>', unsafe_allow_html=True)
    else:
        st.info("No standings data available.")

# ── TAB 2 — xG Table ──────────────────────────────────────────────────────────
with tab2:
    st.markdown('<span class="section-label">xG Performance Table</span>', unsafe_allow_html=True)
    if not team_stats.empty:
        sort_xg = st.selectbox("Sort by", ["xGD", "xG", "xGA", "xG/90", "xGA/90", "G-xG", "GA-xGA", "Sh", "Big Ch"], key="s2")
        asc2 = sort_xg in ("xGA", "xGA/90", "GA-xGA")
        df_x = team_stats.sort_values(sort_xg, ascending=asc2).reset_index(drop=True)
        df_x.insert(0, "Rank", df_x.index + 1)
        show_x = ["Rank", "Team", "GP", "xG", "xGA", "xGD", "xG/90", "xGA/90", "G-xG", "GA-xGA", "Sh", "Big Ch"]
        show_x = [c for c in show_x if c in df_x.columns]
        render_table(
            df_x[show_x],
            heatmap_cols=["xG", "xGD", "xG/90", "Sh", "Big Ch", "G-xG"],
            invert_cols=["xGA", "xGA/90", "GA-xGA"],
            palette_map={"xG": "green", "xGD": "blue", "xG/90": "green",
                         "Sh": "blue", "Big Ch": "green", "G-xG": "green"},
        )
        st.markdown('<p class="footnote">Big Ch = big chances. GA-xGA = goals conceded minus xGA (positive = conceding more than expected).</p>', unsafe_allow_html=True)
    else:
        st.info("No xG data available.")

# ── TAB 3 — Shot Map ──────────────────────────────────────────────────────────
with tab3:
    st.markdown('<span class="section-label">Shot Distribution</span>', unsafe_allow_html=True)
    if not shots_f.empty:
        col_a, col_b = st.columns([1, 2])
        with col_a:
            selected_team = st.selectbox("Team", ["All"] + ALL_TEAMS, key="sm_team")
            body_part = st.multiselect("Body part", shots_f["Bodypart"].dropna().unique().tolist(),
                                       default=shots_f["Bodypart"].dropna().unique().tolist(), key="sm_bp")
            play_type = st.multiselect("Play type", shots_f["Type_of_play"].dropna().unique().tolist(),
                                       default=shots_f["Type_of_play"].dropna().unique().tolist(), key="sm_tp")

        sf = shots_f.copy()
        if selected_team != "All":
            sf = sf[sf["TeamId"] == selected_team]
        if body_part:
            sf = sf[sf["Bodypart"].isin(body_part)]
        if play_type:
            sf = sf[sf["Type_of_play"].isin(play_type)]

        with col_b:
            # Summary stats
            goals  = int(sf["isGoal"].sum())
            total  = len(sf)
            xg_tot = round(sf["xG"].sum(), 2)
            conv   = round(goals / total * 100, 1) if total > 0 else 0
            xg_avg = round(sf["xG"].mean(), 3) if total > 0 else 0
            st.markdown(f"""
            <div class="metric-row">
              <div class="metric-card"><div class="label">Shots</div><div class="value">{total}</div></div>
              <div class="metric-card"><div class="label">Goals</div><div class="value">{goals}</div></div>
              <div class="metric-card"><div class="label">Total xG</div><div class="value">{xg_tot}</div></div>
              <div class="metric-card"><div class="label">Conversion</div><div class="value">{conv}%</div></div>
              <div class="metric-card"><div class="label">Avg xG/shot</div><div class="value">{xg_avg}</div></div>
            </div>
            """, unsafe_allow_html=True)

        # xG distribution by type
        st.markdown('<span class="section-label">xG by Play Type</span>', unsafe_allow_html=True)
        by_type = sf.groupby("Type_of_play").agg(
            Shots=("xG", "count"), Goals=("isGoal", "sum"), xG=("xG", "sum")
        ).reset_index()
        by_type["Conv%"]   = (by_type["Goals"] / by_type["Shots"] * 100).round(1)
        by_type["xG/Shot"] = (by_type["xG"] / by_type["Shots"]).round(3)
        by_type["G-xG"]    = (by_type["Goals"] - by_type["xG"]).round(2)
        by_type["xG"]      = by_type["xG"].round(2)
        by_type = by_type.sort_values("xG", ascending=False).reset_index(drop=True)
        render_table(by_type, heatmap_cols=["xG", "Shots", "Conv%"], palette_map={"xG": "green", "Shots": "blue", "Conv%": "green"})

        st.markdown('<span class="section-label">xG by Body Part</span>', unsafe_allow_html=True)
        by_bp = sf.groupby("Bodypart").agg(
            Shots=("xG", "count"), Goals=("isGoal", "sum"), xG=("xG", "sum")
        ).reset_index()
        by_bp["Conv%"]   = (by_bp["Goals"] / by_bp["Shots"] * 100).round(1)
        by_bp["xG/Shot"] = (by_bp["xG"] / by_bp["Shots"]).round(3)
        by_bp["xG"]      = by_bp["xG"].round(2)
        by_bp = by_bp.sort_values("xG", ascending=False).reset_index(drop=True)
        render_table(by_bp, heatmap_cols=["xG", "Shots", "Conv%"], palette_map={"xG": "green", "Shots": "blue", "Conv%": "green"})
    else:
        st.info("No shot data for selected filters.")

# ── TAB 4 — Results ───────────────────────────────────────────────────────────
with tab4:
    st.markdown('<span class="section-label">Match Results</span>', unsafe_allow_html=True)
    if not match_results.empty:
        mr = match_results.copy()
        if team_filter:
            mr = mr[mr["Home"].isin(team_filter) | mr["Away"].isin(team_filter)]

        show_mr = mr[["Date", "Week", "Home", "Score", "Away", "Result"]].copy() if "Week" in mr.columns else mr[["Date", "Home", "Score", "Away", "Result"]].copy()

        # colour Result column inline
        def result_badge(r):
            color = {"H": "#2196f3", "A": "#e63946", "D": "#888"}.get(r, "#888")
            label = {"H": "H", "A": "A", "D": "D"}.get(r, r)
            return f'<span style="background:{color};color:white;border-radius:3px;padding:1px 8px;font-size:0.75rem;font-weight:700;">{label}</span>'

        rows_html = []
        for _, row in show_mr.iterrows():
            cells = []
            for col in show_mr.columns:
                val = row[col]
                if col == "Result":
                    cells.append(f"<td>{result_badge(val)}</td>")
                elif col == "Score":
                    cells.append(f'<td style="font-weight:700;text-align:center;">{val}</td>')
                else:
                    cells.append(f"<td>{val}</td>")
            rows_html.append("<tr>" + "".join(cells) + "</tr>")

        headers = "".join(f"<th>{c}</th>" for c in show_mr.columns)
        st.markdown(f"""
        <div class="styled-table-wrapper">
          <table><thead><tr>{headers}</tr></thead>
          <tbody>{"".join(rows_html)}</tbody></table>
        </div>""", unsafe_allow_html=True)
    else:
        st.info("No results data available.")

# ── TAB 5 — Team Deep Dive ────────────────────────────────────────────────────
with tab5:
    st.markdown('<span class="section-label">Team Deep Dive</span>', unsafe_allow_html=True)
    if not shots.empty:
        team_sel = st.selectbox("Select team", ALL_TEAMS, key="dd_team")

        t_shots = shots[shots["TeamId"] == team_sel]
        o_shots = shots[(shots["HomeTeam"] == team_sel) | (shots["AwayTeam"] == team_sel)]
        o_shots = o_shots[o_shots["TeamId"] != team_sel]

        c1, c2 = st.columns(2)
        with c1:
            st.markdown('<span class="section-label">Attacking</span>', unsafe_allow_html=True)
            att_rows = [
                {"Metric": "Shots", "Value": len(t_shots)},
                {"Metric": "Goals", "Value": int(t_shots["isGoal"].sum())},
                {"Metric": "xG",    "Value": round(t_shots["xG"].sum(), 2)},
                {"Metric": "xG/Shot","Value": round(t_shots["xG"].mean(), 3)},
                {"Metric": "Big Chances", "Value": int(t_shots["isBigChance"].astype(str).str.upper().isin(["YES","TRUE","1"]).sum())},
                {"Metric": "Goals - xG", "Value": round(t_shots["isGoal"].sum() - t_shots["xG"].sum(), 2)},
            ]
            st.dataframe(pd.DataFrame(att_rows), use_container_width=True, hide_index=True)

        with c2:
            st.markdown('<span class="section-label">Defensive</span>', unsafe_allow_html=True)
            def_rows = [
                {"Metric": "Shots Against", "Value": len(o_shots)},
                {"Metric": "Goals Against", "Value": int(o_shots["isGoal"].sum())},
                {"Metric": "xGA",           "Value": round(o_shots["xG"].sum(), 2)},
                {"Metric": "xGA/Shot",      "Value": round(o_shots["xG"].mean(), 3)},
                {"Metric": "Goals - xGA",   "Value": round(o_shots["isGoal"].sum() - o_shots["xG"].sum(), 2)},
            ]
            st.dataframe(pd.DataFrame(def_rows), use_container_width=True, hide_index=True)

        st.markdown('<span class="section-label">Shot breakdown by play type</span>', unsafe_allow_html=True)
        breakdown = t_shots.groupby("Type_of_play").agg(
            Shots=("xG","count"), Goals=("isGoal","sum"), xG=("xG","sum")
        ).reset_index()
        breakdown["Conv%"] = (breakdown["Goals"] / breakdown["Shots"] * 100).round(1)
        breakdown["xG"]    = breakdown["xG"].round(2)
        breakdown = breakdown.sort_values("xG", ascending=False).reset_index(drop=True)
        render_table(breakdown, heatmap_cols=["xG", "Shots", "Conv%"], palette_map={"xG":"green","Shots":"blue","Conv%":"green"})

        st.markdown('<span class="section-label">Match-by-match xG</span>', unsafe_allow_html=True)
        match_xg = t_shots.groupby(["HomeTeam", "AwayTeam", t_shots["Date"].dt.date]).agg(
            xG_for=("xG","sum"), Shots=("xG","count"), Goals=("isGoal","sum")
        ).reset_index()
        match_xg.columns = ["Home", "Away", "Date", "xG For", "Shots", "Goals"]
        opp_xg = o_shots.groupby(["HomeTeam", "AwayTeam", o_shots["Date"].dt.date]).agg(
            xGA=("xG","sum"), Shots_Ag=("xG","count"), GA=("isGoal","sum")
        ).reset_index()
        opp_xg.columns = ["Home", "Away", "Date", "xGA", "Shots Ag", "GA"]
        mbm = match_xg.merge(opp_xg, on=["Home", "Away", "Date"], how="outer").sort_values("Date", ascending=False)
        mbm["xG For"] = mbm["xG For"].round(2)
        mbm["xGA"]    = mbm["xGA"].round(2)
        mbm["xGD"]    = (mbm["xG For"] - mbm["xGA"]).round(2)
        render_table(
            mbm.reset_index(drop=True),
            heatmap_cols=["xG For", "xGA", "xGD"],
            invert_cols=["xGA"],
            palette_map={"xG For":"green","xGA":"red","xGD":"blue"},
        )
    else:
        st.info("No shot data available.")
