"""
API Flask — Mundial 2026. Endpoints generales + técnicos.
"""
import os, sys, json, math
from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(__file__))
try:
    from dotenv import load_dotenv; load_dotenv()
except ImportError:
    pass

from data.database import get_connection, init_db
from data.seed_real import seed_real_teams, seed_real_matches
from utils.api_fetcher import inject_demo_odds, sync_all
from models.elo import get_elo_win_probability
from models.predictor import predict_match, poisson_score_matrix, elo_to_lambda, get_recent_form_adjustment

app = Flask(__name__, static_folder="web", static_url_path="")
CORS(app)

def ensure_data():
    init_db()
    conn = get_connection(); cur = conn.cursor()
    cur.execute("SELECT COUNT(*) as n FROM teams");  nt = cur.fetchone()["n"]
    cur.execute("SELECT COUNT(*) as n FROM matches"); nm = cur.fetchone()["n"]
    conn.close()
    if nt == 0: seed_real_teams()
    if nm == 0:
        seed_real_matches()
        inject_demo_odds()

ensure_data()

def q(sql, params=()):
    conn = get_connection(); cur = conn.cursor()
    cur.execute(sql, params)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close(); return rows

def q1(sql, params=()):
    r = q(sql, params); return r[0] if r else None

# ── helpers ────────────────────────────────────────────────────────────────
def poisson_p(lam, k):
    return math.exp(-lam) * (lam**k) / math.factorial(k)

def build_matrix(lh, la, max_g=7):
    matrix = []
    for i in range(max_g+1):
        row = []
        for j in range(max_g+1):
            p = poisson_p(lh, i) * poisson_p(la, j)
            row.append(round(p*100, 3))
        matrix.append(row)
    return matrix

def latest_pred_subquery():
    return """(SELECT match_id,home_win_prob,draw_prob,away_win_prob,
                      expected_home_goals,expected_away_goals,
                      recommended_score,top_scores,used_odds,model_version
               FROM predictions GROUP BY match_id HAVING MAX(generated_at))"""

# ── STATIC ──────────────────────────────────────────────────────────────────
@app.route("/")
def index(): return send_from_directory("web","index.html")

# ── GENERAL ─────────────────────────────────────────────────────────────────
@app.route("/api/stats")
def stats():
    conn = get_connection(); cur = conn.cursor()
    cur.execute("SELECT COUNT(*) as n FROM teams");    nt = cur.fetchone()["n"]
    cur.execute("SELECT COUNT(*) as n FROM matches");  nm = cur.fetchone()["n"]
    cur.execute("SELECT COUNT(*) as n FROM matches WHERE status='FINISHED'"); nf = cur.fetchone()["n"]
    cur.execute("SELECT COUNT(*) as n FROM predictions"); np = cur.fetchone()["n"]
    conn.close()
    return jsonify({"teams":nt,"matches":nm,"played":nf,"predictions":np})

@app.route("/api/groups")
def groups():
    teams = q("""
        SELECT t.id,t.name,t.fifa_code,t.group_name,t.elo_rating,
          COUNT(CASE WHEN (m.home_team_id=t.id OR m.away_team_id=t.id) AND m.status='FINISHED' THEN 1 END) as played,
          COUNT(CASE WHEN (m.home_team_id=t.id AND m.home_score>m.away_score) OR (m.away_team_id=t.id AND m.away_score>m.home_score) THEN 1 END) as won,
          COUNT(CASE WHEN (m.home_team_id=t.id OR m.away_team_id=t.id) AND m.status='FINISHED' AND m.home_score=m.away_score THEN 1 END) as drawn,
          COUNT(CASE WHEN (m.home_team_id=t.id AND m.home_score<m.away_score) OR (m.away_team_id=t.id AND m.away_score<m.home_score) THEN 1 END) as lost,
          COALESCE(SUM(CASE WHEN m.home_team_id=t.id THEN m.home_score WHEN m.away_team_id=t.id THEN m.away_score END),0) as gf,
          COALESCE(SUM(CASE WHEN m.home_team_id=t.id THEN m.away_score WHEN m.away_team_id=t.id THEN m.home_score END),0) as ga
        FROM teams t
        LEFT JOIN matches m ON (m.home_team_id=t.id OR m.away_team_id=t.id) AND m.stage LIKE '%Grupo%'
        GROUP BY t.id
        ORDER BY t.group_name,(won*3+drawn) DESC,(gf-ga) DESC,gf DESC
    """)
    out = {}
    for t in teams:
        t["points"] = t["won"]*3 + t["drawn"]; t["gd"] = t["gf"]-t["ga"]
        out.setdefault(t["group_name"],[]).append(t)
    return jsonify(out)

