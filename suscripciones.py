# suscripciones.py

import json
import os
from datetime import datetime, timedelta
from superusuarios import es_superusuario

ARCHIVO = "data/suscripciones.json"


# -----------------------------
# UTILIDADES DE ARCHIVO
# -----------------------------
def _load():
    try:
        if not os.path.exists(ARCHIVO):
            return {}
        with open(ARCHIVO, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print("Error cargando suscripciones:", e)
        return {}


def _save(data):
    try:
        os.makedirs("data", exist_ok=True)
        with open(ARCHIVO, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print("Error guardando suscripciones:", e)


# -----------------------------
# VERIFICAR SI ES PREMIUM
# -----------------------------
def usuario_premium(usuario_id):

    if not usuario_id:
        return False

    usuario_id = usuario_id.lower().strip()

    # ⭐ PRIORIDAD 1 → SUPERUSUARIO = PREMIUM AUTOMÁTICO
    if es_superusuario(usuario_id):
        return True

    # ⭐ PRIORIDAD 2 → SUSCRIPCIÓN NORMAL
    data = _load()
    u = data.get(usuario_id)

    if not u or not u.get("activo"):
        return False

    try:
        vence = datetime.fromisoformat(u["vence"])
    except Exception:
        return False

    if vence < datetime.now():
        u["activo"] = False
        _save(data)
        return False

    return True


# -----------------------------
# ACTIVAR PREMIUM
# -----------------------------
def activar_premium(usuario_id, plan="mensual", payment_id=None):

    if not usuario_id:
        return False

    usuario_id = usuario_id.lower().strip()

    data = _load()
    ahora = datetime.now()

    if plan == "anual":
        vence = ahora + timedelta(days=365)
    else:
        plan = "mensual"
        vence = ahora + timedelta(days=30)

    data[usuario_id] = {
        "plan": plan,
        "activo": True,
        "vence": vence.date().isoformat(),
        "ultimo_pago": ahora.date().isoformat(),
        "payment_id": str(payment_id) if payment_id else "manual"
    }

    _save(data)
    return True


# -----------------------------
# AVISOS DE VENCIMIENTO
# -----------------------------
def aviso_vencimiento(usuario_id):

    if not usuario_id:
        return None

    usuario_id = usuario_id.lower().strip()

    data = _load()
    u = data.get(usuario_id)

    if not u:
        return None

    try:
        vence = datetime.fromisoformat(u["vence"])
    except Exception:
        return None

    dias = (vence - datetime.now()).days

    if dias == 5:
        return "⚠️ Tu suscripción vence en 5 días."
    if dias == 1:
        return "⚠️ Tu suscripción vence mañana."
    if dias < 0:
        return "⛔ Tu suscripción venció. Volvé a activar Premium."

    return None