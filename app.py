import streamlit as st
import pandas as pd
import numpy as np
import glob, os
import plotly.graph_objects as go
import plotly.express as px

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="WSL Stats Hub",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# THEME
# ─────────────────────────────────────────────────────────────────────────────
NAVY   = "#0d1b2a"
RED    = "#e63946"
CREAM  = "#f5f5f0"
WHITE  = "#ffffff"
GREY   = "#f0f0ed"

st.markdown(f"""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
  html, body, [class*="css"] {{ font-family: 'Inter', sans-serif; }}

  /* sidebar */
  [data-testid="stSidebar"] {{ background: {NAVY}; border-right: 3px solid {RED}; }}
  [data-testid="stSidebar"] * {{ color: #e0e0e0 !important; }}
  [data-testid="stSidebar"] hr {{ border-color: #2a3a4a; }}

  /* main bg */
  .main {{ background: {CREAM}; }}
  .block-container {{ padding-top: 0 !important; }}

  /* header */
  .hub-header {{
    background: linear-gradient(135deg, {NAVY} 0%, #1a2e42 100%);
    color: #fff; padding: 1.4rem 2rem;
    border-bottom: 4px solid {RED};
    margin: -1rem -1rem 1.5rem -1rem;
  }}
  .hub-header h1 {{ margin:0; font-size:2rem; font-weight:800; letter-spacing:-0.5px; }}
  .hub-header p  {{ margin:.3rem 0 0; font-size:.85rem; color:#8ab4cc; }}

  /* pill label */
  .pill {{
    background:{RED}; color:#fff; font-size:.62rem; font-weight:700;
    letter-spacing:1.6px; text-transform:uppercase;
    padding:3px 10px; border-radius:2px; display:inline-block; margin-bottom:.6rem;
  }}

  /* KPI cards */
  .kpi-row {{ display:flex; gap:.75rem; flex-wrap:wrap; margin-bottom:1.4rem; }}
  .kpi-card {{
    background:{WHITE}; border-top:4px solid {NAVY};
    padding:.9rem 1.1rem; flex:1; min-width:140px;
    box-shadow:0 2px 6px rgba(0,0,0,.07); border-radius:0 0 4px 4px;
  }}
  .kpi-card .kpi-label {{ font-size:.65rem; text-transform:uppercase; letter-spacing:1px; color:#888; }}
  .kpi-card .kpi-value {{ font-size:1.5rem; font-weight:800; color:{NAVY}; line-height:1.1; margin:.2rem 0; }}
  .kpi-card .kpi-sub   {{ font-size:.75rem; color:#555; }}
  .kpi-card.red  {{ border-top-color:{RED}; }}
  .kpi-card.blue {{ border-top-color:#2196f3; }}
  .kpi-card.green{{ border-top-color:#4caf50; }}

  /* table */
  .tbl-wrap {{
    background:{WHITE}; border:1px solid #ddd;
    box-shadow:0 2px 6px rgba(0,0,0,.05);
    overflow-x:auto; margin-bottom:1.4rem; border-radius:4px;
  }}
  .tbl-wrap table {{ border-collapse:collapse; width:100%; font-size:.82rem; }}
  .tbl-wrap thead tr {{ background:{NAVY}; color:{WHITE}; font-size:.7rem; text-transform:uppercase; letter-spacing:.9px; }}
  .tbl-wrap thead th {{ padding:9px 13px; text-align:right; white-space:nowrap; border-right:1px solid #1f3048; }}
  .tbl-wrap thead th:first-child,
  .tbl-wrap thead th:nth-child(2) {{ text-align:left; }}
  .tbl-wrap tbody tr {{ border-bottom:1px solid #eee; transition:background .1s; }}
  .tbl-wrap tbody tr:hover {{ background:#eef3ff !important; }}
  .tbl-wrap tbody tr:nth-child(even) {{ background:#fafaf8; }}
  .tbl-wrap tbody td {{ padding:7px 13px; text-align:right; color:#222; }}
  .tbl-wrap tbody td:first-child {{ text-align:center; }}
  .tbl-wrap tbody td:nth-child(2) {{ text-align:left; font-weight:600; color:{NAVY}; }}

  /* form dots */
  .form-dot {{
    display:inline-block; width:14px; height:14px; border-radius:50%;
    margin:0 1px; font-size:.6rem; color:#fff; text-align:center;
    line-height:14px; font-weight:700;
  }}

  /* tabs */
  [data-testid="stTabs"] [role="tab"] {{
    font-size:.78rem; font-weight:600; text-transform:uppercase; letter-spacing:.6px; padding:6px 18px;
  }}
  [data-testid="stTabs"] [aria-selected="true"] {{
    color:{RED} !important; border-bottom:3px solid {RED} !important;
  }}

  .footnote {{ font-size:.72rem; color:#999; margin-top:-.4rem; margin-bottom:1rem; }}
  .divider {{ border:none; border-top:1px solid #e0e0d8; margin:1rem 0; }}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# DATA LOADING
# ─────────────────────────────────────────────────────────────────────────────
XG_DIR      = os.path.join(os.path.dirname(__file__), "WSL", "xgCSV")
MATCHES_CSV = os.path.join(os.path.dirname(__file__), "WSL Matches.csv")

@st.cache_data(show_spinner="Loading shot data…")
def load_shots():
    files = glob.glob(os.path.join(XG_DIR, "*.csv"))
    dfs = []
    for f in files:
        try:
            dfs.append(pd.read_csv(f, index_col=0))
        except Exception:
            pass
    if not dfs:
        return pd.DataFrame()
    shots = pd.concat(dfs, ignore_index=True)
    shots["Date"]     = pd.to_datetime(shots["Date"], utc=True, errors="coerce")
    shots["xG"]       = pd.to_numeric(shots["xG"], errors="coerce")
    shots["x"]        = pd.to_numeric(shots["x"], errors="coerce")
    shots["y"]        = pd.to_numeric(shots["y"], errors="coerce")
    shots["distance"] = pd.to_numeric(shots["distance"], errors="coerce")
    shots["angle"]    = pd.to_numeric(shots["angle"], errors="coerce")
    shots["timeMin"]  = pd.to_numeric(shots["timeMin"], errors="coerce")
    shots["isGoal"]   = shots["isGoal"].astype(str).str.upper().isin(["TRUE", "1", "YES"])
    shots["isBigChance"] = shots["isBigChance"].astype(str).str.upper().isin(["YES", "TRUE", "1"])
    shots["isOwnGoal"]   = shots["isOwnGoal"].astype(str).str.upper().isin(["TRUE", "1", "YES"])
    return shots.dropna(subset=["Date", "xG"])

@st.cache_data(show_spinner="Loading match data…")
def load_matches():
    df = pd.read_csv(MATCHES_CSV, encoding="utf-8-sig")
    df.columns = df.columns.str.strip()
    return df

shots   = load_shots()
matches = load_matches()

ALL_TEAMS = sorted(shots["HomeTeam"].dropna().unique()) if not shots.empty else []

# ─────────────────────────────────────────────────────────────────────────────
# DERIVED DATA
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data
def build_match_results(matches_df):
    if matches_df.empty:
        return pd.DataFrame()
    col_map = {
        "matchInfo/date":                       "Date",
        "matchInfo/contestant/0/name":          "Home",
        "matchInfo/contestant/1/name":          "Away",
        "liveData/matchDetails/scores/ft/home": "HG",
        "liveData/matchDetails/scores/ft/away": "AG",
        "matchInfo/week":                       "GW",
    }
    keep = {k: v for k, v in col_map.items() if k in matches_df.columns}
    res = matches_df[list(keep)].rename(columns=keep).copy()
    res["Date"] = pd.to_datetime(res["Date"].astype(str).str.rstrip("Z"), errors="coerce")
    res = res.dropna(subset=["Date"])
    res["Date"] = res["Date"].dt.date
    res["HG"]   = pd.to_numeric(res["HG"], errors="coerce")
    res["AG"]   = pd.to_numeric(res["AG"], errors="coerce")
    res = res.dropna(subset=["HG", "AG"])
    res[["HG","AG"]] = res[["HG","AG"]].astype(int)
    res["Score"]  = res["HG"].astype(str) + " – " + res["AG"].astype(str)
    res["Result"] = res.apply(lambda r: "H" if r.HG > r.AG else ("A" if r.AG > r.HG else "D"), axis=1)
    return res.sort_values("Date", ascending=False).reset_index(drop=True)

@st.cache_data
def build_standings(mr, shots_df):
    if mr.empty:
        return pd.DataFrame()
    teams = sorted(set(mr["Home"]) | set(mr["Away"]))
    rows = []
    for team in teams:
        home = mr[mr["Home"] == team]
        away = mr[mr["Away"] == team]
        gp  = len(home) + len(away)
        w   = int((home["Result"]=="H").sum() + (away["Result"]=="A").sum())
        d   = int((home["Result"]=="D").sum() + (away["Result"]=="D").sum())
        l   = gp - w - d
        gf  = int(home["HG"].sum() + away["AG"].sum())
        ga  = int(home["AG"].sum() + away["HG"].sum())
        pts = w*3 + d

        # form: last 5 chronological results
        all_games = pd.concat([
            home[["Date","Result"]].assign(for_team=lambda d: d["Result"].map({"H":"W","D":"D","A":"L"})),
            away[["Date","Result"]].assign(for_team=lambda d: d["Result"].map({"A":"W","D":"D","H":"L"})),
        ]).sort_values("Date").tail(5)
        form = all_games["for_team"].tolist()

        # xG
        t_sh = shots_df[shots_df["TeamId"] == team] if not shots_df.empty else pd.DataFrame()
        o_sh = shots_df[((shots_df["HomeTeam"]==team)|(shots_df["AwayTeam"]==team)) & (shots_df["TeamId"]!=team)] if not shots_df.empty else pd.DataFrame()

        rows.append({
            "Team": team, "GP": gp, "W": w, "D": d, "L": l,
            "GF": gf, "GA": ga, "GD": gf-ga, "Pts": pts,
            "Form": form,
            "xG":  round(t_sh["xG"].sum(), 1) if not t_sh.empty else 0,
            "xGA": round(o_sh["xG"].sum(), 1) if not o_sh.empty else 0,
        })

    df = pd.DataFrame(rows).sort_values(["Pts","GD","GF"], ascending=False).reset_index(drop=True)
    df.insert(0, "Rank", df.index + 1)
    df["xGD"]  = (df["xG"] - df["xGA"]).round(1)
    df["G-xG"] = (df["GF"] - df["xG"]).round(1)
    df["Pts/GP"] = (df["Pts"] / df["GP"].replace(0, np.nan)).round(2)
    return df

@st.cache_data
def build_team_stats(shots_df, standings_df):
    if shots_df.empty:
        return pd.DataFrame()
    rows = []
    for team in ALL_TEAMS:
        t_sh = shots_df[shots_df["TeamId"] == team]
        o_sh = shots_df[((shots_df["HomeTeam"]==team)|(shots_df["AwayTeam"]==team)) & (shots_df["TeamId"]!=team)]
        gp_row = standings_df[standings_df["Team"]==team]["GP"].values if "Team" in standings_df.columns else []
        gp = int(gp_row[0]) if len(gp_row) else max(
            shots_df[(shots_df["HomeTeam"]==team)|(shots_df["AwayTeam"]==team)]
            .groupby(["HomeTeam","AwayTeam",shots_df["Date"].dt.date]).ngroups, 1
        )

        xg  = t_sh["xG"].sum()
        xga = o_sh["xG"].sum()
        gf  = int(t_sh["isGoal"].sum())
        ga  = int(o_sh["isGoal"].sum())
        bc  = int(t_sh["isBigChance"].sum())
        bc_ag = int(o_sh["isBigChance"].sum())
        sh  = len(t_sh)
        sh_ag = len(o_sh)

        rows.append({
            "Team":      team,
            "GP":        gp,
            "Sh":        sh,
            "Sh Ag":     sh_ag,
            "Sh/90":     round(sh / max(gp,1), 1),
            "ShAg/90":   round(sh_ag / max(gp,1), 1),
            "xG":        round(xg, 1),
            "xGA":       round(xga, 1),
            "xGD":       round(xg - xga, 1),
            "xG/90":     round(xg / max(gp,1), 2),
            "xGA/90":    round(xga / max(gp,1), 2),
            "GF":        gf,
            "GA":        ga,
            "G-xG":      round(gf - xg, 1),
            "GA-xGA":    round(ga - xga, 1),
            "Big Ch":    bc,
            "Big Ch Ag": bc_ag,
            "xG/Sh":     round(xg / max(sh,1), 3),
            "xGA/Sh":    round(xga / max(sh_ag,1), 3),
            "Conv%":     round(gf / max(sh,1) * 100, 1),
            "Save%":     round((1 - ga / max(sh_ag,1)) * 100, 1),
            "Dist Avg":  round(t_sh["distance"].mean(), 1) if "distance" in t_sh else np.nan,
        })
    return pd.DataFrame(rows)

@st.cache_data
def build_player_stats(shots_df):
    if shots_df.empty or "PlayerId" not in shots_df.columns:
        return pd.DataFrame()
    grp = shots_df.groupby(["PlayerId","TeamId"]).agg(
        Shots    = ("xG","count"),
        Goals    = ("isGoal","sum"),
        xG       = ("xG","sum"),
        BigCh    = ("isBigChance","sum"),
        AvgDist  = ("distance","mean"),
        AvgAngle = ("angle","mean"),
    ).reset_index().rename(columns={"PlayerId":"Player","TeamId":"Team"})
    grp["G-xG"]   = (grp["Goals"] - grp["xG"]).round(2)
    grp["xG/Sh"]  = (grp["xG"] / grp["Shots"]).round(3)
    grp["Conv%"]  = (grp["Goals"] / grp["Shots"] * 100).round(1)
    grp["xG"]     = grp["xG"].round(2)
    grp["AvgDist"]= grp["AvgDist"].round(1)
    grp["AvgAngle"]= grp["AvgAngle"].round(1)
    return grp.sort_values("xG", ascending=False).reset_index(drop=True)

@st.cache_data
def build_xg_timeline(shots_df, mr):
    """Cumulative xG per team per gameweek."""
    if shots_df.empty or mr.empty:
        return pd.DataFrame()
    shots_df = shots_df.copy()
    shots_df["_date"] = shots_df["Date"].dt.date
    # join GW via match results
    gw_map = {}
    for _, row in mr.iterrows():
        gw_map[(row["Home"], row["Away"], row["Date"])] = row.get("GW", None)
    def get_gw(r):
        return gw_map.get((r["HomeTeam"], r["AwayTeam"], r.get("_date")),
               gw_map.get((r["AwayTeam"], r["HomeTeam"], r.get("_date")), None))
    shots_df["GW"] = shots_df.apply(get_gw, axis=1)
    shots_df = shots_df.dropna(subset=["GW"])
    shots_df["GW"] = shots_df["GW"].astype(int)
    gw_xg = shots_df.groupby(["TeamId","GW"])["xG"].sum().reset_index()
    gw_xg = gw_xg.sort_values(["TeamId","GW"])
    gw_xg["cum_xG"] = gw_xg.groupby("TeamId")["xG"].cumsum().round(2)
    return gw_xg

match_results = build_match_results(matches)
standings     = build_standings(match_results, shots)
team_stats    = build_team_stats(shots, standings)
player_stats  = build_player_stats(shots)
xg_timeline   = build_xg_timeline(shots, match_results)

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def heat(val, vmin, vmax, pal="blue", inv=False):
    if pd.isna(val):
        return ""
    r = np.clip((val-vmin)/(vmax-vmin+1e-9), 0, 1)
    if inv: r = 1-r
    if pal=="red":    rgb = (int(255*(.95-.55*r)), int(255*(.95-.70*r)), int(255*(.95-.70*r)))
    elif pal=="green":rgb = (int(255*(.95-.70*r)), int(255*(.75+.15*r)), int(255*(.95-.70*r)))
    else:             rgb = (int(255*(.95-.65*r)), int(255*(.95-.55*r)), int(255*(.95-.05*r)))
    txt = "white" if r>.65 else NAVY
    return f"background:rgb{rgb};color:{txt};"

def rank_badge(rank, n=None):
    if n is None: n = len(standings) if not standings.empty else 20
    c = "#2196f3" if rank<=4 else "#ff9800" if rank<=6 else RED if rank>=n-1 else "#555"
    return f'<span style="background:{c};color:#fff;border-radius:3px;padding:1px 8px;font-size:.76rem;font-weight:700;">{rank}</span>'

def form_html(form_list):
    colors = {"W":"#4caf50","D":"#888","L":RED}
    return "".join(
        f'<span class="form-dot" style="background:{colors.get(r,"#ccc")}">{r}</span>'
        for r in form_list
    )

def fmt(val, col):
    if pd.isna(val): return "—"
    sign = {"GD","xGD","G-xG","GA-xGA","Pts diff"}
    if col in sign:
        return (f"{val:+.1f}" if isinstance(val,float) else f"{int(val):+d}")
    if isinstance(val,float):
        return f"{val:.3f}" if (abs(val)<1 and "%" not in col and col not in {"xG","xGA","xGD","G-xG","GA-xGA","cum_xG"}) else (f"{val:.1f}" if abs(val)>=10 else f"{val:.2f}")
    return str(val)

def render_table(df, heatmap_cols=None, invert_cols=None, pal_map=None, form_col=None):
    heatmap_cols = heatmap_cols or []
    invert_cols  = invert_cols  or []
    pal_map      = pal_map      or {}
    stats = {c:(df[c].min(),df[c].max()) for c in heatmap_cols if c in df.columns and pd.api.types.is_numeric_dtype(df[c])}

    rows = []
    for _, row in df.iterrows():
        cells = []
        for col in df.columns:
            val = row[col]
            style = ""
            if col == "Rank":
                cell = rank_badge(int(val))
            elif col == "Team":
                cell = f"<strong>{val}</strong>"
            elif col == "Form":
                cell = form_html(val) if isinstance(val, list) else "—"
            elif col == "Score":
                cell = f'<span style="font-weight:700">{val}</span>'
            elif col == "Result":
                c = {"H":"#2196f3","A":RED,"D":"#888"}.get(val,"#888")
                cell = f'<span style="background:{c};color:#fff;border-radius:3px;padding:1px 8px;font-size:.72rem;font-weight:700;">{val}</span>'
            else:
                if col in stats:
                    vmin,vmax = stats[col]
                    style = heat(val, vmin, vmax, pal_map.get(col,"blue"), col in invert_cols)
                cell = fmt(val, col)
            cells.append(f'<td style="{style}">{cell}</td>')
        rows.append("<tr>"+"".join(cells)+"</tr>")

    headers = "".join(f"<th>{c}</th>" for c in df.columns)
    st.markdown(f"""
    <div class="tbl-wrap">
      <table><thead><tr>{headers}</tr></thead>
      <tbody>{"".join(rows)}</tbody></table>
    </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# PLOTLY THEME
# ─────────────────────────────────────────────────────────────────────────────
PLOTLY_LAYOUT = dict(
    paper_bgcolor="white", plot_bgcolor="white",
    font=dict(family="Inter, sans-serif", color=NAVY, size=12),
    margin=dict(l=40,r=20,t=40,b=40),
    hoverlabel=dict(bgcolor=NAVY,font_color="white",font_size=12),
)

def pitch_shapes():
    """Plotly shapes for a horizontal half-pitch (attacking half, x=50-100, y=0-100)."""
    lw, lc = 2, "#cccccc"
    shapes = [
        # pitch outline (full)
        dict(type="rect", x0=0,x1=100,y0=0,y1=100, line=dict(color=lc,width=lw), fillcolor="#f8fdf8"),
        # halfway
        dict(type="line", x0=50,x1=50,y0=0,y1=100, line=dict(color=lc,width=lw)),
        # centre circle
        dict(type="circle", x0=41,x1=59,y0=41,y1=59, line=dict(color=lc,width=lw)),
        # penalty areas
        dict(type="rect", x0=83,x1=100,y0=21.1,y1=78.9, line=dict(color=lc,width=lw), fillcolor="rgba(0,0,0,0)"),
        dict(type="rect", x0=0,x1=17,y0=21.1,y1=78.9,   line=dict(color=lc,width=lw), fillcolor="rgba(0,0,0,0)"),
        # 6-yard boxes
        dict(type="rect", x0=94.2,x1=100,y0=36.8,y1=63.2, line=dict(color=lc,width=lw), fillcolor="rgba(0,0,0,0)"),
        dict(type="rect", x0=0,x1=5.8,y0=36.8,y1=63.2,    line=dict(color=lc,width=lw), fillcolor="rgba(0,0,0,0)"),
        # goals
        dict(type="rect", x0=100,x1=101.5,y0=44.2,y1=55.8, line=dict(color="#aaa",width=lw), fillcolor="#ddd"),
        dict(type="rect", x0=-1.5,x1=0,y0=44.2,y1=55.8,    line=dict(color="#aaa",width=lw), fillcolor="#ddd"),
    ]
    return shapes

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"## ⚽ WSL Hub")
    st.markdown("**2025/26 Barclays WSL**")
    st.markdown("---")
    team_filter = st.multiselect("Filter Teams", ALL_TEAMS)
    st.markdown("---")
    if not shots.empty:
        min_d = shots["Date"].dt.date.min()
        max_d = shots["Date"].dt.date.max()
        date_range = st.date_input("Date range", value=(min_d,max_d), min_value=min_d, max_value=max_d)
    else:
        date_range = None
    st.markdown("---")
    st.caption("Data: Opta  ·  Design: FBRef × FiveThirtyEight")

