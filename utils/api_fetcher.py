"""
Módulo de datos desde football-data.org y The Odds API.
Lee credenciales desde .env o variables de entorno.
Respeta throttling automático con X-RateLimit headers.
"""
import os, time, requests
from datetime import date, timedelta
from data.database import get_connection

# ── Cargar .env si existe ──────────────────────────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
except ImportError:
    pass

FOOTBALL_DATA_API_KEY = os.getenv("FOOTBALL_DATA_API_KEY", "")
ODDS_API_KEY          = os.getenv("ODDS_API_KEY", "")

FD_BASE   = "https://api.football-data.org/v4"
ODDS_BASE = "https://api.the-odds-api.com/v4"

# Throttle state: football-data.org permite 10 req/min
_last_fd_call = 0.0
_fd_remaining = 10

def _fd_get(path: str, params: dict = None) -> dict:
    """GET a football-data.org con throttling automático."""
    global _last_fd_call, _fd_remaining

    if not FOOTBALL_DATA_API_KEY:
        return {}

    # Si no quedan requests, esperar hasta el próximo minuto
    if _fd_remaining <= 1:
        wait = 65 - (time.time() - _last_fd_call)
        if wait > 0:
            print(f"⏳ Rate limit: esperando {wait:.0f}s...")
            time.sleep(wait)

    for attempt in range(3):
        try:
            r = requests.get(
                f"{FD_BASE}{path}",
                headers={"X-Auth-Token": FOOTBALL_DATA_API_KEY},
                params=params,
                timeout=15,
            )
            # Leer headers de rate limit (como sugiere la doc)
            _fd_remaining = int(r.headers.get("X-Requests-Available-Minute", 10))
            _last_fd_call = time.time()

            if r.status_code == 429:
                wait = int(r.headers.get("X-Wait-For-Reset", 60))
                print(f"⏳ 429 Too Many Requests — esperando {wait}s")
                time.sleep(wait + 2)
                continue

            if r.status_code == 200:
                return r.json()

            print(f"⚠️  football-data.org {r.status_code}: {r.text[:120]}")
            return {}

        except requests.RequestException as e:
            if attempt == 2:
                print(f"❌ Error de red: {e}")
                return {}
            time.sleep(2 ** attempt)
    return {}


def _odds_get(path: str, params: dict = None) -> dict | list:
    """GET a The Odds API."""
    if not ODDS_API_KEY:
        return {}
    try:
        r = requests.get(
            f"{ODDS_BASE}{path}",
            params={"apiKey": ODDS_API_KEY, **(params or {})},
            timeout=15,
        )
        remaining = r.headers.get("x-requests-remaining", "?")
        print(f"🎲 Odds API — requests restantes: {remaining}")
        if r.status_code == 200:
            return r.json()
        print(f"⚠️  Odds API {r.status_code}: {r.text[:120]}")
        return {}
    except requests.RequestException as e:
        print(f"❌ Odds API error: {e}")
        return {}


# ── Mapeo de nombres (football-data ↔ DB) ─────────────────────────────────
NAME_MAP = {
    "Germany":           "Alemania",
    "Argentina":         "Argentina",
    "France":            "Francia",
    "Brazil":            "Brasil",
    "Spain":             "España",
    "England":           "Inglaterra",
    "Portugal":          "Portugal",
    "Netherlands":       "Países Bajos",
    "Belgium":           "Bélgica",
    "Italy":             "Italia",
    "Croatia":           "Croacia",
    "Switzerland":       "Suiza",
    "Denmark":           "Dinamarca",
    "Austria":           "Austria",
    "Serbia":            "Serbia",
    "Scotland":          "Escocia",
    "Turkey":            "Turquía",
    "Hungary":           "Hungría",
    "Mexico":            "México",
    "United States":     "Estados Unidos",
    "USA":               "Estados Unidos",
    "Canada":            "Canadá",
    "Japan":             "Japón",
    "Korea Republic":    "Corea del Sur",
    "South Korea":       "Corea del Sur",
    "Saudi Arabia":      "Arabia Saudita",
    "Iran":              "Irán",
    "Australia":         "Australia",
    "Qatar":             "Qatar",
    "Uzbekistan":        "Uzbekistán",
    "Iraq":              "Irak",
    "Morocco":           "Marruecos",
    "Senegal":           "Senegal",
    "Nigeria":           "Nigeria",
    "Egypt":             "Egipto",
    "Ivory Coast":       "Costa de Marfil",
    "Cameroon":          "Camerún",
    "Mali":              "Mali",
    "Algeria":           "Argelia",
    "Tunisia":           "Túnez",
    "Panama":            "Panamá",
    "Costa Rica":        "Costa Rica",
    "Jamaica":           "Jamaica",
    "New Zealand":       "Nueva Zelanda",
    "Ghana":             "Ghana",
    "Paraguay":          "Paraguay",
    "Sweden":            "Suecia",
    "Poland":            "Polonia",
    "Uruguay":           "Uruguay",
    "Colombia":          "Colombia",
    "Ecuador":           "Ecuador",
    "Venezuela":         "Venezuela",
}

