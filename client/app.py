from __future__ import annotations

import os
import json
import sys
import subprocess
import time
import tkinter as tk
from dataclasses import dataclass
from tkinter import messagebox, scrolledtext, ttk
from typing import Any, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from urllib.parse import urlparse

API_BASE = os.getenv("API_BASE", "http://127.0.0.1:8000")
POLL_MS = 1500  # polling des nouveaux messages
AUTO_START_LOCAL_FASTAPI = os.getenv("AUTO_START_LOCAL_FASTAPI", "true").strip().lower() in (
    "1",
    "true",
    "yes",
    "y",
    "on",
)


def _api_health_url() -> str:
    return f"{API_BASE.rstrip('/')}/health"


def _is_localhost_api() -> bool:
    try:
        u = urlparse(API_BASE)
        return (u.hostname or "").lower() in ("127.0.0.1", "localhost")
    except Exception:
        return False


def ensure_api_running() -> bool:
    try:
        req = Request(_api_health_url(), method="GET", headers={"Accept": "application/json"})
        with urlopen(req, timeout=3) as resp:
            _ = resp.read()
            return True
    except Exception:
        pass

    if not AUTO_START_LOCAL_FASTAPI or not _is_localhost_api():
        return False

    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    server_dir = os.path.join(repo_root, "server")
    u = urlparse(API_BASE)
    host = u.hostname or "127.0.0.1"
    port = u.port or 8000

    cmd = [sys.executable, "-m", "uvicorn", "main:app", "--host", host, "--port", str(port)]
    env = os.environ.copy()
    subprocess.Popen(cmd, cwd=server_dir, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    deadline = time.time() + 15
    while time.time() < deadline:
        try:
            req = Request(_api_health_url(), method="GET", headers={"Accept": "application/json"})
            with urlopen(req, timeout=2) as resp:
                _ = resp.read()
                return True
        except Exception:
            time.sleep(0.5)

    return False


def api_request(
    method: str,
    path: str,
    *,
    token: Optional[str] = None,
    json_body: Optional[dict[str, Any]] = None,
    timeout: float = 8.0,
) -> tuple[int, Any]:
    url = f"{API_BASE}{path}"
    data = None
    headers = {"Accept": "application/json"}

    if json_body is not None:
        data = json.dumps(json_body).encode("utf-8")
        headers["Content-Type"] = "application/json"

    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = Request(url, method=method, data=data, headers=headers)
    try:
        with urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8") if resp.readable() else ""
            if raw:
                return resp.status, json.loads(raw)
            return resp.status, None
    except HTTPError as e:
        raw = e.read().decode("utf-8") if e.fp else ""
        try:
            payload = json.loads(raw) if raw else {"detail": str(e)}
        except json.JSONDecodeError:
            payload = {"detail": raw or str(e)}
        return e.code, payload
    except URLError as e:
        raise ConnectionError(f"Impossible de joindre l'API ({url}). Détail: {e}") from e


@dataclass
class SessionState:
    token: Optional[str] = None
    username: Optional[str] = None
    role: Optional[str] = None
    last_message_id: int = 0


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("ProjetMessage - Chat")
        self.geometry("880x560")
        self.minsize(820, 520)

        self.state = SessionState()

        self.container = ttk.Frame(self)
        self.container.pack(fill="both", expand=True)

        self.frames: dict[str, ttk.Frame] = {}
        for F in (RegisterPage, LoginPage, ChatPage, AdminPage):
            frame = F(parent=self.container, app=self)
            self.frames[F.__name__] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.container.rowconfigure(0, weight=1)
        self.container.columnconfigure(0, weight=1)

        self.show_frame("LoginPage")

    def show_frame(self, name: str) -> None:
        frame = self.frames[name]
        frame.tkraise()
        if hasattr(frame, "on_show"):
            frame.on_show()  # type: ignore[attr-defined]

    def logout(self) -> None:
        self.state = SessionState()
        self.show_frame("LoginPage")


class RegisterPage(ttk.Frame):
    def __init__(self, parent: tk.Misc, app: App) -> None:
        super().__init__(parent)
        self.app = app

        title = ttk.Label(self, text="Inscription", font=("Segoe UI", 18, "bold"))
        title.pack(pady=18)

        form = ttk.Frame(self)
        form.pack(pady=10)

        ttk.Label(form, text="Nom d'utilisateur").grid(row=0, column=0, sticky="w", pady=6)
        self.username = ttk.Entry(form, width=32)
        self.username.grid(row=0, column=1, pady=6)

        ttk.Label(form, text="Mot de passe").grid(row=1, column=0, sticky="w", pady=6)
        self.password = ttk.Entry(form, width=32, show="*")
        self.password.grid(row=1, column=1, pady=6)

        actions = ttk.Frame(self)
        actions.pack(pady=12)

        ttk.Button(actions, text="Créer le compte", command=self.submit).grid(row=0, column=0, padx=6)
        ttk.Button(actions, text="Retour connexion", command=lambda: app.show_frame("LoginPage")).grid(
            row=0, column=1, padx=6
        )

        self.status = ttk.Label(self, text="")
        self.status.pack(pady=10)

    def submit(self) -> None:
        u = self.username.get().strip()
        p = self.password.get().strip()
        if not u or not p:
            messagebox.showwarning("Champs manquants", "Username et mot de passe requis.")
            return

        try:
            code, payload = api_request("POST", "/register", json_body={"username": u, "password": p})
        except ConnectionError as e:
            messagebox.showerror("API indisponible", str(e))
            return

        if code == 201:
            self.status.config(text="Compte créé. Tu peux te connecter.")
            self.app.show_frame("LoginPage")
        else:
            detail = payload.get("detail") if isinstance(payload, dict) else payload
            self.status.config(text=f"Erreur: {detail}")


class LoginPage(ttk.Frame):
    def __init__(self, parent: tk.Misc, app: App) -> None:
        super().__init__(parent)
        self.app = app

        title = ttk.Label(self, text="Connexion", font=("Segoe UI", 18, "bold"))
        title.pack(pady=18)

        form = ttk.Frame(self)
        form.pack(pady=10)

        ttk.Label(form, text="Nom d'utilisateur").grid(row=0, column=0, sticky="w", pady=6)
        self.username = ttk.Entry(form, width=32)
        self.username.grid(row=0, column=1, pady=6)

        ttk.Label(form, text="Mot de passe").grid(row=1, column=0, sticky="w", pady=6)
        self.password = ttk.Entry(form, width=32, show="*")
        self.password.grid(row=1, column=1, pady=6)

        actions = ttk.Frame(self)
        actions.pack(pady=12)

        ttk.Button(actions, text="Se connecter", command=self.submit).grid(row=0, column=0, padx=6)
        ttk.Button(actions, text="Créer un compte", command=lambda: app.show_frame("RegisterPage")).grid(
            row=0, column=1, padx=6
        )

        self.status = ttk.Label(self, text="")
        self.status.pack(pady=10)

        self.bind_all("<Return>", lambda _e: self.submit())

    def submit(self) -> None:
        u = self.username.get().strip()
        p = self.password.get().strip()
        if not u or not p:
            messagebox.showwarning("Champs manquants", "Username et mot de passe requis.")
            return

        try:
            code, payload = api_request("POST", "/login", json_body={"username": u, "password": p})
        except ConnectionError as e:
            messagebox.showerror("API indisponible", str(e))
            return

        if code == 200 and isinstance(payload, dict) and payload.get("access_token"):
            self.app.state.token = payload["access_token"]
            self.app.state.username = payload.get("username")
            self.app.state.role = payload.get("role")
            self.app.state.last_message_id = 0

            self.status.config(text="Connecté.")
            self.app.show_frame("ChatPage")
        else:
            detail = payload.get("detail") if isinstance(payload, dict) else payload
            self.status.config(text=f"Erreur: {detail}")


class ChatPage(ttk.Frame):
    def __init__(self, parent: tk.Misc, app: App) -> None:
        super().__init__(parent)
        self.app = app
        self._poll_after_id: Optional[str] = None

        top = ttk.Frame(self)
        top.pack(fill="x", padx=12, pady=10)

        self.welcome = ttk.Label(top, text="Salon", font=("Segoe UI", 14, "bold"))
        self.welcome.pack(side="left")

        ttk.Button(top, text="Admin", command=self.go_admin).pack(side="right", padx=6)
        ttk.Button(top, text="Déconnexion", command=self.on_logout).pack(side="right", padx=6)

        body = ttk.Frame(self)
        body.pack(fill="both", expand=True, padx=12, pady=10)

        self.chat_box = scrolledtext.ScrolledText(body, state="disabled", wrap="word")
        self.chat_box.pack(fill="both", expand=True)

        bottom = ttk.Frame(self)
        bottom.pack(fill="x", padx=12, pady=10)

        self.msg_entry = ttk.Entry(bottom)
        self.msg_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        ttk.Button(bottom, text="Envoyer", command=self.send).pack(side="left")

        self.status = ttk.Label(self, text="")
        self.status.pack(pady=(0, 10))

        self.msg_entry.bind("<Return>", lambda _e: self.send())

    def on_show(self) -> None:
        if not self.app.state.token:
            self.app.show_frame("LoginPage")
            return
        self.welcome.config(text=f"Salon - connecté: {self.app.state.username} ({self.app.state.role})")
        self.status.config(text="")
        self.start_polling()

    def on_hide(self) -> None:
        self.stop_polling()

    def on_logout(self) -> None:
        self.stop_polling()
        self.app.logout()

    def go_admin(self) -> None:
        if self.app.state.role != "admin":
            messagebox.showinfo("Accès refusé", "Cette page est réservée à l'administrateur.")
            return
        self.stop_polling()
        self.app.show_frame("AdminPage")

    def append_chat(self, line: str) -> None:
        self.chat_box.configure(state="normal")
        self.chat_box.insert("end", line + "\n")
        self.chat_box.configure(state="disabled")
        self.chat_box.see("end")

    def send(self) -> None:
        text = self.msg_entry.get().strip()
        if not text:
            return
        if not self.app.state.token:
            self.app.show_frame("LoginPage")
            return

        try:
            code, payload = api_request(
                "POST",
                "/messages",
                token=self.app.state.token,
                json_body={"message_text": text},
            )
        except ConnectionError as e:
            self.status.config(text=str(e))
            return

        if code == 201:
            self.msg_entry.delete(0, "end")
            self.status.config(text="")
            self.fetch_once()
        else:
            detail = payload.get("detail") if isinstance(payload, dict) else payload
            self.status.config(text=f"Erreur: {detail}")

    def fetch_once(self) -> None:
        token = self.app.state.token
        if not token:
            return

        try:
            code, payload = api_request(
                "GET",
                f"/messages?since_id={self.app.state.last_message_id}",
                token=token,
            )
        except ConnectionError as e:
            self.status.config(text=str(e))
            return

        if code == 200 and isinstance(payload, list):
            for m in payload:
                mid = int(m["id"])
                self.app.state.last_message_id = max(self.app.state.last_message_id, mid)
                self.append_chat(f"[{m['timestamp']}] {m['username']}: {m['message_text']}")
            self.status.config(text="")
        else:
            detail = payload.get("detail") if isinstance(payload, dict) else payload
            self.status.config(text=f"Erreur: {detail}")

    def start_polling(self) -> None:
        self.stop_polling()
        self.fetch_once()
        self._poll_after_id = self.after(POLL_MS, self._poll_tick)

    def stop_polling(self) -> None:
        if self._poll_after_id is not None:
            try:
                self.after_cancel(self._poll_after_id)
            except Exception:
                pass
            self._poll_after_id = None

    def _poll_tick(self) -> None:
        self.fetch_once()
        self._poll_after_id = self.after(POLL_MS, self._poll_tick)


class AdminPage(ttk.Frame):
    def __init__(self, parent: tk.Misc, app: App) -> None:
        super().__init__(parent)
        self.app = app

        top = ttk.Frame(self)
        top.pack(fill="x", padx=12, pady=10)

        ttk.Label(top, text="Admin - Gestion", font=("Segoe UI", 14, "bold")).pack(side="left")
        ttk.Button(top, text="Retour salon", command=self.back).pack(side="right", padx=6)
        ttk.Button(top, text="Déconnexion", command=self.on_logout).pack(side="right", padx=6)

        tabs = ttk.Notebook(self)
        tabs.pack(fill="both", expand=True, padx=12, pady=10)

        self.users_tab = ttk.Frame(tabs)
        self.msg_tab = ttk.Frame(tabs)
        tabs.add(self.users_tab, text="Utilisateurs")
        tabs.add(self.msg_tab, text="Messages")

        self.users_list = tk.Listbox(self.users_tab)
        self.users_list.pack(side="left", fill="both", expand=True, padx=(0, 8), pady=8)
        users_actions = ttk.Frame(self.users_tab)
        users_actions.pack(side="left", fill="y", pady=8)
        ttk.Button(users_actions, text="Rafraîchir", command=self.refresh_users).pack(fill="x", pady=4)
        ttk.Button(users_actions, text="Supprimer", command=self.delete_selected_user).pack(fill="x", pady=4)

        self.msg_list = tk.Listbox(self.msg_tab)
        self.msg_list.pack(side="left", fill="both", expand=True, padx=(0, 8), pady=8)
        msg_actions = ttk.Frame(self.msg_tab)
        msg_actions.pack(side="left", fill="y", pady=8)
        ttk.Button(msg_actions, text="Rafraîchir", command=self.refresh_messages).pack(fill="x", pady=4)
        ttk.Button(msg_actions, text="Supprimer", command=self.delete_selected_message).pack(fill="x", pady=4)

        self.status = ttk.Label(self, text="")
        self.status.pack(pady=(0, 10))

        self._users_cache: list[dict[str, Any]] = []
        self._msgs_cache: list[dict[str, Any]] = []

    def on_show(self) -> None:
        if self.app.state.role != "admin":
            self.app.show_frame("ChatPage")
            return
        self.status.config(text="")
        self.refresh_users()
        self.refresh_messages()

    def back(self) -> None:
        self.app.show_frame("ChatPage")

    def on_logout(self) -> None:
        self.app.logout()

    def refresh_users(self) -> None:
        token = self.app.state.token
        if not token:
            return
        try:
            code, payload = api_request("GET", "/admin/users", token=token)
        except ConnectionError as e:
            self.status.config(text=str(e))
            return

        if code == 200 and isinstance(payload, list):
            self._users_cache = payload
            self.users_list.delete(0, "end")
            for u in payload:
                self.users_list.insert("end", f"#{u['id']}  {u['username']}  ({u['role']})")
            self.status.config(text="")
        else:
            detail = payload.get("detail") if isinstance(payload, dict) else payload
            self.status.config(text=f"Erreur: {detail}")

    def delete_selected_user(self) -> None:
        sel = self.users_list.curselection()
        if not sel:
            return
        idx = int(sel[0])
        user = self._users_cache[idx]
        if not messagebox.askyesno("Confirmation", f"Supprimer l'utilisateur {user['username']} ?"):
            return

        token = self.app.state.token
        if not token:
            return
        code, payload = api_request("DELETE", f"/admin/users/{user['id']}", token=token)
        if code == 204:
            self.refresh_users()
        else:
            detail = payload.get("detail") if isinstance(payload, dict) else payload
            self.status.config(text=f"Erreur: {detail}")

    def refresh_messages(self) -> None:
        token = self.app.state.token
        if not token:
            return
        try:
            code, payload = api_request("GET", "/admin/messages?limit=300", token=token)
        except ConnectionError as e:
            self.status.config(text=str(e))
            return

        if code == 200 and isinstance(payload, list):
            self._msgs_cache = payload
            self.msg_list.delete(0, "end")
            for m in payload:
                line = f"#{m['id']}  [{m['timestamp']}] {m['username']}: {m['message_text']}"
                self.msg_list.insert("end", line[:220])
            self.status.config(text="")
        else:
            detail = payload.get("detail") if isinstance(payload, dict) else payload
            self.status.config(text=f"Erreur: {detail}")

    def delete_selected_message(self) -> None:
        sel = self.msg_list.curselection()
        if not sel:
            return
        idx = int(sel[0])
        msg = self._msgs_cache[idx]
        if not messagebox.askyesno("Confirmation", f"Supprimer le message #{msg['id']} ?"):
            return

        token = self.app.state.token
        if not token:
            return
        code, payload = api_request("DELETE", f"/admin/messages/{msg['id']}", token=token)
        if code == 204:
            self.refresh_messages()
        else:
            detail = payload.get("detail") if isinstance(payload, dict) else payload
            self.status.config(text=f"Erreur: {detail}")


def main() -> None:
    try:
        ok = ensure_api_running()
        if not ok:
            messagebox.showerror(
                "API indisponible",
                "Impossible de joindre l'API FastAPI. "
                "Vérifie que `server/.env` est configuré (MySQL) "
                "ou mets la bonne variable `API_BASE` (URL Railway de l'API).",
            )
        App().mainloop()
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    main()

