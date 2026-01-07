# suscripciones.py
import json, os
from datetime import datetime, timedelta

ARCHIVO = "data/suscripciones.json"

def _load():
    if not os.path.exists(ARCHIVO):
        return {}
    with open(ARCHIVO, "r", encoding="utf-8") as f:
        return json.load(f)

def _save(data):
    os.makedirs("data", exist_ok=True)
    with open(ARCHIVO, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def usuario_premium(usuario_id):
    data = _load()
    u = data.get(usuario_id)
    if not u or not u.get("activo"):
        return False
    vence = datetime.fromisoformat(u["vence"])
    if vence < datetime.now():
        u["activo"] = False
        _save(data)
        return False
    return True

def activar_premium(usuario_id, plan="mensual", payment_id=None):
    data = _load()
    ahora = datetime.now()

    if plan == "anual":
        vence = ahora + timedelta(days=365)
    else:
        vence = ahora + timedelta(days=30)

    data[usuario_id] = {
        "plan": plan,
        "activo": True,
        "vence": vence.date().isoformat(),
        "ultimo_pago": ahora.date().isoformat(),
        "payment_id": str(payment_id)
    }
    _save(data)

def aviso_vencimiento(usuario_id):
    data = _load()
    u = data.get(usuario_id)
    if not u:
        return None

    vence = datetime.fromisoformat(u["vence"])
    dias = (vence - datetime.now()).days

    if dias == 5:
        return "⚠️ Tu suscripción vence en 5 días."
    if dias == 1:
        return "⚠️ Tu suscripción vence mañana."
    if dias < 0:
        return "⛔ Tu suscripción venció. Volvé a activar Premium."
    return None
