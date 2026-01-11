# verificaciones.py
import os
import json
import smtplib
from datetime import datetime
from email.message import EmailMessage

VERIFS_FILE = "data/verificaciones.json"
os.makedirs("data", exist_ok=True)

# ===============================
# STORAGE
# ===============================
def _load():
    if not os.path.exists(VERIFS_FILE):
        return {}
    return json.load(open(VERIFS_FILE, encoding="utf-8"))

def _save(data):
    json.dump(data, open(VERIFS_FILE, "w", encoding="utf-8"), indent=2)

# ===============================
# SMTP (INTERNO)
# ===============================
def _enviar_mail(msg):
    mail_user = os.getenv("MAIL_USER")
    mail_pass = os.getenv("MAIL_PASS")

    if not mail_user or not mail_pass:
        raise RuntimeError("Variables MAIL_USER / MAIL_PASS no configuradas")

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(mail_user, mail_pass)
        smtp.send_message(msg)

# ===============================
# VERIFICACIÓN DE CUENTA
# ===============================
def crear_y_enviar_verificacion(email, token):
    verifs = _load()

    # borrar tokens previos de ese email
    for t in list(verifs.keys()):
        if verifs[t]["email"] == email:
            del verifs[t]

    verifs[token] = {
        "email": email,
        "fecha": datetime.utcnow().isoformat()
    }

    _save(verifs)

    msg = EmailMessage()
    msg["Subject"] = "Verificá tu cuenta – Foschi IA"
    msg["From"] = os.getenv("MAIL_USER")
    msg["To"] = email
    msg.set_content(
        "Hola 👋\n\n"
        "Para verificar tu cuenta ingresá al siguiente link:\n"
        f"https://foschi-ia.onrender.com/verify/{token}\n\n"
        "Foschi IA"
    )

    _enviar_mail(msg)

# ===============================
# RECUPERACIÓN DE CONTRASEÑA
# ===============================
def enviar_recuperacion(email, token):
    msg = EmailMessage()
    msg["Subject"] = "Recuperar contraseña – Foschi IA"
    msg["From"] = os.getenv("MAIL_USER")
    msg["To"] = email
    msg.set_content(
        "Hola 👋\n\n"
        "Para crear una nueva contraseña ingresá acá:\n"
        f"https://foschi-ia.onrender.com/reset/{token}\n\n"
        "Este link vence en 15 minutos.\n\n"
        "Foschi IA"
    )

    _enviar_mail(msg)

# ===============================
# AVISO DE SEGURIDAD
# ===============================
def enviar_aviso_cambio_password(email):
    msg = EmailMessage()
    msg["Subject"] = "Tu contraseña fue cambiada – Foschi IA"
    msg["From"] = os.getenv("MAIL_USER")
    msg["To"] = email
    msg.set_content(
        "Hola 👋\n\n"
        "Te avisamos que tu contraseña fue cambiada correctamente.\n\n"
        "Si NO fuiste vos:\n"
        "• Recuperá la cuenta de inmediato\n"
        "• Cambiá la contraseña nuevamente\n\n"
        "Foschi IA"
    )

    _enviar_mail(msg)
