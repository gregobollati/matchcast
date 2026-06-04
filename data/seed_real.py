"""
Fixture oficial del Mundial 2026.
Horarios en ET convertidos a Argentina (ET + 1 hora).
Fuente: FIFA oficial.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from data.database import get_connection

TEAMS = [
    ("México",                  "MEX", "A", 1820),
    ("Sudáfrica",               "RSA", "A", 1560),
    ("Corea del Sur",           "KOR", "A", 1770),
    ("República Checa",         "CZE", "A", 1680),
    ("Canadá",                  "CAN", "B", 1700),
    ("Bosnia y Herzegovina",    "BIH", "B", 1620),
    ("Qatar",                   "QAT", "B", 1520),
    ("Suiza",                   "SUI", "B", 1810),
    ("Brasil",                  "BRA", "C", 2020),
    ("Marruecos",               "MAR", "C", 1830),
    ("Haití",                   "HAI", "C", 1420),
    ("Escocia",                 "SCO", "C", 1680),
    ("Estados Unidos",          "USA", "D", 1780),
    ("Paraguay",                "PAR", "D", 1550),
    ("Australia",               "AUS", "D", 1730),
    ("Turquía",                 "TUR", "D", 1740),
    ("Alemania",                "GER", "E", 1960),
    ("Curazao",                 "CUW", "E", 1380),
    ("Costa de Marfil",         "CIV", "E", 1660),
    ("Ecuador",                 "ECU", "E", 1760),
    ("Países Bajos",            "NED", "F", 1940),
    ("Japón",                   "JPN", "F", 1840),
    ("Suecia",                  "SWE", "F", 1630),
    ("Túnez",                   "TUN", "F", 1580),
    ("Bélgica",                 "BEL", "G", 1920),
    ("Egipto",                  "EGY", "G", 1640),
    ("Irán",                    "IRN", "G", 1690),
    ("Nueva Zelanda",           "NZL", "G", 1490),
    ("España",                  "ESP", "H", 2040),
    ("Cabo Verde",              "CPV", "H", 1520),
    ("Arabia Saudita",          "KSA", "H", 1670),
    ("Uruguay",                 "URU", "H", 1900),
    ("Francia",                 "FRA", "I", 2050),
    ("Senegal",                 "SEN", "I", 1800),
    ("Irak",                    "IRQ", "I", 1510),
    ("Noruega",                 "NOR", "I", 1750),
    ("Argentina",               "ARG", "J", 2080),
    ("Argelia",                 "ALG", "J", 1530),
    ("Austria",                 "AUT", "J", 1750),
    ("Jordania",                "JOR", "J", 1480),
    ("Portugal",                "POR", "K", 1980),
    ("Rep. Dem. del Congo",     "COD", "K", 1500),
    ("Uzbekistán",              "UZB", "K", 1500),
    ("Colombia",                "COL", "K", 1880),
    ("Inglaterra",              "ENG", "L", 2000),
    ("Croacia",                 "CRO", "L", 1870),
    ("Ghana",                   "GHA", "L", 1570),
    ("Panamá",                  "PAN", "L", 1590),
]

# Horarios ET→ARG (+1h). Formato: (fecha, hora_ARG, grupo, local, visitante, estadio, ciudad)
MATCHES = [
    # ── GRUPO A ──
    ("2026-06-11","16:00","A","México","Sudáfrica","Estadio Ciudad de México","Ciudad de México"),
    ("2026-06-11","23:00","A","Corea del Sur","República Checa","Estadio Guadalajara","Guadalajara"),
    ("2026-06-18","13:00","A","República Checa","Sudáfrica","Mercedes-Benz Stadium","Atlanta"),
    ("2026-06-18","22:00","A","México","Corea del Sur","Estadio Guadalajara","Guadalajara"),
    ("2026-06-24","22:00","A","República Checa","México","Estadio Ciudad de México","Ciudad de México"),
    ("2026-06-24","22:00","A","Sudáfrica","Corea del Sur","Estadio Monterrey","Monterrey"),
    # ── GRUPO B ──
    ("2026-06-12","16:00","B","Canadá","Bosnia y Herzegovina","BMO Field","Toronto"),
    ("2026-06-13","16:00","B","Qatar","Suiza","Levi's Stadium","San Francisco"),
    ("2026-06-18","16:00","B","Suiza","Bosnia y Herzegovina","SoFi Stadium","Los Ángeles"),
    ("2026-06-18","19:00","B","Canadá","Qatar","BC Place","Vancouver"),
    ("2026-06-24","16:00","B","Suiza","Canadá","BC Place","Vancouver"),
    ("2026-06-24","16:00","B","Bosnia y Herzegovina","Qatar","Lumen Field","Seattle"),
    # ── GRUPO C ──
    ("2026-06-13","19:00","C","Brasil","Marruecos","MetLife Stadium","Nueva Jersey"),
    ("2026-06-13","22:00","C","Haití","Escocia","Gillette Stadium","Boston"),
    ("2026-06-19","19:00","C","Escocia","Marruecos","Gillette Stadium","Boston"),
    ("2026-06-19","22:00","C","Brasil","Haití","Lincoln Financial Field","Filadelfia"),
    ("2026-06-24","19:00","C","Brasil","Escocia","Hard Rock Stadium","Miami"),
    ("2026-06-24","19:00","C","Marruecos","Haití","Mercedes-Benz Stadium","Atlanta"),
    # ── GRUPO D ──
    ("2026-06-12","22:00","D","Estados Unidos","Paraguay","SoFi Stadium","Los Ángeles"),
    ("2026-06-13","01:00","D","Australia","Turquía","BC Place","Vancouver"),
    ("2026-06-19","16:00","D","Estados Unidos","Australia","Lumen Field","Seattle"),
    ("2026-06-19","01:00","D","Turquía","Paraguay","Levi's Stadium","San Francisco"),
    ("2026-06-25","23:00","D","Turquía","Estados Unidos","SoFi Stadium","Los Ángeles"),
    ("2026-06-25","23:00","D","Paraguay","Australia","Levi's Stadium","San Francisco"),
    # ── GRUPO E ──
    ("2026-06-14","14:00","E","Alemania","Curazao","NRG Stadium","Houston"),
    ("2026-06-14","20:00","E","Costa de Marfil","Ecuador","Lincoln Financial Field","Filadelfia"),
    ("2026-06-20","17:00","E","Alemania","Costa de Marfil","BMO Field","Toronto"),
    ("2026-06-20","23:00","E","Ecuador","Curazao","Arrowhead Stadium","Kansas City"),
    ("2026-06-25","17:00","E","Curazao","Costa de Marfil","Lincoln Financial Field","Filadelfia"),
    ("2026-06-25","17:00","E","Ecuador","Alemania","MetLife Stadium","Nueva Jersey"),
    # ── GRUPO F ──
    ("2026-06-14","17:00","F","Países Bajos","Japón","AT&T Stadium","Dallas"),
    ("2026-06-14","23:00","F","Suecia","Túnez","Estadio Monterrey","Monterrey"),
    ("2026-06-20","14:00","F","Países Bajos","Suecia","NRG Stadium","Houston"),
    ("2026-06-20","01:00","F","Túnez","Japón","Estadio Monterrey","Monterrey"),
    ("2026-06-25","20:00","F","Japón","Suecia","AT&T Stadium","Dallas"),
    ("2026-06-25","20:00","F","Túnez","Países Bajos","Arrowhead Stadium","Kansas City"),
    # ── GRUPO G ──
    ("2026-06-15","16:00","G","Bélgica","Egipto","Lumen Field","Seattle"),
    ("2026-06-15","22:00","G","Irán","Nueva Zelanda","SoFi Stadium","Los Ángeles"),
    ("2026-06-21","16:00","G","Bélgica","Irán","SoFi Stadium","Los Ángeles"),
    ("2026-06-21","22:00","G","Nueva Zelanda","Egipto","BC Place","Vancouver"),
    ("2026-06-27","00:00","G","Egipto","Irán","Lumen Field","Seattle"),
    ("2026-06-27","00:00","G","Nueva Zelanda","Bélgica","BC Place","Vancouver"),
    # ── GRUPO H ──
    ("2026-06-15","13:00","H","España","Cabo Verde","Mercedes-Benz Stadium","Atlanta"),
    ("2026-06-15","19:00","H","Arabia Saudita","Uruguay","Hard Rock Stadium","Miami"),
    ("2026-06-21","13:00","H","España","Arabia Saudita","Mercedes-Benz Stadium","Atlanta"),
    ("2026-06-21","19:00","H","Uruguay","Cabo Verde","Hard Rock Stadium","Miami"),
    ("2026-06-26","21:00","H","Cabo Verde","Arabia Saudita","NRG Stadium","Houston"),
    ("2026-06-26","21:00","H","Uruguay","España","Estadio Guadalajara","Guadalajara"),
    # ── GRUPO I ──
    ("2026-06-16","16:00","I","Francia","Senegal","MetLife Stadium","Nueva Jersey"),
    ("2026-06-16","19:00","I","Irak","Noruega","Gillette Stadium","Boston"),
    ("2026-06-22","18:00","I","Francia","Irak","Lincoln Financial Field","Filadelfia"),
    ("2026-06-22","21:00","I","Noruega","Senegal","MetLife Stadium","Nueva Jersey"),
    ("2026-06-26","16:00","I","Noruega","Francia","Gillette Stadium","Boston"),
    ("2026-06-26","16:00","I","Senegal","Irak","BMO Field","Toronto"),
    # ── GRUPO J ──
    ("2026-06-16","22:00","J","Argentina","Argelia","Arrowhead Stadium","Kansas City"),
    ("2026-06-17","01:00","J","Austria","Jordania","Levi's Stadium","San Francisco"),
    ("2026-06-22","14:00","J","Argentina","Austria","AT&T Stadium","Dallas"),
    ("2026-06-23","00:00","J","Jordania","Argelia","Levi's Stadium","San Francisco"),
    ("2026-06-27","23:00","J","Argelia","Austria","Arrowhead Stadium","Kansas City"),
    ("2026-06-27","23:00","J","Jordania","Argentina","AT&T Stadium","Dallas"),
    # ── GRUPO K ──
    ("2026-06-17","14:00","K","Portugal","Rep. Dem. del Congo","NRG Stadium","Houston"),
    ("2026-06-17","23:00","K","Uzbekistán","Colombia","Estadio Ciudad de México","Ciudad de México"),
    ("2026-06-23","14:00","K","Portugal","Uzbekistán","NRG Stadium","Houston"),
    ("2026-06-23","23:00","K","Colombia","Rep. Dem. del Congo","Estadio Guadalajara","Guadalajara"),
    ("2026-06-27","20:30","K","Colombia","Portugal","Hard Rock Stadium","Miami"),
    ("2026-06-27","20:30","K","Rep. Dem. del Congo","Uzbekistán","Mercedes-Benz Stadium","Atlanta"),
    # ── GRUPO L ──
    ("2026-06-17","17:00","L","Inglaterra","Croacia","AT&T Stadium","Dallas"),
    ("2026-06-17","20:00","L","Ghana","Panamá","BMO Field","Toronto"),
    ("2026-06-23","17:00","L","Inglaterra","Ghana","Gillette Stadium","Boston"),
    ("2026-06-23","20:00","L","Panamá","Croacia","BMO Field","Toronto"),
    ("2026-06-27","18:00","L","Panamá","Inglaterra","MetLife Stadium","Nueva Jersey"),
    ("2026-06-27","18:00","L","Croacia","Ghana","Lincoln Financial Field","Filadelfia"),
    # ── 16AVOS ──
    ("2026-06-28","00:00","16avos","2º Grupo A","2º Grupo B","SoFi Stadium","Los Ángeles"),
    ("2026-06-29","00:00","16avos","1º Grupo E","3º A/B/C/D/F","Gillette Stadium","Boston"),
    ("2026-06-29","00:00","16avos","1º Grupo F","2º Grupo C","Estadio Monterrey","Monterrey"),
    ("2026-06-29","00:00","16avos","1º Grupo E","2º Grupo F","NRG Stadium","Houston"),
    ("2026-06-30","00:00","16avos","1º Grupo I","3º C/D/F/G/H","MetLife Stadium","Nueva Jersey"),
    ("2026-06-30","00:00","16avos","2º Grupo E","2º Grupo I","AT&T Stadium","Dallas"),
    ("2026-06-30","00:00","16avos","1º Grupo A","3º C/E/F/H/I","Estadio Ciudad de México","Ciudad de México"),
    ("2026-07-01","00:00","16avos","1º Grupo L","3º E/H/I/J/K","Mercedes-Benz Stadium","Atlanta"),
    ("2026-07-01","00:00","16avos","1º Grupo D","3º B/E/F/I/J","Levi's Stadium","San Francisco"),
    ("2026-07-01","00:00","16avos","1º Grupo G","3º A/E/H/I/J","Lumen Field","Seattle"),
    ("2026-07-02","00:00","16avos","2º Grupo K","2º Grupo L","BMO Field","Toronto"),
    ("2026-07-02","00:00","16avos","1º Grupo H","2º Grupo J","SoFi Stadium","Los Ángeles"),
    ("2026-07-02","00:00","16avos","1º Grupo B","3º E/F/G/I/J","BC Place","Vancouver"),
    ("2026-07-03","00:00","16avos","1º Grupo J","2º Grupo H","Hard Rock Stadium","Miami"),
    ("2026-07-03","00:00","16avos","1º Grupo K","3º D/E/I/J/L","Arrowhead Stadium","Kansas City"),
    ("2026-07-03","00:00","16avos","2º Grupo D","2º Grupo G","AT&T Stadium","Dallas"),
    # ── OCTAVOS ──
    ("2026-07-04","00:00","Octavos","G16-2 vs G16-5","","Lincoln Financial Field","Filadelfia"),
    ("2026-07-04","00:00","Octavos","G16-1 vs G16-3","","NRG Stadium","Houston"),
    ("2026-07-05","00:00","Octavos","G16-4 vs G16-6","","MetLife Stadium","Nueva Jersey"),
    ("2026-07-05","00:00","Octavos","G16-7 vs G16-8","","Estadio Ciudad de México","Ciudad de México"),
    ("2026-07-06","00:00","Octavos","G16-11 vs G16-12","","AT&T Stadium","Dallas"),
    ("2026-07-06","00:00","Octavos","G16-9 vs G16-10","","Lumen Field","Seattle"),
    ("2026-07-07","00:00","Octavos","G16-14 vs G16-16","","Mercedes-Benz Stadium","Atlanta"),
    ("2026-07-07","00:00","Octavos","G16-13 vs G16-15","","BC Place","Vancouver"),
    # ── CUARTOS ──
    ("2026-07-09","00:00","Cuartos","Oct-1 vs Oct-2","","Gillette Stadium","Boston"),
    ("2026-07-10","00:00","Cuartos","Oct-5 vs Oct-6","","SoFi Stadium","Los Ángeles"),
    ("2026-07-11","00:00","Cuartos","Oct-3 vs Oct-4","","Hard Rock Stadium","Miami"),
    ("2026-07-11","00:00","Cuartos","Oct-7 vs Oct-8","","Arrowhead Stadium","Kansas City"),
    # ── SEMIS ──
    ("2026-07-14","00:00","Semifinales","Cto-1 vs Cto-2","","AT&T Stadium","Dallas"),
    ("2026-07-15","00:00","Semifinales","Cto-3 vs Cto-4","","Mercedes-Benz Stadium","Atlanta"),
    # ── 3ER PUESTO ──
    ("2026-07-18","00:00","Tercer Puesto","Perdedor Semi-1","Perdedor Semi-2","Hard Rock Stadium","Miami"),
    # ── FINAL ──
    ("2026-07-19","00:00","Final","Ganador Semi-1","Ganador Semi-2","MetLife Stadium","Nueva Jersey"),
]


def seed_real_teams():
    conn = get_connection()
    cur  = conn.cursor()
    for name, code, group, elo in TEAMS:
        cur.execute("INSERT OR IGNORE INTO teams (name, fifa_code, group_name, elo_rating) VALUES (?,?,?,?)",
                    (name, code, group, elo))
    conn.commit()
    conn.close()
    print(f"✅ {len(TEAMS)} equipos insertados")


def seed_real_matches():
    conn = get_connection()
    cur  = conn.cursor()
    inserted = 0
    for date, time, group, home, away, venue, city in MATCHES:
        stage = "Fase de Grupos" if len(group) == 1 else group
        cur.execute("SELECT id FROM teams WHERE name=?", (home,))
        h = cur.fetchone()
        cur.execute("SELECT id FROM teams WHERE name=?", (away,))
        a = cur.fetchone()
        if h and a:
            cur.execute("""INSERT OR IGNORE INTO matches
                (match_date,match_time,stage,group_name,home_team_id,away_team_id,venue,city)
                VALUES (?,?,?,?,?,?,?,?)""",
                (date,time,stage,group,h["id"],a["id"],venue,city))
        else:
            cur.execute("""INSERT OR IGNORE INTO matches
                (match_date,match_time,stage,group_name,venue,city)
                VALUES (?,?,?,NULL,?,?)""",
                (date,time,stage,venue,city))
        inserted += 1
    conn.commit()
    conn.close()
    print(f"✅ {inserted} partidos insertados")


if __name__ == "__main__":
    from data.database import init_db
    init_db()
    seed_real_teams()
    seed_real_matches()
    print("✅ Fixture real del Mundial 2026 cargado")