@app.route("/api/matches")
def matches():
    rows = q(f"""
        SELECT m.id,m.match_date,m.match_time,m.stage,m.group_name,
               m.home_score,m.away_score,m.status,m.venue,m.city,
               th.name as home_name,th.fifa_code as home_code,th.elo_rating as home_elo,
               ta.name as away_name,ta.fifa_code as away_code,ta.elo_rating as away_elo,
               p.home_win_prob,p.draw_prob,p.away_win_prob,
               p.expected_home_goals,p.expected_away_goals,p.recommended_score,p.top_scores
        FROM matches m
        JOIN teams th ON m.home_team_id=th.id
        JOIN teams ta ON m.away_team_id=ta.id
        LEFT JOIN {latest_pred_subquery()} p ON p.match_id=m.id
        ORDER BY m.match_date ASC,m.match_time ASC
    """)
    for r in rows:
        if r["top_scores"]:
            try: r["top_scores"]=json.loads(r["top_scores"])
            except: r["top_scores"]=[]
    return jsonify(rows)

@app.route("/api/matches/today")
def today():
    rows = q(f"""
        SELECT m.id,m.match_date,m.match_time,m.stage,m.group_name,
               m.home_score,m.away_score,m.status,m.city,
               th.name as home_name,th.fifa_code as home_code,th.elo_rating as home_elo,
               ta.name as away_name,ta.fifa_code as away_code,ta.elo_rating as away_elo,
               p.home_win_prob,p.draw_prob,p.away_win_prob,p.recommended_score
        FROM matches m
        JOIN teams th ON m.home_team_id=th.id
        JOIN teams ta ON m.away_team_id=ta.id
        LEFT JOIN {latest_pred_subquery()} p ON p.match_id=m.id
        WHERE m.match_date=?
        ORDER BY m.match_time ASC
    """, (date.today().isoformat(),))
    return jsonify(rows)

@app.route("/api/matches/upcoming")
def upcoming():
    rows = q(f"""
        SELECT m.id,m.match_date,m.match_time,m.stage,m.group_name,m.status,m.city,m.venue,
               th.name as home_name,th.fifa_code as home_code,th.elo_rating as home_elo,
               ta.name as away_name,ta.fifa_code as away_code,ta.elo_rating as away_elo,
               p.home_win_prob,p.draw_prob,p.away_win_prob,
               p.recommended_score,p.expected_home_goals,p.expected_away_goals,p.top_scores
        FROM matches m
        JOIN teams th ON m.home_team_id=th.id
        JOIN teams ta ON m.away_team_id=ta.id
        LEFT JOIN {latest_pred_subquery()} p ON p.match_id=m.id
        WHERE m.match_date BETWEEN ? AND ? AND m.status='SCHEDULED'
        ORDER BY m.match_date ASC,m.match_time ASC
    """, (date.today().isoformat(), (date.today()+timedelta(days=14)).isoformat()))
    for r in rows:
        if r["top_scores"]:
            try: r["top_scores"]=json.loads(r["top_scores"])
            except: r["top_scores"]=[]
        if not r["home_win_prob"]:
            pr = get_elo_win_probability(r["home_name"],r["away_name"])
            r["home_win_prob"]=pr["home_win"]; r["draw_prob"]=pr["draw"]; r["away_win_prob"]=pr["away_win"]
    return jsonify(rows)

@app.route("/api/matches/results")
def results():
    rows = q(f"""
        SELECT m.id,m.match_date,m.match_time,m.stage,m.group_name,
               m.home_score,m.away_score,m.status,m.city,
               th.name as home_name,th.fifa_code as home_code,
               ta.name as away_name,ta.fifa_code as away_code,
               p.recommended_score,p.home_win_prob,p.away_win_prob
        FROM matches m
        JOIN teams th ON m.home_team_id=th.id
        JOIN teams ta ON m.away_team_id=ta.id
        LEFT JOIN {latest_pred_subquery()} p ON p.match_id=m.id
        WHERE m.status='FINISHED'
        ORDER BY m.match_date DESC,m.match_time DESC
    """)
    return jsonify(rows)