# ─────────────────────────────────────────────────────────────────────────────
# FILTER
# ─────────────────────────────────────────────────────────────────────────────
shots_f = shots.copy()
if date_range and len(date_range) == 2:
    d0 = pd.Timestamp(date_range[0], tz="UTC")
    d1 = pd.Timestamp(date_range[1], tz="UTC")
    shots_f = shots_f[(shots_f["Date"]>=d0) & (shots_f["Date"]<=d1)]
if team_filter:
    shots_f = shots_f[(shots_f["HomeTeam"].isin(team_filter))|(shots_f["AwayTeam"].isin(team_filter))]

# ─────────────────────────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────────────────────────
n_matches = len(match_results) if not match_results.empty else 0
gw_max    = int(standings["GP"].max()) if not standings.empty else "?"
st.markdown(f"""
<div class="hub-header">
  <h1>WSL Stats Hub</h1>
  <p>2025/26 Barclays Women's Super League &nbsp;·&nbsp; {n_matches} matches played &nbsp;·&nbsp; GW {gw_max}</p>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# KPI CARDS
# ─────────────────────────────────────────────────────────────────────────────
if not standings.empty and not team_stats.empty:
    leader   = standings.iloc[0]
    top_atk  = team_stats.sort_values("xG/90", ascending=False).iloc[0]
    top_def  = team_stats.sort_values("xGA/90").iloc[0]
    total_g  = int(shots["isGoal"].sum()) if not shots.empty else 0
    total_xg = round(shots["xG"].sum(), 1) if not shots.empty else 0
    gpg      = round(total_g / max(n_matches,1), 2)

    st.markdown(f"""
    <div class="kpi-row">
      <div class="kpi-card">
        <div class="kpi-label">League Leader</div>
        <div class="kpi-value">{leader['Team']}</div>
        <div class="kpi-sub">{leader['Pts']} pts &nbsp;·&nbsp; {leader['GD']:+d} GD</div>
      </div>
      <div class="kpi-card blue">
        <div class="kpi-label">Best Attack (xG/90)</div>
        <div class="kpi-value">{top_atk['Team']}</div>
        <div class="kpi-sub">{top_atk['xG/90']} xG per match</div>
      </div>
      <div class="kpi-card red">
        <div class="kpi-label">Best Defence (xGA/90)</div>
        <div class="kpi-value">{top_def['Team']}</div>
        <div class="kpi-sub">{top_def['xGA/90']} xGA per match</div>
      </div>
      <div class="kpi-card green">
        <div class="kpi-label">Goals Scored</div>
        <div class="kpi-value">{total_g}</div>
        <div class="kpi-sub">{gpg}/match &nbsp;·&nbsp; {total_xg} xG</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📋  Standings", "⚡  xG Analysis", "🎯  Shot Map",
    "📅  Results", "👤  Players", "🔍  Team Deep Dive",
])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — STANDINGS
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    if standings.empty:
        st.info("No standings data.")
    else:
        c_sort, c_toggle = st.columns([2,1])
        with c_sort:
            sort_s = st.selectbox("Sort by", ["Pts","GD","GF","xGD","xG","xGA","G-xG","Pts/GP"], key="s1")
        with c_toggle:
            show_xg = st.toggle("Show xG columns", value=True)

        asc_s  = sort_s in ("xGA","GA")
        df_s   = standings.sort_values(sort_s, ascending=asc_s).reset_index(drop=True)
        df_s["Rank"] = df_s.index + 1

        base  = ["Rank","Team","GP","W","D","L","GF","GA","GD","Pts","Form"]
        extra = ["xG","xGA","xGD","G-xG","Pts/GP"]
        cols  = base + (extra if show_xg else [])
        cols  = [c for c in cols if c in df_s.columns]

        st.markdown('<span class="pill">League Table</span>', unsafe_allow_html=True)
        render_table(
            df_s[cols],
            heatmap_cols=["Pts","GF","xG","xGD","G-xG","Pts/GP"],
            invert_cols=["xGA","GA"],
            pal_map={"Pts":"blue","GF":"green","xG":"green","xGD":"blue","G-xG":"green","Pts/GP":"blue"},
        )
        st.markdown('<p class="footnote">🔵 CL spots (1–4) · 🟠 Europa (5–6) · 🔴 Relegation zone · Form = last 5 results</p>', unsafe_allow_html=True)

        if show_xg and not team_stats.empty:
            st.markdown('<span class="pill">xG vs xGA — Attack vs Defence</span>', unsafe_allow_html=True)
            scatter_df = team_stats.merge(standings[["Team","Pts"]], on="Team", how="left")
            fig = go.Figure()
            fig.add_shape(type="line", x0=scatter_df["xG/90"].mean(), x1=scatter_df["xG/90"].mean(),
                          y0=0, y1=scatter_df["xGA/90"].max()*1.1, line=dict(color="#ccc",dash="dash",width=1))
            fig.add_shape(type="line", x0=0, x1=scatter_df["xG/90"].max()*1.1,
                          y0=scatter_df["xGA/90"].mean(), y1=scatter_df["xGA/90"].mean(),
                          line=dict(color="#ccc",dash="dash",width=1))
            fig.add_trace(go.Scatter(
                x=scatter_df["xG/90"], y=scatter_df["xGA/90"],
                mode="markers+text",
                text=scatter_df["Team"].str.split().str[-1],
                textposition="top center", textfont=dict(size=10, color=NAVY),
                marker=dict(
                    size=scatter_df["Pts"].fillna(10) / scatter_df["Pts"].max() * 30 + 10,
                    color=scatter_df["Pts"], colorscale="Blues", showscale=True,
                    colorbar=dict(title="Pts", thickness=12),
                    line=dict(color=NAVY,width=1),
                ),
                hovertemplate="<b>%{text}</b><br>xG/90: %{x:.2f}<br>xGA/90: %{y:.2f}<extra></extra>",
            ))
            fig.update_layout(
                **PLOTLY_LAYOUT,
                xaxis=dict(title="xG per match (attack →)", gridcolor="#eee"),
                yaxis=dict(title="xGA per match (← better defence)", autorange="reversed", gridcolor="#eee"),
                height=420,
            )
            fig.add_annotation(x=scatter_df["xG/90"].mean()+.02, y=scatter_df["xGA/90"].max()*.98,
                text="Better defence →", showarrow=False, font=dict(size=9,color="#aaa"))
            st.plotly_chart(fig, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — xG ANALYSIS
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    if team_stats.empty:
        st.info("No xG data.")
    else:
        sort_x = st.selectbox("Sort by", ["xGD","xG","xGA","xG/90","xGA/90","G-xG","GA-xGA","Big Ch","Conv%","Save%"], key="s2")
        asc_x  = sort_x in ("xGA","xGA/90","GA-xGA")
        df_x   = team_stats.sort_values(sort_x, ascending=asc_x).reset_index(drop=True)
        df_x.insert(0, "Rank", df_x.index+1)
        show_x = ["Rank","Team","GP","xG","xGA","xGD","xG/90","xGA/90","G-xG","GA-xGA","Sh","Sh Ag","Big Ch","Conv%","Save%"]
        show_x = [c for c in show_x if c in df_x.columns]

        st.markdown('<span class="pill">xG Performance Table</span>', unsafe_allow_html=True)
        render_table(
            df_x[show_x],
            heatmap_cols=["xG","xGD","xG/90","Sh","Big Ch","G-xG","Conv%","Save%"],
            invert_cols=["xGA","xGA/90","GA-xGA","Sh Ag"],
            pal_map={"xG":"green","xGD":"blue","xG/90":"green","Sh":"blue",
                     "Big Ch":"green","G-xG":"green","Conv%":"green","Save%":"green"},
        )
        st.markdown('<p class="footnote">Conv% = goals/shots · Save% = 1-(GA/shots against) · G-xG positive = overperforming xG</p>', unsafe_allow_html=True)

        # xG race chart
        if not xg_timeline.empty:
            st.markdown('<span class="pill">Cumulative xG Race</span>', unsafe_allow_html=True)
            highlight = st.multiselect("Highlight teams", ALL_TEAMS, default=ALL_TEAMS[:4], key="race_hl")
            fig2 = go.Figure()
            colors_cycle = px.colors.qualitative.Bold
            for i, team in enumerate(ALL_TEAMS):
                tdf = xg_timeline[xg_timeline["TeamId"]==team].sort_values("GW")
                opacity = 1.0 if (not highlight or team in highlight) else 0.12
                width   = 2.5 if team in highlight else 1
                fig2.add_trace(go.Scatter(
                    x=tdf["GW"], y=tdf["cum_xG"],
                    name=team, mode="lines",
                    line=dict(color=colors_cycle[i % len(colors_cycle)], width=width),
                    opacity=opacity,
                    hovertemplate=f"<b>{team}</b><br>GW %{{x}}<br>Cum xG: %{{y:.1f}}<extra></extra>",
                ))
            fig2.update_layout(
                **PLOTLY_LAYOUT, height=420,
                xaxis=dict(title="Gameweek", dtick=1, gridcolor="#eee"),
                yaxis=dict(title="Cumulative xG", gridcolor="#eee"),
                legend=dict(orientation="h", y=-0.25, font=dict(size=10)),
            )
            st.plotly_chart(fig2, use_container_width=True)

        # xG bar comparison
        st.markdown('<span class="pill">xG For vs Against per Match</span>', unsafe_allow_html=True)
        bar_df = team_stats.sort_values("xG/90", ascending=True)
        fig3 = go.Figure()
        fig3.add_trace(go.Bar(
            y=bar_df["Team"], x=bar_df["xG/90"], name="xG/90",
            orientation="h", marker_color="#4caf50", marker_line_width=0,
        ))
        fig3.add_trace(go.Bar(
            y=bar_df["Team"], x=-bar_df["xGA/90"], name="xGA/90",
            orientation="h", marker_color=RED, marker_line_width=0,
        ))
        fig3.update_layout(
            **PLOTLY_LAYOUT, height=480, barmode="relative",
            xaxis=dict(title="← xGA/90 | xG/90 →", tickvals=[-2,-1,0,1,2],
                       ticktext=["2","1","0","1","2"], gridcolor="#eee"),
            yaxis=dict(tickfont=dict(size=10)),
            legend=dict(orientation="h", y=1.05),
        )
        st.plotly_chart(fig3, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — SHOT MAP
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    if shots_f.empty:
        st.info("No shot data for selected filters.")
    else:
        c1, c2, c3 = st.columns(3)
        with c1:
            sm_team = st.selectbox("Team", ["All"] + ALL_TEAMS, key="sm_t")
        with c2:
            bp_opts = sorted(shots_f["Bodypart"].dropna().unique())
            sm_bp   = st.multiselect("Body part", bp_opts, default=bp_opts, key="sm_bp")
        with c3:
            tp_opts = sorted(shots_f["Type_of_play"].dropna().unique())
            sm_tp   = st.multiselect("Play type", tp_opts, default=tp_opts, key="sm_tp")

        sf = shots_f.copy()
        if sm_team != "All":
            sf = sf[sf["TeamId"] == sm_team]
        if sm_bp:
            sf = sf[sf["Bodypart"].isin(sm_bp)]
        if sm_tp:
            sf = sf[sf["Type_of_play"].isin(sm_tp)]

        goals_sf = sf[sf["isGoal"]]
        misses_sf = sf[~sf["isGoal"]]

        # KPI row
        tot = len(sf); g = int(sf["isGoal"].sum())
        st.markdown(f"""
        <div class="kpi-row" style="margin-top:.5rem">
          <div class="kpi-card"><div class="kpi-label">Shots</div><div class="kpi-value">{tot}</div></div>
          <div class="kpi-card green"><div class="kpi-label">Goals</div><div class="kpi-value">{g}</div></div>
          <div class="kpi-card blue"><div class="kpi-label">Total xG</div><div class="kpi-value">{sf["xG"].sum():.1f}</div></div>
          <div class="kpi-card"><div class="kpi-label">xG/Shot</div><div class="kpi-value">{sf["xG"].mean():.3f}</div></div>
          <div class="kpi-card"><div class="kpi-label">Conversion</div><div class="kpi-value">{g/max(tot,1)*100:.1f}%</div></div>
          <div class="kpi-card"><div class="kpi-label">Big Chances</div><div class="kpi-value">{int(sf["isBigChance"].sum())}</div></div>
        </div>
        """, unsafe_allow_html=True)

        # Pitch map
        st.markdown('<span class="pill">Shot Map</span>', unsafe_allow_html=True)

        fig_pitch = go.Figure()
        for s in pitch_shapes():
            fig_pitch.add_shape(**s)

        # misses
        fig_pitch.add_trace(go.Scatter(
            x=misses_sf["x"], y=misses_sf["y"],
            mode="markers",
            marker=dict(
                size=misses_sf["xG"]*60+5,
                color="rgba(100,149,237,0.45)",
                line=dict(color="rgba(70,100,180,0.6)", width=1),
            ),
            name="Miss / Save",
            hovertemplate="<b>%{customdata[0]}</b><br>%{customdata[1]}<br>xG: %{customdata[2]:.3f}<br>Dist: %{customdata[3]:.1f}m<extra></extra>",
            customdata=np.column_stack([
                misses_sf["PlayerId"].fillna("Unknown"),
                misses_sf["Type_of_play"].fillna(""),
                misses_sf["xG"].round(3),
                misses_sf["distance"].round(1),
            ]),
        ))
        # goals
        fig_pitch.add_trace(go.Scatter(
            x=goals_sf["x"], y=goals_sf["y"],
            mode="markers",
            marker=dict(
                size=goals_sf["xG"]*60+8,
                color=RED,
                symbol="star",
                line=dict(color="darkred", width=1),
            ),
            name="Goal",
            hovertemplate="<b>⚽ %{customdata[0]}</b><br>%{customdata[1]}<br>xG: %{customdata[2]:.3f}<br>Dist: %{customdata[3]:.1f}m<extra></extra>",
            customdata=np.column_stack([
                goals_sf["PlayerId"].fillna("Unknown"),
                goals_sf["Type_of_play"].fillna(""),
                goals_sf["xG"].round(3),
                goals_sf["distance"].round(1),
            ]),
        ))
        fig_pitch.update_layout(
            **PLOTLY_LAYOUT,
            height=520,
            xaxis=dict(range=[-3,103], showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(range=[-3,103], showgrid=False, zeroline=False, showticklabels=False, scaleanchor="x"),
            legend=dict(orientation="h", y=-0.05),
            margin=dict(l=10,r=10,t=20,b=20),
        )
        st.plotly_chart(fig_pitch, use_container_width=True)
        st.markdown('<p class="footnote">Bubble size = xG value · Stars = goals · Attack left→right</p>', unsafe_allow_html=True)

        # breakdown tables
        bc1, bc2 = st.columns(2)
        with bc1:
            st.markdown('<span class="pill">By Play Type</span>', unsafe_allow_html=True)
            by_type = sf.groupby("Type_of_play").agg(Shots=("xG","count"),Goals=("isGoal","sum"),xG=("xG","sum")).reset_index()
            by_type.columns = ["Type","Shots","Goals","xG"]
            by_type["Conv%"] = (by_type["Goals"]/by_type["Shots"]*100).round(1)
            by_type["xG/Sh"] = (by_type["xG"]/by_type["Shots"]).round(3)
            by_type["G-xG"]  = (by_type["Goals"]-by_type["xG"]).round(2)
            by_type["xG"]    = by_type["xG"].round(2)
            by_type = by_type.sort_values("xG", ascending=False).reset_index(drop=True)
            render_table(by_type, heatmap_cols=["xG","Conv%"], pal_map={"xG":"green","Conv%":"green"})
        with bc2:
            st.markdown('<span class="pill">By Body Part</span>', unsafe_allow_html=True)
            by_bp = sf.groupby("Bodypart").agg(Shots=("xG","count"),Goals=("isGoal","sum"),xG=("xG","sum")).reset_index()
            by_bp.columns = ["Body Part","Shots","Goals","xG"]
            by_bp["Conv%"] = (by_bp["Goals"]/by_bp["Shots"]*100).round(1)
            by_bp["xG/Sh"] = (by_bp["xG"]/by_bp["Shots"]).round(3)
            by_bp["xG"]    = by_bp["xG"].round(2)
            by_bp = by_bp.sort_values("xG", ascending=False).reset_index(drop=True)
            render_table(by_bp, heatmap_cols=["xG","Conv%"], pal_map={"xG":"green","Conv%":"green"})

        # Distance / angle histogram
        st.markdown('<span class="pill">xG by Distance</span>', unsafe_allow_html=True)
        fig_dist = go.Figure()
        fig_dist.add_trace(go.Histogram(
            x=sf[~sf["isGoal"]]["distance"], name="Miss/Save",
            marker_color="rgba(100,149,237,0.6)", xbins=dict(size=2),
        ))
        fig_dist.add_trace(go.Histogram(
            x=sf[sf["isGoal"]]["distance"], name="Goal",
            marker_color=RED, xbins=dict(size=2),
        ))
        fig_dist.update_layout(
            **PLOTLY_LAYOUT, height=300, barmode="overlay",
            xaxis=dict(title="Distance (m)", gridcolor="#eee"),
            yaxis=dict(title="Shots", gridcolor="#eee"),
            legend=dict(orientation="h",y=1.1),
        )
        st.plotly_chart(fig_dist, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — RESULTS
# ══════════════════════════════════════════════════════════════════════════════
with tab4:
    if match_results.empty:
        st.info("No results data.")
    else:
        mr = match_results.copy()
        if team_filter:
            mr = mr[mr["Home"].isin(team_filter)|mr["Away"].isin(team_filter)]

        # search
        search = st.text_input("Search team", "", placeholder="e.g. Arsenal", key="res_search")
        if search:
            mr = mr[mr["Home"].str.contains(search, case=False)|mr["Away"].str.contains(search, case=False)]

        # add xG to results
        def match_xg_lookup(home, away, date):
            s = shots[(shots["HomeTeam"]==home)&(shots["AwayTeam"]==away)&(shots["Date"].dt.date==date)]
            xg_h = round(s[s["TeamId"]==home]["xG"].sum(), 2) if not s.empty else np.nan
            xg_a = round(s[s["TeamId"]==away]["xG"].sum(), 2) if not s.empty else np.nan
            return xg_h, xg_a

        mr = mr.head(60)  # limit for performance
        xg_pairs = mr.apply(lambda r: pd.Series(match_xg_lookup(r["Home"],r["Away"],r["Date"])), axis=1)
        mr["xG H"] = xg_pairs[0]
        mr["xG A"] = xg_pairs[1]
        mr["xG H"] = mr["xG H"].round(2)
        mr["xG A"] = mr["xG A"].round(2)

        show_mr = ["Date","GW","Home","Score","Away","xG H","xG A","Result"] if "GW" in mr.columns else ["Date","Home","Score","Away","xG H","xG A","Result"]
        show_mr = [c for c in show_mr if c in mr.columns]

        st.markdown('<span class="pill">Match Results</span>', unsafe_allow_html=True)
        render_table(mr[show_mr].reset_index(drop=True))
        st.markdown('<p class="footnote">xG H / xG A = expected goals for home and away teams. Showing up to 60 most recent matches.</p>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 5 — PLAYERS
# ══════════════════════════════════════════════════════════════════════════════
with tab5:
    if player_stats.empty:
        st.info("No player data.")
    else:
        c1, c2, c3 = st.columns(3)
        with c1:
            p_team  = st.selectbox("Team", ["All"]+ALL_TEAMS, key="p_t")
        with c2:
            p_min   = st.number_input("Min shots", value=5, min_value=1, step=1)
        with c3:
            p_sort  = st.selectbox("Sort by", ["xG","Goals","Shots","Conv%","G-xG","xG/Sh","AvgDist"], key="p_s")

        pdf = player_stats.copy()
        if p_team != "All":
            pdf = pdf[pdf["Team"] == p_team]
        pdf = pdf[pdf["Shots"] >= p_min]
        pdf = pdf.sort_values(p_sort, ascending=False).reset_index(drop=True)
        pdf.insert(0, "Rank", pdf.index+1)

        show_p = ["Rank","Player","Team","Shots","Goals","xG","G-xG","xG/Sh","Conv%","BigCh","AvgDist"]
        show_p = [c for c in show_p if c in pdf.columns]

        st.markdown(f'<span class="pill">Top Players by {p_sort}</span>', unsafe_allow_html=True)
        render_table(
            pdf[show_p].head(30),
            heatmap_cols=["xG","Goals","Conv%","G-xG"],
            pal_map={"xG":"green","Goals":"green","Conv%":"green","G-xG":"blue"},
        )
        st.markdown('<p class="footnote">G-xG = goals minus expected goals. Positive = clinical finisher.</p>', unsafe_allow_html=True)

        # Top scorers bar
        top_n = pdf.sort_values("Goals", ascending=False).head(15)
        fig_p = go.Figure()
        fig_p.add_trace(go.Bar(
            y=top_n["Player"][::-1], x=top_n["Goals"][::-1],
            orientation="h", name="Goals", marker_color="#4caf50",
        ))
        fig_p.add_trace(go.Bar(
            y=top_n["Player"][::-1], x=top_n["xG"][::-1],
            orientation="h", name="xG", marker_color="rgba(33,150,243,0.55)",
        ))
        fig_p.update_layout(
            **PLOTLY_LAYOUT, height=420, barmode="overlay",
            xaxis=dict(title="Goals / xG", gridcolor="#eee"),
            yaxis=dict(tickfont=dict(size=10)),
            legend=dict(orientation="h",y=1.08),
        )
        st.markdown('<span class="pill">Goals vs xG — Top 15</span>', unsafe_allow_html=True)
        st.plotly_chart(fig_p, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 6 — TEAM DEEP DIVE
# ══════════════════════════════════════════════════════════════════════════════
with tab6:
    if shots.empty:
        st.info("No data.")
    else:
        team_sel = st.selectbox("Select team", ALL_TEAMS, key="dd_t")

        t_sh = shots[shots["TeamId"]==team_sel].copy()
        o_sh = shots[((shots["HomeTeam"]==team_sel)|(shots["AwayTeam"]==team_sel))&(shots["TeamId"]!=team_sel)].copy()
        t_row = team_stats[team_stats["Team"]==team_sel].iloc[0] if not team_stats.empty and (team_stats["Team"]==team_sel).any() else None
        s_row = standings[standings["Team"]==team_sel].iloc[0] if not standings.empty and (standings["Team"]==team_sel).any() else None

        # KPI row
        if t_row is not None and s_row is not None:
            st.markdown(f"""
            <div class="kpi-row">
              <div class="kpi-card"><div class="kpi-label">Points</div><div class="kpi-value">{int(s_row['Pts'])}</div><div class="kpi-sub">Rank #{int(s_row['Rank'])}</div></div>
              <div class="kpi-card green"><div class="kpi-label">xG / Match</div><div class="kpi-value">{t_row['xG/90']}</div><div class="kpi-sub">{t_row['xG']} total</div></div>
              <div class="kpi-card red"><div class="kpi-label">xGA / Match</div><div class="kpi-value">{t_row['xGA/90']}</div><div class="kpi-sub">{t_row['xGA']} total</div></div>
              <div class="kpi-card blue"><div class="kpi-label">G-xG</div><div class="kpi-value">{t_row['G-xG']:+.1f}</div><div class="kpi-sub">{'Over' if t_row['G-xG']>=0 else 'Under'}performing</div></div>
              <div class="kpi-card"><div class="kpi-label">Conv%</div><div class="kpi-value">{t_row['Conv%']}%</div><div class="kpi-sub">{int(t_row['GF'])} goals / {int(t_row['Sh'])} shots</div></div>
            </div>
            """, unsafe_allow_html=True)

        cols_dd = st.columns(2)

        # Match-by-match xG bar chart
        t_sh["_date"] = t_sh["Date"].dt.date
        o_sh["_date"] = o_sh["Date"].dt.date
        mbm_for = t_sh.groupby(["HomeTeam","AwayTeam","_date"]).agg(xGf=("xG","sum"),Gf=("isGoal","sum")).reset_index()
        mbm_ag  = o_sh.groupby(["HomeTeam","AwayTeam","_date"]).agg(xGa=("xG","sum"),Ga=("isGoal","sum")).reset_index()
        mbm = mbm_for.merge(mbm_ag, on=["HomeTeam","AwayTeam","_date"], how="outer")
        mbm["_date"] = pd.to_datetime(mbm["_date"], errors="coerce")
        mbm = mbm.dropna(subset=["_date"]).sort_values("_date")
        mbm["Match"] = mbm.apply(lambda r: f"{str(r['_date'].date())[:10]}\n{r['HomeTeam'].split()[0]} v {r['AwayTeam'].split()[0]}", axis=1)
        mbm["xGf"] = mbm["xGf"].round(2); mbm["xGa"] = mbm["xGa"].round(2)

        with cols_dd[0]:
            st.markdown('<span class="pill">Match-by-Match xG</span>', unsafe_allow_html=True)
            fig_mbm = go.Figure()
            fig_mbm.add_trace(go.Bar(x=mbm["Match"], y=mbm["xGf"], name="xG For",
                                     marker_color="#4caf50", marker_line_width=0))
            fig_mbm.add_trace(go.Bar(x=mbm["Match"], y=-mbm["xGa"], name="xGA",
                                     marker_color=RED, marker_line_width=0))
            fig_mbm.add_trace(go.Scatter(x=mbm["Match"], y=mbm["Gf"].fillna(0), name="Goals",
                                         mode="markers", marker=dict(symbol="star",size=10,color="gold",line=dict(color="darkgoldenrod",width=1))))
            fig_mbm.update_layout(
                **PLOTLY_LAYOUT, height=340, barmode="relative",
                xaxis=dict(showticklabels=False, title="Matches"),
                yaxis=dict(title="← xGA | xG For →", gridcolor="#eee"),
                legend=dict(orientation="h",y=1.1),
            )
            st.plotly_chart(fig_mbm, use_container_width=True)

        with cols_dd[1]:
            st.markdown('<span class="pill">Shot Map — This Season</span>', unsafe_allow_html=True)
            fig_t = go.Figure()
            for s in pitch_shapes():
                fig_t.add_shape(**s)
            miss_t = t_sh[~t_sh["isGoal"]]
            goal_t = t_sh[t_sh["isGoal"]]
            fig_t.add_trace(go.Scatter(
                x=miss_t["x"], y=miss_t["y"], mode="markers",
                marker=dict(size=miss_t["xG"]*50+5, color="rgba(100,149,237,0.45)",
                            line=dict(color="rgba(70,100,180,0.5)",width=1)),
                name="Shot", hovertemplate="%{customdata}<br>xG: %{marker.size:.2f}<extra></extra>",
                customdata=miss_t["PlayerId"].fillna(""),
            ))
            fig_t.add_trace(go.Scatter(
                x=goal_t["x"], y=goal_t["y"], mode="markers",
                marker=dict(size=goal_t["xG"]*50+8, color=RED, symbol="star",
                            line=dict(color="darkred",width=1)),
                name="Goal",
            ))
            fig_t.update_layout(
                **PLOTLY_LAYOUT, height=340,
                xaxis=dict(range=[-2,102],showgrid=False,zeroline=False,showticklabels=False),
                yaxis=dict(range=[-2,102],showgrid=False,zeroline=False,showticklabels=False,scaleanchor="x"),
                margin=dict(l=5,r=5,t=10,b=10),
                legend=dict(orientation="h",y=-0.05),
            )
            st.plotly_chart(fig_t, use_container_width=True)

        # Match-by-match table
        st.markdown('<span class="pill">Match Log</span>', unsafe_allow_html=True)
        mbm_show = mbm[["Match","xGf","xGa","Gf","Ga"]].copy().rename(
            columns={"xGf":"xG For","xGa":"xGA","Gf":"Goals","Ga":"GA"})
        mbm_show["xGD"] = (mbm_show["xG For"] - mbm_show["xGA"]).round(2)
        mbm_show = mbm_show.iloc[::-1].reset_index(drop=True)
        render_table(
            mbm_show, heatmap_cols=["xG For","xGA","xGD"],
            invert_cols=["xGA"],
            pal_map={"xG For":"green","xGA":"red","xGD":"blue"},
        )

        # Player breakdown for this team
        st.markdown('<span class="pill">Player Breakdown</span>', unsafe_allow_html=True)
        p_team_df = player_stats[player_stats["Team"]==team_sel].sort_values("xG",ascending=False).head(20).reset_index(drop=True)
        p_team_df.insert(0,"Rank",p_team_df.index+1)
        show_pt = ["Rank","Player","Shots","Goals","xG","G-xG","xG/Sh","Conv%","BigCh","AvgDist"]
        show_pt = [c for c in show_pt if c in p_team_df.columns]
        render_table(
            p_team_df[show_pt],
            heatmap_cols=["xG","Goals","Conv%"],
            pal_map={"xG":"green","Goals":"green","Conv%":"green"},
        )
