# suscripciones.py
import json
import os
from datetime import datetime, timedelta

ARCHIVO = "suscripciones.json"

# 🔑 SUPER USUARIOS (SIEMPRE PREMIUM)
SUPER_USUARIOS = {
    "gustavo_foschi",
    "agustina_foschi",
    "belen_foschi",
    "antonella_foschi",
    "renata_foschi"
}

def cargar():
    if os.path.exists(ARCHIVO):
        try:
            return json.load(open(ARCHIVO, "r", encoding="utf-8"))
        except:
            return {}
    return {}

def guardar(data):
    with open(ARCHIVO, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def usuario_premium(usuario):
    # 🦸 SUPER USUARIO → SIEMPRE PREMIUM
    if usuario in SUPER_USUARIOS:
        return True

    data = cargar()
    info = data.get(usuario)
    if not info:
        return False

    try:
        vence = datetime.fromisoformat(info["vence"])
        return vence > datetime.now()
    except:
        return False

def activar_premium(usuario, dias=30):
    data = cargar()
    vence = datetime.now() + timedelta(days=dias)

    data[usuario] = {
        "vence": vence.isoformat()
    }
    guardar(data)

def aviso_vencimiento(usuario):
    """
    Devuelve un aviso corto si el Premium está por vencer o vencido.
    Si no hay nada que avisar, devuelve None.
    """
    if not usuario:
        return None

    # Super usuarios no reciben avisos
    if usuario in SUPER_USUARIOS:
        return None

    data = cargar()
    info = data.get(usuario)
    if not info:
        return None

    try:
        vence = datetime.fromisoformat(info["vence"])
    except:
        return None

    ahora = datetime.now()

    if ahora > vence:
        return "❌ Tu Premium venció. Activá nuevamente para seguir usando todas las funciones 💎"

    dias = (vence - ahora).days

    if dias == 0:
        return "⚠️ Tu Premium vence HOY. Evitá cortes renovando ahora 💎"
    elif dias == 1:
        return "⚠️ Tu Premium vence MAÑANA. Renovalo para seguir sin límites 💎"
    elif 1 < dias <= 3:
        return f"⏳ Tu Premium vence en {dias} días. Recordá renovarlo 💎"

    return None

def usuario_premium(usuario):
    """
    Devuelve un texto corto con el estado del Premium del usuario
    """
    if usuario in SUPER_USUARIOS:
        return "👑 Super usuario · Premium ilimitado"

    data = cargar()
    info = data.get(usuario)

    if not info:
        return "🔓 Usuario gratuito"

    try:
        vence = datetime.fromisoformat(info["vence"])
    except:
        return "🔓 Usuario gratuito"

    ahora = datetime.now()

    if ahora > vence:
        return "❌ Premium vencido"

    dias = (vence - ahora).days

    if dias == 0:
        return "⚠️ Premium vence hoy"
    elif dias == 1:
        return "⚠️ Premium vence mañana"
    else:
        return f"✅ Premium activo · vence en {dias} días"
