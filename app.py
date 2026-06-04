"""
🏆 Prode Mundial 2026 — Tema claro
"""
import streamlit as st
import plotly.graph_objects as go
import json, math
from datetime import date, timedelta

st.set_page_config(
    page_title="Prode Mundial 2026",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@400;600;700;800&family=Barlow:wght@400;500;600&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body { background: #F0F4FF !important; }

.stApp {
    background: #F0F4FF !important;
    font-family: 'Barlow', sans-serif !important;
    color: #1A202C !important;
}

#MainMenu, footer, header, .stDeployButton,
[data-testid="collapsedControl"], .stAppHeader,
section[data-testid="stSidebar"] { display: none !important; }

.block-container { padding: 0 !important; max-width: 100% !important; }

/* ── NAVBAR ── */
.navbar {
    background: #1A1F3C;
    padding: 0 2.5rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    height: 60px;
}
.brand { font-family: 'Barlow Condensed', sans-serif; font-size: 1.4rem;
         font-weight: 800; letter-spacing: 3px; color: #FFD200; }
.brand-sub { font-size: 0.6rem; letter-spacing: 4px; color: #4A5568; margin-top: -2px; }
.nav-tag { font-size: 0.65rem; letter-spacing: 2px; color: #4A5568; text-transform: uppercase; }

/* ── TABS ── */
.stTabs [data-baseweb="tab-list"] {
    background: #fff !important;
    border-bottom: 2px solid #E2E8F0 !important;
    gap: 0 !important;
    padding: 0 2rem !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}
.stTabs [data-baseweb="tab"] {
    font-family: 'Barlow Condensed', sans-serif !important;
    font-size: 0.8rem !important;
    font-weight: 700 !important;
    letter-spacing: 2px !important;
    text-transform: uppercase !important;
    color: #94A3B8 !important;
    padding: 1rem 1.5rem !important;
    border: none !important;
    background: transparent !important;
}
.stTabs [aria-selected="true"] {
    color: #1A1F3C !important;
    border-bottom: 3px solid #4F6EF7 !important;
}
.stTabs [data-baseweb="tab-panel"] { padding: 2rem 2.5rem !important; background: #F0F4FF; }

/* ── KPI CARDS ── */
.kpi-grid { display: grid; grid-template-columns: repeat(4,1fr); gap: 1rem; margin-bottom: 2rem; }
.kpi-card {
    background: #fff;
    border-radius: 14px;
    padding: 1.4rem 1.6rem;
    box-shadow: 0 1px 4px rgba(0,0,0,0.07);
    border-top: 4px solid #4F6EF7;
}
.kpi-card.gold  { border-top-color: #F59E0B; }
.kpi-card.green { border-top-color: #10B981; }
.kpi-card.red   { border-top-color: #EF4444; }
.kpi-val { font-family:'Barlow Condensed',sans-serif; font-size:2.6rem; font-weight:800; color:#1A1F3C; line-height:1; }
.kpi-lbl { font-size:0.65rem; letter-spacing:2px; text-transform:uppercase; color:#94A3B8; margin-top:4px; }

/* ── SECTION TITLE ── */
.sec-title {
    font-family:'Barlow Condensed',sans-serif;
    font-size:0.75rem; font-weight:700;
    letter-spacing:4px; text-transform:uppercase;
    color:#94A3B8; margin-bottom:1rem;
    display:flex; align-items:center; gap:0.75rem;
}
.sec-title::after { content:''; flex:1; height:1px; background:#E2E8F0; }

/* ── MATCH CARD ── */
.match-card {
    background: #fff;
    border-radius: 14px;
    padding: 1.2rem 1.4rem 1rem;
    margin-bottom: 0.75rem;
    box-shadow: 0 1px 4px rgba(0,0,0,0.07);
    border-left: 4px solid #4F6EF7;
    transition: box-shadow 0.2s, transform 0.2s;
    position: relative;
}
.match-card:hover { box-shadow: 0 6px 20px rgba(79,110,247,0.15); transform: translateY(-2px); }
.match-stage { font-size:0.62rem; letter-spacing:2px; text-transform:uppercase; color:#CBD5E0; margin-bottom:0.7rem; }
.team-big { font-family:'Barlow Condensed',sans-serif; font-size:1.5rem; font-weight:700; color:#1A1F3C; }
.team-elo { font-size:0.68rem; color:#94A3B8; letter-spacing:1px; margin-top:1px; }
.vs-mid { font-family:'Barlow Condensed',sans-serif; font-size:0.7rem; font-weight:700;
          letter-spacing:3px; color:#CBD5E0; text-align:center; }
.match-time-val { font-size:0.75rem; color:#4F6EF7; font-weight:600; text-align:center; margin-top:2px; }
.venue-txt { font-size:0.62rem; color:#CBD5E0; margin-top:0.5rem; }

/* prob bars */
.prow { display:flex; align-items:center; gap:0.5rem; margin-top:0.5rem; }
.plbl { font-size:0.62rem; letter-spacing:1px; color:#94A3B8; width:20px; text-transform:uppercase; }
.ptrack { flex:1; height:5px; background:#F0F4FF; border-radius:3px; overflow:hidden; }
.phome { height:100%; background:#4F6EF7; border-radius:3px; }
.pdraw { height:100%; background:#94A3B8; border-radius:3px; }
.paway { height:100%; background:#F97316; border-radius:3px; }
.ppct { font-family:'Barlow Condensed',sans-serif; font-size:0.8rem; font-weight:600; color:#4A5568; width:34px; text-align:right; }

/* ── PREDICTOR ── */
.pred-hero {
    background: linear-gradient(135deg, #1A1F3C 0%, #2D3561 100%);
    border-radius: 20px;
    padding: 2.5rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 1.5rem;
    position: relative;
    overflow: hidden;
}
.pred-hero::before {
    content: '';
    position: absolute;
    right: -60px; top: -60px;
    width: 200px; height: 200px;
    background: rgba(255,210,0,0.06);
    border-radius: 50%;
}
.pred-team-name { font-family:'Barlow Condensed',sans-serif; font-size:2rem; font-weight:800;
                  letter-spacing:2px; color:#fff; }
.pred-team-elo  { font-size:0.7rem; color:rgba(255,255,255,0.35); letter-spacing:2px; margin-top:4px; }
.pred-vs        { font-family:'Barlow Condensed',sans-serif; font-size:0.9rem; letter-spacing:4px; color:rgba(255,255,255,0.2); }

.score-hero {
    background: #fff;
    border-radius: 16px;
    padding: 2rem;
    text-align: center;
    box-shadow: 0 4px 20px rgba(0,0,0,0.08);
    border: 2px solid #4F6EF7;
}
.score-hero-lbl { font-size:0.62rem; letter-spacing:3px; text-transform:uppercase; color:#94A3B8; margin-bottom:0.5rem; }
.score-hero-val { font-family:'Barlow Condensed',sans-serif; font-size:5rem; font-weight:800;
                  color:#1A1F3C; line-height:1; letter-spacing:8px; }
.score-hero-sub { font-size:0.72rem; color:#94A3B8; margin-top:0.75rem; line-height:1.5; }

.score-pill {
    display:inline-block; background:#F0F4FF; border:1px solid #E2E8F0;
    border-radius:8px; padding:5px 14px; margin:3px;
    font-family:'Barlow Condensed',sans-serif; font-size:1rem;
    font-weight:700; letter-spacing:2px; color:#4A5568;
    transition: all 0.15s;
}
.score-pill.top { background:#4F6EF7; color:#fff; border-color:#4F6EF7; }

.prob-card {
    background:#fff; border-radius:14px; padding:1.5rem;
    box-shadow:0 1px 4px rgba(0,0,0,0.07);
}
.prob-big-lbl { font-size:0.65rem; letter-spacing:2px; text-transform:uppercase; color:#94A3B8; }
.prob-big-val { font-family:'Barlow Condensed',sans-serif; font-size:2.8rem; font-weight:800; line-height:1.1; }
.prob-home { color:#4F6EF7; }
.prob-draw { color:#94A3B8; }
.prob-away { color:#F97316; }

.goals-chip {
    background:#F0F4FF; border-radius:10px; padding:1rem;
    text-align:center; flex:1;
}
.goals-val { font-family:'Barlow Condensed',sans-serif; font-size:2.2rem; font-weight:700; }
.goals-lbl { font-size:0.62rem; letter-spacing:2px; color:#94A3B8; text-transform:uppercase; margin-top:2px; }

/* ── ELO ── */
.elo-row { display:flex; align-items:center; padding:0.65rem 0.75rem; border-radius:8px; margin-bottom:2px; }
.elo-row:hover { background:#fff; }
.elo-rank { font-family:'Barlow Condensed',sans-serif; font-size:0.85rem; color:#CBD5E0; width:26px; }
.elo-name { flex:1; font-size:0.88rem; font-weight:500; color:#2D3748; }
.elo-grp  { font-size:0.62rem; letter-spacing:2px; color:#CBD5E0; width:36px; text-align:center; }
.elo-bar-wrap { width:120px; height:4px; background:#EDF2F7; border-radius:2px; overflow:hidden; margin:0 0.75rem; }
.elo-bar-fill { height:100%; background:linear-gradient(90deg,#4F6EF7,#7C3AED); border-radius:2px; }
.elo-val { font-family:'Barlow Condensed',sans-serif; font-size:0.95rem; font-weight:700; color:#1A1F3C; width:44px; text-align:right; }

/* ── BUTTONS ── */
.stButton > button {
    background: #4F6EF7 !important;
    color: #fff !important;
    border: none !important;
    border-radius: 10px !important;
    font-family: 'Barlow Condensed', sans-serif !important;
    font-size: 0.8rem !important;
    font-weight: 700 !important;
    letter-spacing: 2px !important;
    text-transform: uppercase !important;
    padding: 0.65rem 1.2rem !important;
    width: 100% !important;
    transition: all 0.15s !important;
}
.stButton > button:hover { background: #3B56D4 !important; transform: translateY(-1px) !important; }

/* ── SELECTBOX ── */
.stSelectbox [data-baseweb="select"] > div {
    background: #fff !important;
    border: 1.5px solid #E2E8F0 !important;
    border-radius: 10px !important;
    color: #1A202C !important;
}

/* ── SLIDER ── */
.stSlider { accent-color: #4F6EF7; }
[data-baseweb="slider"] { accent-color: #4F6EF7 !important; }

/* ── DATE INPUT ── */
.stDateInput input { background:#fff !important; border:1.5px solid #E2E8F0 !important;
                     color:#1A202C !important; border-radius:10px !important; }

/* ── EXPANDER ── */
.stExpander { background:#fff !important; border:1px solid #E2E8F0 !important;
              border-radius:12px !important; }
.stExpander summary { color:#1A202C !important; }

/* ── METRICS ── */
[data-testid="stMetric"] { background:#fff; border-radius:12px; padding:1rem;
                            box-shadow:0 1px 4px rgba(0,0,0,0.07); }
[data-testid="stMetricValue"] { font-family:'Barlow Condensed',sans-serif !important;
                                 font-size:2rem !important; color:#1A1F3C !important; }
[data-testid="stMetricLabel"] { font-size:0.62rem !important; letter-spacing:2px !important;
                                  color:#94A3B8 !important; text-transform:uppercase !important; }

/* ── ALERTS ── */
.stAlert { border-radius:10px !important; }
[data-testid="stInfo"]    { background:#EEF2FF !important; color:#3730A3 !important; border:none !important; }
[data-testid="stSuccess"] { background:#ECFDF5 !important; color:#065F46 !important; border:none !important; }

/* ── SCROLLBAR ── */
::-webkit-scrollbar { width:5px; }
::-webkit-scrollbar-track { background:#F0F4FF; }
::-webkit-scrollbar-thumb { background:#CBD5E0; border-radius:3px; }

hr { border-color:#E2E8F0 !important; }
</style>
""", unsafe_allow_html=True)

# ─── imports ──────────────────────────────────────────────────────────────────
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from data.database import init_db, seed_teams, seed_group_stage_matches, get_connection
from utils.api_fetcher import get_upcoming_matches, sync_all, inject_demo_odds
from models.predictor import predict_match
from models.elo import get_all_elo_ratings, get_elo_win_probability
from utils.report_generator import generate_daily_report, get_performance_stats, evaluate_finished_matches

@st.cache_resource
def initialize_app():
    init_db()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) as n FROM teams");  nt = cur.fetchone()["n"]
    cur.execute("SELECT COUNT(*) as n FROM matches"); nm = cur.fetchone()["n"]
    conn.close()
    if nt == 0: seed_teams()
    if nm == 0:
        seed_group_stage_matches()
        inject_demo_odds()
    return True

initialize_app()

# ── NAVBAR ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="navbar">
    <div>
        <div class="brand">⚽ Prode Mundial 2026</div>
        <div class="brand-sub">Elo · Poisson · Monte Carlo</div>
    </div>
    <div class="nav-tag">FIFA World Cup · USA · CAN · MEX</div>
</div>
""", unsafe_allow_html=True)

tab_dash, tab_pred, tab_report, tab_elo, tab_perf = st.tabs([
    "Dashboard", "Predictor", "Informe", "Ranking Elo", "Rendimiento"
])

# ══════════════════════════════════════════════════════════════
# DASHBOARD
# ══════════════════════════════════════════════════════════════
with tab_dash:
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("SELECT COUNT(*) as n FROM matches WHERE status='SCHEDULED'"); ns = cur.fetchone()["n"]
    cur.execute("SELECT COUNT(*) as n FROM matches WHERE status='FINISHED'");  nf = cur.fetchone()["n"]
    cur.execute("SELECT COUNT(*) as n FROM predictions");                       np = cur.fetchone()["n"]
    cur.execute("SELECT COUNT(*) as n FROM teams");                             nt = cur.fetchone()["n"]
    conn.close()

    st.markdown(f"""
    <div class="kpi-grid">
      <div class="kpi-card">      <div class="kpi-val">{nt}</div> <div class="kpi-lbl">Selecciones</div></div>
      <div class="kpi-card gold"> <div class="kpi-val">{ns}</div> <div class="kpi-lbl">Programados</div></div>
      <div class="kpi-card green"><div class="kpi-val">{nf}</div> <div class="kpi-lbl">Jugados</div></div>
      <div class="kpi-card red">  <div class="kpi-val">{np}</div> <div class="kpi-lbl">Predicciones</div></div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns([3,1,1])
    with c1: days = st.slider("Días", 1, 21, 7, label_visibility="collapsed")
    with c2:
        if st.button("↺ Sincronizar"):
            with st.spinner(): sync_all(demo_mode=True)
            st.success("Listo")
    with c3:
        if st.button("✓ Evaluar"):
            n = evaluate_finished_matches(); st.info(f"{n} evaluados")

    st.markdown('<div class="sec-title">Próximos partidos</div>', unsafe_allow_html=True)

    upcoming = get_upcoming_matches(days)
    if not upcoming:
        st.info("No hay partidos en este período.")
    else:
        by_date = {}
        for m in upcoming: by_date.setdefault(m["match_date"], []).append(m)

        for d, day_matches in by_date.items():
            st.markdown(f'<div style="font-family:Barlow Condensed,sans-serif;font-size:0.7rem;letter-spacing:3px;'
                        f'text-transform:uppercase;color:#4F6EF7;margin:1.2rem 0 0.5rem;font-weight:700;">📅 {d}</div>',
                        unsafe_allow_html=True)
            cols = st.columns(min(len(day_matches), 3))
            for i, m in enumerate(day_matches):
                probs = get_elo_win_probability(m["home_name"], m["away_name"])
                hw = int(probs["home_win"]*100)
                dw = int(probs["draw"]*100)
                aw = int(probs["away_win"]*100)
                accent = "#4F6EF7" if probs["home_win"]>probs["away_win"] else "#F97316"

                with cols[i % len(cols)]:
                    st.markdown(f"""
                    <div class="match-card" style="border-left-color:{accent}">
                      <div class="match-stage">{m.get('stage','')}{'  ·  Grupo '+m['group_name'] if m.get('group_name') else ''}</div>
                      <div style="display:flex;align-items:center;gap:0.5rem;">
                        <div style="flex:1;">
                          <div class="team-big">{m['home_name']}</div>
                          <div class="team-elo">ELO {int(m['home_elo'])}</div>
                        </div>
                        <div>
                          <div class="vs-mid">VS</div>
                          <div class="match-time-val">{m.get('match_time','TBD')}</div>
                        </div>
                        <div style="flex:1;text-align:right;">
                          <div class="team-big">{m['away_name']}</div>
                          <div class="team-elo">ELO {int(m['away_elo'])}</div>
                        </div>
                      </div>
                      <div class="venue-txt">📍 {m.get('city','')}</div>
                      <div style="margin-top:0.75rem;padding-top:0.75rem;border-top:1px solid #F0F4FF;">
                        <div class="prow"><span class="plbl">L</span><div class="ptrack"><div class="phome" style="width:{hw}%"></div></div><span class="ppct">{hw}%</span></div>
                        <div class="prow"><span class="plbl">X</span><div class="ptrack"><div class="pdraw" style="width:{dw}%"></div></div><span class="ppct">{dw}%</span></div>
                        <div class="prow"><span class="plbl">V</span><div class="ptrack"><div class="paway" style="width:{aw}%"></div></div><span class="ppct">{aw}%</span></div>
                      </div>
                    </div>
                    """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# PREDICTOR
# ══════════════════════════════════════════════════════════════
with tab_pred:
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("""SELECT m.id, m.match_date, m.stage, m.group_name,
                          th.name as hn, ta.name as an
                   FROM matches m
                   JOIN teams th ON m.home_team_id=th.id
                   JOIN teams ta ON m.away_team_id=ta.id
                   WHERE m.status='SCHEDULED' ORDER BY m.match_date, m.match_time""")
    all_m = [dict(r) for r in cur.fetchall()]
    conn.close()

    st.markdown('<div class="sec-title">Elegí el partido</div>', unsafe_allow_html=True)

    if not all_m:
        st.warning("Sin partidos disponibles.")
    else:
        opts = {f"{m['match_date']}  ·  {m['hn']}  vs  {m['an']}": m["id"] for m in all_m}
        ca, cb, cc = st.columns([3,1,1])
        with ca: chosen = st.selectbox("Partido", list(opts.keys()), label_visibility="collapsed")
        with cb: n_sim  = st.select_slider("Sims", [10_000,25_000,50_000,100_000], 50_000, label_visibility="collapsed")
        with cc: run    = st.button("⚡  Predecir")

        if run:
            with st.spinner("Corriendo simulaciones Monte Carlo..."):
                pred = predict_match(opts[chosen], n_simulations=n_sim)

            if not pred:
                st.error("No se pudo generar la predicción.")
            else:
                # Hero header
                st.markdown(f"""
                <div class="pred-hero">
                  <div>
                    <div class="pred-team-name">{pred['home_team']}</div>
                    <div class="pred-team-elo">ELO {int(pred['home_elo'])} · Forma {'↑' if pred['home_form']>1 else '↓'} {pred['home_form']:.2f}</div>
                  </div>
                  <div style="text-align:center;">
                    <div class="pred-vs">VS</div>
                    {'<div style="font-size:0.6rem;color:#FFD200;letter-spacing:2px;margin-top:4px;">CON CUOTAS REALES</div>' if pred['used_odds'] else ''}
                  </div>
                  <div style="text-align:right;">
                    <div class="pred-team-name">{pred['away_team']}</div>
                    <div class="pred-team-elo">ELO {int(pred['away_elo'])} · Forma {'↑' if pred['away_form']>1 else '↓'} {pred['away_form']:.2f}</div>
                  </div>
                </div>
                """, unsafe_allow_html=True)

                col_l, col_r = st.columns([1,1])

                with col_l:
                    # Probabilidades grandes
                    st.markdown('<div class="sec-title">Probabilidades</div>', unsafe_allow_html=True)
                    st.markdown(f"""
                    <div style="display:flex;gap:1rem;margin-bottom:1rem;">
                      <div class="prob-card" style="flex:1;text-align:center;">
                        <div class="prob-big-lbl">{pred['home_team'][:12]}</div>
                        <div class="prob-big-val prob-home">{pred['home_win_prob']*100:.0f}%</div>
                      </div>
                      <div class="prob-card" style="flex:1;text-align:center;">
                        <div class="prob-big-lbl">Empate</div>
                        <div class="prob-big-val prob-draw">{pred['draw_prob']*100:.0f}%</div>
                      </div>
                      <div class="prob-card" style="flex:1;text-align:center;">
                        <div class="prob-big-lbl">{pred['away_team'][:12]}</div>
                        <div class="prob-big-val prob-away">{pred['away_win_prob']*100:.0f}%</div>
                      </div>
                    </div>
                    """, unsafe_allow_html=True)

                    # Goles esperados
                    st.markdown(f"""
                    <div style="display:flex;gap:1rem;margin-bottom:1.5rem;">
                      <div class="goals-chip">
                        <div class="goals-val" style="color:#4F6EF7;">{pred['expected_home_goals']:.2f}</div>
                        <div class="goals-lbl">Goles {pred['home_team'][:10]}</div>
                      </div>
                      <div class="goals-chip">
                        <div class="goals-val" style="color:#F97316;">{pred['expected_away_goals']:.2f}</div>
                        <div class="goals-lbl">Goles {pred['away_team'][:10]}</div>
                      </div>
                    </div>
                    """, unsafe_allow_html=True)

                    # Gráfico barras
                    fig = go.Figure(go.Bar(
                        x=[pred['home_team'][:10], "Empate", pred['away_team'][:10]],
                        y=[pred['home_win_prob']*100, pred['draw_prob']*100, pred['away_win_prob']*100],
                        marker=dict(color=['#4F6EF7','#94A3B8','#F97316'], line=dict(width=0)),
                        text=[f"{v:.1f}%" for v in [pred['home_win_prob']*100, pred['draw_prob']*100, pred['away_win_prob']*100]],
                        textposition='outside',
                        textfont=dict(size=13, family='Barlow Condensed', color='#1A202C'),
                        width=0.5,
                    ))
                    fig.update_layout(
                        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                        font=dict(color='#94A3B8', family='Barlow Condensed'),
                        yaxis=dict(range=[0,85], showgrid=False, showticklabels=False, zeroline=False),
                        xaxis=dict(showgrid=False, tickfont=dict(size=12, color='#4A5568')),
                        showlegend=False, height=240,
                        margin=dict(t=30,b=10,l=0,r=0),
                    )
                    st.plotly_chart(fig, use_container_width=True)

                with col_r:
                    # Marcador recomendado
                    st.markdown('<div class="sec-title">Para tu prode</div>', unsafe_allow_html=True)
                    st.markdown(f"""
                    <div class="score-hero">
                      <div class="score-hero-lbl">Marcador recomendado</div>
                      <div class="score-hero-val">{pred['recommended_score']}</div>
                      <div class="score-hero-sub">{pred['recommendation_rationale']}</div>
                    </div>
                    """, unsafe_allow_html=True)

                    st.markdown('<div class="sec-title" style="margin-top:1.2rem;">Top 5 marcadores</div>', unsafe_allow_html=True)
                    pills = ""
                    for i, s in enumerate(pred['top_scores'][:5]):
                        cls = "score-pill top" if i==0 else "score-pill"
                        pills += f'<span class="{cls}">{s["score"]} <span style="font-size:0.7rem;opacity:0.65">{s["prob"]*100:.1f}%</span></span>'
                    st.markdown(f'<div style="line-height:2.4;">{pills}</div>', unsafe_allow_html=True)

                    if pred.get('alternatives'):
                        st.markdown(f'<div style="margin-top:0.75rem;font-size:0.72rem;color:#94A3B8;">Alternativas: {" · ".join(pred["alternatives"])}</div>', unsafe_allow_html=True)

                # Heatmap
                st.markdown('<div class="sec-title" style="margin-top:1.5rem;">Probabilidad por marcador exacto</div>', unsafe_allow_html=True)
                mg = 5
                lh, la = pred['lambda_home'], pred['lambda_away']
                matrix = [[math.exp(-lh)*(lh**i)/math.factorial(i)*math.exp(-la)*(la**j)/math.factorial(j)*100
                           for j in range(mg+1)] for i in range(mg+1)]

                fig_hm = go.Figure(go.Heatmap(
                    z=matrix,
                    x=[str(j) for j in range(mg+1)],
                    y=[str(i) for i in range(mg+1)],
                    colorscale=[[0,'#EEF2FF'],[0.4,'#A5B4FC'],[0.7,'#4F6EF7'],[1,'#1E40AF']],
                    showscale=False,
                    text=[[f"{v:.1f}%" for v in row] for row in matrix],
                    texttemplate="%{text}",
                    textfont=dict(size=11, color='#1A202C'),
                ))
                fig_hm.update_layout(
                    xaxis=dict(title=dict(text=f"Goles {pred['away_team']}", font=dict(color='#94A3B8',size=11)), tickfont=dict(color='#94A3B8')),
                    yaxis=dict(title=dict(text=f"Goles {pred['home_team']}", font=dict(color='#94A3B8',size=11)), tickfont=dict(color='#94A3B8')),
                    plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(family='Barlow Condensed'),
                    height=320, margin=dict(t=10,b=60,l=60,r=10),
                )
                st.plotly_chart(fig_hm, use_container_width=True)

# ══════════════════════════════════════════════════════════════
# INFORME
# ══════════════════════════════════════════════════════════════
with tab_report:
    st.markdown('<div class="sec-title">Informe diario de predicciones</div>', unsafe_allow_html=True)

    wc_start = date(2026,6,11); wc_end = date(2026,7,19)
    default  = min(max(date.today()+timedelta(days=1), wc_start), wc_end)

    cd, cb2 = st.columns([2,1])
    with cd: target = st.date_input("Fecha", value=default, min_value=wc_start, max_value=wc_end, label_visibility="collapsed")
    with cb2: gen = st.button("📋  Generar informe")

    if gen:
        with st.spinner("Generando..."):
            report = generate_daily_report(target.isoformat())

        st.markdown(f'<div style="font-size:0.8rem;color:#64748B;margin-bottom:1rem;">{report["summary"]}</div>', unsafe_allow_html=True)

        if not report["predictions"]:
            st.info("Sin partidos para esta fecha.")
        else:
            for item in report["predictions"]:
                p = item["prediction"]
                with st.expander(f"⚽  {p['home_team']}  vs  {p['away_team']}  —  Recomendado: {p['recommended_score']}", expanded=False):
                    mc1,mc2,mc3 = st.columns(3)
                    mc1.metric(p['home_team'][:14], f"{p['home_win_prob']*100:.1f}%")
                    mc2.metric("Empate", f"{p['draw_prob']*100:.1f}%")
                    mc3.metric(p['away_team'][:14], f"{p['away_win_prob']*100:.1f}%")
                    st.markdown(f"""
                    <div style="margin-top:1rem;padding:1rem 1.2rem;background:#EEF2FF;
                                border-left:3px solid #4F6EF7;border-radius:0 10px 10px 0;">
                      <span style="font-family:'Barlow Condensed';font-size:1.6rem;font-weight:800;
                                   color:#1A1F3C;letter-spacing:4px;">{p['recommended_score']}</span>
                      <span style="font-size:0.75rem;color:#64748B;margin-left:1rem;">{p['recommendation_rationale']}</span>
                    </div>
                    <div style="margin-top:0.75rem;font-size:0.78rem;color:#94A3B8;">
                      Top marcadores: {'  ·  '.join([s['score']+f" ({s['prob']*100:.1f}%)" for s in p['top_scores'][:5]])}
                    </div>
                    """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# RANKING ELO
# ══════════════════════════════════════════════════════════════
with tab_elo:
    st.markdown('<div class="sec-title">Ranking Elo — 50 selecciones</div>', unsafe_allow_html=True)

    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("SELECT name, group_name, elo_rating FROM teams ORDER BY elo_rating DESC")
    teams = [dict(r) for r in cur.fetchall()]
    conn.close()

    if teams:
        max_e, min_e = teams[0]["elo_rating"], teams[-1]["elo_rating"]
        half = len(teams)//2
        col_a, col_b = st.columns(2)

        for col, chunk, offset in [(col_a, teams[:half], 0), (col_b, teams[half:], half)]:
            with col:
                for i, t in enumerate(chunk):
                    rank = offset + i + 1
                    pct  = (t["elo_rating"]-min_e)/(max_e-min_e)*100
                    rc   = "#F59E0B" if rank<=3 else ("#4F6EF7" if rank<=10 else "#CBD5E0")
                    st.markdown(f"""
                    <div class="elo-row">
                      <span class="elo-rank" style="color:{rc};">#{rank}</span>
                      <span class="elo-name">{t['name']}</span>
                      <span class="elo-grp">G {t['group_name']}</span>
                      <div class="elo-bar-wrap"><div class="elo-bar-fill" style="width:{pct}%"></div></div>
                      <span class="elo-val">{int(t['elo_rating'])}</span>
                    </div>
                    """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# RENDIMIENTO
# ══════════════════════════════════════════════════════════════
with tab_perf:
    st.markdown('<div class="sec-title">Rendimiento del sistema</div>', unsafe_allow_html=True)

    stats   = get_performance_stats()
    overall = stats.get("overall", {})

    if not overall.get("total"):
        st.markdown("""
        <div style="background:#fff;border-radius:14px;padding:2.5rem;text-align:center;
                    box-shadow:0 1px 4px rgba(0,0,0,0.07);">
          <div style="font-size:3rem;margin-bottom:0.5rem;">📊</div>
          <div style="font-family:'Barlow Condensed';font-size:1rem;letter-spacing:2px;color:#94A3B8;text-transform:uppercase;">
            Las estadísticas aparecen cuando terminen los primeros partidos</div>
        </div>
        """, unsafe_allow_html=True)

        with st.expander("¿Cómo funciona la puntuación?"):
            st.markdown("""
**Sistema de puntos del prode:**
- ✅ Marcador exacto → **3 puntos**
- ☑️ Resultado correcto (1X2) → **1 punto**

**Estrategia para 30 participantes:**

El sistema calcula el valor esperado considerando que los demás también eligen.
En partidos parejos recomienda marcadores menos populares para maximizar puntos exclusivos.
            """)
    else:
        total  = overall.get("total", 0)
        exact  = overall.get("exact_matches", 0) or 0
        cor    = overall.get("correct_outcomes", 0) or 0
        pts    = overall.get("total_points", 0) or 0

        st.markdown(f"""
        <div class="kpi-grid">
          <div class="kpi-card">      <div class="kpi-val">{total}</div> <div class="kpi-lbl">Evaluados</div></div>
          <div class="kpi-card gold"> <div class="kpi-val">{exact}</div> <div class="kpi-lbl">Exactos ({exact/total*100:.0f}%)</div></div>
          <div class="kpi-card green"><div class="kpi-val">{cor}</div>   <div class="kpi-lbl">Resultado OK</div></div>
          <div class="kpi-card red">  <div class="kpi-val">{pts}</div>   <div class="kpi-lbl">Puntos totales</div></div>
        </div>
        """, unsafe_allow_html=True)

        if stats.get("exact_hits"):
            st.markdown('<div class="sec-title">Aciertos exactos</div>', unsafe_allow_html=True)
            for hit in stats["exact_hits"]:
                st.markdown(f"""
                <div style="display:flex;align-items:center;gap:1rem;padding:0.75rem 1rem;
                            background:#fff;border-radius:10px;margin-bottom:4px;
                            border-left:4px solid #4F6EF7;box-shadow:0 1px 3px rgba(0,0,0,0.06);">
                  <span style="font-family:'Barlow Condensed';font-size:1.2rem;font-weight:800;
                               color:#4F6EF7;letter-spacing:3px;">{hit['predicted_score']}</span>
                  <span style="font-size:0.85rem;color:#4A5568;">
                    {hit['home_name']} {hit['actual_home_score']}-{hit['actual_away_score']} {hit['away_name']}
                  </span>
                  <span style="margin-left:auto;font-size:0.7rem;color:#CBD5E0;">{hit['match_date']}</span>
                </div>
                """, unsafe_allow_html=True)

# footer
st.markdown("""
<div style="text-align:center;padding:2rem;font-size:0.62rem;letter-spacing:2px;
            color:#CBD5E0;text-transform:uppercase;background:#F0F4FF;">
  Prode Mundial 2026 &nbsp;·&nbsp; Elo + Poisson + Monte Carlo
  &nbsp;·&nbsp; football-data.org &nbsp;·&nbsp; the-odds-api.com
</div>
""", unsafe_allow_html=True)