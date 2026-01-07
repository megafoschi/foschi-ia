import json, os
from datetime import datetime, timedelta

USUARIOS_FILE = "data/usuarios.json"

def load_users():
    if not os.path.exists(USUARIOS_FILE):
        return {}
    return json.load(open(USUARIOS_FILE, encoding="utf-8"))

def save_users(users):
    json.dump(users, open(USUARIOS_FILE, "w", encoding="utf-8"), indent=2)

def registrar_usuario(email):
    users = load_users()
    if email not in users:
        users[email] = {
            "premium": False,
            "alta": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        save_users(users)

def es_premium(email):
    users = load_users()
    return users.get(email, {}).get("premium", False)

def activar_premium(email, dias=30):
    users = load_users()
    users[email]["premium"] = True
    users[email]["vence"] = (
        datetime.now() + timedelta(days=dias)
    ).strftime("%Y-%m-%d %H:%M")
    save_users(users)