@app.route("/api/predict/<int:match_id>")
def predict(match_id):
    pred = predict_match(match_id, n_simulations=30_000)
    return jsonify(pred or {})

@app.route("/api/standings")
def standings():
    rows = q("SELECT name,fifa_code,group_name,elo_rating FROM teams ORDER BY elo_rating DESC")
    return jsonify(rows)

@app.route("/api/fixture/knockout")
def knockout():
    rows = q("""
        SELECT m.id,m.match_date,m.stage,m.home_score,m.away_score,m.status,
               th.name as home_name,th.fifa_code as home_code,
               ta.name as away_name,ta.fifa_code as away_code
        FROM matches m
        JOIN teams th ON m.home_team_id=th.id
        JOIN teams ta ON m.away_team_id=ta.id
        WHERE m.stage NOT LIKE '%Grupo%'
        ORDER BY m.match_date ASC
    """)
    return jsonify(rows)

@app.route("/api/sync", methods=["POST"])
def sync():
    demo = request.json.get("demo", True) if request.json else True
    results = sync_all(demo_mode=demo)
    return jsonify({"ok": True, "results": results})

# ── TECHNICAL ENDPOINTS ─────────────────────────────────────────────────────

@app.route("/api/tech/match/<int:match_id>")
def tech_match(match_id):
    """
    Análisis técnico completo de un partido:
    - Lambdas de Poisson
    - Matriz completa de marcadores (8x8)
    - Probabilidades por resultado
    - Historial de forma (últimos 5)
    - Historial Elo de ambos equipos
    - Distribución marginal de goles
    - Valor esperado de goles
    - Entropía de la distribución
    - Odds implícitas vs modelo
    """
    m = q1(f"""
        SELECT m.*,
               th.name as home_name,th.fifa_code as home_code,th.elo_rating as home_elo,th.id as home_id,
               ta.name as away_name,ta.fifa_code as away_code,ta.elo_rating as away_elo,ta.id as away_id,
               p.home_win_prob,p.draw_prob,p.away_win_prob,
               p.expected_home_goals,p.expected_away_goals,p.recommended_score,p.top_scores,p.used_odds
        FROM matches m
        JOIN teams th ON m.home_team_id=th.id
        JOIN teams ta ON m.away_team_id=ta.id
        LEFT JOIN {latest_pred_subquery()} p ON p.match_id=m.id
        WHERE m.id=?
    """, (match_id,))
    if not m: return jsonify({"error":"Match not found"}), 404

    he, ae = m["home_elo"], m["away_elo"]
    hf = get_recent_form_adjustment(m["home_name"])
    af = get_recent_form_adjustment(m["away_name"])
    lh = elo_to_lambda(he-ae, 1.38) * hf
    la = elo_to_lambda(ae-he, 1.07) * af

    # Use stored lambdas if available
    if m.get("expected_home_goals"): lh = m["expected_home_goals"]
    if m.get("expected_away_goals"): la = m["expected_away_goals"]

    # Score matrix 8x8
    matrix = build_matrix(lh, la, max_g=7)

    # Marginal distributions
    home_marginal = [round(sum(matrix[i])/100, 4) for i in range(8)]
    away_marginal = [round(sum(row[j] for row in matrix)/100, 4) for j in range(8)]

    # Win/draw/away probs from matrix
    hw = da = aw = 0
    for i in range(8):
        for j in range(8):
            p = matrix[i][j]/100
            if i>j: hw+=p
            elif i==j: da+=p
            else: aw+=p

    # Entropy (uncertainty measure)
    flat = [matrix[i][j]/100 for i in range(8) for j in range(8)]
    entropy = -sum(p*math.log(p+1e-12) for p in flat)

    # Expected goals exact
    eg_home = sum(i * sum(matrix[i])/100 for i in range(8))
    eg_away = sum(j * sum(row[j] for row in matrix)/100 for j in range(8))

    # Top 15 scores
    scores_flat = []
    for i in range(8):
        for j in range(8):
            scores_flat.append({"score":f"{i}-{j}","prob":round(matrix[i][j]/100,4),"home":i,"away":j})
    scores_flat.sort(key=lambda x:-x["prob"])

    # Elo history (últimos 10 cambios)
    home_elo_hist = q("""
        SELECT eh.elo_rating, eh.recorded_at, m.match_date,
               CASE WHEN m.home_team_id=eh.team_id THEN ta.name ELSE th.name END as opponent
        FROM elo_history eh
        LEFT JOIN matches m ON m.id=eh.match_id
        LEFT JOIN teams th ON m.home_team_id=th.id
        LEFT JOIN teams ta ON m.away_team_id=ta.id
        WHERE eh.team_id=? ORDER BY eh.recorded_at DESC LIMIT 10
    """, (m["home_id"],))
    away_elo_hist = q("""
        SELECT eh.elo_rating, eh.recorded_at, m.match_date,
               CASE WHEN m.home_team_id=eh.team_id THEN ta.name ELSE th.name END as opponent
        FROM elo_history eh
        LEFT JOIN matches m ON m.id=eh.match_id
        LEFT JOIN teams th ON m.home_team_id=th.id
        LEFT JOIN teams ta ON m.away_team_id=ta.id
        WHERE eh.team_id=? ORDER BY eh.recorded_at DESC LIMIT 10
    """, (m["away_id"],))

    # Recent matches form
    home_form_matches = q("""
        SELECT m.match_date, m.home_score, m.away_score, m.status,
               CASE WHEN m.home_team_id=t.id THEN 'home' ELSE 'away' END as side,
               CASE WHEN m.home_team_id=t.id THEN ta.name ELSE th.name END as opponent
        FROM matches m
        JOIN teams t ON (m.home_team_id=t.id OR m.away_team_id=t.id)
        JOIN teams th ON m.home_team_id=th.id
        JOIN teams ta ON m.away_team_id=ta.id
        WHERE t.id=? AND m.status='FINISHED'
        ORDER BY m.match_date DESC LIMIT 5
    """, (m["home_id"],))
    away_form_matches = q("""
        SELECT m.match_date, m.home_score, m.away_score, m.status,
               CASE WHEN m.home_team_id=t.id THEN 'home' ELSE 'away' END as side,
               CASE WHEN m.home_team_id=t.id THEN ta.name ELSE th.name END as opponent
        FROM matches m
        JOIN teams t ON (m.home_team_id=t.id OR m.away_team_id=t.id)
        JOIN teams th ON m.home_team_id=th.id
        JOIN teams ta ON m.away_team_id=ta.id
        WHERE t.id=? AND m.status='FINISHED'
        ORDER BY m.match_date DESC LIMIT 5
    """, (m["away_id"],))

    # Odds comparison
    odds = q1("SELECT home_odds,draw_odds,away_odds FROM odds WHERE match_id=? ORDER BY fetched_at DESC LIMIT 1", (match_id,))
    odds_implied = None
    if odds and odds["home_odds"]:
        total = 1/odds["home_odds"] + 1/odds["draw_odds"] + 1/odds["away_odds"]
        odds_implied = {
            "home": round(1/odds["home_odds"]/total, 4),
            "draw": round(1/odds["draw_odds"]/total, 4) if odds["draw_odds"] else None,
            "away": round(1/odds["away_odds"]/total, 4),
            "margin": round((total-1)*100, 2),
            "home_odds": odds["home_odds"], "draw_odds": odds["draw_odds"], "away_odds": odds["away_odds"]
        }

    # Calibration: model vs odds
    model_edge = None
    if odds_implied:
        model_edge = {
            "home": round(hw - odds_implied["home"], 4),
            "draw": round(da - (odds_implied["draw"] or 0), 4),
            "away": round(aw - odds_implied["away"], 4),
        }

    top_scores_stored = []
    if m.get("top_scores"):
        try: top_scores_stored = json.loads(m["top_scores"])
        except: pass

    return jsonify({
        "match": {
            "id": m["id"], "date": m["match_date"], "time": m["match_time"],
            "stage": m["stage"], "group": m["group_name"],
            "status": m["status"], "city": m["city"],
            "home_score": m["home_score"], "away_score": m["away_score"]
        },
        "home": {"name":m["home_name"],"code":m["home_code"],"elo":he,"form_factor":round(hf,4)},
        "away": {"name":m["away_name"],"code":m["away_code"],"elo":ae,"form_factor":round(af,4)},
        "model": {
            "lambda_home": round(lh,4), "lambda_away": round(la,4),
            "elo_diff": round(he-ae,1),
            "home_win_prob": round(hw,4), "draw_prob": round(da,4), "away_win_prob": round(aw,4),
            "expected_home_goals": round(eg_home,4), "expected_away_goals": round(eg_away,4),
            "entropy": round(entropy,4),
            "recommended_score": m.get("recommended_score"),
            "used_odds": bool(m.get("used_odds"))
        },
        "matrix": matrix,
        "matrix_labels": list(range(8)),
        "top_scores": scores_flat[:15],
        "home_marginal": home_marginal,
        "away_marginal": away_marginal,
        "home_elo_history": home_elo_hist,
        "away_elo_history": away_elo_hist,
        "home_form": home_form_matches,
        "away_form": away_form_matches,
        "odds": odds_implied,
        "model_edge": model_edge
    })

