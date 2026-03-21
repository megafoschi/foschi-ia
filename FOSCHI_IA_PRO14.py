#!/usr/bin/env python3
# coding: utf-8

import os
import uuid
import json
import io
import re
import time
import threading
import secrets
from datetime import datetime, timedelta, date

import pytz
import requests
import urllib.parse

from flask import (
    Flask,
    request,
    session,
    jsonify,
    redirect,
    render_template_string,
    send_file,
    after_this_request
)

from flask_session import Session
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

try:
    from flask_talisman import Talisman
    TALISMAN_AVAILABLE = True
except ImportError:
    TALISMAN_AVAILABLE = False

from gtts import gTTS

from superusuarios import (
    es_superusuario,
    obtener_superusuario,
    rol_superusuario,
    nivel_superusuario
)

from usuarios import registrar_usuario, autenticar_usuario
from suscripciones import usuario_premium, aviso_vencimiento
from suscripciones import activar_premium

from openai import OpenAI

# --- librerías adicionales para documentos ---
import PyPDF2
from docx import Document as DocxDocument
import docx as docx_reader

from werkzeug.utils import secure_filename

# ---------------- CONFIG ----------------
APP_NAME   = "FOSCHI IA WEB"
CREADOR    = "Gustavo Enrique Foschi"
DATA_DIR   = "data"
STATIC_DIR = "static"
TEMP_DIR   = os.path.join(DATA_DIR, "temp_docs")

os.makedirs(DATA_DIR,   exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(TEMP_DIR,   exist_ok=True)
os.makedirs("temp",     exist_ok=True)

# ---------------- KEYS (solo desde variables de entorno) ----------------
OPENAI_API_KEY  = os.getenv("OPENAI_API_KEY")
GOOGLE_API_KEY  = os.getenv("GOOGLE_API_KEY")
GOOGLE_CSE_ID   = os.getenv("GOOGLE_CSE_ID")
OWM_API_KEY     = os.getenv("OWM_API_KEY")
SECRET_KEY      = os.getenv("SECRET_KEY") or secrets.token_hex(32)
ADMIN_KEY       = os.getenv("ADMIN_KEY", secrets.token_hex(16))   # loguear en arranque
MP_MERCHANT_ID  = os.getenv("MP_MERCHANT_ID")

# ---------------- CLIENTE OPENAI (único, global) ----------------
openai_client = OpenAI(api_key=OPENAI_API_KEY)

# ---------------- APP ----------------
app = Flask(__name__)
app.secret_key = SECRET_KEY

app.config["SESSION_TYPE"]       = "filesystem"
app.config["SESSION_PERMANENT"]  = False
app.config["SESSION_USE_SIGNER"] = True          # firma la cookie de sesión

Session(app)

# ---------------- RATE LIMITER ----------------
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "60 per hour"],
    storage_uri="memory://",
)

# ---------------- SEGURIDAD DE HEADERS ----------------
if TALISMAN_AVAILABLE:
    Talisman(
        app,
        content_security_policy=False,   # ajustar si tenés CSP propio
        force_https=os.getenv("FORCE_HTTPS", "false").lower() == "true",
    )

# Imprimir ADMIN_KEY al arrancar (solo visible en logs del servidor)
print(f"[FOSCHI IA] ADMIN_KEY={ADMIN_KEY}  — guardá este valor en un lugar seguro.")

# ---------------- LOCK GLOBAL PARA MEMORY_CACHE ----------------
_memory_lock = threading.Lock()

# ---------------- UTIL / CACHE / HTTP ----------------
HTTPS      = requests.Session()
URL_REGEX  = re.compile(r'(https?://[^\s]+)', re.UNICODE)

MEMORY_FILE  = os.path.join(DATA_DIR, "memory.json")
MEMORY_CACHE: dict = {}

MAX_DAILY_FREE = 5   # preguntas diarias para usuarios no-premium

# ----------------------------------------------------------------
# MEMORY
# ----------------------------------------------------------------
def load_json(path: str) -> dict:
    """Carga memory.json en caché RAM (thread-safe)."""
    global MEMORY_CACHE
    with _memory_lock:
        if MEMORY_CACHE:
            return MEMORY_CACHE
        if not os.path.exists(path):
            MEMORY_CACHE = {}
            return MEMORY_CACHE
        try:
            with open(path, "r", encoding="utf-8") as f:
                MEMORY_CACHE = json.load(f)
        except Exception:
            MEMORY_CACHE = {}
        return MEMORY_CACHE


