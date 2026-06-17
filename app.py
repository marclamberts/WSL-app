"""
WSL Stats Hub — FBRef-style player & team statistics
Data: Opta event JSON + xG CSV  |  Design: FBRef × FiveThirtyEight
"""
import streamlit as st
import pandas as pd
import numpy as np
import glob, os, json, io

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="WSL Stats Hub",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)

NAVY  = "#0d1b2a"
RED   = "#e63946"
CREAM = "#f7f7f5"

# ─────────────────────────────────────────────────────────────────────────────
# CSS — strip Streamlit chrome, custom design system
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:ital,wght@0,400;0,500;0,600;0,700;0,800;1,400&display=swap');

  /* ── Reset & base ── */
  html, body, [class*="css"], .stApp {{
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    color: {NAVY};
  }}

  /* ── Hide Streamlit chrome ── */
  #MainMenu, footer, header,
  [data-testid="stToolbar"],
  [data-testid="stDecoration"],
  [data-testid="stStatusWidget"],
  .viewerBadge_container__1QSob {{ display: none !important; }}

  /* ── Main canvas ── */
  .stApp {{ background: {CREAM}; }}
  .block-container {{
    padding: 0 2rem 3rem 2rem !important;
    max-width: 1400px !important;
  }}

  /* ── Sidebar ── */
  [data-testid="stSidebar"] {{
    background: {NAVY} !important;
    border-right: none !important;
    box-shadow: 2px 0 12px rgba(0,0,0,.15);
  }}
  [data-testid="stSidebar"] > div {{ padding-top: 0 !important; }}
  [data-testid="stSidebar"] * {{ color: #c8d8e8 !important; }}
  [data-testid="stSidebar"] hr {{ border-color: #1e3248 !important; margin: .75rem 0; }}

  /* Sidebar section header */
  [data-testid="stSidebar"] h3 {{
    color: #ffffff !important;
    font-size: .8rem !important;
    font-weight: 700 !important;
    letter-spacing: 1.2px !important;
    text-transform: uppercase !important;
    margin: 1.2rem 0 .5rem !important;
  }}

  /* Sidebar widget labels */
  [data-testid="stSidebar"] label,
  [data-testid="stSidebar"] .stSlider label {{
    color: #8aafc8 !important;
    font-size: .72rem !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: .8px !important;
  }}

  /* Sidebar multiselect + selectbox */
  [data-testid="stSidebar"] [data-testid="stMultiSelect"] > div > div,
  [data-testid="stSidebar"] [data-testid="stSelectbox"] > div > div {{
    background: #152535 !important;
    border: 1px solid #1e3248 !important;
    border-radius: 6px !important;
    color: #e0eaf4 !important;
  }}
  [data-testid="stSidebar"] [data-baseweb="tag"] {{
    background: {RED} !important;
    border-radius: 3px !important;
  }}
  [data-testid="stSidebar"] [data-baseweb="tag"] span {{ color: #fff !important; }}

  /* Sidebar slider */
  [data-testid="stSidebar"] [data-testid="stSlider"] [role="slider"] {{
    background: {RED} !important;
  }}
  [data-testid="stSidebar"] [data-testid="stSlider"] div[data-testid] > div > div:nth-child(2) {{
    background: {RED} !important;
  }}

  /* Sidebar toggle */
  [data-testid="stSidebar"] [data-testid="stToggle"] {{
    accent-color: {RED};
  }}
  [data-testid="stSidebar"] [role="switch"][aria-checked="true"] {{
    background-color: {RED} !important;
  }}
  [data-testid="stSidebar"] .stCaption p {{
    color: #4a6882 !important;
    font-size: .68rem !important;
    line-height: 1.5;
  }}

  /* ── Page header band ── */
  .hub-header {{
    background: {NAVY};
    color: #fff;
    padding: 1.25rem 2rem;
    border-bottom: 3px solid {RED};
    margin: 0 -2rem 1.75rem -2rem;
  }}
  .hub-header h1 {{
    margin: 0; font-size: 1.75rem; font-weight: 800; letter-spacing: -.5px;
    display: flex; align-items: center; gap: .5rem;
  }}
  .hub-header h1 span.badge {{
    font-size: .65rem; font-weight: 700; letter-spacing: 1.2px;
    text-transform: uppercase; background: {RED};
    padding: 3px 8px; border-radius: 3px; vertical-align: middle;
  }}
  .hub-header p {{ margin: .3rem 0 0; font-size: .8rem; color: #7a9db8; }}

  /* ── Section pill ── */
  .pill {{
    background: {RED}; color: #fff;
    font-size: .6rem; font-weight: 700; letter-spacing: 1.8px;
    text-transform: uppercase; padding: 3px 9px;
    border-radius: 2px; display: inline-block; margin-bottom: .6rem;
  }}

  /* ── KPI cards ── */
  .kpi-row {{ display: flex; gap: .65rem; flex-wrap: wrap; margin-bottom: 1.5rem; }}
  .kpi-card {{
    background: #fff;
    border-top: 3px solid {NAVY};
    padding: .9rem 1.1rem;
    flex: 1; min-width: 130px;
    border-radius: 0 0 6px 6px;
    box-shadow: 0 1px 4px rgba(0,0,0,.06), 0 4px 12px rgba(0,0,0,.04);
    transition: box-shadow .15s;
  }}
  .kpi-card:hover {{ box-shadow: 0 2px 8px rgba(0,0,0,.1), 0 6px 20px rgba(0,0,0,.06); }}
  .kpi-card.red   {{ border-top-color: {RED}; }}
  .kpi-card.blue  {{ border-top-color: #2196f3; }}
  .kpi-card.green {{ border-top-color: #2e7d32; }}
  .kpi-card .kl {{ font-size: .62rem; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; color: #999; }}
  .kpi-card .kv {{ font-size: 1.35rem; font-weight: 800; color: {NAVY}; line-height: 1.15; margin: .2rem 0 .1rem; }}
  .kpi-card .ks {{ font-size: .72rem; color: #666; }}

  /* ── Tables ── */
  .tbl-wrap {{
    background: #fff;
    border: 1px solid #e4e4e0;
    box-shadow: 0 1px 3px rgba(0,0,0,.05);
    overflow-x: auto; margin-bottom: 1.25rem;
    border-radius: 6px;
  }}
  .tbl-wrap table {{ border-collapse: collapse; width: 100%; font-size: .8rem; white-space: nowrap; }}
  .tbl-wrap thead tr {{
    background: {NAVY}; color: #fff;
    font-size: .67rem; font-weight: 600;
    text-transform: uppercase; letter-spacing: .9px;
  }}
  .tbl-wrap thead th {{
    padding: 9px 13px; text-align: right;
    border-right: 1px solid #1a2e42;
    position: sticky; top: 0;
  }}
  .tbl-wrap thead th.left {{ text-align: left; }}
  .tbl-wrap tbody tr {{ border-bottom: 1px solid #f0f0ec; transition: background .08s; }}
  .tbl-wrap tbody tr:hover {{ background: #f0f5ff !important; }}
  .tbl-wrap tbody tr:nth-child(even) {{ background: #fafaf7; }}
  .tbl-wrap tbody td {{ padding: 7px 13px; text-align: right; }}
  .tbl-wrap tbody td.left  {{ text-align: left; }}
  .tbl-wrap tbody td.rank  {{ text-align: center; color: #aaa; font-weight: 600; font-size: .75rem; width: 32px; }}
  .tbl-wrap tbody td.name  {{ font-weight: 600; color: {NAVY}; }}
  .tbl-wrap tbody td.team  {{ color: #777; font-size: .76rem; }}
  .tbl-wrap tbody td.pos   {{ text-align: center; }}

  /* ── Position badges ── */
  .pos-badge {{
    border-radius: 3px; padding: 2px 6px;
    font-size: .66rem; font-weight: 700; color: #fff;
    letter-spacing: .3px;
  }}
  .pos-GK  {{ background: #7b1fa2; }}
  .pos-DEF {{ background: #1565c0; }}
  .pos-MID {{ background: #2e7d32; }}
  .pos-FWD {{ background: {RED}; }}

  /* ── Tabs ── */
  [data-testid="stTabs"] {{
    border-bottom: 2px solid #e4e4e0;
    margin-bottom: .1rem;
  }}
  [data-testid="stTabs"] [role="tablist"] {{ gap: 0; }}
  [data-testid="stTabs"] [role="tab"] {{
    font-size: .74rem; font-weight: 600;
    text-transform: uppercase; letter-spacing: .7px;
    padding: 8px 20px; color: #888;
    border-bottom: 3px solid transparent !important;
    transition: color .15s;
    margin-bottom: -2px;
  }}
  [data-testid="stTabs"] [role="tab"]:hover {{ color: {NAVY}; }}
  [data-testid="stTabs"] [aria-selected="true"] {{
    color: {RED} !important;
    border-bottom-color: {RED} !important;
  }}

  /* ── Selectbox in main area ── */
  [data-testid="stSelectbox"] > div > div {{
    border-radius: 6px !important;
    border-color: #ddd !important;
    font-size: .82rem !important;
  }}

  /* ── Download buttons ── */
  .stDownloadButton > button {{
    background: #fff !important;
    color: {NAVY} !important;
    border: 1.5px solid #ddd !important;
    border-radius: 6px !important;
    font-size: .75rem !important;
    font-weight: 600 !important;
    padding: .35rem .9rem !important;
    transition: all .15s !important;
    box-shadow: 0 1px 3px rgba(0,0,0,.06) !important;
  }}
  .stDownloadButton > button:hover {{
    border-color: {RED} !important;
    color: {RED} !important;
    box-shadow: 0 2px 6px rgba(230,57,70,.15) !important;
  }}

  /* ── Footnote ── */
  .footnote {{ font-size: .7rem; color: #aaa; margin-top: -.2rem; margin-bottom: .9rem; }}

  /* ── Custom scrollbar ── */
  ::-webkit-scrollbar {{ width: 6px; height: 6px; }}
  ::-webkit-scrollbar-track {{ background: #f0f0ec; }}
  ::-webkit-scrollbar-thumb {{ background: #ccc; border-radius: 3px; }}
  ::-webkit-scrollbar-thumb:hover {{ background: #aaa; }}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────
WSL_DIR     = os.path.join(os.path.dirname(__file__), "WSL")
XG_DIR      = os.path.join(WSL_DIR, "xgCSV")
MATCHES_CSV = os.path.join(os.path.dirname(__file__), "WSL Matches.csv")
MATCH_MINS  = 90

POS_MAP  = {"1": "GK", "2": "DEF", "3": "MID", "4": "FWD"}
POS_ORDER = {"GK": 0, "DEF": 1, "MID": 2, "FWD": 3}

# Opta event type IDs
T_PASS        = 1
T_OFFSIDE_P   = 2
T_TAKE_ON     = 3
T_FOUL        = 4
T_SHOT_MISS   = 13
T_SHOT_POST   = 14
T_SHOT_SAVED  = 15
T_GOAL        = 16
T_CARD        = 17
T_SUB_OFF     = 18
T_SUB_ON      = 19
T_SAVE        = 10
T_CLAIM       = 11
T_CLEARANCE   = 12
T_INTERCEPTION= 8
T_TACKLE      = 7
T_AERIAL      = 74
T_DRIBBLE     = 3
T_KEEPER_PICK = 11

SHOT_TYPES = {T_SHOT_MISS, T_SHOT_POST, T_SHOT_SAVED, T_GOAL}

# ─────────────────────────────────────────────────────────────────────────────
# JSON PARSER
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner="Parsing match events…")
def parse_all_matches():
    json_files = glob.glob(os.path.join(WSL_DIR, "*.json"))
    if not json_files:
        return pd.DataFrame(), pd.DataFrame()

    player_rows = []   # one row per player per match
    event_rows  = []   # one row per event (for raw stats)

    for fp in json_files:
        fname = os.path.basename(fp).replace(".json", "")
        # filename: YYYY-MM-DD_HomeTeam - AwayTeam
        try:
            date_str, match_str = fname.split("_", 1)
            home_name, away_name = [s.strip() for s in match_str.split(" - ", 1)]
        except ValueError:
            continue

        with open(fp, "r", encoding="utf-8") as fh:
            try:
                data = json.load(fh)
            except Exception:
                continue

        events = data.get("event", [])
        md     = data.get("matchDetails", {})
        match_len = md.get("matchLengthMin", MATCH_MINS)

        # ── build contestant -> team name map ──────────────────────────────
        lineup_events = [e for e in events if e.get("typeId") == 34]
        contestant_team = {}
        if len(lineup_events) >= 2:
            contestant_team[lineup_events[0]["contestantId"]] = home_name
            contestant_team[lineup_events[1]["contestantId"]] = away_name
        elif len(lineup_events) == 1:
            contestant_team[lineup_events[0]["contestantId"]] = home_name

        # ── build player roster from lineup ───────────────────────────────
        # {playerId: {name, team, position, jersey, starter}}
        roster = {}
        for le in lineup_events:
            team_name = contestant_team.get(le["contestantId"], "Unknown")
            qs = {q["qualifierId"]: q.get("value", "") for q in le.get("qualifier", [])}
            player_ids = [x.strip() for x in qs.get(30, "").split(",") if x.strip()]
            positions  = [x.strip() for x in qs.get(44, "").split(",") if x.strip()]
            jerseys    = [x.strip() for x in qs.get(59, "").split(",") if x.strip()]
            jersey_map = {str(i+1): j for i, j in enumerate(jerseys)}
            starter_list = [x.strip() for x in qs.get(131, "").split(",") if x.strip()]

            for idx, pid in enumerate(player_ids):
                pos_code = positions[idx] if idx < len(positions) else "5"
                pos      = POS_MAP.get(pos_code, "SUB")
                jersey   = jerseys[idx] if idx < len(jerseys) else ""
                is_start = (starter_list[idx] if idx < len(starter_list) else "0") != "0"
                roster[pid] = {
                    "team": team_name,
                    "pos":  pos,
                    "jersey": jersey,
                    "starter": is_start,
                    "name": "",   # filled from events
                }

        # ── extract minutes played from sub events ────────────────────────
        sub_off_times = {}  # playerId -> timeMin
        sub_on_times  = {}  # playerId -> timeMin
        for e in events:
            tid = e.get("typeId")
            pid = e.get("playerId", "")
            if not pid:
                continue
            if tid == T_SUB_OFF:
                sub_off_times[pid] = e.get("timeMin", match_len)
            elif tid == T_SUB_ON:
                sub_on_times[pid] = e.get("timeMin", 0)
                # grab position from qualifier 44 if available
                qs = {q["qualifierId"]: q.get("value","") for q in e.get("qualifier",[])}
                if qs.get(44) and pid in roster:
                    pos_txt = qs.get(44,"").strip()
                    pos_map2 = {"Goalkeeper":"GK","Defender":"DEF","Midfielder":"MID","Forward":"FWD"}
                    roster.setdefault(pid, {})["pos"] = pos_map2.get(pos_txt, roster[pid].get("pos","SUB"))

        # Fill player names from events
        for e in events:
            pid  = e.get("playerId","")
            pname= e.get("playerName","")
            cid  = e.get("contestantId","")
            if pid and pname and pid in roster:
                roster[pid]["name"] = pname
            elif pid and pname and pid not in roster:
                # sub-on player not in starting lineup entry
                roster[pid] = {
                    "team": contestant_team.get(cid, "Unknown"),
                    "pos":  "SUB",
                    "jersey": "",
                    "starter": False,
                    "name": pname,
                }

        # Compute minutes for each player
        def calc_mins(pid, info):
            if info.get("starter"):
                if pid in sub_off_times:
                    return sub_off_times[pid]
                return match_len
            else:
                on  = sub_on_times.get(pid, None)
                off = sub_off_times.get(pid, None)
                if on is not None:
                    return (off if off is not None else match_len) - on
                return 0

        # ── aggregate events per player ───────────────────────────────────
        stats = {}  # playerId -> dict of counts
        for e in events:
            pid = e.get("playerId","")
            if not pid:
                continue
            tid = e.get("typeId")
            outcome = e.get("outcome", 0)
            qs_list = e.get("qualifier",[])
            qs = {q["qualifierId"]: q.get("value","") for q in qs_list}

            s = stats.setdefault(pid, {
                "passes":0,"passes_cmp":0,"key_passes":0,
                "shots":0,"goals":0,"saves":0,
                "tackles":0,"tackles_won":0,
                "interceptions":0,"clearances":0,
                "dribbles":0,"dribbles_won":0,
                "fouls_committed":0,"fouls_won":0,
                "yellow":0,"red":0,
                "aerials":0,"aerials_won":0,
                "ga":0,"clean_sheet":0,
            })

            if tid == T_PASS:
                s["passes"] += 1
                if outcome == 1:
                    s["passes_cmp"] += 1
                # key pass: qualifier 210 or 55 with specific value
                if 210 in qs or 211 in qs:
                    s["key_passes"] += 1
            elif tid == T_TACKLE:
                s["tackles"] += 1
                if outcome == 1:
                    s["tackles_won"] += 1
            elif tid == T_INTERCEPTION:
                s["interceptions"] += 1
            elif tid == T_CLEARANCE:
                s["clearances"] += 1
            elif tid in SHOT_TYPES:
                s["shots"] += 1
                if tid == T_GOAL:
                    s["goals"] += 1
            elif tid == T_SAVE:
                s["saves"] += 1
                s["ga"] += 0  # GA counted from goal events vs GK team
            elif tid == T_FOUL:
                if outcome == 0:
                    s["fouls_committed"] += 1
                else:
                    s["fouls_won"] += 1
            elif tid == T_CARD:
                if 31 in qs:
                    s["yellow"] += 1
                if 32 in qs or 33 in qs:
                    s["red"] += 1
            elif tid == T_TAKE_ON:
                s["dribbles"] += 1
                if outcome == 1:
                    s["dribbles_won"] += 1
            elif tid == T_AERIAL:
                s["aerials"] += 1
                if outcome == 1:
                    s["aerials_won"] += 1

        # ── count GA for GKs ─────────────────────────────────────────────
        goal_events = [e for e in events if e.get("typeId") == T_GOAL]
        for ge in goal_events:
            scoring_team_cid = ge.get("contestantId")
            # GA goes to the opposing GK
            for pid, info in roster.items():
                team_cid = next((k for k,v in contestant_team.items() if v==info["team"]), None)
                if team_cid and team_cid != scoring_team_cid and info.get("pos") == "GK":
                    stats.setdefault(pid, {}).setdefault("ga", 0)
                    stats[pid]["ga"] = stats[pid].get("ga", 0) + 1

        # ── build player rows ─────────────────────────────────────────────
        for pid, info in roster.items():
            if not info.get("name"):
                continue
            mins = calc_mins(pid, info)
            if mins <= 0:
                continue
            s = stats.get(pid, {})
            player_rows.append({
                "Player":   info["name"],
                "Team":     info["team"],
                "Pos":      info["pos"],
                "Jersey":   info["jersey"],
                "Match":    match_str,
                "Date":     date_str,
                "Home":     home_name,
                "Away":     away_name,
                "Mins":     mins,
                "Starter":  int(info.get("starter", False)),
                "Goals":    s.get("goals", 0),
                "Shots":    s.get("shots", 0),
                "Saves":    s.get("saves", 0),
                "GA":       s.get("ga", 0),
                "Passes":   s.get("passes", 0),
                "PassCmp":  s.get("passes_cmp", 0),
                "KP":       s.get("key_passes", 0),
                "Tackles":  s.get("tackles", 0),
                "TklWon":   s.get("tackles_won", 0),
                "Inter":    s.get("interceptions", 0),
                "Clears":   s.get("clearances", 0),
                "Dribbles": s.get("dribbles", 0),
                "DribWon":  s.get("dribbles_won", 0),
                "FoulsCom": s.get("fouls_committed", 0),
                "FoulsWon": s.get("fouls_won", 0),
                "Yellow":   s.get("yellow", 0),
                "Red":      s.get("red", 0),
                "Aerials":  s.get("aerials", 0),
                "AerWon":   s.get("aerials_won", 0),
            })

    df = pd.DataFrame(player_rows) if player_rows else pd.DataFrame()
    return df


@st.cache_data(show_spinner="Loading xG data…")
def load_xg():
    files = glob.glob(os.path.join(XG_DIR, "*.csv"))
    if not files:
        return pd.DataFrame()
    dfs = []
    for f in files:
        try:
            dfs.append(pd.read_csv(f, index_col=0))
        except Exception:
            pass
    shots = pd.concat(dfs, ignore_index=True)
    shots["xG"]     = pd.to_numeric(shots["xG"], errors="coerce").fillna(0)
    shots["isGoal"] = shots["isGoal"].astype(str).str.upper().isin(["TRUE","1","YES"])
    shots["isBigChance"] = shots["isBigChance"].astype(str).str.upper().isin(["YES","TRUE","1"])
    return shots


# ─────────────────────────────────────────────────────────────────────────────
# AGGREGATE PLAYER STATS
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data
def build_player_summary(match_df, xg_df):
    if match_df.empty:
        return pd.DataFrame()

    grp = match_df.groupby(["Player","Team","Pos"]).agg(
        GP       =("Match","nunique"),
        Starts   =("Starter","sum"),
        Mins     =("Mins","sum"),
        Goals    =("Goals","sum"),
        Shots    =("Shots","sum"),
        Saves    =("Saves","sum"),
        GA       =("GA","sum"),
        Passes   =("Passes","sum"),
        PassCmp  =("PassCmp","sum"),
        KP       =("KP","sum"),
        Tackles  =("Tackles","sum"),
        TklWon   =("TklWon","sum"),
        Inter    =("Inter","sum"),
        Clears   =("Clears","sum"),
        Dribbles =("Dribbles","sum"),
        DribWon  =("DribWon","sum"),
        FoulsCom =("FoulsCom","sum"),
        FoulsWon =("FoulsWon","sum"),
        Yellow   =("Yellow","sum"),
        Red      =("Red","sum"),
        Aerials  =("Aerials","sum"),
        AerWon   =("AerWon","sum"),
    ).reset_index()

    # xG merge
    if not xg_df.empty:
        xg_grp = xg_df.groupby("PlayerId").agg(
            xG       =("xG","sum"),
            npxG     =("xG","sum"),   # simplified: no pen separation
            BigCh    =("isBigChance","sum"),
        ).reset_index().rename(columns={"PlayerId":"Player"})
        grp = grp.merge(xg_grp, on="Player", how="left")
    else:
        grp["xG"] = np.nan
        grp["npxG"] = np.nan
        grp["BigCh"] = np.nan

    grp["xG"]   = grp["xG"].fillna(0).round(2)
    grp["npxG"] = grp["npxG"].fillna(0).round(2)
    grp["BigCh"]= grp["BigCh"].fillna(0).astype(int)

    # per-90 helpers
    m90 = grp["Mins"].replace(0, np.nan) / 90
    grp["G/90"]    = (grp["Goals"] / m90).round(2)
    grp["xG/90"]   = (grp["xG"]   / m90).round(2)
    grp["Sh/90"]   = (grp["Shots"] / m90).round(2)
    grp["KP/90"]   = (grp["KP"]   / m90).round(2)
    grp["Tkl/90"]  = (grp["Tackles"] / m90).round(2)
    grp["Int/90"]  = (grp["Inter"]   / m90).round(2)
    grp["Pass/90"] = (grp["Passes"]  / m90).round(2)

    grp["Pass%"]   = (grp["PassCmp"] / grp["Passes"].replace(0,np.nan) * 100).round(1)
    grp["Tkl%"]    = (grp["TklWon"]  / grp["Tackles"].replace(0,np.nan) * 100).round(1)
    grp["Drib%"]   = (grp["DribWon"] / grp["Dribbles"].replace(0,np.nan) * 100).round(1)
    grp["Aer%"]    = (grp["AerWon"]  / grp["Aerials"].replace(0,np.nan) * 100).round(1)
    grp["Save%"]   = (grp["Saves"]   / (grp["Saves"]+grp["GA"]).replace(0,np.nan) * 100).round(1)
    grp["G-xG"]    = (grp["Goals"]   - grp["xG"]).round(2)
    grp["SoT"]     = grp["Goals"]     # approx: shots on target ≈ goals + saves against (not tracked per shooter in JSON)
    # Better SoT from xgCSV if available
    if not xg_df.empty:
        sot = xg_df[xg_df["isGoal"] | xg_df["Bodypart"].notna()].groupby("PlayerId").size().reset_index()
        # Use shots on target from xg file directly (every row is a shot attempt, goals are SoT)
        goals_xg = xg_df[xg_df["isGoal"]].groupby("PlayerId").size().reset_index(name="SoT_g")
        # shots on target = goals + saves (we can't separate easily, so just use shots)
        grp["SoT"] = np.nan  # leave as nan, compute from available data

    grp = grp.sort_values(["Pos","Mins"], key=lambda s: s.map(POS_ORDER) if s.name=="Pos" else s, ascending=[True,False])
    return grp.reset_index(drop=True)


# ─────────────────────────────────────────────────────────────────────────────
# LOAD DATA
# ─────────────────────────────────────────────────────────────────────────────
match_df = parse_all_matches()
xg_df    = load_xg()
player_df = build_player_summary(match_df, xg_df)

ALL_TEAMS = sorted(player_df["Team"].dropna().unique()) if not player_df.empty else []
ALL_POS   = ["GK","DEF","MID","FWD"]

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR FILTERS
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"""
    <div style="background:{RED};margin:-1rem -1rem 0 -1rem;padding:1rem 1.25rem .9rem;">
      <div style="font-size:.62rem;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;color:rgba(255,255,255,.7);margin-bottom:.2rem;">Barclays WSL 2025/26</div>
      <div style="font-size:1.1rem;font-weight:800;color:#fff;letter-spacing:-.3px;">⚽ Stats Hub</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### Filters")
    sel_teams = st.multiselect("Team", ALL_TEAMS, placeholder="All teams")
    sel_pos   = st.multiselect("Position", ALL_POS, placeholder="All positions")
    min_mins  = st.slider("Min. minutes", 0, 900, 90, step=45)

    st.markdown("---")
    st.markdown("### Display")
    per90_mode = st.toggle("Per-90 mode", value=False,
                           help="Show rate stats per 90 minutes instead of totals")
    show_n = st.slider("Rows to show", 10, 100, 30, step=10)

    st.markdown("---")
    st.caption("Data: Opta / StatsBomb\nDesign: FBRef × FiveThirtyEight\nMinutes & positions from match lineups")


# ─────────────────────────────────────────────────────────────────────────────
# FILTER DATA
# ─────────────────────────────────────────────────────────────────────────────
df = player_df.copy()
if sel_teams:
    df = df[df["Team"].isin(sel_teams)]
if sel_pos:
    df = df[df["Pos"].isin(sel_pos)]
df = df[df["Mins"] >= min_mins]


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def heat(val, vmin, vmax, pal="blue", inv=False):
    try:
        val = float(val)
    except (TypeError, ValueError):
        return ""
    if np.isnan(val) or vmin == vmax:
        return ""
    r = np.clip((val - vmin) / (vmax - vmin), 0, 1)
    if inv:
        r = 1 - r
    if pal == "red":
        rgb = (int(255*(.95-.55*r)), int(255*(.95-.70*r)), int(255*(.95-.70*r)))
    elif pal == "green":
        rgb = (int(255*(.95-.70*r)), int(255*(.75+.15*r)), int(255*(.95-.70*r)))
    else:
        rgb = (int(255*(.95-.65*r)), int(255*(.95-.55*r)), int(255*(.95-.05*r)))
    txt = "white" if r > .62 else NAVY
    return f"background:rgb{rgb};color:{txt};"

def pos_badge(pos):
    return f'<span class="pos-badge pos-{pos}">{pos}</span>'

def fmt_val(val, decimals=1):
    if pd.isna(val):
        return "—"
    if isinstance(val, float):
        return f"{val:.{decimals}f}"
    return str(int(val))

def render_table(df_show, heat_cols=None, inv_cols=None, pal_map=None,
                 left_cols=None, pct_cols=None):
    heat_cols = heat_cols or []
    inv_cols  = inv_cols  or []
    pal_map   = pal_map   or {}
    left_cols = left_cols or ["Player","Team","Pos"]
    pct_cols  = pct_cols  or []

    # compute min/max for heat
    col_stats = {}
    for c in heat_cols:
        if c in df_show.columns:
            vals = pd.to_numeric(df_show[c], errors="coerce").dropna()
            if len(vals):
                col_stats[c] = (float(vals.min()), float(vals.max()))

    header = "".join(
        f'<th class="left">{c}</th>' if c in left_cols else f"<th>{c}</th>"
        for c in df_show.columns
    )
    rows_html = []
    for i, row in enumerate(df_show.itertuples(index=False), 1):
        cells = []
        for c in df_show.columns:
            val = getattr(row, c.replace(" ","_").replace("/","_").replace("%","_").replace("-","_"), None)
            val = row[df_show.columns.get_loc(c)]
            style = ""
            if c == "Rank":
                cell = f'<td class="rank">{i}</td>'
                cells.append(cell); continue
            elif c == "Player":
                cell = f'<td class="name left">{val}</td>'
                cells.append(cell); continue
            elif c == "Team":
                cell = f'<td class="team left">{val}</td>'
                cells.append(cell); continue
            elif c == "Pos":
                cell = f'<td class="pos">{pos_badge(val) if val in ALL_POS else val}</td>'
                cells.append(cell); continue
            else:
                if c in col_stats:
                    vmin, vmax = col_stats[c]
                    style = heat(val, vmin, vmax, pal_map.get(c,"blue"), c in inv_cols)
                decimals = 1 if c in pct_cols or "/" in c else (2 if isinstance(val, float) and not pd.isna(val) and abs(float(val)) < 10 else 0)
                cell_txt = fmt_val(val, decimals)
                td_class = "left" if c in left_cols else ""
                cells.append(f'<td class="{td_class}" style="{style}">{cell_txt}</td>')
        rows_html.append("<tr>" + "".join(cells) + "</tr>")

    st.markdown(f"""
    <div class="tbl-wrap">
      <table>
        <thead><tr>{header}</tr></thead>
        <tbody>{"".join(rows_html)}</tbody>
      </table>
    </div>""", unsafe_allow_html=True)


def download_buttons(df_dl, label):
    """CSV + Excel download buttons side by side."""
    col1, col2, col3 = st.columns([1,1,4])
    csv_bytes = df_dl.to_csv(index=False).encode()
    col1.download_button(f"⬇ CSV", csv_bytes, f"wsl_{label}.csv", "text/csv", use_container_width=True)
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="xlsxwriter") as writer:
        df_dl.to_excel(writer, index=False, sheet_name=label[:31])
    col2.download_button(f"⬇ Excel", buf.getvalue(), f"wsl_{label}.xlsx",
                         "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                         use_container_width=True)


def top_n(df_in, sort_col, n, ascending=False):
    if sort_col not in df_in.columns:
        return df_in.head(n)
    return df_in.sort_values(sort_col, ascending=ascending).head(n).reset_index(drop=True)


# ─────────────────────────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────────────────────────
n_players = len(df)
n_matches = match_df["Match"].nunique() if not match_df.empty else 0
st.markdown(f"""
<div class="hub-header">
  <h1>WSL Stats Hub <span class="badge">2025/26</span></h1>
  <p>Barclays Women's Super League &nbsp;·&nbsp;
     {n_matches} matches &nbsp;·&nbsp; {n_players} players shown
     {"&nbsp;·&nbsp; <strong style='color:#e9c46a'>Per-90 mode</strong>" if per90_mode else ""}
  </p>
</div>
""", unsafe_allow_html=True)

# KPI cards
if not df.empty:
    top_scorer = df.sort_values("Goals", ascending=False).iloc[0] if "Goals" in df else None
    top_xg     = df.sort_values("xG",    ascending=False).iloc[0] if "xG"    in df else None
    top_pass   = df[df["Passes"]>50].sort_values("Pass%", ascending=False).iloc[0] if "Pass%" in df and len(df[df["Passes"]>50]) else None
    top_tkl    = df.sort_values("Tackles",ascending=False).iloc[0] if "Tackles" in df else None

    st.markdown(f"""
    <div class="kpi-row">
      <div class="kpi-card green">
        <div class="kl">Top Scorer</div>
        <div class="kv">{top_scorer['Player'] if top_scorer is not None else '—'}</div>
        <div class="ks">{int(top_scorer['Goals']) if top_scorer is not None else 0} goals · {top_scorer['Team'] if top_scorer is not None else ''}</div>
      </div>
      <div class="kpi-card blue">
        <div class="kl">Top xG</div>
        <div class="kv">{top_xg['Player'] if top_xg is not None else '—'}</div>
        <div class="ks">{top_xg['xG'] if top_xg is not None else 0} xG · {top_xg['Team'] if top_xg is not None else ''}</div>
      </div>
      <div class="kpi-card">
        <div class="kl">Best Pass%</div>
        <div class="kv">{top_pass['Player'] if top_pass is not None else '—'}</div>
        <div class="ks">{top_pass['Pass%'] if top_pass is not None else 0}% · {top_pass['Passes'] if top_pass is not None else 0} passes</div>
      </div>
      <div class="kpi-card red">
        <div class="kl">Most Tackles</div>
        <div class="kv">{top_tkl['Player'] if top_tkl is not None else '—'}</div>
        <div class="ks">{int(top_tkl['Tackles']) if top_tkl is not None else 0} tackles · {top_tkl['Team'] if top_tkl is not None else ''}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────────────────────────────────────
tab_sum, tab_shoot, tab_pass, tab_def, tab_gk, tab_misc = st.tabs([
    "📊  Summary", "⚽  Shooting", "🎯  Passing", "🛡  Defence", "🧤  Goalkeeping", "🃏  Discipline & Duels"
])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — SUMMARY
# ══════════════════════════════════════════════════════════════════════════════
with tab_sum:
    st.markdown('<span class="pill">Player Summary</span>', unsafe_allow_html=True)

    sort_sum = st.selectbox("Sort by", ["Goals","xG","Mins","GP","Shots","Passes","Tackles","KP"], key="ss")
    df_s = top_n(df, sort_sum, show_n)

    cols_sum = ["Player","Team","Pos","GP","Starts","Mins","Goals","xG","G-xG","Shots","Passes","Pass%","KP","Tackles","Yellow","Red"]
    cols_sum = [c for c in cols_sum if c in df_s.columns]

    if per90_mode:
        for c, r in [("Goals","G/90"),("xG","xG/90"),("Shots","Sh/90"),("Passes","Pass/90"),("KP","KP/90"),("Tackles","Tkl/90")]:
            if r in df_s.columns:
                cols_sum = [r if x==c else x for x in cols_sum]
        cols_sum = list(dict.fromkeys(cols_sum))  # dedupe

    df_s = df_s[[c for c in cols_sum if c in df_s.columns]]
    render_table(df_s,
        heat_cols=["Goals","xG","G-xG","Mins","Passes","KP","G/90","xG/90","Sh/90"],
        inv_cols=[],
        pal_map={"Goals":"green","xG":"green","G-xG":"blue","Mins":"blue",
                 "Passes":"blue","G/90":"green","xG/90":"green"},
    )
    st.markdown('<p class="footnote">G-xG = goals minus expected goals (positive = overperforming). KP = key passes.</p>', unsafe_allow_html=True)
    download_buttons(df_s, "summary")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — SHOOTING
# ══════════════════════════════════════════════════════════════════════════════
with tab_shoot:
    st.markdown('<span class="pill">Shooting Statistics</span>', unsafe_allow_html=True)

    sort_sh = st.selectbox("Sort by", ["xG","Goals","Shots","G-xG","xG/90","Sh/90","BigCh"], key="ssh")
    df_sh = top_n(df, sort_sh, show_n)

    # Goals per shot
    df_sh = df_sh.copy()
    df_sh["G/Sh"] = (df_sh["Goals"] / df_sh["Shots"].replace(0,np.nan)).round(3)
    df_sh["xG/Sh"]= (df_sh["xG"]   / df_sh["Shots"].replace(0,np.nan)).round(3)

    cols_sh = ["Player","Team","Pos","GP","Mins","Goals","Shots","G/Sh","xG","npxG","xG/Sh","G-xG","BigCh","xG/90","Sh/90","G/90"]
    cols_sh = [c for c in cols_sh if c in df_sh.columns]
    df_sh = df_sh[cols_sh]

    render_table(df_sh,
        heat_cols=["Goals","xG","Shots","G-xG","BigCh","xG/90","Sh/90","G/90","G/Sh","xG/Sh"],
        pal_map={"Goals":"green","xG":"green","Shots":"blue","G-xG":"blue",
                 "BigCh":"green","xG/90":"green","G/90":"green"},
    )
    st.markdown('<p class="footnote">npxG = non-penalty xG (approx). G/Sh = goals per shot. xG/Sh = xG per shot quality. BigCh = big chances.</p>', unsafe_allow_html=True)
    download_buttons(df_sh, "shooting")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — PASSING
# ══════════════════════════════════════════════════════════════════════════════
with tab_pass:
    st.markdown('<span class="pill">Passing Statistics</span>', unsafe_allow_html=True)

    sort_pa = st.selectbox("Sort by", ["Passes","Pass%","KP","Pass/90","KP/90"], key="spa")
    df_pa = top_n(df[df["Passes"] > 0], sort_pa, show_n)

    cols_pa = ["Player","Team","Pos","GP","Mins","Passes","PassCmp","Pass%","KP","Pass/90","KP/90","FoulsWon"]
    cols_pa = [c for c in cols_pa if c in df_pa.columns]
    df_pa = df_pa[cols_pa]

    render_table(df_pa,
        heat_cols=["Passes","PassCmp","Pass%","KP","Pass/90","KP/90"],
        pal_map={"Passes":"blue","PassCmp":"blue","Pass%":"green","KP":"green","Pass/90":"blue","KP/90":"green"},
    )
    st.markdown('<p class="footnote">PassCmp = completed passes. Pass% = completion rate. KP = key passes (Opta qualifier). FoulsWon = fouls drawn.</p>', unsafe_allow_html=True)
    download_buttons(df_pa, "passing")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — DEFENCE
# ══════════════════════════════════════════════════════════════════════════════
with tab_def:
    st.markdown('<span class="pill">Defensive Statistics</span>', unsafe_allow_html=True)

    df_def_base = df[df["Pos"].isin(["DEF","MID","FWD","GK"])]
    sort_de = st.selectbox("Sort by", ["Tackles","TklWon","Inter","Clears","Tkl%","Tkl/90","Int/90","Aerials","Aer%"], key="sde")
    df_de = top_n(df_def_base, sort_de, show_n)

    cols_de = ["Player","Team","Pos","GP","Mins","Tackles","TklWon","Tkl%","Inter","Clears","Aerials","AerWon","Aer%","Tkl/90","Int/90","FoulsCom","Yellow","Red"]
    cols_de = [c for c in cols_de if c in df_de.columns]
    df_de = df_de[cols_de]

    render_table(df_de,
        heat_cols=["Tackles","TklWon","Tkl%","Inter","Clears","Aerials","AerWon","Aer%","Tkl/90","Int/90"],
        inv_cols=["FoulsCom","Yellow","Red"],
        pal_map={"Tackles":"blue","TklWon":"green","Tkl%":"green","Inter":"blue","Clears":"blue",
                 "Aerials":"blue","Aer%":"green","Tkl/90":"blue","Int/90":"blue"},
        pct_cols=["Tkl%","Aer%"],
    )
    st.markdown('<p class="footnote">TklWon = tackles won. Tkl% = tackle success rate. Aer% = aerial duel win rate.</p>', unsafe_allow_html=True)
    download_buttons(df_de, "defence")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 5 — GOALKEEPING
# ══════════════════════════════════════════════════════════════════════════════
with tab_gk:
    st.markdown('<span class="pill">Goalkeeping Statistics</span>', unsafe_allow_html=True)

    df_gk_base = df[df["Pos"] == "GK"].copy()
    if df_gk_base.empty:
        st.info("No goalkeeper data for current filters.")
    else:
        # Clean sheets: matches where GA = 0
        cs_data = match_df[match_df["Pos"] == "GK"].groupby(["Player","Team"]).apply(
            lambda g: (g["GA"] == 0).sum()
        ).reset_index(name="CS") if not match_df.empty else pd.DataFrame(columns=["Player","Team","CS"])

        df_gk_m = df_gk_base.merge(cs_data, on=["Player","Team"], how="left")
        df_gk_m["CS"] = df_gk_m["CS"].fillna(0).astype(int)
        df_gk_m["GA/90"] = (df_gk_m["GA"] / (df_gk_m["Mins"] / 90).replace(0, np.nan)).round(2)

        sort_gk = st.selectbox("Sort by", ["Saves","Save%","GA","CS","Mins","GA/90"], key="sgk")
        asc_gk  = sort_gk in ("GA","GA/90")
        df_gk_s = df_gk_m.sort_values(sort_gk, ascending=asc_gk).head(show_n).reset_index(drop=True)

        cols_gk = ["Player","Team","GP","Starts","Mins","GA","Saves","Save%","CS","GA/90"]
        cols_gk = [c for c in cols_gk if c in df_gk_s.columns]
        df_gk_s = df_gk_s[cols_gk]

        render_table(df_gk_s,
            heat_cols=["Saves","Save%","CS"],
            inv_cols=["GA","GA/90"],
            pal_map={"Saves":"blue","Save%":"green","CS":"green","GA":"red","GA/90":"red"},
            pct_cols=["Save%"],
        )
        st.markdown('<p class="footnote">Save% = saves/(saves+GA). CS = clean sheets. GA/90 = goals against per 90 min.</p>', unsafe_allow_html=True)
        download_buttons(df_gk_s, "goalkeeping")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 6 — DISCIPLINE & DUELS
# ══════════════════════════════════════════════════════════════════════════════
with tab_misc:
    st.markdown('<span class="pill">Discipline & Duels</span>', unsafe_allow_html=True)

    c1, c2 = st.columns(2)

    with c1:
        st.markdown('<span class="pill">Discipline</span>', unsafe_allow_html=True)
        sort_disc = st.selectbox("Sort by", ["Yellow","Red","FoulsCom","FoulsWon"], key="sdisc")
        df_disc = top_n(df, sort_disc, show_n)
        cols_disc = ["Player","Team","Pos","GP","Mins","FoulsCom","FoulsWon","Yellow","Red"]
        cols_disc = [c for c in cols_disc if c in df_disc.columns]
        render_table(df_disc[cols_disc],
            heat_cols=["FoulsCom","Yellow","Red","FoulsWon"],
            inv_cols=["FoulsCom","Yellow","Red"],
            pal_map={"FoulsCom":"red","Yellow":"red","Red":"red","FoulsWon":"green"},
        )
        download_buttons(df_disc[cols_disc], "discipline")

    with c2:
        st.markdown('<span class="pill">Dribbles & Aerials</span>', unsafe_allow_html=True)
        sort_duel = st.selectbox("Sort by", ["Dribbles","DribWon","Drib%","Aerials","AerWon","Aer%"], key="sduel")
        df_duel = top_n(df, sort_duel, show_n)
        cols_duel = ["Player","Team","Pos","GP","Mins","Dribbles","DribWon","Drib%","Aerials","AerWon","Aer%"]
        cols_duel = [c for c in cols_duel if c in df_duel.columns]
        render_table(df_duel[cols_duel],
            heat_cols=["Dribbles","DribWon","Drib%","Aerials","AerWon","Aer%"],
            pal_map={"Dribbles":"blue","DribWon":"green","Drib%":"green",
                     "Aerials":"blue","AerWon":"green","Aer%":"green"},
            pct_cols=["Drib%","Aer%"],
        )
        download_buttons(df_duel[cols_duel], "duels")

    st.markdown('<p class="footnote">FoulsCom = fouls committed. FoulsWon = fouls drawn. Drib% = successful take-on rate. Aer% = aerial duel win %.</p>', unsafe_allow_html=True)
