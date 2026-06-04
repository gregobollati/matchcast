"""
Modelo predictivo basado en distribución de Poisson + simulación Monte Carlo.
Combina Elo, cuotas de apuestas y resultados recientes del torneo.
"""
import math
import random
import json
from collections import defaultdict
from typing import Optional
from models.elo import get_elo_win_probability, get_all_elo_ratings
from data.database import get_connection


# Promedio histórico de goles por partido en Mundiales
AVG_GOALS_WORLD_CUP = 2.65
AVG_GOALS_HOME = 1.38  # como "local" en partido neutral
AVG_GOALS_AWAY = 1.07


def poisson_prob(lam: float, k: int) -> float:
    """P(X=k) con distribución de Poisson(λ)."""
    if lam <= 0:
        return 1.0 if k == 0 else 0.0
    return (math.exp(-lam) * (lam ** k)) / math.factorial(k)


def poisson_score_matrix(lambda_home: float, lambda_away: float, max_goals: int = 8):
    """
    Matriz de probabilidad de marcadores exactos P(home=i, away=j).
    """
    matrix = {}
    home_win = draw = away_win = 0.0

    for i in range(max_goals + 1):
        for j in range(max_goals + 1):
            p = poisson_prob(lambda_home, i) * poisson_prob(lambda_away, j)
            matrix[(i, j)] = p
            if i > j:
                home_win += p
            elif i == j:
                draw += p
            else:
                away_win += p

    return matrix, home_win, draw, away_win


def elo_to_lambda(elo_diff: float, base_avg: float = 1.3) -> float:
    """
    Convierte diferencia de Elo en lambda de Poisson.
    Un elo_diff positivo = equipo más fuerte.
    """
    # Factor de escala: 400 puntos Elo ≈ 2x los goles esperados
    factor = 10 ** (elo_diff / 800.0)
    return base_avg * factor


def odds_to_probability(odds: float) -> float:
    """Convierte cuota decimal a probabilidad implícita."""
    if odds <= 0:
        return 0.0
    return 1.0 / odds


def blend_probabilities(
    elo_probs: dict,
    odds_probs: Optional[dict] = None,
    odds_weight: float = 0.35,
) -> dict:
    """
    Combina probabilidades de Elo con cuotas de apuestas.
    Si no hay cuotas, usa solo Elo.
    """
    if odds_probs is None or not any(odds_probs.values()):
        return elo_probs

    elo_w = 1.0 - odds_weight
    return {
        "home_win": elo_w * elo_probs["home_win"] + odds_weight * odds_probs["home_win"],
        "draw":     elo_w * elo_probs["draw"]     + odds_weight * odds_probs["draw"],
        "away_win": elo_w * elo_probs["away_win"] + odds_weight * odds_probs["away_win"],
    }


def get_recent_form_adjustment(team_name: str, n_matches: int = 3) -> float:
    """
    Ajuste de forma reciente basado en resultados del torneo.
    Retorna multiplicador entre 0.85 y 1.15.
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT m.home_score, m.away_score,
               CASE WHEN m.home_team_id = t.id THEN 'home' ELSE 'away' END as side
        FROM matches m
        JOIN teams t ON (m.home_team_id = t.id OR m.away_team_id = t.id)
        WHERE t.name = ? AND m.status = 'FINISHED'
        ORDER BY m.match_date DESC
        LIMIT ?
    """, (team_name, n_matches))
    results = cur.fetchall()
    conn.close()

    if not results:
        return 1.0

    points = 0
    max_points = len(results) * 3
    for r in results:
        if r["side"] == "home":
            if r["home_score"] > r["away_score"]:
                points += 3
            elif r["home_score"] == r["away_score"]:
                points += 1
        else:
            if r["away_score"] > r["home_score"]:
                points += 3
            elif r["home_score"] == r["away_score"]:
                points += 1

    form_ratio = points / max_points  # 0 a 1
    # Mapear a [0.88, 1.12]
    return 0.88 + form_ratio * 0.24


