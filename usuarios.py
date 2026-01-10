# usuarios.py
import json, os
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

USUARIOS_FILE = "data/usuarios.json"

def _load():
    if not os.path.exists(USUARIOS_FILE):
        return {}
    return json.load(open(USUARIOS_FILE, encoding="utf-8"))

def _save(data):
    json.dump(data, open(USUARIOS_FILE, "w", encoding="utf-8"), indent=2)

def registrar_usuario(email, password):
    users = _load()
    if email in users:
        return False, "El usuario ya existe"

    users[email] = {
        "password": generate_password_hash(password),
        "creado": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "verificado": False,
        "premium_hasta": None
    }
    _save(users)
    return True, "Usuario creado"

def autenticar_usuario(email, password):
    users = _load()
    if email not in users:
        return False
    return check_password_hash(users[email]["password"], password)

def marcar_verificado(email):
    users = _load()
    if email in users:
        users[email]["verificado"] = True
        _save(users)

def es_premium(email):
    users = _load()
    if email not in users:
        return False
    hasta = users[email].get("premium_hasta")
    if not hasta:
        return False
    return datetime.fromisoformat(hasta) > datetime.now()

def activar_premium(email, dias):
    users = _load()
    if email not in users:
        return
    vencimiento = datetime.now() + timedelta(days=dias)
    users[email]["premium_hasta"] = vencimiento.isoformat()
    _save(users)
