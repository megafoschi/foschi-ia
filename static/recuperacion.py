# recuperacion.py
import os
import json
from datetime import datetime, timedelta

RECUP_FILE = "data/recuperacion.json"
EXP_MIN = 15

os.makedirs("data", exist_ok=True)

# ===============================
# STORAGE
# ===============================
def _load():
    if not os.path.exists(RECUP_FILE):
        return {}
    return json.load(open(RECUP_FILE, encoding="utf-8"))

def _save(data):
    json.dump(data, open(RECUP_FILE, "w", encoding="utf-8"), indent=2)

# ===============================
# TOKEN CREATION
# ===============================
def crear_token_recuperacion(email, token):
    data = _load()

    # borrar tokens previos del mail
    for t in list(data.keys()):
        if data[t]["email"] == email:
            del data[t]

    data[token] = {
        "email": email,
        "fecha": datetime.utcnow().isoformat()
    }

    _save(data)

# ===============================
# TOKEN VALIDATION
# ===============================
def validar_token(token):
    data = _load()
    if token not in data:
        return None

    fecha = datetime.fromisoformat(data[token]["fecha"])
    if datetime.utcnow() - fecha > timedelta(minutes=EXP_MIN):
        del data[token]
        _save(data)
        return None

    return data[token]["email"]

# ===============================
# TOKEN CONSUMPTION
# ===============================
def consumir_token(token):
    data = _load()
    if token in data:
        del data[token]
        _save(data)