@app.route("/api/tech/elo-matrix")
def elo_matrix():
    """Matriz de probabilidades Elo para todos los pares de grupos."""
    teams = q("SELECT name,fifa_code,group_name,elo_rating FROM teams ORDER BY elo_rating DESC")
    top20 = teams[:20]
    result = []
    for home in top20:
        row = []
        for away in top20:
            if home["name"] == away["name"]:
                row.append(None)
            else:
                pr = get_elo_win_probability(home["name"], away["name"])
                row.append(round(pr["home_win"]*100, 1))
        result.append(row)
    return jsonify({
        "teams": [{"name":t["name"],"code":t["fifa_code"],"elo":t["elo_rating"]} for t in top20],
        "matrix": result
    })

@app.route("/api/tech/simulation/<int:match_id>")
def simulation(match_id):
    """Monte Carlo con N simulaciones, devuelve distribución completa."""
    n = min(int(request.args.get("n", 50000)), 100000)
    import random, collections
    m = q1(f"""
        SELECT th.elo_rating as he, ta.elo_rating as ae,
               th.name as hn, ta.name as an,
               p.expected_home_goals as lh, p.expected_away_goals as la
        FROM matches m
        JOIN teams th ON m.home_team_id=th.id
        JOIN teams ta ON m.away_team_id=ta.id
        LEFT JOIN {latest_pred_subquery()} p ON p.match_id=m.id
        WHERE m.id=?
    """, (match_id,))
    if not m: return jsonify({"error":"not found"}),404

    lh = m["lh"] or elo_to_lambda(m["he"]-m["ae"], 1.38)
    la = m["la"] or elo_to_lambda(m["ae"]-m["he"], 1.07)
    probs_h = [poisson_p(lh,k) for k in range(10)]
    probs_a = [poisson_p(la,k) for k in range(10)]
    counts = collections.Counter()
    hw=da=aw=0
    for _ in range(n):
        h = random.choices(range(10),weights=probs_h)[0]
        a = random.choices(range(10),weights=probs_a)[0]
        counts[(h,a)]+=1
        if h>a: hw+=1
        elif h==a: da+=1
        else: aw+=1

    top = sorted(counts.items(),key=lambda x:-x[1])[:20]
    return jsonify({
        "n_simulations": n,
        "lambda_home": round(lh,4), "lambda_away": round(la,4),
        "home_win": round(hw/n,4), "draw": round(da/n,4), "away_win": round(aw/n,4),
        "top_scores":[{"score":f"{s[0]}-{s[1]}","count":c,"prob":round(c/n,4)} for (s,c) in top],
        "home_name": m["hn"], "away_name": m["an"]
    })

