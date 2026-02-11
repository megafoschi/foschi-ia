# usuarios.py

import json
import os
from datetime import datetime
from dateutil.relativedelta import relativedelta
from werkzeug.security import generate_password_hash, check_password_hash

USUARIOS_FILE = "data/usuarios_auth.json"


# ==========================================================
# UTILIDADES INTERNAS
# ==========================================================

def _load():
    if not os.path.exists(USUARIOS_FILE):
        return {}

    try:
        with open(USUARIOS_FILE, encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        print("⚠️ JSON corrupto, recreando archivo...")
        return {}


def _save(data):
    os.makedirs(os.path.dirname(USUARIOS_FILE), exist_ok=True)
    with open(USUARIOS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _normalizar_email(email):
    return email.strip().lower()


# ==========================================================
# REGISTRO / LOGIN
# ==========================================================

def registrar_usuario(email, password):
    users = _load()
    email = _normalizar_email(email)

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
    email = _normalizar_email(email)

    if email not in users:
        return False

    return check_password_hash(users[email]["password"], password)


def marcar_verificado(email):
    users = _load()
    email = _normalizar_email(email)

    if email in users:
        users[email]["verificado"] = True
        _save(users)
        return True

    return False


def eliminar_usuario(email):
    users = _load()
    email = _normalizar_email(email)

    if email in users:
        del users[email]
        _save(users)
        return True

    return False


def listar_usuarios():
    return _load()


# ==========================================================
# PREMIUM
# ==========================================================

def es_premium(email):
    users = _load()
    email = _normalizar_email(email)

    if email not in users:
        return False

    hasta = users[email].get("premium_hasta")
    if not hasta:
        return False

    try:
        return datetime.fromisoformat(hasta) > datetime.now()
    except:
        return False


def activar_premium(email, plan="mensual"):
    """
    plan: mensual | trimestral | anual
    """

    users = _load()
    email = _normalizar_email(email)

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
    actual = users[email].get("premium_hasta")

    if actual:
        try:
            actual_dt = datetime.fromisoformat(actual)
            base = actual_dt if actual_dt > ahora else ahora
        except:
            base = ahora
    else:
        base = ahora

    vencimiento = base + delta
    users[email]["premium_hasta"] = vencimiento.isoformat()

    _save(users)
    return True


def limpiar_premium_vencidos():
    users = _load()
    ahora = datetime.now()
    cambiado = False

    for email, data in users.items():
        hasta = data.get("premium_hasta")

        if hasta:
            try:
                if datetime.fromisoformat(hasta) <= ahora:
                    data["premium_hasta"] = None
                    cambiado = True
            except:
                data["premium_hasta"] = None
                cambiado = True

    if cambiado:
        _save(users)

    return cambiado
