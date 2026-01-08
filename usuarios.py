import json, os
from datetime import datetime, timedelta

USUARIOS_FILE = "data/usuarios.json"


def load_users():
    if not os.path.exists(USUARIOS_FILE):
        return {}
    with open(USUARIOS_FILE, encoding="utf-8") as f:
        return json.load(f)


def save_users(users):
    with open(USUARIOS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2, ensure_ascii=False)


def registrar_usuario(email):
    users = load_users()
    if email not in users:
        users[email] = {
            "premium": False,
            "alta": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        save_users(users)


def es_premium(email):
    users = load_users()
    user = users.get(email)

    if not user:
        return False

    if not user.get("premium"):
        return False

    vence_str = user.get("vence")
    if not vence_str:
        return False

    vence = datetime.strptime(vence_str, "%Y-%m-%d %H:%M")

    if datetime.now() > vence:
        # 🔻 Premium vencido → limpiar
        user["premium"] = False
        user.pop("vence", None)
        save_users(users)
        return False

    return True


def activar_premium(email, dias=30):
    users = load_users()

    if email not in users:
        users[email] = {
            "alta": datetime.now().strftime("%Y-%m-%d %H:%M")
        }

    users[email]["premium"] = True
    users[email]["vence"] = (
        datetime.now() + timedelta(days=dias)
    ).strftime("%Y-%m-%d %H:%M")

    save_users(users)
