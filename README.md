# 🏆 Prode Mundial 2026

Sistema de predicción inteligente para ganar el prode del Mundial FIFA 2026.
Combina **Rating Elo**, **Distribución de Poisson** y **Simulación Monte Carlo**.

---

## 📁 Estructura del proyecto

```
prode_mundial/
├── app.py                    # Dashboard principal Streamlit
├── requirements.txt
├── data/
│   ├── database.py           # SQLite: inicialización, schema, seed data
│   └── mundial2026.db        # Base de datos (auto-generada)
├── models/
│   ├── elo.py                # Cálculo y actualización de ratings Elo
│   └── predictor.py          # Poisson + Monte Carlo + recomendación prode
└── utils/
    ├── api_fetcher.py         # Clientes de football-data.org y The Odds API
    └── report_generator.py   # Informes diarios y evaluación de rendimiento
```

---

## 🚀 Instalación y ejecución

```bash
# 1. Clonar / descomprimir el proyecto
cd prode_mundial

# 2. Crear entorno virtual (recomendado)
python -m venv .venv
source .venv/bin/activate        # Linux/Mac
.venv\Scripts\activate           # Windows

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. (Opcional) Configurar API keys para datos reales
export FOOTBALL_DATA_API_KEY="tu_key"   # gratis en football-data.org
export ODDS_API_KEY="tu_key"            # gratis en the-odds-api.com

# 5. Ejecutar la aplicación
streamlit run app.py
```

La app abre en: **http://localhost:8501**

---

## 🔑 APIs gratuitas

| API | Free tier | Uso en este proyecto |
|-----|-----------|---------------------|
| [football-data.org](https://www.football-data.org/) | 10 req/min | Fixture, resultados, equipos |
| [The Odds API](https://the-odds-api.com/) | 500 req/mes | Cuotas de apuestas |

Sin API keys, la app funciona en **modo demo** con datos sintéticos.

---

## 🧠 Metodología

### 1. Rating Elo
- Cada selección tiene un rating inicial basado en su historial FIFA.
- Después de cada partido del Mundial, los ratings se actualizan con la fórmula Elo estándar.
- Factor K = 60 para partidos mundialistas (partido neutral → sin ventaja de local).
- La diferencia de margen de goles modifica el cambio de rating.

### 2. Distribución de Poisson
- Los goles de cada equipo siguen una distribución de Poisson(λ).
- λ se calcula a partir de la diferencia de Elo y el promedio histórico del Mundial (2.65 goles/partido).
- Se ajusta con un factor de **forma reciente** calculado desde los resultados del torneo.
- Si hay cuotas disponibles, se hace un blend 65% Elo / 35% cuotas.

### 3. Simulación Monte Carlo
- Se simulan **50.000 partidos** (configurable hasta 100.000).
- Se obtiene la distribución completa de marcadores.
- Se calculan probabilidades de victoria, empate y derrota.

### 4. Recomendación para el prode
- En un prode de N participantes, la estrategia óptima no es solo maximizar P(acierto).
- El sistema calcula el **valor esperado de puntos exclusivos**:
  ```
  EV = P(exacto) × bonus_exclusividad + P(resultado correcto) × 1
  ```
- Favoritos claros → se recomienda el marcador más probable.
- Partidos parejos → se busca un marcador con alta probabilidad pero baja popularidad.

---

## 📊 Sistema de puntuación

| Acierto | Puntos |
|---------|--------|
| Marcador exacto | 3 pts |
| Resultado correcto (1X2) | 1 pt |
| Sin acierto | 0 pts |

---

## 🔄 Flujo de trabajo recomendado

1. **Antes del torneo**: Correr la app → los ratings Elo iniciales están pre-cargados.
2. **Cada día**: Ir al tab "Informe diario" → seleccionar la fecha de mañana → generar.
3. **Después de cada partido**: Clic en "Evaluar" en el sidebar para actualizar Elo y performance.
4. **Monitoreo**: Tab "Rendimiento" para ver qué tan bien predice el sistema.

---

## 📝 Notas

- Los partidos de la fase de grupos están pre-cargados con fechas y horarios reales (UTC-5 aprox).
- Los ratings Elo iniciales son estimaciones basadas en el ranking FIFA de mayo 2026.
- Los partidos de eliminatorias directas (octavos en adelante) se cargan automáticamente cuando
  la API retorna los fixtures oficiales una vez clasificados los equipos.
