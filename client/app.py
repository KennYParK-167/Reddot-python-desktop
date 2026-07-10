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


# COMPOSANTS BRR/
class UI:
    @staticmethod
    def draw_round_rect(canvas, x1, y1, x2, y2, radius, fill):
        # CALCUL FAIT PAR IA.
        points = [
            x1+radius, y1, x1+radius, y1, x2-radius, y1, x2-radius, y1, x2, y1,
            x2, y1+radius, x2, y1+radius, x2, y2-radius, x2, y2-radius, x2, y2,
            x2-radius, y2, x2-radius, y2, x1+radius, y2, x1+radius, y2, x1, y2,
            x1, y2-radius, x1, y2-radius, x1, y1+radius, x1, y1+radius, x1, y1
        ]
        return canvas.create_polygon(points, fill=fill, smooth=True, outline="")

    @staticmethod
    def entry(p, is_pwd=False, h=40):
        c = tk.Canvas(p, height=h, bg=p["bg"], bd=0, highlightthickness=0)
        e = tk.Entry(c, bg=INPUT_BG, fg="#191919", bd=0, highlightthickness=0, font=("Segoe UI", 11), show="*" if is_pwd else "")
        
        rect_id = None
        win_id = c.create_window(0, 0, window=e, anchor="nw")

        def resize(event):
            nonlocal rect_id
            w = event.width
            rect_id = UI.draw_round_rect(c, 0, 0, w, h, 10, INPUT_BG)
            c.coords(win_id, 10, h // 2)
            c.itemconfigure(win_id, width=w - 20, anchor="w")

        c.bind("<Configure>", resize)
        return c, e

    @staticmethod
    def btn(p, txt, col, cmd, w=140, h=40, fg="#FFFFFF"):
        c = tk.Canvas(p, width=w, height=h, bg=p["bg"], bd=0, highlightthickness=0, cursor="hand2")
        UI.draw_round_rect(c, 0, 0, w, h, 10, col)
        c.create_text(w//2, h//2, text=txt, fill=fg, font=("Segoe UI", 11, "bold"), tags="btn_text")
        c.bind("<Button-1>", lambda _: cmd())
        
        def recolor(new_col, new_fg=None):
            c.delete("all")
            UI.draw_round_rect(c, 0, 0, w, h, 10, new_col)
            c.create_text(w//2, h//2, text=txt, fill=new_fg if new_fg else fg, font=("Segoe UI", 11, "bold"), tags="btn_text")
        c.recolor = recolor
        return c