def monte_carlo_simulation(
    lambda_home: float,
    lambda_away: float,
    n_simulations: int = 50_000,
) -> dict:
    """
    Simulación Monte Carlo de N partidos.
    Retorna distribución de marcadores y probabilidades.
    """
    score_counts = defaultdict(int)
    home_wins = draws = away_wins = 0
    total_home_goals = total_away_goals = 0

    for _ in range(n_simulations):
        h = random.choices(
            range(9),
            weights=[poisson_prob(lambda_home, k) for k in range(9)]
        )[0]
        a = random.choices(
            range(9),
            weights=[poisson_prob(lambda_away, k) for k in range(9)]
        )[0]
        score_counts[(h, a)] += 1
        total_home_goals += h
        total_away_goals += a
        if h > a:
            home_wins += 1
        elif h == a:
            draws += 1
        else:
            away_wins += 1

    # Top 10 marcadores más probables
    top_scores = sorted(
        score_counts.items(),
        key=lambda x: x[1],
        reverse=True
    )[:10]

    return {
        "home_win_prob": home_wins / n_simulations,
        "draw_prob": draws / n_simulations,
        "away_win_prob": away_wins / n_simulations,
        "top_scores": [
            {"score": f"{s[0][0]}-{s[0][1]}", "prob": s[1] / n_simulations}
            for s in top_scores
        ],
        "expected_home_goals": total_home_goals / n_simulations,
        "expected_away_goals": total_away_goals / n_simulations,
    }


def recommend_prode_score(
    top_scores: list,
    home_win_prob: float,
    draw_prob: float,
    away_win_prob: float,
    n_competitors: int = 30,
) -> dict:
    """
    Recomienda el marcador óptimo para ganar un prode de N participantes.
    
    Estrategia: maximizar valor esperado de puntos.
    En un prode de 30 personas, conviene buscar marcadores con alta probabilidad
    individual pero que otros no elijan (evitar el 1-0, el 2-0 más obvios).
    
    Scoring típico de prode:
    - Marcador exacto: 3 puntos
    - Resultado correcto (1X2): 1 punto
    - Nada: 0 puntos
    """
    if not top_scores:
        return {"score": "1-0", "rationale": "Sin datos suficientes"}

    # Probabilidades de que otros elijan cada marcador
    # Asumimos que los otros 29 se distribuyen con sesgo hacia marcadores populares
    popular_bias = {
        "1-0": 0.12, "2-0": 0.10, "2-1": 0.09, "1-1": 0.09,
        "0-0": 0.06, "3-0": 0.07, "0-1": 0.08, "0-2": 0.07,
        "3-1": 0.05, "2-2": 0.04,
    }

    best_score = None
    best_ev = -1

    for item in top_scores[:8]:
        score_str = item["score"]
        p_correct = item["prob"]
        p_others_pick = popular_bias.get(score_str, 0.03)
        
        # Valor esperado de PUNTOS ÚNICOS (si nadie más lo acierta)
        # EV = P(marcador exacto) × [3 + bonus_exclusividad] + P(resultado) × 1
        parts = score_str.split("-")
        if len(parts) == 2:
            h, a = int(parts[0]), int(parts[1])
            if h > a:
                p_outcome = home_win_prob
            elif h == a:
                p_outcome = draw_prob
            else:
                p_outcome = away_win_prob
        else:
            p_outcome = 0.33

        # Probabilidad de ser el único en acertar el marcador exacto
        p_unique = p_correct * ((1 - p_others_pick) ** (n_competitors - 1))

        ev = p_unique * 5.0 + p_correct * 3.0 + p_outcome * 1.0
        
        if ev > best_ev:
            best_ev = ev
            best_score = score_str

    # Determinar si vale la pena arriesgar por marcador único o ir a lo seguro
    top_prob = top_scores[0]["prob"] if top_scores else 0
    
    if home_win_prob > 0.55 and top_prob > 0.12:
        strategy = "Favorito claro — elegir el marcador más probable"
    elif draw_prob > 0.35:
        strategy = "Partido parejo — el empate tiene alta probabilidad"
    else:
        strategy = "Partido reñido — marcador sorpresivo puede dar ventaja en el prode"

    return {
        "score": best_score,
        "expected_value": round(best_ev, 4),
        "rationale": strategy,
        "alternatives": [s["score"] for s in top_scores[1:4]],
    }