@app.route("/api/tech/team/<string:code>")
def team_profile(code):
    """Perfil técnico completo de un equipo."""
    t = q1("SELECT * FROM teams WHERE fifa_code=?", (code,))
    if not t: return jsonify({"error":"not found"}),404
    matches_played = q("""
        SELECT m.id,m.match_date,m.stage,m.home_score,m.away_score,m.status,
               CASE WHEN m.home_team_id=t.id THEN 'home' ELSE 'away' END as side,
               CASE WHEN m.home_team_id=t.id THEN ta.name ELSE th.name END as opponent,
               CASE WHEN m.home_team_id=t.id THEN ta.fifa_code ELSE th.fifa_code END as opp_code,
               CASE WHEN m.home_team_id=t.id THEN m.home_score ELSE m.away_score END as gf,
               CASE WHEN m.home_team_id=t.id THEN m.away_score ELSE m.home_score END as ga
        FROM matches m
        JOIN teams t ON (m.home_team_id=t.id OR m.away_team_id=t.id)
        JOIN teams th ON m.home_team_id=th.id
        JOIN teams ta ON m.away_team_id=ta.id
        WHERE t.fifa_code=? AND m.status='FINISHED'
        ORDER BY m.match_date DESC
    """, (code,))
    upcoming = q("""
        SELECT m.id,m.match_date,m.match_time,m.stage,m.city,
               CASE WHEN m.home_team_id=t.id THEN 'home' ELSE 'away' END as side,
               CASE WHEN m.home_team_id=t.id THEN ta.name ELSE th.name END as opponent,
               CASE WHEN m.home_team_id=t.id THEN ta.fifa_code ELSE th.fifa_code END as opp_code,
               th.elo_rating as home_elo, ta.elo_rating as away_elo
        FROM matches m
        JOIN teams t ON (m.home_team_id=t.id OR m.away_team_id=t.id)
        JOIN teams th ON m.home_team_id=th.id
        JOIN teams ta ON m.away_team_id=ta.id
        WHERE t.fifa_code=? AND m.status='SCHEDULED'
        ORDER BY m.match_date ASC
    """, (code,))
    elo_hist = q("""
        SELECT eh.elo_rating, eh.recorded_at FROM elo_history eh
        JOIN teams t ON eh.team_id=t.id WHERE t.fifa_code=?
        ORDER BY eh.recorded_at ASC
    """, (code,))

    gf_total = sum(m["gf"] or 0 for m in matches_played)
    ga_total = sum(m["ga"] or 0 for m in matches_played)
    wins   = sum(1 for m in matches_played if (m["gf"] or 0)>(m["ga"] or 0))
    draws  = sum(1 for m in matches_played if (m["gf"] or 0)==(m["ga"] or 0))
    losses = sum(1 for m in matches_played if (m["gf"] or 0)<(m["ga"] or 0))

    return jsonify({
        "team": dict(t),
        "stats": {"played":len(matches_played),"wins":wins,"draws":draws,"losses":losses,"gf":gf_total,"ga":ga_total,"gd":gf_total-ga_total,"points":wins*3+draws},
        "matches": matches_played,
        "upcoming": upcoming,
        "elo_history": elo_hist,
        "form_factor": round(get_recent_form_adjustment(t["name"]),4)
    })