def save_json(path: str, data: dict) -> None:
    """Guarda MEMORY_CACHE actualizado en disco (thread-safe)."""
    global MEMORY_CACHE
    with _memory_lock:
        MEMORY_CACHE.update(data)
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(MEMORY_CACHE, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print("Error guardando memory.json:", e)


# ----------------------------------------------------------------
# LÍMITE DIARIO (backend)
# ----------------------------------------------------------------
_daily_lock   = threading.Lock()
_daily_counts: dict = {}   # { usuario: {"fecha": "YYYY-MM-DD", "count": N} }


def puede_preguntar(usuario: str) -> bool:
    """Devuelve True si el usuario puede hacer una pregunta más hoy."""
    if es_superusuario(usuario) or usuario_premium(usuario):
        return True

    hoy = date.today().isoformat()
    with _daily_lock:
        entry = _daily_counts.get(usuario, {})
        if entry.get("fecha") != hoy:
            entry = {"fecha": hoy, "count": 0}
        if entry["count"] >= MAX_DAILY_FREE:
            return False
        entry["count"] += 1
        _daily_counts[usuario] = entry
        return True


# ----------------------------------------------------------------
# HELPERS
# ----------------------------------------------------------------
def fecha_hora_en_es() -> str:
    tz    = pytz.timezone("America/Argentina/Buenos_Aires")
    ahora = datetime.now(tz)
    meses = ["enero","febrero","marzo","abril","mayo","junio",
             "julio","agosto","septiembre","octubre","noviembre","diciembre"]
    dias  = ["lunes","martes","miércoles","jueves","viernes","sábado","domingo"]
    return (f"{dias[ahora.weekday()]}, {ahora.day} de {meses[ahora.month-1]} "
            f"de {ahora.year}, {ahora.hour:02d}:{ahora.minute:02d}")


def hacer_links_clicleables(texto: str) -> str:
    return URL_REGEX.sub(r'<a href="\1" target="_blank" rel="noopener noreferrer" '
                         r'style="color:#ff0000;">\1</a>', texto)


# ----------------------------------------------------------------
# HISTORIAL
# ----------------------------------------------------------------
def guardar_en_historial(usuario: str, entrada: str, respuesta: str) -> None:
    path  = os.path.join(DATA_DIR, f"{usuario}.json")
    datos = []
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                datos = json.load(f)
        except Exception:
            datos = []
    datos.append({
        "fecha":  datetime.now(pytz.timezone("America/Argentina/Buenos_Aires"))
                          .strftime("%d/%m/%Y %H:%M:%S"),
        "usuario": entrada,
        "foschi":  respuesta,
    })
    datos = datos[-200:]
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("Error guardando historial:", e)


def cargar_historial(usuario: str) -> list:
    path = os.path.join(DATA_DIR, f"{usuario}.json")
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


# ----------------------------------------------------------------
# CLIMA
# ----------------------------------------------------------------
def obtener_clima(ciudad=None, lat=None, lon=None) -> str:
    if not OWM_API_KEY:
        return "No está configurada la API de clima (OWM_API_KEY)."
    try:
        if lat and lon:
            url = (f"http://api.openweathermap.org/data/2.5/weather"
                   f"?lat={lat}&lon={lon}&appid={OWM_API_KEY}&units=metric&lang=es")
        else:
            ciudad = ciudad or "Buenos Aires"
            url = (f"http://api.openweathermap.org/data/2.5/weather"
                   f"?q={ciudad}&appid={OWM_API_KEY}&units=metric&lang=es")
        r    = HTTPS.get(url, timeout=3)
        data = r.json()
        if r.status_code != 200:
            return f"No pude obtener el clima: {r.status_code} - {data.get('message','')}"
        desc = data.get("weather", [{}])[0].get("description", "Sin descripción").capitalize()
        temp = data.get("main", {}).get("temp")
        hum  = data.get("main", {}).get("humidity")
        name = data.get("name", ciudad or "la ubicación")
        parts = [f"El clima en {name} es {desc}"]
        if temp is not None:
            parts.append(f"temperatura {round(temp)}°C")
        if hum is not None:
            parts.append(f"humedad {hum}%")
        return ", ".join(parts) + "."
    except Exception:
        return "No pude obtener el clima."


# ----------------------------------------------------------------
# RECORDATORIOS
# ----------------------------------------------------------------
RECORD_FILE = os.path.join(DATA_DIR, "recordatorios.json")
TZ          = pytz.timezone("America/Argentina/Buenos_Aires")
_record_lock = threading.Lock()


def load_recordatorios() -> list:
    with _record_lock:
        if not os.path.exists(RECORD_FILE):
            return []
        try:
            with open(RECORD_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []


def save_recordatorios(lista: list) -> None:
    with _record_lock:
        try:
            with open(RECORD_FILE, "w", encoding="utf-8") as f:
                json.dump(lista, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print("Error guardando recordatorios:", e)


def interpretar_fecha_hora(texto: str):
    ahora = datetime.now(TZ)

    m = re.search(r"en (\d+)\s*minutos?", texto)
    if m:
        return ahora + timedelta(minutes=int(m.group(1)))

    m = re.search(r"en (\d+)\s*horas?", texto)
    if m:
        return ahora + timedelta(hours=int(m.group(1)))

    m = re.search(r"mañana a las (\d{1,2})(?::(\d{2}))?", texto)
    if m:
        hora   = int(m.group(1))
        minuto = int(m.group(2)) if m.group(2) else 0
        return (ahora + timedelta(days=1)).replace(hour=hora, minute=minuto,
                                                   second=0, microsecond=0)

    m = re.search(r"a las (\d{1,2}):(\d{2})", texto)
    if m:
        posible = ahora.replace(hour=int(m.group(1)), minute=int(m.group(2)),
                                second=0, microsecond=0)
        if posible <= ahora:
            posible += timedelta(days=1)
        return posible

    m = re.search(r"el (\d{1,2}) de (\w+) a las (\d{1,2})(?::(\d{2}))?", texto)
    if m:
        dia  = int(m.group(1))
        mes_texto = m.group(2).lower()
        hora = int(m.group(3))
        minuto = int(m.group(4)) if m.group(4) else 0
        meses = {
            "enero":1,"febrero":2,"marzo":3,"abril":4,"mayo":5,"junio":6,
            "julio":7,"agosto":8,"septiembre":9,"octubre":10,"noviembre":11,"diciembre":12
        }
        mes = meses.get(mes_texto)
        if mes:
            año = ahora.year
            try:
                candidato = TZ.localize(datetime(año, mes, dia, hora, minuto))
            except Exception:
                return None
            if candidato <= ahora:
                try:
                    candidato = TZ.localize(datetime(año + 1, mes, dia, hora, minuto))
                except Exception:
                    return None
            return candidato
    return None


def agregar_recordatorio(usuario: str, motivo_texto: str, fecha_hora_dt) -> None:
    if fecha_hora_dt.tzinfo is None:
        fecha_hora_dt = fecha_hora_dt.replace(tzinfo=TZ)
    lista = load_recordatorios()
    lista.append({
        "usuario": usuario,
        "motivo":  motivo_texto.strip(),
        "cuando":  fecha_hora_dt.strftime("%Y-%m-%d %H:%M:%S"),
    })
    save_recordatorios(lista)


def listar_recordatorios(usuario: str) -> list:
    return [r for r in load_recordatorios() if r.get("usuario") == usuario]


def borrar_recordatorios(usuario: str) -> None:
    save_recordatorios([r for r in load_recordatorios() if r.get("usuario") != usuario])


def monitor_recordatorios() -> None:
    """Hilo daemon que dispara recordatorios vencidos."""
    while True:
        try:
            lista   = load_recordatorios()
            ahora   = datetime.now(TZ)
            restantes = []
            for r in lista:
                try:
                    cuando = TZ.localize(datetime.strptime(r["cuando"], "%Y-%m-%d %H:%M:%S"))
                except Exception:
                    try:
                        cuando = datetime.fromisoformat(r["cuando"])
                        if cuando.tzinfo is None:
                            cuando = TZ.localize(cuando)
                    except Exception:
                        continue
                if cuando <= ahora:
                    aviso = f"⏰ Tenés un recordatorio: {r.get('motivo','(sin motivo)')}"
                    try:
                        guardar_en_historial(r.get("usuario", "anon"),
                                             f"[recordatorio] {r.get('motivo','')}",
                                             aviso)
                    except Exception:
                        pass
                else:
                    restantes.append(r)
            save_recordatorios(restantes)
        except Exception as e:
            print("Error en monitor_recordatorios:", e)
        time.sleep(30)


threading.Thread(target=monitor_recordatorios, daemon=True).start()


# ----------------------------------------------------------------
# LIMPIEZA PERIÓDICA DE ARCHIVOS TEMPORALES
# ----------------------------------------------------------------
def limpiar_temp_periodico() -> None:
    """Elimina archivos de TEMP_DIR y temp/ con más de 1 hora de antigüedad."""
    while True:
        time.sleep(1800)   # cada 30 minutos
        limite = time.time() - 3600
        for directorio in [TEMP_DIR, "temp"]:
            try:
                for nombre in os.listdir(directorio):
                    ruta = os.path.join(directorio, nombre)
                    try:
                        if os.path.isfile(ruta) and os.path.getmtime(ruta) < limite:
                            os.remove(ruta)
                    except Exception:
                        pass
            except Exception:
                pass


threading.Thread(target=limpiar_temp_periodico, daemon=True).start()


# ----------------------------------------------------------------
# LEARN FROM MESSAGE
# ----------------------------------------------------------------
def learn_from_message(usuario: str, mensaje: str, respuesta: str) -> None:
    try:
        memory = load_json(MEMORY_FILE)
        if usuario not in memory:
            memory[usuario] = {"temas": {}, "mensajes": [], "ultima_interaccion": None}
        memory[usuario]["mensajes"].append({"usuario": str(mensaje), "foschi": str(respuesta)})
        memory[usuario]["mensajes"] = memory[usuario]["mensajes"][-200:]
        memory[usuario]["ultima_interaccion"] = (
            datetime.now(pytz.timezone("America/Argentina/Buenos_Aires"))
            .strftime("%d/%m/%Y %H:%M:%S")
        )
        for palabra in str(mensaje).lower().split():
            if len(palabra) > 3:
                memory[usuario]["temas"][palabra] = memory[usuario]["temas"].get(palabra, 0) + 1
        save_json(MEMORY_FILE, memory)
    except Exception as e:
        print("Error en learn_from_message:", e)


# ----------------------------------------------------------------
# DICTADO A WORD
# ----------------------------------------------------------------
@app.route("/dictado_word", methods=["POST"])
@limiter.limit("30 per hour")
def dictado_word():
    data  = request.json or {}
    texto = data.get("texto", "").strip()
    if not texto:
        return jsonify({"ok": False, "error": "Texto vacío"})

    nombre = f"dictado_{uuid.uuid4().hex}.docx"
    ruta   = os.path.join(TEMP_DIR, nombre)
    doc    = DocxDocument()
    doc.add_heading("Dictado Foschi IA", 0)
    doc.add_paragraph(texto)
    doc.save(ruta)

    @after_this_request
    def remove_file(response):
        try:
            os.remove(ruta)
        except Exception:
            pass
        return response

    return send_file(ruta, as_attachment=True)


# ----------------------------------------------------------------
# GENERAR RESPUESTA IA
# ----------------------------------------------------------------
def generar_respuesta(mensaje: str, usuario: str,
                      lat=None, lon=None, tz=None, max_hist: int = 5) -> dict:

    # Bloqueo por no premium (mensajes largos)
    if not usuario_premium(usuario) and not es_superusuario(usuario):
        if len(mensaje) > 200:
            return {
                "texto": ("🔒 Esta función es solo para usuarios Premium.\n\n"
                          "💎 Activá Foschi IA Premium desde el botón superior para seguir."),
                "imagenes": [],
                "borrar_historial": False,
            }

    if not isinstance(mensaje, str):
        mensaje = str(mensaje)

    mensaje_lower = mensaje.lower().strip()

    # --- RECORDATORIOS ---
    try:
        if mensaje_lower in ["mis recordatorios", "lista de recordatorios", "ver recordatorios"]:
            recs = listar_recordatorios(usuario)
            if not recs:
                return {"texto": "📭 No tenés recordatorios pendientes.", "imagenes": [], "borrar_historial": False}
            texto = "📌 Tus recordatorios:\n" + "\n".join(
                [f"- {r['motivo']} → {r['cuando']}" for r in recs])
            return {"texto": texto, "imagenes": [], "borrar_historial": False}

        if "borrar recordatorios" in mensaje_lower or "eliminar recordatorios" in mensaje_lower:
            borrar_recordatorios(usuario)
            return {"texto": "🗑️ Listo, eliminé todos tus recordatorios.", "imagenes": [], "borrar_historial": False}

        if mensaje_lower.startswith(("recordame", "haceme acordar", "avisame", "recordá")):
            fecha_hora = interpretar_fecha_hora(mensaje_lower)
            if fecha_hora is None:
                return {
                    "texto": ("⏰ Decime cuándo: ejemplo 'mañana a las 9', "
                              "'en 15 minutos' o 'el 5 de diciembre a las 18'."),
                    "imagenes": [], "borrar_historial": False,
                }
            motivo = mensaje
            for p in ["recordame", "haceme acordar", "avisame", "recordá"]:
                motivo = re.sub(p, "", motivo, flags=re.IGNORECASE).strip()
            if not motivo:
                motivo = "Recordatorio"
            agregar_recordatorio(usuario, motivo, fecha_hora)
            return {
                "texto": f"✅ Listo, te lo recuerdo el {fecha_hora.strftime('%d/%m %H:%M')}.",
                "imagenes": [], "borrar_historial": False,
            }
    except Exception as e:
        print("Error en manejo de recordatorios:", e)

    # BORRAR HISTORIAL
    if any(p in mensaje_lower for p in ["borrar historial", "limpiar historial", "reset historial"]):
        path = os.path.join(DATA_DIR, f"{usuario}.json")
        if os.path.exists(path):
            os.remove(path)
        memory = load_json(MEMORY_FILE)
        if usuario in memory:
            memory[usuario]["mensajes"] = []
            save_json(MEMORY_FILE, memory)
        return {"texto": "✅ Historial borrado correctamente.", "imagenes": [], "borrar_historial": True}

    # FECHA / HORA
    if any(p in mensaje_lower for p in ["qué día", "que día", "qué fecha", "que fecha",
                                         "qué hora", "que hora", "día es hoy", "fecha hoy"]):
        texto = fecha_hora_en_es()
        learn_from_message(usuario, mensaje, texto)
        return {"texto": texto, "imagenes": [], "borrar_historial": False}

    # CLIMA
    if "clima" in mensaje_lower:
        ciudad_match = re.search(r"clima en ([a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+)", mensaje_lower)
        ciudad = ciudad_match.group(1).strip() if ciudad_match else None
        texto  = obtener_clima(ciudad=ciudad, lat=lat, lon=lon)
        learn_from_message(usuario, mensaje, texto)
        return {"texto": texto, "imagenes": [], "borrar_historial": False}

    # QUIÉN CREÓ
    if any(p in mensaje_lower for p in [
        "quién te creó", "quien te creo", "quién te hizo", "quien te hizo",
        "quién te programó", "quien te programo", "quién te inventó", "quien te invento",
        "quién te desarrolló", "quien te desarrollo", "quién te construyó", "quien te construyo"
    ]):
        texto = "Fui creada por Gustavo Enrique Foschi, el mejor 😎."
        learn_from_message(usuario, mensaje, texto)
        return {"texto": texto, "imagenes": [], "borrar_historial": False}

    # NOTICIAS / INFORMACIÓN ACTUALIZADA
    if any(word in mensaje_lower for word in [
        "presidente", "actualidad", "noticias", "quién es",
        "últimas noticias", "evento actual"
    ]):
        return _responder_con_busqueda(mensaje, usuario, "noticias")

    # DEPORTES
    if any(p in mensaje_lower for p in [
        "resultado", "marcador", "ganó", "empató", "perdió",
        "partido", "deporte", "fútbol", "futbol", "nba", "tenis", "f1",
        "formula 1", "motogp"
    ]):
        return _responder_con_busqueda(mensaje, usuario, "deportes")

    # RESPUESTA GENERAL VÍA OPENAI
    try:
        memoria   = load_json(MEMORY_FILE)
        historial = memoria.get(usuario, {}).get("mensajes", [])[-max_hist:]
        resumen   = " ".join([m["usuario"] + ": " + m["foschi"] for m in historial[-3:]]) if historial else ""

        prompt_messages = [
            {
                "role": "system",
                "content": (
                    "Sos FOSCHI IA, una inteligencia amable, directa y con humor ligero. "
                    "Tus respuestas deben ser claras, ordenadas y sonar naturales en español argentino. "
                    "Si el usuario pide información o ayuda técnica, explicá paso a paso y sin mezclar temas. "
                    f"Resumen de últimas interacciones: {resumen if resumen else 'ninguna.'}"
                ),
            },
            {"role": "user", "content": mensaje},
        ]

        resp  = openai_client.chat.completions.create(
            model="gpt-4-turbo",
            messages=prompt_messages,
            temperature=0.7,
            max_tokens=700,
        )
        texto = resp.choices[0].message.content.strip()
        texto = hacer_links_clicleables(texto)

    except Exception as e:
        texto = f"No pude generar respuesta: {e}"

    aviso = aviso_vencimiento(usuario)
    if aviso:
        texto += "\n\n" + aviso

    learn_from_message(usuario, mensaje, texto)
    return {"texto": texto, "imagenes": [], "borrar_historial": False}


def _responder_con_busqueda(mensaje: str, usuario: str, tipo: str) -> dict:
    """Consulta Google CSE y resume con OpenAI."""
    resultados = []
    if GOOGLE_API_KEY and GOOGLE_CSE_ID:
        try:
            q = mensaje if tipo == "noticias" else mensaje + " resultados deportivos actualizados"
            url = (
                f"https://www.googleapis.com/customsearch/v1"
                f"?key={GOOGLE_API_KEY}&cx={GOOGLE_CSE_ID}"
                f"&q={urllib.parse.quote(q)}&sort=date"
            )
            r    = HTTPS.get(url, timeout=5)
            data = r.json()
            for item in data.get("items", [])[:5]:
                snippet = item.get("snippet", "").strip()
                if snippet and snippet not in resultados:
                    resultados.append(snippet)
        except Exception as e:
            print(f"Error buscando ({tipo}):", e)

    if resultados:
        texto_bruto = " ".join(resultados)
        if tipo == "noticias":
            prompt = (
                f"Tengo estos fragmentos de texto recientes: {texto_bruto}\n\n"
                f"Respondé a la pregunta: '{mensaje}'. "
                f"Usá un tono natural y directo en español argentino, sin frases como "
                f"'según los textos'. Contestá con una sola oración clara y actualizada."
            )
        else:
            prompt = (
                f"Tengo estos fragmentos recientes sobre deportes: {texto_bruto}\n\n"
                f"Respondé brevemente la consulta '{mensaje}' con los resultados deportivos actuales. "
                f"Usá un tono natural, tipo boletín deportivo argentino, sin frases como 'según los textos'. "
                f"Respondé en una sola oración clara."
            )
        try:
            resp  = openai_client.chat.completions.create(
                model="gpt-4-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5,
                max_tokens=150,
            )
            texto = resp.choices[0].message.content.strip()
        except Exception as e:
            texto = "No pude generar la respuesta."
    else:
        texto = "No pude obtener información actualizada en este momento."

    learn_from_message(usuario, mensaje, texto)
    return {"texto": texto, "imagenes": [], "borrar_historial": False}


# ----------------------------------------------------------------
# HTML TEMPLATE
# ----------------------------------------------------------------
HTML_TEMPLATE = """
<!doctype html>
<html>
<head>
<title>{{APP_NAME}}</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body{
 font-family:'Segoe UI',Tahoma,Geneva,Verdana,sans-serif;
 background:#000814;color:#00eaff;margin:0;padding:0;
 display:flex;flex-direction:column;height:100vh;overflow:hidden;
 text-shadow:0 0 6px #00eaff;
}
#header{display:flex;align-items:center;justify-content:space-between;
 padding:8px 16px;background:linear-gradient(#000814,#00111a);flex-shrink:0;
 position:sticky;top:0;z-index:10;box-shadow:0 0 12px #00eaff66;}
#leftButtons{display:flex;align-items:center;gap:12px;}
#rightButtons{display:flex;align-items:center;gap:8px;}
.separator{border-left:1px solid #00eaff55;height:32px;margin:0 8px;}
#header button{font-size:14px;padding:6px 10px;border-radius:6px;
 background:#001f2e;color:#00eaff;border:1px solid #006688;cursor:pointer;
 text-shadow:0 0 4px #00eaff;box-shadow:0 0 8px #0099bb;transition:0.3s;}
body.day{background:#ffffff;color:#000000;text-shadow:none;}
body.day #header{background:#ffffff;box-shadow:0 2px 8px rgba(0,0,0,0.1);}
body.day #chat{background:#f5f5f5;border-top:1px solid #ccc;border-bottom:1px solid #ccc;box-shadow:none;}
body.day #inputBar{background:#ffffff;border-top:1px solid #ccc;}
body.day button{background:#ffffff!important;color:#000000!important;border:1px solid #000000!important;box-shadow:none!important;text-shadow:none!important;}
body.day input{background:#ffffff!important;color:#000000!important;border:1px solid #000000!important;box-shadow:none!important;}
body.day #premiumBtn{animation:none;font-weight:600;}
#header button:hover{background:#003547;box-shadow:0 0 14px #00eaff;}
#premiumBtn{animation:neonGlow 1.5s ease-in-out infinite alternate;}
@keyframes neonGlow{
 0%{box-shadow:0 0 8px #00eaff,0 0 12px #00eaff,0 0 16px #00eaff;color:#00eaff;}
 50%{box-shadow:0 0 12px #00ffff,0 0 20px #00ffff,0 0 28px #00ffff;color:#00ffff;}
 100%{box-shadow:0 0 8px #00eaff,0 0 12px #00eaff,0 0 16px #00eaff;color:#00eaff;}
}
#logo{width:120px;cursor:pointer;transition:transform 0.5s,filter 0.5s;filter:drop-shadow(0 0 12px #00eaff);}
#logo:hover{transform:scale(1.2) rotate(6deg);filter:drop-shadow(0 0 20px #00eaff);}
#chat{flex:1;overflow-y:auto;padding:10px;background:linear-gradient(#00111a,#000814);
 border-top:2px solid #00eaff44;border-bottom:2px solid #00eaff44;
 box-shadow:inset 0 0 15px #00eaff55;padding-bottom:120px;}
.message{margin:5px 0;padding:8px 12px;border-radius:15px;max-width:80%;
 word-wrap:break-word;opacity:0;transition:opacity 0.5s,box-shadow 0.5s,background 0.5s;font-size:15px;}
.message.show{opacity:1;}
.user{background:rgba(51,0,255,0.3);color:#b4b7ff;margin-left:auto;text-align:right;
 border:1px solid #4455ff;box-shadow:0 0 8px #3344ff;}
.ai{background:rgba(0,255,255,0.2);color:#00eaff;margin-right:auto;text-align:left;
 border:1px solid #00eaff;box-shadow:0 0 10px #00eaff;}
a{color:#00eaff;text-decoration:underline;}
img{max-width:300px;border-radius:10px;margin:5px 0;box-shadow:0 0 10px #00eaff88;border:1px solid #00eaff55;}
#inputBar{display:flex;align-items:center;gap:6px;padding:8px;background:#001d29;
 border-top:2px solid #00eaff44;flex-shrink:0;position:fixed;bottom:0;left:0;
 width:100%;box-sizing:border-box;z-index:20;}
#inputBar input[type=text]{flex:1;padding:10px;font-size:16px;background:#00121d;
 color:#00eaff;border:1px solid #003344;box-shadow:0 0 6px #00eaff55 inset;border-radius:5px;}
#inputBar button{padding:10px;font-size:16px;border:none;border-radius:5px;
 background:#001f2e;color:#00eaff;cursor:pointer;border:1px solid #006688;
 text-shadow:0 0 4px #00eaff;box-shadow:0 0 8px #0099bb;transition:0.25s;}
#inputBar button:hover{background:#003547;box-shadow:0 0 14px #00eaff;}
#vozBtn,#borrarBtn,#premiumBtn{font-size:14px;padding:6px 10px;}
#clipBtn{width:40px;height:40px;display:flex;align-items:center;justify-content:center;
 font-size:20px;cursor:pointer;border-radius:6px;background:#001f2e;color:#00eaff;
 border:1px solid #006688;box-shadow:0 0 10px #0099bb;transition:0.25s;user-select:none;}
#clipBtn:hover{background:#003547;box-shadow:0 0 16px #00eaff;transform:scale(1.08);}
body.day #clipBtn{background:#ffffff;color:#000000;border:1px solid #000000;box-shadow:none;}
body.day #clipBtn:hover{background:#f0f0f0;}
#adjuntos_menu{position:absolute;left:0;bottom:50px;display:none;
 background:#001f2e;border:1px solid #003547;padding:8px;border-radius:8px;
 box-shadow:0 6px 16px rgba(0,0,0,0.6);z-index:999;max-width:90vw;}
#adjuntos_menu button{display:block;width:160px;margin:6px;text-align:left;}
.hidden_file_input{display:none;}
#premiumMenu button{display:block;width:120px;margin:4px 0;text-align:left;}
@media(max-width:600px){
 #inputBar input[type=text]{font-size:18px;padding:12px;}
 #inputBar button{font-size:16px;padding:10px;}
 #logo{width:140px;}
}
body.day .user{background:#e9e9e9;color:#000000;border:1px solid #000000;box-shadow:none;}
body.day .ai{background:#f5f5f5;color:#000000;border:1px solid #000000;box-shadow:none;}
body.day .ai a,body.day .user a{color:#000000;}
.form-premium{width:100%;max-width:320px;margin:0 auto;display:flex;flex-direction:column;align-items:center;gap:10px;}
.form-premium input{width:100%;padding:10px;border-radius:6px;border:1px solid #006688;background:#00121d;color:#00eaff;box-shadow:0 0 6px #00eaff55 inset;}
.form-premium button{width:100%;padding:10px;border-radius:6px;border:1px solid #006688;background:#001f2e;color:#00eaff;cursor:pointer;box-shadow:0 0 8px #0099bb;}
.form-premium button:hover{background:#003547;box-shadow:0 0 14px #00eaff;}
.wave{width:6px;height:20px;background:#00eaff;animation:wave 1s infinite ease-in-out;border-radius:4px;}
.wave:nth-child(2){animation-delay:0.1s;}
.wave:nth-child(3){animation-delay:0.2s;}
.wave:nth-child(4){animation-delay:0.3s;}
.wave:nth-child(5){animation-delay:0.4s;}
@keyframes wave{0%,100%{height:10px;}50%{height:40px;}}
</style>
</head>

<body>
<div id="header">
  <div id="leftButtons">
    <img src="/static/logo.png" id="logo" onclick="logoClick()" alt="logo">
    <div id="premiumContainer" style="position:relative;margin-left:12px;">
      <button id="dayNightBtn" onclick="toggleDayNight()">🌙</button>
      <button id="premiumBtn" onclick="togglePremiumMenu()">
        {% if premium %}💎 Premium activo{% else %}💎 Pasar a Premium{% endif %}
      </button>
      {% if not premium %}
      <div id="premiumMenu"
           style="display:none;position:absolute;top:36px;left:0;background:#001f2e;
                  border:1px solid #003547;border-radius:6px;padding:6px;
                  box-shadow:0 6px 16px rgba(0,0,0,0.6);z-index:100;">
        <button onclick="irPremium('mensual')">💎 Pago Mensual</button>
        <button onclick="irPremium('anual')">💎 Pago Anual</button>
      </div>
      {% endif %}
    </div>
  </div>
  <div id="rightButtons">
    <div class="separator"></div>
    <button onclick="detenerVoz()">⏹️ Detener voz</button>
    <button id="vozBtn" onclick="toggleVoz()">🔊 Voz activada</button>
    <button id="borrarBtn" onclick="borrarPantalla()">🧹 Borrar pantalla</button>
    <button onclick="verHistorial()">🗂️ Historial</button>
  </div>
</div>

<div id="chat" role="log" aria-live="polite"></div>

<div id="voiceWave" style="position:fixed;bottom:110px;left:50%;transform:translateX(-50%);
     display:none;gap:4px;z-index:999;">
  <div class="wave"></div><div class="wave"></div><div class="wave"></div>
  <div class="wave"></div><div class="wave"></div>
</div>

<div id="dictadoEstado" style="position:fixed;bottom:70px;right:10px;background:#ff0000;
     color:white;padding:6px 10px;border-radius:6px;display:none;font-weight:bold;z-index:999;">
  🎤 Dictado activo
</div>

<div id="inputBar">
  <div style="position:relative;">
    <div id="clipBtn" title="Adjuntar" onclick="toggleAdjuntosMenu()">📎</div>
    <div id="adjuntos_menu" aria-hidden="true">
      <button onclick="toggleModoConversacion()">🧠 Modo conversación</button>
      <button onclick="checkPremium('audio')">🎵 Audio (mp3/wav) a Texto</button>
      <button onclick="checkPremium('doc')">📄 Resumir PDF / WORD</button>
      <button onclick="toggleDictado()">🎤 Dictado por voz</button>
    </div>
  </div>
  <input id="audioInput" class="hidden_file_input" type="file" accept=".mp3,audio/*,.wav" />
  <input id="archivo_pdf_word" class="hidden_file_input" type="file" accept=".pdf,.docx" />
  <input type="text" id="mensaje" placeholder="Escribí tu mensaje o hablá" autocomplete="off" />
  <button onclick="checkDailyLimit()">Enviar</button>
  <button onclick="hablar()">🎤 Hablar</button>
</div>

<script>
// ── constantes ──────────────────────────────────────────────────
const MAX_NO_PREMIUM = {{ max_daily }};
const hoy            = new Date().toISOString().slice(0,10);
let isPremium        = {{ 'true' if premium else 'false' }};
let isSuper          = {{ 'true' if is_super else 'false' }};
let rolUsuario       = "{{ rol or '' }}";
let nivelUsuario     = {{ nivel or 0 }};
let usuario_id       = "{{ usuario_id }}";

// ── estado ──────────────────────────────────────────────────────
let vozActiva           = true;
let audioActual         = null;
let mensajeActual       = null;
let modoConversacion    = false;
let recognitionConv     = null;
let silencioTimer       = null;
let activadorActivo     = true;
let recognitionWake     = null;
let esperandoComando    = false;
let dictadoActivo       = false;
let dictadoPausado      = false;
let reconocimiento      = null;
let textoDictado        = "";
let ultimoTexto         = "";
let ultimoTiempo        = 0;
let ultimoTiempoTexto   = Date.now();
const UMBRAL_PARRAFO    = 2000;

// ── helpers ─────────────────────────────────────────────────────
function logoClick(){ alert("FOSCHI NUNCA MUERE, TRASCIENDE..."); }

function toggleVoz(estado=null){
  vozActiva = estado !== null ? estado : !vozActiva;
  document.getElementById("vozBtn").textContent = vozActiva ? "🔊 Voz activada" : "🔇 Silenciada";
}

function detenerVoz(){
  if(audioActual){
    audioActual.pause();
    audioActual.currentTime = 0;
    audioActual.src = "";
    audioActual.load();
    audioActual = null;
    if(mensajeActual) mensajeActual.classList.remove("playing");
    mensajeActual = null;
  }
}

function agregar(msg, cls, imagenes=[]){
  const c   = document.getElementById("chat");
  const div = document.createElement("div");
  div.className = "message " + cls;
  div.innerHTML = msg;
  c.appendChild(div);
  setTimeout(()=> div.classList.add("show"), 50);
  imagenes.forEach(url=>{
    const img = document.createElement("img"); img.src = url; div.appendChild(img);
  });
  c.scroll({ top: c.scrollHeight, behavior: "smooth" });
  if(cls === "ai") hablarTexto(msg, div);
  return div;
}

// ── límite diario ────────────────────────────────────────────────
function checkDailyLimit(){
  // El límite real se valida en el backend; esto solo evita clicks extra en el frontend
  enviar();
}

// ── enviar mensaje ───────────────────────────────────────────────
function enviar(){
  const input = document.getElementById("mensaje");
  const msg   = input.value.trim();
  if(!msg) return;
  agregar(msg, "user");
  input.value = "";
  fetch("/preguntar",{
    method:"POST",
    headers:{"Content-Type":"application/json"},
    body: JSON.stringify({ mensaje: msg, usuario_id })
  })
  .then(r=> r.json())
  .then(data=>{
    if(data.limite){
      agregar(data.texto, "ai");
      return;
    }
    agregar(data.texto, "ai", data.imagenes);
    if(data.borrar_historial) document.getElementById("chat").innerHTML = "";
  })
  .catch(()=> agregar("Error al comunicarse con el servidor.", "ai"));
}

document.getElementById("mensaje")
  .addEventListener("keydown", e=>{ if(e.key === "Enter"){ e.preventDefault(); enviar(); } });

// ── texto a voz ──────────────────────────────────────────────────
function hablarTexto(texto, div=null){
  if(!vozActiva) return;
  if(modoConversacion && recognitionConv) recognitionConv.stop();
  detenerVoz();
  if(mensajeActual) mensajeActual.classList.remove("playing");
  if(div) div.classList.add("playing");
  mensajeActual = div;
  audioActual   = new Audio("/tts?texto=" + encodeURIComponent(texto));
  audioActual.playbackRate = 1.25;
  audioActual.onended = ()=>{
    if(mensajeActual) mensajeActual.classList.remove("playing");
    mensajeActual = null;
    if(modoConversacion && recognitionConv) recognitionConv.start();
  };
  audioActual.play();
}

// ── modo conversación ────────────────────────────────────────────
function toggleModoConversacion(){
  if(!isPremium && !isSuper){ alert("🔒 El modo conversación es Premium"); return; }
  modoConversacion ? detenerConversacion() : iniciarConversacion();
}

function iniciarConversacion(){
  if(!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)){
    alert("Tu navegador no soporta conversación por voz"); return;
  }
  document.getElementById("voiceWave").style.display = "flex";
  const Rec = window.SpeechRecognition || window.webkitSpeechRecognition;
  recognitionConv = new Rec();
  recognitionConv.lang            = "es-AR";
  recognitionConv.continuous      = true;
  recognitionConv.interimResults  = false;
  modoConversacion = true;

  recognitionConv.onresult = function(event){
    const texto = event.results[event.results.length-1][0].transcript;
    if(texto.trim().length < 3) return;
    if(audioActual){ audioActual.pause(); audioActual.currentTime = 0; }
    document.getElementById("mensaje").value = texto;
    enviar();
    clearTimeout(silencioTimer);
    silencioTimer = setTimeout(()=> console.log("Silencio detectado"), 2000);
  };

  recognitionConv.onend = function(){
    if(modoConversacion && !audioActual) recognitionConv.start();
  };

  recognitionConv.start();
  agregar("🧠 Modo conversación activado", "ai");
}

function detenerConversacion(){
  modoConversacion = false;
  if(recognitionConv){ recognitionConv.stop(); recognitionConv = null; }
  document.getElementById("voiceWave").style.display = "none";
  agregar("🛑 Modo conversación desactivado", "ai");
}

// ── premium ──────────────────────────────────────────────────────
function togglePremiumMenu(){
  if(isPremium) return;
  const menu = document.getElementById("premiumMenu");
  if(!menu) return;
  menu.style.display = (menu.style.display === "block") ? "none" : "block";
  if(menu.style.display === "block"){
    setTimeout(()=> window.addEventListener("click", closePremiumMenuOnClickOutside), 50);
  }
}

function closePremiumMenuOnClickOutside(e){
  const menu = document.getElementById("premiumMenu");
  const btn  = document.getElementById("premiumBtn");
  if(menu && !menu.contains(e.target) && !btn.contains(e.target)){
    menu.style.display = "none";
    window.removeEventListener("click", closePremiumMenuOnClickOutside);
  }
}

function irPremium(tipo){
  fetch(`/premium?tipo=${tipo}`)
    .then(r=>{ if(r.status === 401){ openAuth(); return null; } return r.json(); })
    .then(data=>{ if(data && data.init_point) window.location.href = data.init_point; })
    .catch(err=> console.error(err));
}

function checkPremium(tipo){
  if(!isPremium){ alert("⚠️ Esta función requiere Premium."); return; }
  if(tipo === "audio") document.getElementById("audioInput").click();
  if(tipo === "doc")   document.getElementById("archivo_pdf_word").click();
}

// ── menú adjuntos ─────────────────────────────────────────────────
function toggleAdjuntosMenu(){
  const m = document.getElementById("adjuntos_menu");
  m.style.display = m.style.display === "block" ? "none" : "block";
  if(m.style.display === "block"){
    setTimeout(()=> window.addEventListener("click", closeMenuOnClickOutside), 50);
  }
}

function closeMenuOnClickOutside(e){
  const menu = document.getElementById("adjuntos_menu");
  const clip = document.getElementById("clipBtn");
  if(!menu.contains(e.target) && !clip.contains(e.target)){
    menu.style.display = "none";
    window.removeEventListener("click", closeMenuOnClickOutside);
  }
}

// ── historial ─────────────────────────────────────────────────────
function verHistorial(){
  fetch("/historial/" + usuario_id)
    .then(r=> r.json())
    .then(data=>{
      document.getElementById("chat").innerHTML = "";
      if(!data.length){ agregar("No hay historial todavía.", "ai"); return; }
      data.slice(-20).forEach(e=>{
        agregar(`<small>${e.fecha}</small><br>${e.usuario}`, "user");
        agregar(`<small>${e.fecha}</small><br>${e.foschi}`, "ai");
      });
    });
}

function borrarPantalla(){ detenerVoz(); document.getElementById("chat").innerHTML = ""; }

// ── auth modal ────────────────────────────────────────────────────
function openAuth(){ document.getElementById("authModal").style.display = "block"; }
function closeAuth(){ document.getElementById("authModal").style.display = "none"; }

async function login(){
  const r = await fetch("/auth/login",{
    method:"POST", headers:{"Content-Type":"application/json"},
    body: JSON.stringify({ email: authEmail.value, password: authPassword.value })
  });
  const j = await r.json();
  if(j.ok) location.reload(); else authMsg.innerText = j.msg;
}

async function register(){
  const r = await fetch("/auth/register",{
    method:"POST", headers:{"Content-Type":"application/json"},
    body: JSON.stringify({ email: authEmail.value, password: authPassword.value })
  });
  const j = await r.json();
  if(j.ok) location.reload(); else authMsg.innerText = j.msg;
}

// ── hablar (voz a texto, comando simple) ──────────────────────────
function hablar(){
  if(!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)){
    alert("Tu navegador no soporta reconocimiento de voz."); return;
  }
  const Rec = window.SpeechRecognition || window.webkitSpeechRecognition;
  const rec = new Rec();
  rec.lang            = "es-AR";
  rec.continuous      = false;
  rec.interimResults  = false;
  rec.onresult = function(event){
    const txt = event.results[0][0].transcript.toLowerCase();
    if(txt.includes("activar dictado")){ iniciarDictado(); return; }
    if(txt.includes("desactivar dictado")){ detenerDictado(); return; }
    document.getElementById("mensaje").value = txt;
    enviar();
  };
  rec.onerror = e=> console.log("Error voz:", e.error);
  rec.start();
}

// ── wake word ─────────────────────────────────────────────────────
function iniciarActivador(){
  if(!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)){
    console.log("Wake word no soportado"); return;
  }
  const Rec = window.SpeechRecognition || window.webkitSpeechRecognition;
  recognitionWake = new Rec();
  recognitionWake.lang           = "es-AR";
  recognitionWake.continuous     = true;
  recognitionWake.interimResults = false;
  recognitionWake.onresult = function(event){
    const texto = event.results[event.results.length-1][0].transcript.toLowerCase().trim();
    if(texto.includes("foschi") && !esperandoComando){
      esperandoComando = true;
      agregar("👂 Te escucho...", "ai");
      new Audio("/static/beep.mp3").play().catch(()=>{});
      escucharComando();
    }
  };
  recognitionWake.onend = function(){ if(activadorActivo) recognitionWake.start(); };
  recognitionWake.start();
}

function escucharComando(){
  const Rec = window.SpeechRecognition || window.webkitSpeechRecognition;
  const rec = new Rec();
  rec.lang           = "es-AR";
  rec.continuous     = false;
  rec.interimResults = false;
  rec.onresult = function(event){
    const comando = event.results[0][0].transcript;
    document.getElementById("mensaje").value = comando;
    agregar(comando, "user");
    enviar();
    esperandoComando = false;
  };
  rec.onerror = ()=>{ esperandoComando = false; };
  rec.start();
}

// ── recordatorios polling ─────────────────────────────────────────
function chequearRecordatorios(){
  fetch("/avisos",{
    method:"POST", headers:{"Content-Type":"application/json"},
    body: JSON.stringify({ usuario_id })
  })
  .then(r=> r.json())
  .then(data=>{
    if(Array.isArray(data) && data.length > 0)
      data.forEach(r=> agregar(`⏰ Tenés un recordatorio: ${r.motivo || "(sin motivo)"}`, "ai"));
  })
  .catch(e=> console.error(e));
}
setInterval(chequearRecordatorios, 10000);

// ── modo day / night ──────────────────────────────────────────────
function toggleDayNight(){
  document.body.classList.toggle("day");
  document.getElementById("dayNightBtn").textContent =
    document.body.classList.contains("day") ? "☀️" : "🌙";
}

// ── dictado por voz ───────────────────────────────────────────────
function capitalizarTexto(t){
  return t.toLowerCase().replace(/(^\s*\w|[.!?\n]\s*\w)/g, c=> c.toUpperCase());
}

function actualizarEstadoDictado(txt, color){
  const el = document.getElementById("dictadoEstado");
  el.innerText = txt; el.style.background = color;
}

function toggleDictado(){
  if(!isPremium && !isSuper){ alert("🔒 Esta función es solo Premium"); return; }
  if(!dictadoActivo){ iniciarDictado(); return; }
  if(dictadoActivo && !dictadoPausado){ pausarDictado(); return; }
  if(dictadoActivo && dictadoPausado){ continuarDictado(); return; }
}

function iniciarDictado(){
  if(!('webkitSpeechRecognition' in window)){
    alert("Tu navegador no soporta dictado por voz"); return;
  }
  reconocimiento = new webkitSpeechRecognition();
  reconocimiento.lang            = "es-AR";
  reconocimiento.continuous      = true;
  reconocimiento.interimResults  = true;
  textoDictado   = "";
  dictadoActivo  = true;
  dictadoPausado = false;
  document.getElementById("dictadoEstado").style.display = "block";
  actualizarEstadoDictado("🎤 Escuchando...", "green");

  reconocimiento.onresult = function(event){
    let parcial = "";
    for(let i = event.resultIndex; i < event.results.length; i++){
      const trans = event.results[i][0].transcript;
      const txt   = trans.toLowerCase();
      if(txt.includes("pausar dictado")){ pausarDictado(); return; }
      if(txt.includes("continuar dictado")){ continuarDictado(); return; }
      if(txt.includes("finalizar dictado")){ finalizarDictado(); return; }
      if(txt.includes("borrar texto")){
        textoDictado = ""; ultimoTexto = "";
        document.getElementById("mensaje").value = ""; return;
      }
      if(txt.includes("enviar mensaje")){ finalizarDictado(); enviar(); return; }

      let limpio = trans
        .replace(/nuevo párrafo/gi, "\n\n")
        .replace(/punto y aparte/gi, "\n\n")
        .replace(/punto/gi, ". ")
        .replace(/coma/gi, ", ")
        .replace(/dos puntos/gi, ": ")
        .replace(/punto y coma/gi, "; ")
        .replace(/signo de pregunta/gi, "? ")
        .replace(/signo de exclamación/gi, "! ")
        .replace(/pausar dictado|continuar dictado|finalizar dictado/gi, "")
        .replace(/\s+([.,;:!?])/g, "$1")
        .replace(/\s+/g, " ")
        .trim();

      const ahora = Date.now();
      if(ahora - ultimoTiempoTexto > UMBRAL_PARRAFO) textoDictado += "\n\n";
      ultimoTiempoTexto = ahora;
      if(limpio === ultimoTexto && ahora - ultimoTiempo < 2000) return;
      ultimoTexto = limpio;
      ultimoTiempo = ahora;
      if(event.results[i].isFinal) textoDictado += limpio + " ";
      else parcial += limpio;
    }
    document.getElementById("mensaje").value = capitalizarTexto(textoDictado + parcial);
  };

  // ✅ CORREGIDO: onend fuera de onresult
  reconocimiento.onend = function(){
    if(dictadoActivo && !dictadoPausado) reconocimiento.start();
  };

  reconocimiento.start();
}

function pausarDictado(){
  if(reconocimiento) reconocimiento.stop();
  dictadoPausado = true;
  actualizarEstadoDictado("⏸️ Dictado pausado", "orange");
}

function continuarDictado(){
  if(!dictadoActivo) return;
  reconocimiento.start();
  dictadoPausado = false;
  actualizarEstadoDictado("🎤 Escuchando...", "green");
}

function finalizarDictado(){
  dictadoActivo  = false;
  dictadoPausado = false;
  if(reconocimiento){ reconocimiento.stop(); reconocimiento = null; }
  actualizarEstadoDictado("🛑 Finalizado", "red");
  setTimeout(()=> document.getElementById("dictadoEstado").style.display = "none", 1000);
  if(textoDictado.trim().length > 0) descargarWordDictado(textoDictado);
}

function detenerDictado(){ finalizarDictado(); }

function descargarWordDictado(texto){
  fetch("/dictado_word",{
    method:"POST", headers:{"Content-Type":"application/json"},
    body: JSON.stringify({ texto })
  })
  .then(r=> r.blob())
  .then(blob=>{
    const url = window.URL.createObjectURL(blob);
    const a   = document.createElement("a");
    a.href = url; a.download = "dictado_foschi.docx"; a.click();
  });
}

// ── saludo inicial ────────────────────────────────────────────────
window.onload = function(){
  agregar("👋 ¡Hola! Bienvenido a Foschi IA", "ai");
  const saludoAudio = new Audio("/tts?texto=" + encodeURIComponent("¡Hola! Bienvenido a Foschi IA"));
  saludoAudio.playbackRate = 1.25;
  saludoAudio.play();
  iniciarActivador();
};
</script>

<!-- AUTH MODAL -->
<div id="authModal" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,.85);z-index:9999;">
  <div style="max-width:360px;margin:10% auto;background:#001d3d;padding:20px;border-radius:12px;color:#00eaff;">
    <h3>Ingresar</h3>
    <div class="form-premium">
      <input id="authEmail" type="email" placeholder="Email" autocomplete="email">
      <input id="authPassword" type="password" placeholder="Contraseña" autocomplete="current-password">
      <button onclick="login()">Ingresar</button>
      <button onclick="register()">Crear cuenta</button>
    </div>
    <p id="authMsg" style="margin-top:10px;"></p>
    <button onclick="closeAuth()" style="margin-top:10px;">Cerrar</button>
  </div>
</div>

</body>
</html>
"""


# ================================================================
# RUTAS
# ================================================================
import mercadopago
sdk = mercadopago.SDK(os.getenv("MP_ACCESS_TOKEN"))


# ── auth ────────────────────────────────────────────────────────
@app.route("/auth/register", methods=["POST"])
@limiter.limit("10 per hour")
def register():
    data     = request.get_json() or {}
    email    = data.get("email", "").lower().strip()
    password = data.get("password", "")
    if not email or not password:
        return jsonify({"ok": False, "msg": "Email y contraseña requeridos"})
    ok, msg = registrar_usuario(email, password)
    if not ok:
        return jsonify({"ok": False, "msg": msg})
    session["user_email"] = email
    return jsonify({"ok": True})


@app.route("/auth/login", methods=["POST"])
@limiter.limit("20 per hour")
def login():
    data     = request.get_json() or {}
    email    = data.get("email", "").lower().strip()
    password = data.get("password", "")
    if not autenticar_usuario(email, password):
        return jsonify({"ok": False, "msg": "Credenciales incorrectas"})
    session["user_email"] = email
    return jsonify({"ok": True})


@app.route("/auth/logout")
def logout():
    session.pop("user_email", None)
    return redirect("/")


# ── premium / MercadoPago ────────────────────────────────────────
@app.route("/premium")
def premium_route():
    usuario = session.get("user_email")
    if not usuario:
        return jsonify({"error": "No logueado"}), 401
    tipo = request.args.get("tipo", "mensual")
    if tipo == "anual":
        titulo = "Foschi IA Premium Anual (12 meses PAGA 10)"
        precio = 100000
    else:
        titulo = "Foschi IA Premium Mensual"
        precio = 10000
    pref = {
        "items": [{"title": titulo, "quantity": 1, "unit_price": precio}],
        "external_reference": usuario,
        "notification_url": "https://foschi-ia.onrender.com/webhook/mp",
    }
    preference = sdk.preference().create(pref)
    return jsonify(preference["response"])


@app.route("/webhook/mp", methods=["POST"])
def webhook_mp():
    data = request.json
    if not data or "data" not in data:
        return "ok"
    if data.get("type") != "payment":
        return "ok"
    payment_id = data["data"].get("id")
    if not payment_id:
        return "ok"

    payment = sdk.payment().get(payment_id)
    info    = payment.get("response", {})

    # Validar merchant (evita notificaciones de otras cuentas)
    if MP_MERCHANT_ID and info.get("merchant_account_id") != MP_MERCHANT_ID:
        return "ok"
    if info.get("status") != "approved":
        return "ok"

    usuario = info.get("external_reference")
    if not usuario:
        return "ok"

    from pagos import pago_ya_registrado, registrar_pago
    if pago_ya_registrado(str(payment_id)):
        return "ok"

    items  = info.get("additional_info", {}).get("items", [])
    titulo = items[0]["title"] if items else ""
    plan   = "anual" if ("12" in titulo or "Anual" in titulo) else "mensual"
    monto  = info.get("transaction_amount", 0)

    activar_premium(usuario, plan)
    registrar_pago(usuario=usuario, monto=monto, plan=plan, payment_id=str(payment_id))
    return "ok"


# ── index ────────────────────────────────────────────────────────
@app.route("/")
def index():
    if "usuario_id" not in session:
        session["usuario_id"] = str(uuid.uuid4())
    usuario  = session.get("user_email") or session["usuario_id"]
    premium  = usuario_premium(usuario)
    is_super = es_superusuario(usuario)
    return render_template_string(
        HTML_TEMPLATE,
        APP_NAME=APP_NAME,
        usuario_id=usuario,
        premium=premium,
        is_super=is_super,
        rol=rol_superusuario(usuario),
        nivel=nivel_superusuario(usuario),
        max_daily=MAX_DAILY_FREE,
    )


# ── preguntar ────────────────────────────────────────────────────
@app.route("/preguntar", methods=["POST"])
@limiter.limit("30 per minute")
def preguntar():
    data = request.get_json() or {}
    mensaje = data.get("mensaje", "").strip()

    if not mensaje:
        return jsonify({"texto": "Mensaje vacío.", "imagenes": [], "borrar_historial": False})

    if "usuario_id" not in session:
        session["usuario_id"] = str(uuid.uuid4())
    usuario = session.get("user_email") or session["usuario_id"]

    # ── LÍMITE DIARIO (backend) ───────────────────────────────────
    if not puede_preguntar(usuario):
        return jsonify({
            "texto": (f"⚠️ Alcanzaste el límite de {MAX_DAILY_FREE} preguntas diarias. "
                      "💎 Pasá a Premium para preguntas ilimitadas."),
            "imagenes": [],
            "borrar_historial": False,
            "limite": True,
        })

    lat = data.get("lat")
    lon = data.get("lon")
    tz  = data.get("timeZone") or data.get("time_zone")

    respuesta = generar_respuesta(mensaje, usuario, lat=lat, lon=lon, tz=tz)

    # Guardar historial (una sola vez, aquí)
    texto_hist = respuesta.get("texto", "") if isinstance(respuesta, dict) else str(respuesta)
    guardar_en_historial(usuario, mensaje, texto_hist)

    return jsonify(respuesta)


# ── historial ────────────────────────────────────────────────────
@app.route("/historial/<usuario_id>")
@limiter.limit("30 per minute")
def historial(usuario_id):
    # Solo el propio usuario puede ver su historial
    usuario_sesion = session.get("user_email") or session.get("usuario_id", "")
    if usuario_id != usuario_sesion and not es_superusuario(usuario_sesion):
        return jsonify([]), 403
    return jsonify(cargar_historial(usuario_id))


# ── TTS ──────────────────────────────────────────────────────────
@app.route("/tts")
@limiter.limit("60 per minute")
def tts():
    texto = request.args.get("texto", "")[:500]   # límite de longitud
    try:
        tts_obj = gTTS(text=texto, lang="es", slow=False, tld="com.mx")
        archivo = io.BytesIO()
        tts_obj.write_to_fp(archivo)
        archivo.seek(0)
        return send_file(archivo, mimetype="audio/mpeg")
    except Exception as e:
        return f"Error TTS: {e}", 500


# ── clima ────────────────────────────────────────────────────────
@app.route("/clima")
def clima():
    return obtener_clima(
        ciudad=request.args.get("ciudad"),
        lat=request.args.get("lat"),
        lon=request.args.get("lon"),
    )


# ── favicon ──────────────────────────────────────────────────────
@app.route("/favicon.ico")
def favicon():
    ico = os.path.join(STATIC_DIR, "favicon.ico")
    if os.path.exists(ico):
        return send_file(ico)
    return "", 204


# ── avisos (recordatorios polling) ──────────────────────────────
@app.route("/avisos", methods=["POST"])
@limiter.limit("12 per minute")
def avisos():
    usuario = request.json.get("usuario_id", "anon")
    lista   = load_recordatorios()
    ahora   = datetime.now(TZ)
    vencidos, restantes = [], []
    for r in lista:
        try:
            cuando = TZ.localize(datetime.strptime(r["cuando"], "%Y-%m-%d %H:%M:%S"))
        except Exception:
            restantes.append(r)
            continue
        if cuando <= ahora and r.get("usuario") == usuario:
            vencidos.append(r)
        else:
            restantes.append(r)
    save_recordatorios(restantes)
    return jsonify(vencidos)


# ── admin pagos (protegido con header, no query param) ───────────
@app.route("/admin/pagos")
def admin_pagos():
    # La clave va en el header X-Admin-Key, no en la URL
    if request.headers.get("X-Admin-Key") != ADMIN_KEY:
        return "Acceso denegado", 403

    archivo = os.path.join(DATA_DIR, "pagos.json")
    if not os.path.exists(archivo):
        return "<h2>No hay pagos todavía</h2>"

    with open(archivo) as f:
        pagos = json.load(f)

    filas = "".join(
        f"<tr><td>{u}</td><td>{p['plan']}</td><td>{p['fecha']}</td>"
        f"<td>{p['payment_id']}</td><td>{p['status']}</td></tr>"
        for u, p in pagos.items()
    )
    return (
        "<h2>💎 Pagos Foschi IA</h2>"
        "<table border='1' cellpadding='8'>"
        "<tr><th>Usuario</th><th>Plan</th><th>Fecha</th><th>Payment ID</th><th>Status</th></tr>"
        + filas + "</table>"
    )


# ── upload audio → transcripción → docx ──────────────────────────
@app.route("/upload_audio", methods=["POST"])
@limiter.limit("10 per hour")
def upload_audio():
    if "audio" not in request.files:
        return "No se envió archivo", 400
    file     = request.files["audio"]
    filename = secure_filename(file.filename or "audio")
    if not filename:
        return "Nombre de archivo inválido", 400

    temp_path = os.path.join("temp", f"{uuid.uuid4()}_{filename}")
    file.save(temp_path)
    docx_path = None

    try:
        with open(temp_path, "rb") as f:
            transcript = openai_client.audio.transcriptions.create(
                model="gpt-4o-transcribe", file=f
            )
        texto_transcrito = transcript.text if hasattr(transcript, "text") else str(transcript)

        nombre_docx = filename.rsplit(".", 1)[0] + ".docx"
        docx_path   = os.path.join("temp", nombre_docx)
        doc = DocxDocument()
        doc.add_heading("Transcripción de audio", level=1)
        doc.add_paragraph(texto_transcrito)
        doc.save(docx_path)

        @after_this_request
        def _cleanup(response):
            for p in [docx_path, temp_path]:
                try:
                    if p and os.path.exists(p): os.remove(p)
                except Exception:
                    pass
            return response

        return send_file(
            docx_path,
            as_attachment=True,
            mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            download_name=nombre_docx,
        )
    except Exception as e:
        for p in [docx_path, temp_path]:
            try:
                if p and os.path.exists(p): os.remove(p)
            except Exception:
                pass
        return f"Error en transcripción: {e}", 500


# ── helpers extracción de texto ──────────────────────────────────
def extract_text_from_pdf(path: str) -> str:
    text = ""
    try:
        with open(path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                try:
                    p = page.extract_text()
                    if p: text += p + "\n"
                except Exception:
                    continue
    except Exception as e:
        print("Error leyendo PDF:", e)
    return text


def extract_text_from_docx(path: str) -> str:
    text = ""
    try:
        doc = docx_reader.Document(path)
        for p in doc.paragraphs:
            if p.text: text += p.text + "\n"
    except Exception as e:
        print("Error leyendo DOCX:", e)
    return text


# ── upload doc → txt temporal ─────────────────────────────────────
@app.route("/upload_doc", methods=["POST"])
@limiter.limit("20 per hour")
def upload_doc():
    if "archivo" not in request.files:
        return "No se envió archivo", 400
    file     = request.files["archivo"]
    filename = secure_filename(file.filename or "")
    if not filename:
        return "Archivo sin nombre", 400
    ext = filename.rsplit(".", 1)[-1].lower()
    if ext not in ["pdf", "docx"]:
        return "Formato no permitido. Solo PDF o DOCX.", 400

    doc_id    = str(uuid.uuid4())
    temp_path = os.path.join(TEMP_DIR, f"{doc_id}_{filename}")
    try:
        file.save(temp_path)
    except Exception as e:
        return f"Error guardando archivo temporal: {e}", 500

    text = extract_text_from_pdf(temp_path) if ext == "pdf" else extract_text_from_docx(temp_path)

    if not text or not text.strip():
        try: os.remove(temp_path)
        except Exception: pass
        return "No pude extraer texto del documento.", 400

    txt_path = os.path.join(TEMP_DIR, f"{doc_id}.txt")
    try:
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(text)
    except Exception as e:
        try: os.remove(temp_path)
        except Exception: pass
        return f"Error guardando texto temporal: {e}", 500

    snippet = text[:800].replace("\n", " ") + ("..." if len(text) > 800 else "")
    return jsonify({"doc_id": doc_id, "name": filename, "snippet": snippet})


# ── resumir doc → docx ────────────────────────────────────────────
@app.route("/resumir_doc", methods=["POST"])
@limiter.limit("10 per hour")
def resumir_doc():
    data    = request.get_json() or {}
    doc_id  = data.get("doc_id")
    modo    = data.get("modo", "normal")
    if not doc_id:
        return "Falta doc_id", 400

    txt_path = os.path.join(TEMP_DIR, f"{doc_id}.txt")
    if not os.path.exists(txt_path):
        return "Documento temporal no encontrado (subilo nuevamente).", 404

    try:
        with open(txt_path, "r", encoding="utf-8") as f:
            texto = f.read()
    except Exception as e:
        return f"Error leyendo texto temporal: {e}", 500

    instrucciones = {
        "breve":   "Resumí el siguiente texto en 4-6 líneas muy concisas, en español claro y directo.",
        "profundo": ("Hacé un resumen detallado: explicá los puntos clave, sub-puntos y conclusiones. "
                     "Usá viñetas y subtítulos cuando corresponda. Estilo formal y completo."),
    }.get(modo, "Resumí el siguiente texto en puntos claros y ordenados, abarcando las ideas importantes.")

    max_chars  = 120_000
    texto_envio = texto[:max_chars] + ("\n\n[Documento truncado por tamaño]\n" if len(texto) > max_chars else "")
    prompt      = f"{instrucciones}\n\n--- TEXTO ---\n\n{texto_envio}"

    try:
        resp   = openai_client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=1000,
        )
        resumen = resp.choices[0].message.content.strip()
    except Exception as e:
        return f"No pude generar el resumen: {e}", 500

    fecha           = datetime.now().strftime("%Y-%m-%d")
    resumen_filename = f"Resumen_{fecha}.docx"
    resumen_path    = os.path.join(TEMP_DIR, f"{doc_id}_resumen_{fecha}.docx")

    try:
        doc = DocxDocument()
        doc.add_heading("Resumen del Documento", level=1)
        for linea in resumen.split("\n"):
            doc.add_paragraph("" if not linea.strip() else linea)
        doc.save(resumen_path)
    except Exception as e:
        return f"Error creando archivo Word: {e}", 500

    @after_this_request
    def _cleanup(response):
        for p in [resumen_path, txt_path]:
            try:
                if os.path.exists(p): os.remove(p)
            except Exception:
                pass
        try:
            for fn in os.listdir(TEMP_DIR):
                if fn.startswith(doc_id + "_"):
                    try: os.remove(os.path.join(TEMP_DIR, fn))
                    except Exception: pass
        except Exception:
            pass
        return response

    return send_file(
        resumen_path,
        as_attachment=True,
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        download_name=resumen_filename,
    )


# ================================================================
# MAIN
# ================================================================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
