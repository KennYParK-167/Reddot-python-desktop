# INITIAL CODE GENERER DANS LE /BACKUPS/app.py.IA.bak  --  ON A PRIS LES MODELES GENERER ET LES AI REMODELISER.
# DESIGN FAIT AVEC TKINTER BUUILDER UI.
# DESIGN FIGMA/PENPOT : https://design.penpot.app/#/workspace?team-id=511bd401-aa1d-80ff-8008-3373a9bae12e&file-id=f2b396a6-c4f1-8031-8008-4ccedff9943c&page-id=f2b396a6-c4f1-8031-8008-4ccedff9943d.


from __future__ import annotations
import os, sys, json, time, subprocess, tkinter as tk
from tkinter import messagebox, scrolledtext
from urllib.request import Request, urlopen

API_BASE = os.getenv("API_BASE", "http://127.0.0.1:8000")
POLL_MS = 4000

# COLORS.
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
    
    
# APP/ TKINTER SOURCE.
class App(tk.Tk):
    def __init__(appc):
        super().__init__()
        appc.title("Reddot - Desktop"); appc.geometry("650x600"); appc.configure(bg=BG_WHITE)
        appc.token = appc.username = appc.role = None
        appc.last_msg_id = 0
        appc.frames = {}
        for F in (LoginPage, RegisterPage, ChatPage, AdminPage):
            f = F(appc); appc.frames[F.__name__] = f; f.grid(row=0, column=0, sticky="nsew")
        appc.columnconfigure(0, weight=1); appc.rowconfigure(0, weight=1)
        appc.show_frame("LoginPage")

    def show_frame(appc, name: str):
        if hasattr(appc.frames.get(name), "on_show"): appc.frames[name].on_show()
        appc.frames[name].tkraise()
        


# APP/ LOGIN PAGE. [CONNEXION]
class LoginPage(tk.Frame):
    def __init__(appc, app):
        super().__init__(app, bg=BG_WHITE)
        appc.app = app
        tk.Label(appc, text="CONNEXION", font=("Segoe UI", 22, "bold"), fg=BTN_DARK, bg=BG_WHITE).pack(pady=(60, 30))
        
        container = tk.Frame(appc, bg=BG_WHITE)
        container.pack(fill="x", padx=125, pady=10)

        tk.Label(container, text="Nom d'utilisateur :", font=("Segoe UI", 11), fg=BTN_DARK, bg=BG_WHITE).pack(anchor="w", pady=(10,2))
        cu, appc.u = UI.entry(container); cu.pack(fill="x", expand=True)
        
        tk.Label(container, text="Mot de passe :", font=("Segoe UI", 11), fg=BTN_DARK, bg=BG_WHITE).pack(anchor="w", pady=(15,2))
        cp, appc.p = UI.entry(container, is_pwd=True); cp.pack(fill="x", expand=True)
        
        UI.btn(container, "Se connecter", BTN_DARK, appc.login, w=160).pack(anchor="w", pady=25)
        
        sep = tk.Frame(container, bg=INPUT_BG, height=1); sep.pack(fill="x", pady=15)
        
        f_inf = tk.Frame(container, bg=BG_WHITE)
        f_inf.pack(anchor="w")
        tk.Label(f_inf, text="Pas encore de compte ?", font=("Segoe UI", 11), fg=BTN_DARK, bg=BG_WHITE).pack(side="left", padx=(0,10))
        UI.btn(f_inf, "S'inscrire", BTN_DARK, lambda: app.show_frame("RegisterPage"), w=110, h=35).pack(side="left")

    def login(appc):
        try:
            c, res = api_request("POST", "/login", body={"username": appc.u.get(), "password": appc.p.get()})
            if c == 200:
                appc.app.token, appc.app.username, appc.app.role, appc.app.last_msg_id = res["access_token"], res.get("username"), res.get("role"), 0
                appc.app.show_frame("ChatPage")
            else: messagebox.showerror("Erreur", res.get("detail", "Identifiant ou mot de passe invalide."))
        except Exception as e:
            messagebox.showerror("Erreur de Connexion", str(e))
    
