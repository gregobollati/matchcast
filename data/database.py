"""
Módulo de base de datos SQLite para Prode Mundial 2026.
Gestiona equipos, partidos, resultados, ratings Elo y predicciones.
"""
import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "mundial2026.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """Inicializa todas las tablas de la base de datos."""
    conn = get_connection()
    cur = conn.cursor()

    # Equipos participantes
    cur.execute("""
        CREATE TABLE IF NOT EXISTS teams (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL UNIQUE,
            fifa_code   TEXT,
            group_name  TEXT,
            elo_rating  REAL DEFAULT 1500.0,
            updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Partidos del torneo
    cur.execute("""
        CREATE TABLE IF NOT EXISTS matches (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            match_date      DATE NOT NULL,
            match_time      TEXT,
            stage           TEXT NOT NULL,
            group_name      TEXT,
            home_team_id    INTEGER REFERENCES teams(id),
            away_team_id    INTEGER REFERENCES teams(id),
            venue           TEXT,
            city            TEXT,
            home_score      INTEGER,
            away_score      INTEGER,
            status          TEXT DEFAULT 'SCHEDULED',
            api_match_id    TEXT UNIQUE,
            updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Historial de resultados previos al torneo (para Elo)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS historical_results (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            match_date      DATE NOT NULL,
            home_team       TEXT NOT NULL,
            away_team       TEXT NOT NULL,
            home_score      INTEGER NOT NULL,
            away_score      INTEGER NOT NULL,
            tournament      TEXT,
            importance      REAL DEFAULT 1.0
        )
    """)

    # Predicciones generadas
    cur.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            match_id            INTEGER REFERENCES matches(id),
            generated_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            home_win_prob       REAL,
            draw_prob           REAL,
            away_win_prob       REAL,
            expected_home_goals REAL,
            expected_away_goals REAL,
            recommended_score   TEXT,
            top_scores          TEXT,
            model_version       TEXT DEFAULT '1.0',
            used_odds           INTEGER DEFAULT 0
        )
    """)

    # Ratings Elo históricos
    cur.execute("""
        CREATE TABLE IF NOT EXISTS elo_history (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            team_id     INTEGER REFERENCES teams(id),
            elo_rating  REAL NOT NULL,
            recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            match_id    INTEGER
        )
    """)

    # Cuotas de apuestas
    cur.execute("""
        CREATE TABLE IF NOT EXISTS odds (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            match_id    INTEGER REFERENCES matches(id),
            bookmaker   TEXT,
            home_odds   REAL,
            draw_odds   REAL,
            away_odds   REAL,
            fetched_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Performance de predicciones
    cur.execute("""
        CREATE TABLE IF NOT EXISTS prediction_results (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            match_id            INTEGER REFERENCES matches(id),
            prediction_id       INTEGER REFERENCES predictions(id),
            actual_home_score   INTEGER,
            actual_away_score   INTEGER,
            predicted_score     TEXT,
            exact_match         INTEGER DEFAULT 0,
            correct_outcome     INTEGER DEFAULT 0,
            points_earned       INTEGER DEFAULT 0,
            evaluated_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()
    print(f"✅ Base de datos inicializada en: {DB_PATH}")


def seed_teams():
    """Redirige al seed real del Mundial 2026."""
    from data.seed_real import seed_real_teams, seed_real_matches
    seed_real_teams()
    seed_real_matches()


def _seed_teams_legacy():
    """LEGACY — no usar. Solo conservado como referencia."""
    teams = [
        # CONMEBOL (6)
        ("Argentina", "ARG", "A"),
        ("Brasil", "BRA", "B"),
        ("Uruguay", "URU", "C"),
        ("Colombia", "COL", "D"),
        ("Ecuador", "ECU", "E"),
        ("Venezuela", "VEN", "F"),
        # UEFA (16)
        ("Francia", "FRA", "G"),
        ("España", "ESP", "H"),
        ("Inglaterra", "ENG", "I"),
        ("Portugal", "POR", "J"),
        ("Alemania", "GER", "K"),
        ("Países Bajos", "NED", "L"),
        ("Bélgica", "BEL", "A"),
        ("Italia", "ITA", "B"),
        ("Croacia", "CRO", "C"),
        ("Suiza", "SUI", "D"),
        ("Dinamarca", "DEN", "E"),
        ("Austria", "AUT", "F"),
        ("Serbia", "SRB", "G"),
        ("Escocia", "SCO", "H"),
        ("Turquía", "TUR", "I"),
        ("Hungría", "HUN", "J"),
        # CONMEBOL/CONCACAF (3)
        ("México", "MEX", "K"),
        ("Estados Unidos", "USA", "L"),
        ("Canadá", "CAN", "A"),
        # AFC (8)
        ("Japón", "JPN", "B"),
        ("Corea del Sur", "KOR", "C"),
        ("Arabia Saudita", "KSA", "D"),
        ("Irán", "IRN", "E"),
        ("Australia", "AUS", "F"),
        ("Qatar", "QAT", "G"),
        ("Uzbekistán", "UZB", "H"),
        ("Irak", "IRQ", "I"),
        # CAF (9)
        ("Marruecos", "MAR", "J"),
        ("Senegal", "SEN", "K"),
        ("Nigeria", "NGA", "L"),
        ("Egipto", "EGY", "A"),
        ("Costa de Marfil", "CIV", "B"),
        ("Camerún", "CMR", "C"),
        ("Mali", "MLI", "D"),
        ("Argelia", "ALG", "E"),
        ("Túnez", "TUN", "F"),
        # CONCACAF
        ("Panamá", "PAN", "G"),
        ("Costa Rica", "CRC", "H"),
        ("Jamaica", "JAM", "I"),
        # OFC
        ("Nueva Zelanda", "NZL", "J"),
        # Repechajes
        ("Ghana", "GHA", "K"),
        ("Paraguay", "PAR", "L"),
        ("Suecia", "SWE", "A"),
        ("Polonia", "POL", "B"),
    ]

    # Ratings Elo iniciales basados en rankings FIFA actuales
    elo_ratings = {
        "Argentina": 2080, "Francia": 2050, "España": 2040, "Brasil": 2020,
        "Inglaterra": 2000, "Portugal": 1980, "Alemania": 1960, "Países Bajos": 1940,
        "Bélgica": 1920, "Uruguay": 1900, "Colombia": 1880, "Croacia": 1870,
        "Italia": 1860, "Japón": 1840, "Marruecos": 1830, "México": 1820,
        "Suiza": 1810, "Senegal": 1800, "Dinamarca": 1790, "Estados Unidos": 1780,
        "Corea del Sur": 1770, "Ecuador": 1760, "Austria": 1750, "Turquía": 1740,
        "Australia": 1730, "Serbia": 1720, "Nigeria": 1710, "Canadá": 1700,
        "Irán": 1690, "Escocia": 1680, "Arabia Saudita": 1670, "Costa de Marfil": 1660,
        "Hungría": 1650, "Egipto": 1640, "Suecia": 1630, "Polonia": 1620,
        "Camerún": 1610, "Venezuela": 1600, "Panamá": 1590, "Túnez": 1580,
        "Ghana": 1570, "Costa Rica": 1560, "Paraguay": 1550, "Mali": 1540,
        "Argelia": 1530, "Qatar": 1520, "Irak": 1510, "Uzbekistán": 1500,
        "Nueva Zelanda": 1490, "Jamaica": 1480,
    }

    conn = get_connection()
    cur = conn.cursor()
    for name, code, group in teams:
        elo = elo_ratings.get(name, 1500)
        cur.execute("""
            INSERT OR IGNORE INTO teams (name, fifa_code, group_name, elo_rating)
            VALUES (?, ?, ?, ?)
        """, (name, code, group, elo))
    conn.commit()
    conn.close()
    print(f"✅ {len(teams)} equipos insertados")


def seed_group_stage_matches():
    """Redirige al seed real (ya ejecutado por seed_teams)."""
    pass  # Los partidos ya se insertan en seed_teams via seed_real


def _seed_group_stage_matches_legacy():
    """LEGACY — no usar."""
    # Fixture fase de grupos (partidos entre los equipos de cada grupo A-L)
    # Fechas reales del Mundial 2026: 11 junio - 2 julio 2026 (fase de grupos)
    sample_matches = [
        # Grupo A
        ("2026-06-11", "10:00", "Fase de Grupos", "A", "México", "Argentina", "SoFi Stadium", "Los Ángeles"),
        ("2026-06-11", "13:00", "Fase de Grupos", "A", "Bélgica", "Canadá", "Rose Bowl", "Los Ángeles"),
        ("2026-06-15", "13:00", "Fase de Grupos", "A", "México", "Canadá", "AT&T Stadium", "Dallas"),
        ("2026-06-15", "16:00", "Fase de Grupos", "A", "Argentina", "Bélgica", "MetLife Stadium", "Nueva York"),
        ("2026-06-19", "18:00", "Fase de Grupos", "A", "Canadá", "Argentina", "BC Place", "Vancouver"),
        ("2026-06-19", "18:00", "Fase de Grupos", "A", "México", "Bélgica", "Estadio Azteca", "Ciudad de México"),
        # Grupo B
        ("2026-06-12", "10:00", "Fase de Grupos", "B", "Brasil", "Italia", "Gillette Stadium", "Boston"),
        ("2026-06-12", "13:00", "Fase de Grupos", "B", "Japón", "Venezuela", "Lincoln Financial Field", "Filadelfia"),
        ("2026-06-16", "13:00", "Fase de Grupos", "B", "Brasil", "Venezuela", "Hard Rock Stadium", "Miami"),
        ("2026-06-16", "16:00", "Fase de Grupos", "B", "Italia", "Japón", "NRG Stadium", "Houston"),
        ("2026-06-20", "18:00", "Fase de Grupos", "B", "Venezuela", "Italia", "Levi's Stadium", "San Francisco"),
        ("2026-06-20", "18:00", "Fase de Grupos", "B", "Brasil", "Japón", "Allegiant Stadium", "Las Vegas"),
        # Grupo C
        ("2026-06-12", "16:00", "Fase de Grupos", "C", "Uruguay", "Corea del Sur", "Empower Field", "Denver"),
        ("2026-06-12", "19:00", "Fase de Grupos", "C", "Croacia", "Camerún", "Arrowhead Stadium", "Kansas City"),
        ("2026-06-16", "10:00", "Fase de Grupos", "C", "Uruguay", "Camerún", "SoFi Stadium", "Los Ángeles"),
        ("2026-06-16", "13:00", "Fase de Grupos", "C", "Corea del Sur", "Croacia", "Rose Bowl", "Los Ángeles"),
        ("2026-06-21", "18:00", "Fase de Grupos", "C", "Camerún", "Corea del Sur", "MetLife Stadium", "Nueva York"),
        ("2026-06-21", "18:00", "Fase de Grupos", "C", "Uruguay", "Croacia", "AT&T Stadium", "Dallas"),
        # Grupo D
        ("2026-06-13", "10:00", "Fase de Grupos", "D", "Colombia", "Suiza", "BC Place", "Vancouver"),
        ("2026-06-13", "13:00", "Fase de Grupos", "D", "Arabia Saudita", "Mali", "Gillette Stadium", "Boston"),
        ("2026-06-17", "13:00", "Fase de Grupos", "D", "Colombia", "Mali", "Estadio Azteca", "Ciudad de México"),
        ("2026-06-17", "16:00", "Fase de Grupos", "D", "Suiza", "Arabia Saudita", "Lincoln Financial Field", "Filadelfia"),
        ("2026-06-22", "18:00", "Fase de Grupos", "D", "Mali", "Suiza", "Hard Rock Stadium", "Miami"),
        ("2026-06-22", "18:00", "Fase de Grupos", "D", "Colombia", "Arabia Saudita", "NRG Stadium", "Houston"),
        # Grupo E
        ("2026-06-13", "16:00", "Fase de Grupos", "E", "Ecuador", "Dinamarca", "Levi's Stadium", "San Francisco"),
        ("2026-06-13", "19:00", "Fase de Grupos", "E", "Irán", "Argelia", "Allegiant Stadium", "Las Vegas"),
        ("2026-06-17", "10:00", "Fase de Grupos", "E", "Ecuador", "Argelia", "Empower Field", "Denver"),
        ("2026-06-17", "13:00", "Fase de Grupos", "E", "Dinamarca", "Irán", "Arrowhead Stadium", "Kansas City"),
        ("2026-06-23", "18:00", "Fase de Grupos", "E", "Argelia", "Dinamarca", "SoFi Stadium", "Los Ángeles"),
        ("2026-06-23", "18:00", "Fase de Grupos", "E", "Ecuador", "Irán", "Rose Bowl", "Los Ángeles"),
        # Grupo F
        ("2026-06-14", "10:00", "Fase de Grupos", "F", "Austria", "Venezuela", "MetLife Stadium", "Nueva York"),
        ("2026-06-14", "13:00", "Fase de Grupos", "F", "Australia", "Túnez", "AT&T Stadium", "Dallas"),
        ("2026-06-18", "13:00", "Fase de Grupos", "F", "Austria", "Túnez", "BC Place", "Vancouver"),
        ("2026-06-18", "16:00", "Fase de Grupos", "F", "Australia", "Venezuela", "Gillette Stadium", "Boston"),
        ("2026-06-24", "18:00", "Fase de Grupos", "F", "Túnez", "Venezuela", "Lincoln Financial Field", "Filadelfia"),
        ("2026-06-24", "18:00", "Fase de Grupos", "F", "Austria", "Australia", "Hard Rock Stadium", "Miami"),
        # Grupo G
        ("2026-06-14", "16:00", "Fase de Grupos", "G", "Francia", "Panamá", "NRG Stadium", "Houston"),
        ("2026-06-14", "19:00", "Fase de Grupos", "G", "Serbia", "Qatar", "Levi's Stadium", "San Francisco"),
        ("2026-06-18", "10:00", "Fase de Grupos", "G", "Francia", "Qatar", "Allegiant Stadium", "Las Vegas"),
        ("2026-06-18", "13:00", "Fase de Grupos", "G", "Panamá", "Serbia", "Empower Field", "Denver"),
        ("2026-06-25", "18:00", "Fase de Grupos", "G", "Qatar", "Panamá", "Arrowhead Stadium", "Kansas City"),
        ("2026-06-25", "18:00", "Fase de Grupos", "G", "Francia", "Serbia", "SoFi Stadium", "Los Ángeles"),
        # Grupo H
        ("2026-06-15", "10:00", "Fase de Grupos", "H", "España", "Escocia", "Rose Bowl", "Los Ángeles"),
        ("2026-06-15", "13:00", "Fase de Grupos", "H", "Costa Rica", "Jamaica", "MetLife Stadium", "Nueva York"),
        ("2026-06-19", "10:00", "Fase de Grupos", "H", "España", "Jamaica", "AT&T Stadium", "Dallas"),
        ("2026-06-19", "13:00", "Fase de Grupos", "H", "Escocia", "Costa Rica", "BC Place", "Vancouver"),
        ("2026-06-26", "18:00", "Fase de Grupos", "H", "Jamaica", "Escocia", "Gillette Stadium", "Boston"),
        ("2026-06-26", "18:00", "Fase de Grupos", "H", "España", "Costa Rica", "Lincoln Financial Field", "Filadelfia"),
        # Grupo I
        ("2026-06-15", "16:00", "Fase de Grupos", "I", "Inglaterra", "Turquía", "Hard Rock Stadium", "Miami"),
        ("2026-06-15", "19:00", "Fase de Grupos", "I", "Irak", "Nueva Zelanda", "NRG Stadium", "Houston"),
        ("2026-06-20", "10:00", "Fase de Grupos", "I", "Inglaterra", "Nueva Zelanda", "Levi's Stadium", "San Francisco"),
        ("2026-06-20", "13:00", "Fase de Grupos", "I", "Turquía", "Irak", "Allegiant Stadium", "Las Vegas"),
        ("2026-06-27", "18:00", "Fase de Grupos", "I", "Nueva Zelanda", "Turquía", "Empower Field", "Denver"),
        ("2026-06-27", "18:00", "Fase de Grupos", "I", "Inglaterra", "Irak", "Arrowhead Stadium", "Kansas City"),
        # Grupo J
        ("2026-06-16", "16:00", "Fase de Grupos", "J", "Portugal", "Hungría", "SoFi Stadium", "Los Ángeles"),
        ("2026-06-16", "19:00", "Fase de Grupos", "J", "Marruecos", "Uzbekistán", "Rose Bowl", "Los Ángeles"),
        ("2026-06-21", "10:00", "Fase de Grupos", "J", "Portugal", "Uzbekistán", "MetLife Stadium", "Nueva York"),
        ("2026-06-21", "13:00", "Fase de Grupos", "J", "Hungría", "Marruecos", "AT&T Stadium", "Dallas"),
        ("2026-06-28", "18:00", "Fase de Grupos", "J", "Uzbekistán", "Hungría", "BC Place", "Vancouver"),
        ("2026-06-28", "18:00", "Fase de Grupos", "J", "Portugal", "Marruecos", "Gillette Stadium", "Boston"),
        # Grupo K
        ("2026-06-17", "16:00", "Fase de Grupos", "K", "Alemania", "Paraguay", "Lincoln Financial Field", "Filadelfia"),
        ("2026-06-17", "19:00", "Fase de Grupos", "K", "Ghana", "Senegal", "Hard Rock Stadium", "Miami"),
        ("2026-06-22", "10:00", "Fase de Grupos", "K", "Alemania", "Senegal", "NRG Stadium", "Houston"),
        ("2026-06-22", "13:00", "Fase de Grupos", "K", "Paraguay", "Ghana", "Levi's Stadium", "San Francisco"),
        ("2026-06-29", "18:00", "Fase de Grupos", "K", "Senegal", "Paraguay", "Allegiant Stadium", "Las Vegas"),
        ("2026-06-29", "18:00", "Fase de Grupos", "K", "Alemania", "Ghana", "Empower Field", "Denver"),
        # Grupo L
        ("2026-06-18", "16:00", "Fase de Grupos", "L", "Países Bajos", "Polonia", "Arrowhead Stadium", "Kansas City"),
        ("2026-06-18", "19:00", "Fase de Grupos", "L", "Nigeria", "Ecuador", "SoFi Stadium", "Los Ángeles"),
        ("2026-06-23", "10:00", "Fase de Grupos", "L", "Países Bajos", "Ecuador", "Rose Bowl", "Los Ángeles"),
        ("2026-06-23", "13:00", "Fase de Grupos", "L", "Polonia", "Nigeria", "MetLife Stadium", "Nueva York"),
        ("2026-06-30", "18:00", "Fase de Grupos", "L", "Ecuador", "Polonia", "AT&T Stadium", "Dallas"),
        ("2026-06-30", "18:00", "Fase de Grupos", "L", "Países Bajos", "Nigeria", "BC Place", "Vancouver"),
    ]

    conn = get_connection()
    cur = conn.cursor()

    for row in sample_matches:
        date, time, stage, group, home, away, venue, city = row
        # Buscar IDs
        cur.execute("SELECT id FROM teams WHERE name=?", (home,))
        h = cur.fetchone()
        cur.execute("SELECT id FROM teams WHERE name=?", (away,))
        a = cur.fetchone()
        if h and a:
            cur.execute("""
                INSERT OR IGNORE INTO matches
                (match_date, match_time, stage, group_name, home_team_id, away_team_id, venue, city)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (date, time, stage, group, h["id"], a["id"], venue, city))

    conn.commit()
    conn.close()
    print(f"✅ Partidos de fase de grupos insertados")


if __name__ == "__main__":
    init_db()
    seed_teams()
    seed_group_stage_matches()
