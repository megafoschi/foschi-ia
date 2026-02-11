# usuarios.py
import json
import os
from datetime import datetime
from dateutil.relativedelta import relativedelta
from werkzeug.security import generate_password_hash, check_password_hash

USUARIOS_FILE = "data/usuarios_auth.json"

def _load():
    if not os.path.exists(USUARIOS_FILE):
        return {}
    with open(USUARIOS_FILE, encoding="utf-8") as f:
        return json.load(f)

def _save(data):
    with open(USUARIOS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# ------------------------
# REGISTRO / LOGIN
# ------------------------

def registrar_usuario(email, password):
    users = _load()
    email = email.lower()

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
    email = email.lower()

    if email not in users:
        return False

    return check_password_hash(users[email]["password"], password)

def marcar_verificado(email):
    users = _load()
    email = email.lower()

    if email in users:
        users[email]["verificado"] = True
        _save(users)

# ------------------------
# PREMIUM
# ------------------------

def es_premium(email):
    users = _load()
    email = email.lower()

    if email not in users:
        return False

    hasta = users[email].get("premium_hasta")
    if not hasta:
        return False

    return datetime.fromisoformat(hasta) > datetime.now()

def activar_premium(email, plan="mensual"):
    """
    plan: mensual | trimestral | anual
    """
    users = _load()
    email = email.lower()

    if email not in users:
        return False

    delta = {
        "mensual": relativedelta(months=1),
        "trimestral": relativedelta(months=3),
        "anual": relativedelta(years=1)
    }.get(plan)

    if not delta:
        return False

    ahora = datetime.now()

    # Si ya es premium, se suma desde la fecha actual de vencimiento
    actual = users[email].get("premium_hasta")
    base = datetime.fromisoformat(actual) if actual and datetime.fromisoformat(actual) > ahora else ahora

    vencimiento = base + delta
    users[email]["premium_hasta"] = vencimiento.isoformat()

    _save(users)
    return True