def normalize(name: str) -> str:
    return NAME_MAP.get(name, name)


# ── Descubrir el ID del Mundial 2026 ──────────────────────────────────────
def find_wc2026_id() -> str | None:
    """Busca el código de competición del Mundial 2026 en football-data.org"""
    data = _fd_get("/competitions")
    for comp in data.get("competitions", []):
        name = comp.get("name", "")
        code = comp.get("code", "")
        year = comp.get("currentSeason", {}).get("startDate", "")[:4]
        if "World Cup" in name and year in ("2026", "2025"):
            print(f"✅ Encontrado: {name} — código: {code}")
            return code
        if code == "WC":
            return "WC"
    return None


# ── Sincronizar fixture y resultados ──────────────────────────────────────
def fd_sync_matches() -> int:
    """Descarga fixture y resultados del Mundial desde football-data.org"""
    if not FOOTBALL_DATA_API_KEY:
        print("⚠️  FOOTBALL_DATA_API_KEY no configurada")
        return 0

    # Intentar con WC primero, luego buscar el código real
    code = "WC"
    data = _fd_get(f"/competitions/{code}/matches")

    if not data.get("matches"):
        print("🔍 Buscando código de competición del Mundial 2026...")
        code = find_wc2026_id()
        if not code:
            print("❌ No se encontró el Mundial 2026 en la API (puede no estar disponible aún)")
            return 0
        data = _fd_get(f"/competitions/{code}/matches")

    matches = data.get("matches", [])
    if not matches:
        print("⚠️  Sin partidos en la respuesta")
        return 0

    conn = get_connection()
    cur  = conn.cursor()
    updated = 0

    for m in matches:
        api_id   = str(m.get("id", ""))
        utc_date = m.get("utcDate", "")[:10]
        utc_time = m.get("utcDate", "")[11:16] if len(m.get("utcDate","")) > 10 else ""
        stage    = m.get("stage", "").replace("_"," ").title()
        grp_raw  = m.get("group") or ""
        group    = grp_raw.replace("GROUP_","").replace("Group ","").strip() or None
        status   = m.get("status", "SCHEDULED")
        home_n   = normalize(m.get("homeTeam",{}).get("name",""))
        away_n   = normalize(m.get("awayTeam",{}).get("name",""))

        ft = m.get("score",{}).get("fullTime",{})
        home_sc = ft.get("home")
        away_sc = ft.get("away")

        # Mapear status
        if status in ("FINISHED","FT"):          status = "FINISHED"
        elif status in ("IN_PLAY","LIVE","HT"):  status = "LIVE"
        else:                                     status = "SCHEDULED"

        cur.execute("SELECT id FROM teams WHERE name=?", (home_n,))
        h = cur.fetchone()
        cur.execute("SELECT id FROM teams WHERE name=?", (away_n,))
        a = cur.fetchone()
        if not h or not a:
            continue

        cur.execute("""
            INSERT INTO matches
              (api_match_id, match_date, match_time, stage, group_name,
               home_team_id, away_team_id, home_score, away_score, status)
            VALUES (?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(api_match_id) DO UPDATE SET
              home_score=excluded.home_score,
              away_score=excluded.away_score,
              status=excluded.status,
              updated_at=CURRENT_TIMESTAMP
        """, (api_id, utc_date, utc_time, stage, group,
              h["id"], a["id"], home_sc, away_sc, status))
        updated += 1

    conn.commit()
    conn.close()
    print(f"✅ {updated} partidos sincronizados desde football-data.org")
    return updated