def predict_match(match_id: int, n_simulations: int = 50_000) -> dict:
    """
    Genera predicción completa para un partido dado su ID.
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT m.*,
               th.name as home_name, ta.name as away_name,
               th.elo_rating as home_elo, ta.elo_rating as away_elo
        FROM matches m
        JOIN teams th ON m.home_team_id = th.id
        JOIN teams ta ON m.away_team_id = ta.id
        WHERE m.id = ?
    """, (match_id,))
    match = cur.fetchone()

    if not match:
        conn.close()
        return {}

    # Cuotas disponibles
    cur.execute("""
        SELECT home_odds, draw_odds, away_odds
        FROM odds WHERE match_id = ?
        ORDER BY fetched_at DESC LIMIT 1
    """, (match_id,))
    odds_row = cur.fetchone()
    conn.close()

    home_name = match["home_name"]
    away_name = match["away_name"]
    home_elo = match["home_elo"]
    away_elo = match["away_elo"]

    # Probabilidades por Elo
    elo_data = get_elo_win_probability(home_name, away_name)

    # Ajuste de forma reciente
    home_form = get_recent_form_adjustment(home_name)
    away_form = get_recent_form_adjustment(away_name)

    # Lambdas de Poisson ajustadas
    elo_diff_home = home_elo - away_elo
    elo_diff_away = away_elo - home_elo

    lambda_home = elo_to_lambda(elo_diff_home, AVG_GOALS_HOME) * home_form
    lambda_away = elo_to_lambda(elo_diff_away, AVG_GOALS_AWAY) * away_form

    # Probabilidades de cuotas (si existen)
    odds_probs = None
    if odds_row:
        raw_home = odds_to_probability(odds_row["home_odds"])
        raw_draw = odds_to_probability(odds_row["draw_odds"])
        raw_away = odds_to_probability(odds_row["away_odds"])
        total = raw_home + raw_draw + raw_away
        if total > 0:
            odds_probs = {
                "home_win": raw_home / total,
                "draw": raw_draw / total,
                "away_win": raw_away / total,
            }
            # Ajustar lambdas con cuotas
            if odds_probs["home_win"] > 0 and odds_probs["away_win"] > 0:
                ratio = odds_probs["home_win"] / odds_probs["away_win"]
                lambda_home = lambda_home * (ratio ** 0.3)
                lambda_away = lambda_away * ((1 / ratio) ** 0.3)

    # Simulación Monte Carlo
    sim = monte_carlo_simulation(lambda_home, lambda_away, n_simulations)

    # Blend final de probabilidades
    blended = blend_probabilities(
        elo_data,
        odds_probs,
        odds_weight=0.35 if odds_probs else 0.0,
    )

    # Recomendación de prode
    recommendation = recommend_prode_score(
        sim["top_scores"],
        blended["home_win"],
        blended["draw"],
        blended["away_win"],
    )

    result = {
        "match_id": match_id,
        "home_team": home_name,
        "away_team": away_name,
        "home_elo": home_elo,
        "away_elo": away_elo,
        "lambda_home": round(lambda_home, 3),
        "lambda_away": round(lambda_away, 3),
        "home_win_prob": round(blended["home_win"], 4),
        "draw_prob": round(blended["draw"], 4),
        "away_win_prob": round(blended["away_win"], 4),
        "expected_home_goals": round(sim["expected_home_goals"], 2),
        "expected_away_goals": round(sim["expected_away_goals"], 2),
        "top_scores": sim["top_scores"][:5],
        "recommended_score": recommendation["score"],
        "recommendation_rationale": recommendation["rationale"],
        "alternatives": recommendation["alternatives"],
        "used_odds": odds_probs is not None,
        "home_form": round(home_form, 3),
        "away_form": round(away_form, 3),
    }

    # Guardar predicción en DB
    save_prediction(result)

    return result


def save_prediction(pred: dict):
    """Guarda la predicción en la base de datos."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO predictions
        (match_id, home_win_prob, draw_prob, away_win_prob,
         expected_home_goals, expected_away_goals, recommended_score,
         top_scores, used_odds)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        pred["match_id"],
        pred["home_win_prob"],
        pred["draw_prob"],
        pred["away_win_prob"],
        pred["expected_home_goals"],
        pred["expected_away_goals"],
        pred["recommended_score"],
        json.dumps(pred["top_scores"]),
        int(pred["used_odds"]),
    ))
    conn.commit()
    conn.close()