# APP/ REGISTER PAGE. [INSCRIPTION]
class RegisterPage(tk.Frame):
    def __init__(appc, app):
        super().__init__(app, bg=BG_WHITE)
        appc.app = app
        tk.Label(appc, text="INSCRIPTION", font=("Segoe UI", 22, "bold"), fg=BTN_DARK, bg=BG_WHITE).pack(pady=(50, 25))
        
        container = tk.Frame(appc, bg=BG_WHITE)
        container.pack(fill="x", padx=125, pady=10)

        tk.Label(container, text="Nom d'utilisateur :", font=("Segoe UI", 11), fg=BTN_DARK, bg=BG_WHITE).pack(anchor="w", pady=(5,2))
        cu, appc.u = UI.entry(container); cu.pack(fill="x", expand=True)
        
        tk.Label(container, text="Mot de passe :", font=("Segoe UI", 11), fg=BTN_DARK, bg=BG_WHITE).pack(anchor="w", pady=(10,2))
        cp, appc.p = UI.entry(container, is_pwd=True); cp.pack(fill="x", expand=True)
        
        tk.Label(container, text="Confirmation du Mot de Passe :", font=("Segoe UI", 11), fg=BTN_DARK, bg=BG_WHITE).pack(anchor="w", pady=(10,2))
        ccp, appc.cp = UI.entry(container, is_pwd=True); ccp.pack(fill="x", expand=True)
        
        f_btn = tk.Frame(container, bg=BG_WHITE); f_btn.pack(anchor="w", pady=25)
        UI.btn(f_btn, "S'inscrire", BTN_DARK, appc.reg, w=120).pack(side="left", padx=(0,15))
        UI.btn(f_btn, "Retour", BTN_DARK, lambda: app.show_frame("LoginPage"), w=100).pack(side="left")

    def reg(appc):
        if appc.p.get() != appc.cp.get(): return messagebox.showwarning("Erreur", "Mots de passe différents")
        try:
            c, res = api_request("POST", "/register", body={"username": appc.u.get(), "password": appc.p.get()})
            if c == 201: messagebox.showinfo("OK", "Compte créé !"); appc.app.show_frame("LoginPage")
            else: messagebox.showerror("Erreur", res.get("detail", "Erreur"))
        except Exception as e:
            messagebox.showerror("Erreur de Connexion", str(e))
    
    
