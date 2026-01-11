# usuarios.py
import json, os, secrets
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash

USUARIOS_FILE = "data/usuarios.json"
os.makedirs("data", exist_ok=True)

def _load():
    if not os.path.exists(USUARIOS_FILE):
        return {}
    return json.load(open(USUARIOS_FILE, encoding="utf-8"))

def _save(data):
    json.dump(data, open(USUARIOS_FILE, "w", encoding="utf-8"), indent=2)

# ===============================
# REGISTRO
# ===============================
def registrar_usuario(email, password):
    users = _load()
    if email in users:
        return False, "El usuario ya existe"

    users[email] = {
        "password": generate_password_hash(password),
        "creado": datetime.utcnow().strftime("%Y-%m-%d %H:%M"),
        "verificado": False,
        "premium_hasta": None,
        "session_token": secrets.token_hex(16)
    }
    _save(users)
    return True, "Usuario creado"

# ===============================
# LOGIN
# ===============================
def autenticar_usuario(email, password):
    users = _load()
    if email not in users:
        return False, "Usuario inexistente"

    if not users[email].get("verificado"):
        return False, "Correo no verificado"

    if not check_password_hash(users[email]["password"], password):
        return False, "Contraseña incorrecta"

    return True, "OK"

# ===============================
# VERIFICACIÓN
# ===============================
def marcar_verificado(email):
    users = _load()
    if email in users:
        users[email]["verificado"] = True
        _save(users)

# ===============================
# PREMIUM
# ===============================
def es_premium(email):
    users = _load()
    if email not in users:
        return False

    hasta = users[email].get("premium_hasta")
    if not hasta:
        return False

    return datetime.fromisoformat(hasta) > datetime.utcnow()

def activar_premium(email, dias):
    users = _load()
    if email not in users:
        return

    vencimiento = datetime.utcnow() + timedelta(days=dias)
    users[email]["premium_hasta"] = vencimiento.isoformat()
    _save(users)

# ===============================
# SESIONES
# ===============================
def rotar_sesion(email):
    users = _load()
    if email in users:
        users[email]["session_token"] = secrets.token_hex(16)
        _save(users)