@app.route("/api/tech/poisson-table")
def poisson_table():
    """Tabla de distribución de Poisson para lambdas 0.5 a 3.5."""
    result = {}
    for lam_10 in range(5, 36, 5):
        lam = lam_10 / 10
        result[str(lam)] = [round(poisson_p(lam,k),4) for k in range(9)]
    return jsonify(result)

@app.route("/api/team-history/<fifa_code>")
def team_history(fifa_code):
    """Últimos partidos de una selección desde la BD local."""
    fifa_code = fifa_code.upper()
    team = q1("SELECT id, name, fifa_code FROM teams WHERE fifa_code=?", (fifa_code,))
    if not team:
        return jsonify({"matches": [], "team_name": fifa_code, "source": "not_found"})
    matches = q("""
        SELECT m.match_date,
               th.name as home_name, th.fifa_code as home_code,
               ta.name as away_name, ta.fifa_code as away_code,
               m.home_score, m.away_score, m.status,
               m.stage as competition, m.city
        FROM matches m
        JOIN teams th ON m.home_team_id=th.id
        JOIN teams ta ON m.away_team_id=ta.id
        WHERE (m.home_team_id=? OR m.away_team_id=?)
          AND m.status='FINISHED'
        ORDER BY m.match_date DESC LIMIT 10
    """, (team["id"], team["id"]))
    return jsonify({"matches": matches, "team_name": team["name"], "source": "local"})

if __name__ == "__main__":
    print("🌐 http://localhost:5000")
    app.run(host="0.0.0.0", port=5000, debug=False)