# APP/ CHAT PAGE. [SALON DE DISCUSSION]
class ChatPage(tk.Frame):
    def __init__(appc, app):
        super().__init__(app, bg=BG_WHITE); appc.app = app; appc._pid = None
        appc.fetched_ids = set()
        
        appc.hd = tk.Frame(appc, bg=HEADER_BG, height=85)
        appc.hd.pack(fill="x", side="top")
        appc.hd.pack_propagate(False)
        
        lbl_f = tk.Frame(appc.hd, bg=HEADER_BG)
        lbl_f.pack(side="left", padx=20, pady=12)
        appc.lbl_title = tk.Label(lbl_f, text="Chat Page", font=("Segoe UI", 20, "bold"), fg=BG_WHITE, bg=HEADER_BG)
        appc.lbl_title.pack(anchor="w")
        appc.lbl_usr = tk.Label(lbl_f, text="", font=("Segoe UI", 12, "bold"), fg=BG_WHITE, bg=HEADER_BG)
        appc.lbl_usr.pack(anchor="w", pady=(2, 0))
        
        appc.btn_deco = UI.btn(appc.hd, "Deconnexion", BTN_RED, appc.deco, w=130, h=38, fg=BG_WHITE)
        appc.btn_deco.pack(side="right", padx=20, pady=22)
        
        appc.btn_adm = UI.btn(appc.hd, "Admin Page", BG_WHITE, lambda: app.show_frame("AdminPage"), w=130, h=38, fg=BTN_DARK)
        
        appc.bf = tk.Frame(appc, bg=BG_WHITE, height=70)
        appc.bf.pack(fill="x", side="bottom", padx=20, pady=15)
        
        appc.ce, appc.e = UI.entry(appc.bf, h=45)
        appc.ce.pack(side="left", fill="x", expand=True, padx=(0, 15))
        appc.e.bind("<Return>", lambda _: appc.send())
        
        appc.btn_send = UI.btn(appc.bf, "Envoyer", BTN_DARK, appc.send, w=110, h=45, fg=BG_WHITE)
        appc.btn_send.pack(side="right")
        
        appc.box = scrolledtext.ScrolledText(appc, state="disabled", wrap="word", bg=BG_WHITE, bd=0, highlightthickness=0)
        appc.box.pack(fill="both", expand=True, padx=20, pady=10)

    def on_show(appc):
        role_clean = appc.app.role.capitalize() if appc.app.role else 'User'
        appc.lbl_usr.config(text=f"{appc.app.username} - {role_clean}")
        
        if appc.app.role == "admin":
            appc.btn_adm.pack(side="right", padx=5, pady=22)
        else:
            appc.btn_adm.pack_forget()
            
        if appc.app.last_msg_id == 0:
            appc.fetched_ids.clear()
            appc.box.config(state="normal"); appc.box.delete("1.0", "end"); appc.box.config(state="disabled")
        appc.tick()

    def deco(appc):
        if appc._pid: appc.after_cancel(appc._pid)
        appc.app.show_frame("LoginPage")

    def send(appc):
        if not appc.e.get().strip(): return
        try:
            if api_request("POST", "/messages", appc.app.token, {"message_text": appc.e.get()})[0] == 201:
                appc.e.delete(0, "end"); appc.fetch()
        except: pass

    def make_bubble_widget(appc, text, bg_color):
        dummy = tk.Canvas(appc.box, bg=BG_WHITE, bd=0, highlightthickness=0)
        lbl = tk.Label(dummy, text=text, bg=bg_color, fg=BTN_DARK, font=("Segoe UI", 11), wraplength=380, justify="left")
        lbl.update_idletasks()
        tw, th = lbl.winfo_reqwidth(), lbl.winfo_reqheight()
        w, h = max(tw + 24, 80), th + 16
        dummy.config(width=w, height=h)
        UI.draw_round_rect(dummy, 0, 0, w, h, 10, bg_color)
        dummy.create_window(w//2, h//2, window=lbl, width=w-24, height=h-16)
        return dummy


    #  FETCH LES MESSAGE. []
    def fetch(appc):
        try:
            c, res = api_request("GET", f"/messages?since_id={appc.app.last_msg_id}", appc.app.token)
            if c == 200 and res:
                has_new = False
                for m in res:
                    if m["id"] not in appc.fetched_ids:
                        if not has_new:
                            appc.box.config(state="normal")
                            has_new = True
                        
                        appc.fetched_ids.add(m["id"])
                        if m["id"] > appc.app.last_msg_id:
                            appc.app.last_msg_id = m["id"]
                        
                        is_me = (m["username"] == appc.app.username)
                        sender_name = m["username"]
                        
                        if is_me and appc.app.role:
                            role_name = appc.app.role.capitalize()
                        else:
                            role_name = m.get('role', 'User').capitalize()
                            
                        bg_bubble = BLUE_MSG if is_me else GRAY_MSG
                        
                        appc.box.insert("end", f"{sender_name} - {role_name}\n", "header_tag")
                        bubble_widget = appc.make_bubble_widget(m['message_text'], bg_bubble)
                        appc.box.window_create("end", window=bubble_widget)
                        appc.box.insert("end", "\n")
                        t_str = m.get('timestamp', 'Date - Heure')
                        appc.box.insert("end", f"[ {t_str} ]\n\n", "time_tag")
                
                if has_new:
                    appc.box.tag_config("header_tag", font=("Segoe UI", 11, "bold"), foreground=BTN_DARK, spacing3=4)
                    appc.box.tag_config("time_tag", font=("Segoe UI", 10), foreground=BTN_DARK, spacing1=4)
                    appc.box.config(state="disabled")
                    appc.box.see("end")
        except: pass

    def tick(appc):
        if appc.winfo_viewable(): appc.fetch(); appc._pid = appc.after(POLL_MS, appc.tick)




# APP/ ADMIN PAGE. [PAGE D'ADMINISTRATION]
class AdminPage(tk.Frame):
    def __init__(appc, app):
        super().__init__(app, bg=BG_WHITE); appc.app = app
        
        appc.hd = tk.Frame(appc, bg=HEADER_BG, height=85)
        appc.hd.pack(fill="x", side="top")
        appc.hd.pack_propagate(False)
        
        lbl_f = tk.Frame(appc.hd, bg=HEADER_BG)
        lbl_f.pack(side="left", padx=20, pady=12)
        tk.Label(lbl_f, text="Admin Page", font=("Segoe UI", 20, "bold"), fg=BG_WHITE, bg=HEADER_BG).pack(anchor="w")
        appc.lbl_usr = tk.Label(lbl_f, text="", font=("Segoe UI", 12, "bold"), fg=BG_WHITE, bg=HEADER_BG)
        appc.lbl_usr.pack(anchor="w", pady=(2, 0))
        
        UI.btn(appc.hd, "Retour au Salon", BG_WHITE, lambda: app.show_frame("ChatPage"), w=150, h=38, fg=BTN_DARK).pack(side="right", padx=20, pady=22)
        
        appc.tabs_f = tk.Frame(appc, bg=BG_WHITE)
        appc.tabs_f.pack(fill="x", padx=20, pady=(15, 5))
        
        appc.b_u = UI.btn(appc.tabs_f, "Utilisateurs", BTN_DARK, appc.show_users, w=120, h=35, fg=BG_WHITE)
        appc.b_u.pack(side="left", padx=(0, 10))
        appc.b_m = UI.btn(appc.tabs_f, "Messages", "#5C5C5C", appc.show_msgs, w=120, h=35, fg=BG_WHITE)
        appc.b_m.pack(side="left")
        
        appc.content_f = tk.Frame(appc, bg=BG_WHITE)
        appc.content_f.pack(fill="both", expand=True, padx=20, pady=10)
        
        appc.list_bg = tk.Canvas(appc.content_f, bg=BG_WHITE, bd=0, highlightthickness=0)
        appc.list_bg.pack(side="left", fill="both", expand=True)
        
        appc.list_box = tk.Listbox(appc.list_bg, bg=GRAY_MSG, bd=0, highlightthickness=0, font=("Segoe UI", 11), fg=BTN_DARK, selectbackground=BLUE_MSG, selectforeground=BTN_DARK)
        appc.list_bg.bind("<Configure>", appc._resize_list_bg)
        
        appc.btn_del_f = tk.Frame(appc.content_f, bg=BG_WHITE)
        appc.btn_del_f.pack(side="right", fill="y", padx=(15, 0))
        UI.btn(appc.btn_del_f, "Supprimer", BTN_RED, appc.delete_item, w=120, h=40, fg=BG_WHITE).pack(side="bottom", pady=(0, 5))
        
        appc.mode = "users"; appc.items = []

    def _resize_list_bg(appc, event):
        w, h = event.width, event.height
        appc.list_bg.delete("all")
        UI.draw_round_rect(appc.list_bg, 0, 0, w, h, 10, GRAY_MSG)
        appc.list_bg.create_window(w//2, h//2, window=appc.list_box, width=w-20, height=h-20)

    def on_show(appc):
        role_clean = appc.app.role.capitalize() if appc.app.role else 'User'
        appc.lbl_usr.config(text=f"{appc.app.username} - {role_clean}")
        appc.show_users()
        
    def show_users(appc):
        appc.mode = "users"
        appc.b_u.recolor(BTN_DARK, BG_WHITE)
        appc.b_m.recolor("#5C5C5C", BG_WHITE)
        
        try:
            c, res = api_request("GET", "/admin/users", appc.app.token)
            if c == 200:
                appc.list_box.delete(0, "end"); appc.items = res
                for u in res: 
                    appc.list_box.insert("end", f"  #{u['id']}  {u['username']} ({u['role'].capitalize() if u.get('role') else 'User'})")
        except Exception as e:
            appc.list_box.delete(0, "end")
            appc.list_box.insert("end", " Erreur : Impossible de joindre la base de données MySQL sur le serveur.")

    def show_msgs(appc):
        appc.mode = "messages"
        appc.b_u.recolor("#5C5C5C", BG_WHITE)
        appc.b_m.recolor(BTN_DARK, BG_WHITE)
        
        try:
            c, res = api_request("GET", "/admin/messages?limit=100", appc.app.token)
            if c == 200:
                appc.list_box.delete(0, "end"); appc.items = res
                for m in res: 
                    is_me = (m["username"] == appc.app.username)
                    if is_me and appc.app.role:
                        m_role = appc.app.role.capitalize()
                    else:
                        m_role = m.get('role', 'User').capitalize()
                    appc.list_box.insert("end", f"  #{m['id']}  {m['username']} ({m_role}): {m['message_text']}")
        except Exception as e:
            appc.list_box.delete(0, "end")

    def delete_item(appc):
        if not appc.list_box.curselection() or appc.list_box.get(appc.list_box.curselection()[0]).startswith(" Erreur"): return
        item = appc.items[appc.list_box.curselection()[0]]
        path = f"/admin/users/{item['id']}" if appc.mode == "users" else f"/admin/messages/{item['id']}"
        if messagebox.askyesno("Suppression", "Veuillez confimrer la suppression ?"):
            try:
                if api_request("DELETE", path, appc.app.token)[0] in (200, 204):
                    appc.show_users() if appc.mode == "users" else appc.show_msgs()
            except Exception as e:
                messagebox.showerror("Erreur", str(e))



# FONCTION DE LANCEMENT. [LOOP DU TKINTER INTERFACE]
if __name__ == "__main__":
    ensure_api()
    App().mainloop()