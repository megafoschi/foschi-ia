import json
import os
from datetime import datetime

ARCHIVO_PAGOS = "data/pagos.json"


def pago_ya_registrado(payment_id):
    if not os.path.exists(ARCHIVO_PAGOS):
        return False

    with open(ARCHIVO_PAGOS, encoding="utf-8") as f:
        pagos = json.load(f)

    return payment_id in pagos


def registrar_pago(usuario, monto, plan, payment_id):
    pagos = {}

    if os.path.exists(ARCHIVO_PAGOS):
        with open(ARCHIVO_PAGOS, encoding="utf-8") as f:
            pagos = json.load(f)

    pagos[str(payment_id)] = {
        "usuario": usuario,
        "monto": monto,
        "plan": plan,
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "status": "approved"
    }

    os.makedirs("data", exist_ok=True)
    with open(ARCHIVO_PAGOS, "w", encoding="utf-8") as f:
        json.dump(pagos, f, indent=2, ensure_ascii=False)
