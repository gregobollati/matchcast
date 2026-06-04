"""
MatchCast — Punto de entrada único.
Flask + auto-sync en un solo proceso.

Uso local:   python run.py
Producción:  python run.py --no-browser
"""
import sys, os, time, threading, logging, argparse
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

parser = argparse.ArgumentParser()
parser.add_argument("--port",       type=int, default=int(os.getenv("PORT", 5000)))
parser.add_argument("--host",       type=str, default="0.0.0.0")
parser.add_argument("--no-browser", action="store_true")
parser.add_argument("--no-sync",    action="store_true")
parser.add_argument("--sync-hours", type=str, default="8,12,16,20,23")
args = parser.parse_args()

SYNC_HOURS = [int(h) for h in args.sync_hours.split(",")]

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger("matchcast")

log.info(f"🚀 MatchCast arrancando en puerto {args.port}")

def auto_sync_loop():
    from utils.api_fetcher import sync_all
    has_key = bool(os.getenv("FOOTBALL_DATA_API_KEY"))
    demo    = not has_key
    if demo:
        log.info("⚠️  Sin API keys — modo demo")
    else:
        log.info(f"🔑 API keys OK — sync a las {SYNC_HOURS}hs ARG")
    last = -1
    time.sleep(5)
    log.info("🔄 Sincronización inicial...")
    try:
        sync_all(demo_mode=demo)
        log.info("✅ Sync inicial OK")
    except Exception as e:
        log.warning(f"Sync inicial: {e}")
    while True:
        now = datetime.now()
        if now.hour in SYNC_HOURS and now.hour != last:
            log.info(f"🔄 Sync programada ({now.hour}hs)...")
            try:
                sync_all(demo_mode=demo)
                log.info("✅ Sync OK")
                last = now.hour
            except Exception as e:
                log.warning(f"Sync: {e}")
        time.sleep(60)

if not args.no_sync:
    threading.Thread(target=auto_sync_loop, daemon=True, name="sync").start()

if not args.no_browser:
    import webbrowser
    def open_b():
        time.sleep(2)
        webbrowser.open(f"http://localhost:{args.port}")
    threading.Thread(target=open_b, daemon=True).start()

from api import app
import logging as fl
fl.getLogger("werkzeug").setLevel(logging.WARNING)
log.info(f"✅ Listo — http://localhost:{args.port}\n")
app.run(host=args.host, port=args.port, debug=False, use_reloader=False)