# ── Cuotas ────────────────────────────────────────────────────────────────
def odds_sync() -> int:
    """Descarga cuotas del Mundial desde The Odds API"""
    if not ODDS_API_KEY:
        print("⚠️  ODDS_API_KEY no configurada")
        return 0

    # Intentar con el sport key del Mundial 2026
    for sport_key in ("soccer_fifa_world_cup_2026", "soccer_world_cup"):
        data = _odds_get(f"/sports/{sport_key}/odds", {
            "regions": "eu",
            "markets": "h2h",
            "oddsFormat": "decimal",
        })
        if isinstance(data, list) and data:
            break
    else:
        print("⚠️  No hay cuotas del Mundial disponibles aún en The Odds API")
        return 0

    conn = get_connection()
    cur  = conn.cursor()
    synced = 0

    for event in data:
        home_n = normalize(event.get("home_team",""))
        away_n = normalize(event.get("away_team",""))

        cur.execute("""
            SELECT m.id FROM matches m
            JOIN teams th ON m.home_team_id=th.id
            JOIN teams ta ON m.away_team_id=ta.id
            WHERE th.name=? AND ta.name=? AND m.status='SCHEDULED'
            LIMIT 1
        """, (home_n, away_n))
        match = cur.fetchone()
        if not match:
            continue

        for bm in event.get("bookmakers",[])[:1]:
            for mkt in bm.get("markets",[]):
                if mkt["key"] != "h2h": continue
                outcomes = {o["name"]: o["price"] for o in mkt["outcomes"]}
                ho = outcomes.get(event.get("home_team"))
                ao = outcomes.get(event.get("away_team"))
                do = outcomes.get("Draw")
                if ho and ao:
                    cur.execute("""
                        INSERT INTO odds (match_id,bookmaker,home_odds,draw_odds,away_odds)
                        VALUES (?,?,?,?,?)
                    """, (match["id"], bm["title"], ho, do, ao))
                    synced += 1

    conn.commit()
    conn.close()
    print(f"✅ {synced} cuotas sincronizadas")
    return synced


# ── Demo odds ─────────────────────────────────────────────────────────────
def inject_demo_odds():
    """Cuotas sintéticas basadas en Elo (solo si no hay cuotas reales)."""
    import random
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("""
        SELECT m.id, th.elo_rating as he, ta.elo_rating as ae
        FROM matches m
        JOIN teams th ON m.home_team_id=th.id
        JOIN teams ta ON m.away_team_id=ta.id
        WHERE m.status='SCHEDULED'
          AND NOT EXISTS (SELECT 1 FROM odds o WHERE o.match_id=m.id)
        ORDER BY m.match_date ASC LIMIT 30
    """)
    matches = cur.fetchall()
    for m in matches:
        diff = m["he"] - m["ae"]
        if diff > 200:   ho,do,ao = random.uniform(1.3,1.8), random.uniform(3.5,4.5), random.uniform(4.0,6.0)
        elif diff > 0:   ho,do,ao = random.uniform(1.8,2.5), random.uniform(3.0,3.8), random.uniform(2.5,4.0)
        else:             ho,do,ao = random.uniform(2.5,4.5), random.uniform(3.0,3.8), random.uniform(1.6,2.5)
        cur.execute("INSERT INTO odds (match_id,bookmaker,home_odds,draw_odds,away_odds) VALUES (?,?,?,?,?)",
                    (m["id"],"Demo", round(ho,2), round(do,2), round(ao,2)))
    conn.commit()
    conn.close()
    print(f"✅ Cuotas demo para {len(matches)} partidos")


# ── Queries de consulta ───────────────────────────────────────────────────
def _match_query(where: str, params: tuple) -> list:
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute(f"""
        SELECT m.*, th.name as home_name, th.elo_rating as home_elo,
               ta.name as away_name, ta.elo_rating as away_elo,
               o.home_odds, o.draw_odds, o.away_odds
        FROM matches m
        JOIN teams th ON m.home_team_id=th.id
        JOIN teams ta ON m.away_team_id=ta.id
        LEFT JOIN (SELECT match_id, home_odds, draw_odds, away_odds
                   FROM odds GROUP BY match_id) o ON o.match_id=m.id
        WHERE {where}
        ORDER BY m.match_date ASC, m.match_time ASC
    """, params)
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_upcoming_matches(days_ahead: int = 7) -> list:
    today = date.today()
    until = today + timedelta(days=days_ahead)
    return _match_query("m.match_date BETWEEN ? AND ? AND m.status='SCHEDULED'",
                        (today.isoformat(), until.isoformat()))

def get_tomorrows_matches() -> list:
    tomorrow = (date.today()+timedelta(days=1)).isoformat()
    return _match_query("m.match_date=?", (tomorrow,))

def sync_all(demo_mode: bool = False) -> dict:
    """Sincroniza todo. Con API keys usa datos reales; si no, demo."""
    results = {}
    if FOOTBALL_DATA_API_KEY:
        results["matches"] = fd_sync_matches()
    else:
        print("⚠️  Sin FOOTBALL_DATA_API_KEY — sin sincronización de partidos")
        results["matches"] = 0

    if ODDS_API_KEY:
        results["odds"] = odds_sync()
    else:
        results["odds"] = 0

    if demo_mode or (not ODDS_API_KEY):
        inject_demo_odds()

    return results