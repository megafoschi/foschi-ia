# pagos.py
import json
import os
from datetime import datetime

ARCHIVO = "pagos.json"

def cargar():
    if os.path.exists(ARCHIVO):
        try:
            with open(ARCHIVO, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []

def guardar(data):
    with open(ARCHIVO, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def registrar_pago(usuario, monto, plan, payment_id):
    data = cargar()

    data.append({
        "usuario": usuario,
        "monto": monto,
        "plan": plan,  # "mensual" o "anual"
        "payment_id": payment_id,
        "fecha": datetime.now().isoformat()
    })

    guardar(data)

def pagos_por_usuario(usuario):
    data = cargar()
    return [p for p in data if p["usuario"] == usuario]
