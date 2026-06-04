import sys, os, webbrowser, threading, time 
sys.path.insert(0, os.path.dirname(__file__)) 
def open_browser(): 
    time.sleep(1.5) 
    webbrowser.open("http://localhost:5000") 
threading.Thread(target=open_browser, daemon=True).start() 
from api import app 
print("Abriendo en http://localhost:5000") 
app.run(host="0.0.0.0", port=5000, debug=False) 
