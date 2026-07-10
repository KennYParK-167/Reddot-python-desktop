from __future__ import annotations
import os, sys, json, time, subprocess, tkinter as tk
from tkinter import messagebox, scrolledtext
from urllib.request import Request, urlopen

API_BASE = os.getenv("API_BASE", "http://127.0.0.1:8000")
POLL_MS = 4000


BG_WHITE = "#FFFFFF"
INPUT_BG = "#EAEAEA"
BTN_DARK = "#191919"
BTN_RED  = "#FF0000"
BLUE_MSG = "#91A9DC"
GRAY_MSG = "#EAEAEA"
HEADER_BG = "#191919"


def api_request(method: str, path: str, token: str = None, body: dict = None) -> tuple[int, any]:
    hdrs = {"Accept": "application/json"}
    if body: hdrs["Content-Type"] = "application/json"
    if token: hdrs["Authorization"] = f"Bearer {token}"
    try:
        req = Request(f"{API_BASE}{path}", method=method, data=json.dumps(body).encode() if body else None, headers=hdrs)
        with urlopen(req, timeout=4) as r:
            return r.status, json.loads(r.read().decode()) if r.readable() else None
    except Exception as e:
        if hasattr(e, 'code'):
            try: return e.code, json.loads(e.read().decode())
            except: return e.code, {"detail": "Erreur SQL/Serveur."}
        raise ConnectionError("Echec du connexion au server.") from e
    
def ensure_api() -> bool:
    try:
        with urlopen(f"{API_BASE.rstrip('/')}/health", timeout=2): return True
    except:
        if "127.0.0.1" in API_BASE or "localhost" in API_BASE:
            s_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "server"))
            try:
                subprocess.Popen([sys.executable, "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8000"],
                                 cwd=s_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                for _ in range(15):
                    time.sleep(0.4)
                    try:
                        with urlopen(f"{API_BASE.rstrip('/')}/health", timeout=1): return True
                    except: pass
            except: pass
    return False