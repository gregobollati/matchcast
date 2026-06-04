"""
Generador de informes diarios de predicciones para el prode.
"""
from datetime import date, timedelta
from models.predictor import predict_match
from data.database import get_connection
import json


def generate_daily_report(target_date: str = None) -> dict:
    if target_date is None:
        target_date = (date.today() + timedelta(days=1)).isoformat()

    conn = get_connection()
    cur = conn.cursor()

    # DISTINCT por match id para evitar duplicados por el JOIN con odds
    cur.execute("""
        SELECT m.id, m.match_date, m.match_time, m.stage, m.group_name,
               th.name as home_name, th.elo_rating as home_elo,
               ta.name as away_name, ta.elo_rating as away_elo,
               (SELECT home_odds FROM odds WHERE match_id=m.id ORDER BY fetched_at DESC LIMIT 1) as home_odds,
               (SELECT draw_odds FROM odds WHERE match_id=m.id ORDER BY fetched_at DESC LIMIT 1) as draw_odds,
               (SELECT away_odds FROM odds WHERE match_id=m.id ORDER BY fetched_at DESC LIMIT 1) as away_odds
        FROM matches m
        JOIN teams th ON m.home_team_id = th.id
        JOIN teams ta ON m.away_team_id = ta.id
        WHERE m.match_date = ?
        ORDER BY m.match_time ASC
    """, (target_date,))
    matches = [dict(r) for r in cur.fetchall()]

    if not matches:
        conn.close()
        return {
            "date": target_date,
            "matches": [],
            "summary": "No hay partidos programados para esta fecha.",
        }

    predictions = []
    for m in matches:
        # Reusar predicción existente si ya fue generada hoy
        cur.execute("""
            SELECT * FROM predictions
            WHERE match_id = ?
            ORDER BY generated_at DESC LIMIT 1
        """, (m["id"],))
        existing = cur.fetchone()

        if existing:
            # Reconstruir pred desde DB
            pred = {
                "match_id": m["id"],
                "home_team": m["home_name"],
                "away_team": m["away_name"],
                "home_elo": m["home_elo"],
                "away_elo": m["away_elo"],
                "home_win_prob": existing["home_win_prob"],
                "draw_prob": existing["draw_prob"],
                "away_win_prob": existing["away_win_prob"],
                "expected_home_goals": existing["expected_home_goals"],
                "expected_away_goals": existing["expected_away_goals"],
                "recommended_score": existing["recommended_score"],
                "top_scores": json.loads(existing["top_scores"]) if existing["top_scores"] else [],
                "recommendation_rationale": "",
                "used_odds": bool(existing["used_odds"]),
                "home_form": 1.0,
                "away_form": 1.0,
                "lambda_home": existing["expected_home_goals"] or 1.0,
                "lambda_away": existing["expected_away_goals"] or 1.0,
                "alternatives": [],
            }
        else:
            pred = predict_match(m["id"])

        if pred:
            predictions.append({"match": m, "prediction": pred})

    conn.close()

    total = len(predictions)
    favorites_win = sum(1 for p in predictions if p["prediction"]["home_win_prob"] > 0.45)

    return {
        "date": target_date,
        "total_matches": total,
        "matches_with_odds": sum(1 for p in predictions if p["prediction"]["used_odds"]),
        "predictions": predictions,
        "summary": f"📅 {target_date} — {total} partido(s). Favoritos locales en {favorites_win}/{total} partidos.",
    }


def get_performance_stats() -> dict:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT COUNT(*) as total,
               SUM(exact_match) as exact_matches,
               SUM(correct_outcome) as correct_outcomes,
               SUM(points_earned) as total_points,
               AVG(points_earned) as avg_points
        FROM prediction_results
    """)
    stats = dict(cur.fetchone() or {})

    cur.execute("""
        SELECT m.stage, COUNT(*) as total,
               SUM(pr.exact_match) as exact,
               SUM(pr.correct_outcome) as outcomes
        FROM prediction_results pr
        JOIN matches m ON pr.match_id = m.id
        GROUP BY m.stage
    """)
    by_stage = [dict(r) for r in cur.fetchall()]

    cur.execute("""
        SELECT pr.*, m.match_date,
               th.name as home_name, ta.name as away_name,
               pr.actual_home_score, pr.actual_away_score, pr.predicted_score
        FROM prediction_results pr
        JOIN matches m ON pr.match_id = m.id
        JOIN teams th ON m.home_team_id = th.id
        JOIN teams ta ON m.away_team_id = ta.id
        WHERE pr.exact_match = 1
        ORDER BY pr.evaluated_at DESC LIMIT 10
    """)
    exact_hits = [dict(r) for r in cur.fetchall()]
    conn.close()

    return {"overall": stats, "by_stage": by_stage, "exact_hits": exact_hits}


def evaluate_finished_matches():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT m.id as match_id, m.home_score, m.away_score,
               p.id as pred_id, p.recommended_score
        FROM matches m
        JOIN predictions p ON p.match_id = m.id
        LEFT JOIN prediction_results pr ON pr.match_id = m.id
        WHERE m.status = 'FINISHED' AND pr.id IS NULL AND m.home_score IS NOT NULL
    """)
    pending = cur.fetchall()
    evaluated = 0
    for row in pending:
        actual_h, actual_a = row["home_score"], row["away_score"]
        predicted = row["recommended_score"]
        exact = correct_outcome = points = 0
        if predicted:
            parts = predicted.split("-")
            if len(parts) == 2:
                try:
                    ph, pa = int(parts[0]), int(parts[1])
                    if ph == actual_h and pa == actual_a:
                        exact = 1; points = 3
                    elif (ph > pa) == (actual_h > actual_a) and (ph == pa) == (actual_h == actual_a):
                        correct_outcome = 1; points = 1
                except ValueError:
                    pass
        cur.execute("""
            INSERT INTO prediction_results
            (match_id, prediction_id, actual_home_score, actual_away_score,
             predicted_score, exact_match, correct_outcome, points_earned)
            VALUES (?,?,?,?,?,?,?,?)
        """, (row["match_id"], row["pred_id"], actual_h, actual_a,
              predicted, exact, correct_outcome, points))
        evaluated += 1
    conn.commit()
    conn.close()
    return evaluated