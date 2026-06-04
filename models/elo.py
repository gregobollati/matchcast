"""
Modelo de Rating Elo para selecciones de fútbol.
Basado en la metodología de World Football Elo Ratings (eloratings.net)
con ajustes para torneos internacionales.
"""
import math
from data.database import get_connection


# Factores K por tipo de competición
K_FACTORS = {
    "Mundial": 60,
    "Eliminatorias": 40,
    "Copa Confederaciones": 40,
    "Copa Continental": 35,
    "Amistoso": 20,
    "default": 20,
}

# Peso de margen de victoria
def goal_margin_factor(goal_diff: int) -> float:
    """Factor multiplicador según diferencia de goles."""
    if goal_diff == 1:
        return 1.0
    elif goal_diff == 2:
        return 1.5
    elif goal_diff >= 3:
        return 1.75 + (goal_diff - 3) * 0.1
    return 1.0


def expected_score(rating_a: float, rating_b: float) -> float:
    """Probabilidad esperada de victoria del equipo A vs B."""
    return 1.0 / (1.0 + 10 ** ((rating_b - rating_a) / 400.0))


def update_elo(
    home_rating: float,
    away_rating: float,
    home_score: int,
    away_score: int,
    tournament: str = "default",
    home_advantage: float = 65.0,
) -> tuple[float, float]:
    """
    Actualiza ratings Elo después de un partido.
    
    Returns:
        (nuevo_rating_local, nuevo_rating_visitante)
    """
    k = K_FACTORS.get(tournament, K_FACTORS["default"])

    # Ventaja de local (solo en partidos neutrales del Mundial = 0)
    adjusted_home = home_rating + home_advantage
    exp_home = expected_score(adjusted_home, away_rating)
    exp_away = 1.0 - exp_home

    # Resultado real
    if home_score > away_score:
        actual_home, actual_away = 1.0, 0.0
    elif home_score < away_score:
        actual_home, actual_away = 0.0, 1.0
    else:
        actual_home, actual_away = 0.5, 0.5

    goal_diff = abs(home_score - away_score)
    gm = goal_margin_factor(goal_diff)

    delta_home = k * gm * (actual_home - exp_home)
    delta_away = k * gm * (actual_away - exp_away)

    return home_rating + delta_home, away_rating + delta_away


def get_all_elo_ratings() -> dict[str, float]:
    """Retorna dict {nombre_equipo: elo} para todos los equipos."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT name, elo_rating FROM teams")
    ratings = {row["name"]: row["elo_rating"] for row in cur.fetchall()}
    conn.close()
    return ratings


def update_team_elo(team_id: int, new_rating: float, match_id: int = None):
    """Actualiza el Elo de un equipo en la DB y guarda historial."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE teams SET elo_rating=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
        (new_rating, team_id),
    )
    cur.execute(
        "INSERT INTO elo_history (team_id, elo_rating, match_id) VALUES (?, ?, ?)",
        (team_id, new_rating, match_id),
    )
    conn.commit()
    conn.close()


def process_match_result(match_id: int):
    """
    Procesa el resultado de un partido y actualiza ratings Elo.
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT m.*, 
               th.elo_rating as home_elo, ta.elo_rating as away_elo,
               th.id as home_id, ta.id as away_id
        FROM matches m
        JOIN teams th ON m.home_team_id = th.id
        JOIN teams ta ON m.away_team_id = ta.id
        WHERE m.id = ? AND m.status = 'FINISHED'
    """, (match_id,))
    match = cur.fetchone()
    conn.close()

    if not match or match["home_score"] is None:
        return False

    # El Mundial se juega en sede neutral → sin ventaja local
    new_home, new_away = update_elo(
        home_rating=match["home_elo"],
        away_rating=match["away_elo"],
        home_score=match["home_score"],
        away_score=match["away_score"],
        tournament="Mundial",
        home_advantage=0.0,
    )

    update_team_elo(match["home_id"], new_home, match_id)
    update_team_elo(match["away_id"], new_away, match_id)
    return True


def get_elo_win_probability(home_team: str, away_team: str) -> dict:
    """
    Calcula probabilidades de victoria basadas en Elo.
    
    Returns:
        dict con home_win, draw, away_win (suman 1.0)
    """
    ratings = get_all_elo_ratings()
    home_elo = ratings.get(home_team, 1500)
    away_elo = ratings.get(away_team, 1500)

    # Probabilidad pura de ganar/perder
    p_home_wins = expected_score(home_elo, away_elo)
    p_away_wins = expected_score(away_elo, home_elo)

    # Estimación de empate basada en diferencia de Elo
    elo_diff = abs(home_elo - away_elo)
    # A menor diferencia de Elo, mayor probabilidad de empate
    draw_base = 0.28 - (elo_diff / 10000)
    draw_prob = max(0.10, min(0.35, draw_base))

    # Reajustar para que sumen 1
    remaining = 1.0 - draw_prob
    total_win = p_home_wins + p_away_wins
    home_win = (p_home_wins / total_win) * remaining
    away_win = (p_away_wins / total_win) * remaining

    return {
        "home_win": round(home_win, 4),
        "draw": round(draw_prob, 4),
        "away_win": round(away_win, 4),
        "home_elo": home_elo,
        "away_elo": away_elo,
        "elo_diff": home_elo - away_elo,
    }
