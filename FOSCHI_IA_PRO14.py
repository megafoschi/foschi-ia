#!/usr/bin/env python3
# coding: utf-8

import os
import uuid
import json
import io
import re
import time
import threading
from datetime import datetime, timedelta

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

client = OpenAI()

# --- librerías adicionales para documentos ---
import PyPDF2
from docx import Document as DocxDocument  # para crear / leer .docx
import docx as docx_reader  # para leer .docx (Document ya importado para crear)

# ---------------- CONFIG ----------------
APP_NAME = "FOSCHI IA WEB"
CREADOR = "Gustavo Enrique Foschi"
DATA_DIR = "data"
STATIC_DIR = "static"
TEMP_DIR = os.path.join(DATA_DIR, "temp_docs")
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

# ---------------- KEYS ---------------- (usa variables de entorno)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")
OWM_API_KEY = os.getenv("OWM_API_KEY")

# ---------------- APP ----------------
app = Flask(__name__)
app.secret_key = "FoschiWebKey"
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# ---------------- UTIL / CACHE / HTTP ----------------
HTTPS = requests.Session()
URL_REGEX = re.compile(r'(https?://[^\s]+)', re.UNICODE)

MEMORY_FILE = os.path.join(DATA_DIR, "memory.json")
MEMORY_CACHE = {}

from datetime import date

def puede_preguntar(usuario):
    if es_superusuario(usuario):
        return True  # 👑 sin límites

    hoy = date.today().isoformat()

    if usuario.get("fecha_preguntas") != hoy:
        usuario["fecha_preguntas"] = hoy
        usuario["preguntas_hoy"] = 0

    if usuario["preguntas_hoy"] >= 5:
        return False

    usuario["preguntas_hoy"] += 1
    return True

def load_json(path):
    """Carga memory.json en cache en RAM para accesos rápidos."""
    global MEMORY_CACHE
    if MEMORY_CACHE:
        return MEMORY_CACHE
    if not os.path.exists(path):
        MEMORY_CACHE = {}
        return MEMORY_CACHE
    try:
        with open(path, "r", encoding="utf-8") as f:
            MEMORY_CACHE = json.load(f)
            return MEMORY_CACHE
    except:
        MEMORY_CACHE = {}
        return MEMORY_CACHE

def save_json(path, data):
    """Guarda MEMORY_CACHE actualizado en disco."""
    global MEMORY_CACHE
    MEMORY_CACHE.update(data)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(MEMORY_CACHE, f, ensure_ascii=False, indent=2)

def fecha_hora_en_es():
    tz = pytz.timezone("America/Argentina/Buenos_Aires")
    ahora = datetime.now(tz)
    meses = ["enero","febrero","marzo","abril","mayo","junio","julio","agosto","septiembre","octubre","noviembre","diciembre"]
    dias = ["lunes","martes","miércoles","jueves","viernes","sábado","domingo"]
    return f"{dias[ahora.weekday()]}, {ahora.day} de {meses[ahora.month-1]} de {ahora.year}, {ahora.hour:02d}:{ahora.minute:02d}"

def hacer_links_clicleables(texto):
    return URL_REGEX.sub(r'<a href="\1" target="_blank" style="color:#ff0000;">\1</a>', texto)

# ---------------- HISTORIAL POR USUARIO ----------------
def guardar_en_historial(usuario, entrada, respuesta):
    path = os.path.join(DATA_DIR, f"{usuario}.json")
    datos = []
    if os.path.exists(path):
        try:
            with open(path,"r",encoding="utf-8") as f:
                datos = json.load(f)
        except:
            datos = []
    datos.append({
        "fecha": datetime.now(pytz.timezone("America/Argentina/Buenos_Aires")).strftime("%d/%m/%Y %H:%M:%S"),
        "usuario": entrada,
        "foschi": respuesta
    })
    datos = datos[-200:]
    try:
        with open(path,"w",encoding="utf-8") as f:
            json.dump(datos,f,ensure_ascii=False,indent=2)
    except Exception as e:
        print("Error guardando historial:", e)

def cargar_historial(usuario):
    path = os.path.join(DATA_DIR, f"{usuario}.json")
    if not os.path.exists(path): return []
    try:
        with open(path,"r",encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

# ---------------- CLIMA ----------------
def obtener_clima(ciudad=None, lat=None, lon=None):
    if not OWM_API_KEY:
        return "No está configurada la API de clima (OWM_API_KEY)."
    try:
        if lat and lon:
            url = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OWM_API_KEY}&units=metric&lang=es"
        else:
            ciudad = ciudad if ciudad else "Buenos Aires"
            url = f"http://api.openweathermap.org/data/2.5/weather?q={ciudad}&appid={OWM_API_KEY}&units=metric&lang=es"
        r = HTTPS.get(url, timeout=3)
        data = r.json()
        if r.status_code != 200:
            msg = data.get("message", "Respuesta no OK de OpenWeatherMap.")
            return f"No pude obtener el clima: {r.status_code} - {msg}"
        desc = data.get("weather", [{}])[0].get("description", "Sin descripción").capitalize()
        temp = data.get("main", {}).get("temp")
        hum = data.get("main", {}).get("humidity")
        name = data.get("name", ciudad if ciudad else "la ubicación")
        parts = [f"El clima en {name} es {desc}"]
        if temp is not None:
            parts.append(f"temperatura {round(temp)}°C")
        if hum is not None:
            parts.append(f"humedad {hum}%")
        return ", ".join(parts) + "."
    except:
        return "No pude obtener el clima."

# ---------------- RECORDATORIOS ----------------
RECORD_FILE = os.path.join(DATA_DIR, "recordatorios.json")
TZ = pytz.timezone("America/Argentina/Buenos_Aires")

def load_recordatorios():
    if not os.path.exists(RECORD_FILE): return []
    try:
        with open(RECORD_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def save_recordatorios(lista):
    try:
        with open(RECORD_FILE, "w", encoding="utf-8") as f:
            json.dump(lista, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("Error guardando recordatorios:", e)

def interpretar_fecha_hora(texto):
    """Intenta interpretar frases de tiempo en español. Devuelve datetime (con TZ) o None."""
    ahora = datetime.now(TZ)

    m = re.search(r"en (\d+)\s*minutos?", texto)
    if m:
        return ahora + timedelta(minutes=int(m.group(1)))

    m = re.search(r"en (\d+)\s*horas?", texto)
    if m:
        return ahora + timedelta(hours=int(m.group(1)))

    m = re.search(r"mañana a las (\d{1,2})(?::(\d{2}))?", texto)
    if m:
        hora = int(m.group(1))
        minuto = int(m.group(2)) if m.group(2) else 0
        mañana = (ahora + timedelta(days=1)).replace(hour=hora, minute=minuto, second=0, microsecond=0)
        return mañana

    m = re.search(r"a las (\d{1,2}):(\d{2})", texto)
    if m:
        hora = int(m.group(1))
        minuto = int(m.group(2))
        posible = ahora.replace(hour=hora, minute=minuto, second=0, microsecond=0)
        if posible <= ahora:
            posible = posible + timedelta(days=1)
        return posible

    m = re.search(r"el (\d{1,2}) de (\w+) a las (\d{1,2})(?::(\d{2}))?", texto)
    if m:
        dia = int(m.group(1))
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
                candidato = datetime(año, mes, dia, hora, minuto)
                candidato = TZ.localize(candidato)
            except Exception:
                return None
            if candidato <= ahora:
                try:
                    candidato = datetime(año+1, mes, dia, hora, minuto)
                    candidato = TZ.localize(candidato)
                except:
                    return None
            return candidato

    return None

def agregar_recordatorio(usuario, motivo_texto, fecha_hora_dt):
    """Agrega un recordatorio persistente. fecha_hora_dt debe ser datetime con TZ (o naive en TZ)."""
    if fecha_hora_dt.tzinfo is None:
        fecha_hora_dt = fecha_hora_dt.replace(tzinfo=TZ)
    lista = load_recordatorios()
    lista.append({
        "usuario": usuario,
        "motivo": motivo_texto.strip(),
        "cuando": fecha_hora_dt.strftime("%Y-%m-%d %H:%M:%S")
    })
    save_recordatorios(lista)

def listar_recordatorios(usuario):
    lista = load_recordatorios()
    return [r for r in lista if r.get("usuario") == usuario]

def borrar_recordatorios(usuario):
    lista = load_recordatorios()
    lista = [r for r in lista if r.get("usuario") != usuario]
    save_recordatorios(lista)

def monitor_recordatorios():
    """Hilo que revisa recordatorios y los dispara. Cuando se dispara, lo guarda en el historial del usuario."""
    while True:
        try:
            lista = load_recordatorios()
            ahora = datetime.now(TZ)
            restantes = []
            for r in lista:
                try:
                    cuando = datetime.strptime(r["cuando"], "%Y-%m-%d %H:%M:%S")
                    cuando = TZ.localize(cuando)
                except Exception:
                    try:
                        cuando = datetime.fromisoformat(r["cuando"])
                        if cuando.tzinfo is None:
                            cuando = TZ.localize(cuando)
                    except:
                        continue
                if cuando <= ahora:
                    usuario = r.get("usuario", "anon")
                    motivo = r.get("motivo", "(sin motivo)")
                    aviso_texto = f"⏰ Tenés un recordatorio: {motivo}"
                    try:
                        guardar_en_historial(usuario, f"[recordatorio] {motivo}", aviso_texto)
                    except Exception:
                        pass
                    print(aviso_texto)
                else:
                    restantes.append(r)
            save_recordatorios(restantes)
        except Exception as e:
            print("Error en monitor_recordatorios:", e)
        time.sleep(30)

# iniciar hilo del monitor (daemon)
threading.Thread(target=monitor_recordatorios, daemon=True).start()

# ---------------- learn_from_message (registro de memoria) ----------------
def learn_from_message(usuario, mensaje, respuesta):
    try:
        memory = load_json(MEMORY_FILE)
        if usuario not in memory:
            memory[usuario] = {"temas": {}, "mensajes": [], "ultima_interaccion": None}
        # Guardar texto en memoria (limitamos)
        memory[usuario]["mensajes"].append({"usuario": str(mensaje), "foschi": str(respuesta)})
        memory[usuario]["mensajes"] = memory[usuario]["mensajes"][-200:]
        ahora = datetime.now(pytz.timezone("America/Argentina/Buenos_Aires"))
        memory[usuario]["ultima_interaccion"] = ahora.strftime("%d/%m/%Y %H:%M:%S")
        # Tópicos simples
        for palabra in str(mensaje).lower().split():
            if len(palabra) > 3:
                memory[usuario]["temas"][palabra] = memory[usuario]["temas"].get(palabra, 0) + 1
        save_json(MEMORY_FILE, memory)
    except Exception as e:
        print("Error en learn_from_message:", e)

# ---------------- DICTADO A WORD ----------------
@app.route("/dictado_word", methods=["POST"])
def dictado_word():

    data = request.get_json(silent=True) or {}

    texto = data.get("texto", "").strip()

    if not texto:
        return jsonify({
            "ok": False,
            "error": "Texto vacío"
        })

    nombre = f"dictado_{uuid.uuid4().hex}.docx"

    ruta = os.path.join(TEMP_DIR, nombre)

    doc = DocxDocument()

    doc.add_heading("Dictado Foschi IA", 0)

    for linea in texto.split("\n"):

        linea = linea.strip()

        if linea:
            doc.add_paragraph(linea)

    doc.save(ruta)

    @after_this_request
    def remove_file(response):

        try:
            if os.path.exists(ruta):
                os.remove(ruta)
        except Exception as e:
            print("Error eliminando temporal:", e)

        return response

    return send_file(
        ruta,
        as_attachment=True,
        download_name="dictado_foschi.docx"
    )
    
# ---------------- RESPUESTA IA ----------------

def generar_respuesta(mensaje, usuario, lat=None, lon=None, tz=None, max_hist=5):
       
    # Bloqueo por no premium
    if not usuario_premium(usuario) and not es_superusuario(usuario):
        if len(mensaje) > 200:
            return {
                "texto": "🔒 Esta función es solo para usuarios Premium.\n\n💎 Activá Foschi IA Premium desde el botón superior para seguir.",
                "imagenes": [],
                "borrar_historial": False
            }

    # Asegurar string
    if not isinstance(mensaje, str):
        mensaje = str(mensaje)

    mensaje_lower = mensaje.lower().strip()
           
    # --- RECORDATORIOS: comandos y detección ---
    try:
        if mensaje_lower in ["mis recordatorios", "lista de recordatorios", "ver recordatorios"]:
            recs = listar_recordatorios(usuario)
            if not recs:
                return {"texto": "📭 No tenés recordatorios pendientes.", "imagenes": [], "borrar_historial": False}
            texto = "📌 Tus recordatorios:\n" + "\n".join([f"- {r['motivo']} → {r['cuando']}" for r in recs])
            return {"texto": texto, "imagenes": [], "borrar_historial": False}

        if "borrar recordatorios" in mensaje_lower or "eliminar recordatorios" in mensaje_lower:
            borrar_recordatorios(usuario)
            return {"texto": "🗑️ Listo, eliminé todos tus recordatorios.", "imagenes": [], "borrar_historial": False}

        if mensaje_lower.startswith(("recordame", "haceme acordar", "avisame", "recordá")):
            fecha_hora = interpretar_fecha_hora(mensaje_lower)
            if fecha_hora is None:
                return {"texto": "⏰ Decime cuándo: ejemplo 'mañana a las 9', 'en 15 minutos' o 'el 5 de diciembre a las 18'.", "imagenes": [], "borrar_historial": False}
            motivo = mensaje
            for p in ["recordame", "haceme acordar", "avisame", "recordá"]:
                motivo = re.sub(p, "", motivo, flags=re.IGNORECASE).strip()
            if not motivo:
                motivo = "Recordatorio"
            agregar_recordatorio(usuario, motivo, fecha_hora)
            return {"texto": f"✅ Listo, te lo recuerdo el {fecha_hora.strftime('%d/%m %H:%M')}.", "imagenes": [], "borrar_historial": False}
    except Exception as e:
        print("Error en manejo de recordatorios:", e)

    # BORRAR HISTORIAL
    if any(p in mensaje_lower for p in ["borrar historial", "limpiar historial", "reset historial"]):
        path = os.path.join(DATA_DIR, f"{usuario}.json")
        if os.path.exists(path): os.remove(path)
        memory = load_json(MEMORY_FILE)
        if usuario in memory:
            memory[usuario]["mensajes"] = []
            save_json(MEMORY_FILE, memory)
        return {"texto": "✅ Historial borrado correctamente.", "imagenes": [], "borrar_historial": True}

    # FECHA / HORA
    if any(p in mensaje_lower for p in ["qué día", "que día", "qué fecha", "que fecha", "qué hora", "que hora", "día es hoy", "fecha hoy"]):
        texto = fecha_hora_en_es()
        learn_from_message(usuario, mensaje, texto)
        return {"texto": texto, "imagenes": [], "borrar_historial": False}

    # CLIMA
    if "clima" in mensaje_lower:
        ciudad_match = re.search(r"clima en ([a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+)", mensaje_lower)
        ciudad = ciudad_match.group(1).strip() if ciudad_match else None
        texto = obtener_clima(ciudad=ciudad, lat=lat, lon=lon)
        learn_from_message(usuario, mensaje, texto)
        return {"texto": texto, "imagenes": [], "borrar_historial": False}

    # INFORMACIÓN ACTUALIZADA (NOTICIAS)
    if any(word in mensaje_lower for word in ["presidente", "actualidad", "noticias", "quién es", "últimas noticias", "evento actual"]):
        resultados = []
        if GOOGLE_API_KEY and GOOGLE_CSE_ID:
            try:
                url = (
                    f"https://www.googleapis.com/customsearch/v1"
                    f"?key={GOOGLE_API_KEY}&cx={GOOGLE_CSE_ID}"
                    f"&q={urllib.parse.quote(mensaje)}&sort=date"
                )
                r = HTTPS.get(url, timeout=5)
                data = r.json()
                for item in data.get("items", [])[:5]:
                    snippet = item.get("snippet", "").strip()
                    if snippet and snippet not in resultados:
                        resultados.append(snippet)
            except Exception as e:
                print("Error al obtener noticias:", e)

        if resultados:
            texto_bruto = " ".join(resultados)
            try:
                client = OpenAI(api_key=OPENAI_API_KEY)
                prompt = (
                    f"Tengo estos fragmentos de texto recientes: {texto_bruto}\n\n"
                    f"Respondé a la pregunta: '{mensaje}'. "
                    f"Usá un tono natural y directo en español argentino, sin frases como "
                    f"'según los textos', 'según los fragmentos' o 'de acuerdo a las fuentes'. "
                    f"Contestá con una sola oración clara y actualizada. Si no hay información suficiente, decílo sin inventar."
                )

                resp = client.chat.completions.create(
                    model="gpt-4-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.5,
                    max_tokens=120
                )

                texto = resp.choices[0].message.content.strip()
            except Exception as e:
                texto = "No pude generar la respuesta con OpenAI."
        else:
            texto = "No pude obtener información actualizada en este momento."

        learn_from_message(usuario, mensaje, texto)
        return {"texto": texto, "imagenes": [], "borrar_historial": False}

    # QUIÉN CREÓ / PREGUNTAS ESTÁTICAS
    if any(p in mensaje_lower for p in [
        "quién te creó", "quien te creo",
        "quién te hizo", "quien te hizo",
        "quién te programó", "quien te programo",
        "quién te inventó", "quien te invento",
        "quién te desarrolló", "quien te desarrollo",
        "quién te construyó", "quien te construyo"
    ]):
        texto = "Fui creada por Gustavo Enrique Foschi, el mejor 😎."
        learn_from_message(usuario, mensaje, texto)
        return {"texto": texto, "imagenes": [], "borrar_historial": False}

    # RESULTADOS DEPORTIVOS (actualizados)
    if any(p in mensaje_lower for p in [
        "resultado", "marcador", "ganó", "empató", "perdió",
        "partido", "deporte", "fútbol", "futbol", "nba", "tenis", "f1", "formula 1", "motogp"
    ]):
        resultados = []
        if GOOGLE_API_KEY and GOOGLE_CSE_ID:
            try:
                url = (
                    f"https://www.googleapis.com/customsearch/v1"
                    f"?key={GOOGLE_API_KEY}&cx={GOOGLE_CSE_ID}"
                    f"&q={urllib.parse.quote(mensaje + ' resultados deportivos actualizados')}"
                    f"&sort=date"
                )
                r = HTTPS.get(url, timeout=5)
                data = r.json()
                for item in data.get("items", [])[:5]:
                    snippet = item.get("snippet", "").strip()
                    if snippet and snippet not in resultados:
                        resultados.append(snippet)
            except Exception as e:
                print("Error al obtener resultados deportivos:", e)

        if resultados:
            texto_bruto = " ".join(resultados)
            try:
                client = OpenAI(api_key=OPENAI_API_KEY)
                prompt = (
                    f"Tengo estos fragmentos recientes sobre deportes: {texto_bruto}\n\n"
                    f"Respondé brevemente la consulta '{mensaje}' con los resultados deportivos actuales. "
                    f"Usá un tono natural, tipo boletín deportivo argentino, sin frases como 'según los textos'. "
                    f"Respondé en una sola oración clara."
                )

                resp = client.chat.completions.create(
                    model="gpt-4-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.5,
                    max_tokens=150
                )
                texto = resp.choices[0].message.content.strip()
            except Exception as e:
                texto = "No pude generar la respuesta deportiva."
        else:
            texto = "No pude encontrar resultados deportivos recientes en este momento."

        learn_from_message(usuario, mensaje, texto)
        return {"texto": texto, "imagenes": [], "borrar_historial": False}

    # SALIDA GENERAL: pasar a OpenAI para respuesta conversacional
    try:
        memoria = load_json(MEMORY_FILE)
        historial = memoria.get(usuario, {}).get("mensajes", [])[-max_hist:]
        resumen = " ".join([m["usuario"] + ": " + m["foschi"] for m in historial[-3:]]) if historial else ""

        client = OpenAI(api_key=OPENAI_API_KEY)

        prompt_messages = [
            {
                "role": "system",
                "content": (
                    "Sos FOSCHI IA, una inteligencia amable, directa y con humor ligero. "
                    "Tus respuestas deben ser claras, ordenadas y sonar naturales en español argentino. "
                    "Si el usuario pide información o ayuda técnica, explicá paso a paso y sin mezclar temas. "
                    f"Resumen de últimas interacciones: {resumen if resumen else 'ninguna.'}"
                )
            },
            {"role": "user", "content": mensaje}
        ]

        resp = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=prompt_messages,
            temperature=0.7,
            max_tokens=700
        )

        texto = resp.choices[0].message.content.strip()

    except Exception as e:
        texto = f"No pude generar respuesta: {e}"

        texto = hacer_links_clicleables(texto)

    aviso = aviso_vencimiento(usuario)
    if aviso:
        texto += "\n\n" + aviso

    learn_from_message(usuario, mensaje, texto)
    return {
        "texto": texto,
        "imagenes": [],
        "borrar_historial": False
    }

# ---------------- Plantilla HTML (modificada para menu clip + subir pdf/docx) ----------------
HTML_TEMPLATE = """  
<!doctype html>
<html>
<head>
<title>{{APP_NAME}}</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
/* --- ESTILOS GENERALES --- */
body{
 font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
 background:#000814;
 color:#00eaff;
 margin:0;
 padding:0;
 display:flex;
 flex-direction:column;
 height:100vh;
 overflow:hidden;
 text-shadow:0 0 6px #00eaff;
}

/* --- HEADER SUPERIOR (LOGO + BOTONES) --- */
#header{
  display:flex;
  align-items:center;
  justify-content:space-between;
  padding:8px 16px;
  background: linear-gradient(#000814,#00111a);
  flex-shrink:0;
  position:sticky;
  top:0;
  z-index:10;
  box-shadow:0 0 12px #00eaff66;
}

#leftButtons{
  display:flex;
  align-items:center;
  gap:12px;
}

#rightButtons{
  display:flex;
  align-items:center;
  gap:8px;
}

.separator{
  border-left:1px solid #00eaff55;
  height:32px;
  margin:0 8px;
}

#header button{
  font-size:14px;
  padding:6px 10px;
  border-radius:6px;
  background:#001f2e;
  color:#00eaff;
  border:1px solid #006688;
  cursor:pointer;
  text-shadow:0 0 4px #00eaff;
  box-shadow:0 0 8px #0099bb;
  transition:0.3s;
}
/* ===================== */
/* === MODO DAY ======== */
/* ===================== */
body.day{
  background:#ffffff;
  color:#000000;
  text-shadow:none;
}

body.day #header{
  background:#ffffff;
  box-shadow:0 2px 8px rgba(0,0,0,0.1);
}

body.day #chat{
  background:#f5f5f5;
  border-top:1px solid #ccc;
  border-bottom:1px solid #ccc;
  box-shadow:none;
}

body.day #inputBar{
  background:#ffffff;
  border-top:1px solid #ccc;
}

body.day button{
  background:#ffffff !important;
  color:#000000 !important;
  border:1px solid #000000 !important;
  box-shadow:none !important;
  text-shadow:none !important;
}

body.day input{
  background:#ffffff !important;
  color:#000000 !important;
  border:1px solid #000000 !important;
  box-shadow:none !important;
}

/* Premium en Day */
body.day #premiumBtn{
  animation:none;
  font-weight:600;
}

#header button:hover{
  background:#003547;
  box-shadow:0 0 14px #00eaff;
}

#premiumBtn{
  animation: neonGlow 1.5s ease-in-out infinite alternate;
}

@keyframes neonGlow {
  0% { box-shadow: 0 0 8px #00eaff, 0 0 12px #00eaff, 0 0 16px #00eaff; color:#00eaff; }
  50% { box-shadow: 0 0 12px #00ffff, 0 0 20px #00ffff, 0 0 28px #00ffff; color:#00ffff; }
  100% { box-shadow: 0 0 8px #00eaff, 0 0 12px #00eaff, 0 0 16px #00eaff; color:#00eaff; }
}

#logo{
  width:120px;
  cursor:pointer;
  transition: transform 0.5s, filter 0.5s;
  filter: drop-shadow(0 0 12px #00eaff);
}
#logo:hover{
  transform:scale(1.2) rotate(6deg);
  filter:drop-shadow(0 0 20px #00eaff);
}

/* --- CHAT --- */
#chat{
  flex:1;
  overflow-y:auto;
  padding:10px;
  background: linear-gradient(#00111a,#000814);
  border-top:2px solid #00eaff44;
  border-bottom:2px solid #00eaff44;
  box-shadow: inset 0 0 15px #00eaff55;
  padding-bottom:120px; /* espacio para la barra inferior */
}

/* --- MENSAJES --- */
.message{
 margin:5px 0;
 padding:8px 12px;
 border-radius:15px;
 max-width:80%;
 word-wrap:break-word;
 opacity:0;
 transition:opacity 0.5s, box-shadow 0.5s, background 0.5s;
 font-size:15px;
}
.message.show{ opacity:1; }
.user{
 background:rgba(51,0,255,0.3);
 color:#b4b7ff;
 margin-left:auto;
 text-align:right;
 border:1px solid #4455ff;
 box-shadow:0 0 8px #3344ff;
}
.ai{
 background:rgba(0,255,255,0.2);
 color:#00eaff;
 margin-right:auto;
 text-align:left;
 border:1px solid #00eaff;
 box-shadow:0 0 10px #00eaff;
}
a{ color:#00eaff; text-decoration:underline; }
img{ max-width:300px; border-radius:10px; margin:5px 0; box-shadow:0 0 10px #00eaff88; border:1px solid #00eaff55; }

/* --- BARRA DE ENTRADA FIJA ABAJO --- */
#inputBar{
 display:flex;
 align-items:center;
 gap:6px;
 padding:8px;
 background:#001d29;
 border-top:2px solid #00eaff44;
 flex-shrink:0;
 position:fixed;
 bottom:0;
 left:0;
 width:100%;
 box-sizing:border-box;
 z-index:20;
}
#inputBar input[type=text]{
 flex:1;
 padding:10px;
 font-size:16px;
 background:#00121d;
 color:#00eaff;
 border:1px solid #003344;
 box-shadow:0 0 6px #00eaff55 inset;
 border-radius:5px;
}
#inputBar button{
 padding:10px;
 font-size:16px;
 border:none;
 border-radius:5px;
 background:#001f2e;
 color:#00eaff;
 cursor:pointer;
 border:1px solid #006688;
 text-shadow:0 0 4px #00eaff;
 box-shadow:0 0 8px #0099bb;
 transition:0.25s;
}
#inputBar button:hover{
 background:#003547;
 box-shadow:0 0 14px #00eaff;
}

/* --- BOTONES PEQUEÑOS --- */
#vozBtn,#borrarBtn,#premiumBtn{ font-size:14px; padding:6px 10px; }

/* --- BOTÓN ADJUNTAR (CLIP) --- */
#clipBtn{
  width:40px;
  height:40px;
  display:flex;
  align-items:center;
  justify-content:center;
  font-size:20px;
  cursor:pointer;
  border-radius:6px;
  background:#001f2e;
  color:#00eaff;
  border:1px solid #006688;
  box-shadow:0 0 10px #0099bb;
  transition:0.25s;
  user-select:none;
}

#clipBtn:hover{
  background:#003547;
  box-shadow:0 0 16px #00eaff;
  transform:scale(1.08);
}

/* --- CLIP EN MODO DAY --- */
body.day #clipBtn{
  background:#ffffff;
  color:#000000;
  border:1px solid #000000;
  box-shadow:none;
}

body.day #clipBtn:hover{
  background:#f0f0f0;
}

/* --- MENÚ DE ADJUNTOS (overlay fijo sobre la barra) --- */
#adjuntos_menu{
 position:fixed;
 left:10px;
 bottom:62px;
 display:none;
 background:#001f2e;
 border:1px solid #003547;
 padding:8px;
 border-radius:8px;
 box-shadow:0 6px 16px rgba(0,0,0,0.6);
 z-index:999;
 max-width:90vw;
}
#adjuntos_menu button{ display:block; width:200px; margin:4px 0; text-align:left; }
.hidden_file_input{ display:none; }

/* --- MENÚ PREMIUM --- */
#premiumMenu button{
  display:block;
  width:120px;
  margin:4px 0;
  text-align:left;
}

/* --- AJUSTES RESPONSIVE PARA MÓVIL --- */
@media (max-width:600px){
  #inputBar input[type=text]{ font-size:18px; padding:12px; }
  #inputBar button{ font-size:16px; padding:10px; }
  #logo{ width:140px; } /* logo más grande en móvil */
}
/* =============================== */
/* === MENSAJES EN MODO DAY ====== */
/* =============================== */

body.day .user{
  background:#e9e9e9;
  color:#000000;
  border:1px solid #000000;
  box-shadow:none;
}

body.day .ai{
  background:#f5f5f5;
  color:#000000;
  border:1px solid #000000;
  box-shadow:none;
}

body.day .ai a,
body.day .user a{
  color:#000000;
}

/* ===== FORMULARIO PREMIUM CENTRADO ===== */
.form-premium{
  width:100%;
  max-width:320px;
  margin:0 auto;
  display:flex;
  flex-direction:column;
  align-items:center;
  gap:10px;
}

.form-premium input{
  width:100%;
  padding:10px;
  border-radius:6px;
  border:1px solid #006688;
  background:#00121d;
  color:#00eaff;
  box-shadow:0 0 6px #00eaff55 inset;
}

.form-premium button{
  width:100%;
  padding:10px;
  border-radius:6px;
  border:1px solid #006688;
  background:#001f2e;
  color:#00eaff;
  cursor:pointer;
  box-shadow:0 0 8px #0099bb;
}

.form-premium button:hover{
  background:#003547;
  box-shadow:0 0 14px #00eaff;
}

.wave{
 width:6px;
 height:20px;
 background:#00eaff;
 animation:wave 1s infinite ease-in-out;
 border-radius:4px;
}

.wave:nth-child(2){animation-delay:0.1s;}
.wave:nth-child(3){animation-delay:0.2s;}
.wave:nth-child(4){animation-delay:0.3s;}
.wave:nth-child(5){animation-delay:0.4s;}
/* ========================= */
/* 🎤 DICTADO PRO */
/* ========================= */

/* Panel de texto acumulado durante dictado */
#dictadoPanel{
  position:fixed;
  bottom:62px;
  left:0; right:0;
  max-height:180px;
  overflow-y:auto;
  background:#00060d;
  border-top:2px solid #ff003366;
  padding:10px 16px;
  font-size:15px;
  color:#ffffff;
  line-height:1.7;
  z-index:25;
  display:none;
  white-space:pre-wrap;
  word-break:break-word;
  scrollbar-width:thin;
  scrollbar-color:#ff003366 transparent;
}
#dictadoPanel::-webkit-scrollbar{ width:4px; }
#dictadoPanel::-webkit-scrollbar-thumb{ background:#ff003366; border-radius:4px; }

body.day #dictadoPanel{
  background:#f5f5f5;
  color:#111;
  border-color:#cc000055;
}

#dictadoBtn.activo{
  background:#ff0033 !important;
  color:#fff !important;
  border:1px solid #ff3355 !important;
  box-shadow:0 0 20px #ff0033 !important;
  animation:pulseDictado 1s infinite;
}

@keyframes pulseDictado{
  0%{transform:scale(1);}
  50%{transform:scale(1.06);}
  100%{transform:scale(1);}
}

#dictadoEstado{
  box-shadow:0 0 20px #ff0033;
  animation:pulseEstado 1s infinite;
}

@keyframes pulseEstado{
  0%{opacity:1;}
  50%{opacity:0.6;}
  100%{opacity:1;}
}

@keyframes wave{
0%,100%{height:10px;}
50%{height:40px;}
}

</style>
</head>

<body>
<!-- HEADER -->
<div id="header">
  <div id="leftButtons">
    <img src="/static/logo.png" id="logo" onclick="logoClick()" alt="logo">

    <div id="premiumContainer" style="position:relative; margin-left:12px;">
      <button id="dayNightBtn" onclick="toggleDayNight()">🌙</button>

      <button id="premiumBtn" onclick="togglePremiumMenu()">
        {% if premium %}
          💎 Premium activo
        {% else %}
          💎 Pasar a Premium
        {% endif %}
      </button>

      {% if not premium %}
      <div id="premiumMenu"
           style="display:none; position:absolute; top:36px; left:0;
                  background:#001f2e; border:1px solid #003547;
                  border-radius:6px; padding:6px;
                  box-shadow:0 6px 16px rgba(0,0,0,0.6); z-index:100;">
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

<!-- CHAT -->
<div id="chat" role="log" aria-live="polite"></div>
<div id="voiceWave" style="
position:fixed;
bottom:110px;
left:50%;
transform:translateX(-50%);
display:none;
gap:4px;
z-index:999;
">
<div class="wave"></div>
<div class="wave"></div>
<div class="wave"></div>
<div class="wave"></div>
<div class="wave"></div>
</div>

<div id="dictadoEstado" style="
 position:fixed;
 bottom:70px;
 right:10px;
 background:#ff0000;
 color:white;
 padding:6px 10px;
 border-radius:6px;
 display:none;
 font-weight:bold;
 z-index:999;">
🎤 Dictado activo
</div>
<!-- MENÚ ADJUNTOS (overlay fuera de la barra) -->
<div id="adjuntos_menu" aria-hidden="true">
  <button onclick="toggleModoConversacion()">🧠 Modo conversación</button>
  <button onclick="checkPremium('audio')">🎵 Audio (mp3/wav) a Texto</button>
  <button onclick="checkPremium('doc')">📄 Analizar Documento</button>
  <button onclick="abrirDictadoDesdeMenu()">🎤 Dictado</button>
</div>

<!-- INPUTS OCULTOS -->
<input id="audioInput" class="hidden_file_input" type="file" accept=".mp3,audio/*,.wav" />
<input id="archivo_pdf_word" class="hidden_file_input" type="file" accept=".pdf,.docx" />

<!-- BARRA DE ENTRADA -->
<div id="inputBar">

  <!-- Clip — visible cuando NO está dictando -->
  <div id="clipBtn" title="Adjuntar" onclick="toggleAdjuntosMenu()">📎</div>

  <!-- Input de texto -->
  <input type="text" id="mensaje" placeholder="Escribí tu mensaje o hablá" />

  <!-- Botones normales — se ocultan durante dictado -->
  <div id="botonesNormales" style="display:flex;gap:6px;align-items:center;">
    <button onclick="checkDailyLimit()">Enviar</button>
    <button onclick="hablar()">🎤 Hablar</button>
  </div>

  <!-- Botones dictado — solo visibles durante dictado -->
  <div id="botonesDictado" style="display:none;gap:6px;align-items:center;">
    <button id="dictadoBtn" onclick="toggleDictado()">⏸️ Pausar</button>
    <button id="finalizarDictadoBtn"
      onclick="finalizarDictadoManual()"
      style="background:#ff0033;color:white;border:1px solid #ff5577;">
      ✅ Finalizar
    </button>
    <button onclick="cancelarDictado()"
      style="background:#333;color:#ccc;border:1px solid #555;">
      ❌ Cancelar
    </button>
  </div>

</div>

<script>
// --- Variables y funciones generales ---
let usuario_id="{{usuario_id}}";
let documentoActual = null;
let textoDocumento = "";
let vozActiva=true,audioActual=null,mensajeActual=null;
let modoConversacion = false;
let escuchandoContinuo = false;
let recognitionConversacion = null;
let silencioTimer=null;

function toggleModoConversacion(){

  if(!isPremium && !isSuper){
    alert("🔒 El modo conversación es Premium");
    return;
  }

  if(!modoConversacion){
    iniciarConversacion();
  }else{
    detenerConversacion();
  }

}

function iniciarConversacion(){

  if(!('webkitSpeechRecognition' in window)){
    alert("Tu navegador no soporta conversación por voz");
    return;
  }

  document.getElementById("voiceWave").style.display="flex";


  const Rec = window.SpeechRecognition || window.webkitSpeechRecognition;

  recognitionConversacion = new Rec();

  recognitionConversacion.lang = "es-AR";
  recognitionConversacion.continuous = true;
  recognitionConversacion.interimResults = false;

  modoConversacion = true;
  escuchandoContinuo = true;

  agregar("🧠 Modo conversación activado","ai");

recognitionConversacion.onresult = function(event){

  let texto = event.results[event.results.length-1][0].transcript;
  if(texto.length < 3) return;

  if(texto.trim() === "") return;

  if(audioActual){
  audioActual.pause();
  audioActual.currentTime = 0;
}
  document.getElementById("mensaje").value = texto;

  enviar();

  // 👇 DETECTOR DE SILENCIO
  clearTimeout(silencioTimer);

  silencioTimer = setTimeout(()=>{
     console.log("Silencio detectado");
  },2000);

};

  recognitionConversacion.onend = function(){

  if(modoConversacion && !audioActual){
    recognitionConversacion.start();
  }

};

  recognitionConversacion.start();

}

function detenerConversacion(){

  modoConversacion = false;
  escuchandoContinuo = false;

  if(recognitionConversacion){
    recognitionConversacion.stop();
    recognitionConversacion = null;
  }

  document.getElementById("voiceWave").style.display = "none";

  agregar("🛑 Modo conversación desactivado","ai");

}

let MAX_NO_PREMIUM = 5;
let isPremium = {{ 'true' if premium else 'false' }};
const hoy = new Date().toISOString().slice(0,10); // YYYY-MM-DD
let preguntasHoy = parseInt(
  localStorage.getItem("preguntasHoy_" + hoy) || "0"
);

let isSuper = {{ 'true' if is_super else 'false' }};
let rolUsuario = "{{ rol or '' }}";
let nivelUsuario = {{ nivel or 0 }};

function logoClick(){ alert("FOSCHI NUNCA MUERE, TRASCIENDE..."); }
function toggleVoz(estado=null){ vozActiva=estado!==null?estado:!vozActiva; document.getElementById("vozBtn").textContent=vozActiva?"🔊 Voz activada":"🔇 Silenciada"; }
function detenerVoz(){ if(audioActual){ audioActual.pause(); audioActual.currentTime=0; audioActual.src=""; audioActual.load(); audioActual=null; if(mensajeActual) mensajeActual.classList.remove("playing"); mensajeActual=null; } }

function agregar(msg,cls,imagenes=[]){
  let c=document.getElementById("chat"),div=document.createElement("div");
  div.className="message "+cls; div.innerHTML=msg;
  c.appendChild(div);
  setTimeout(()=>div.classList.add("show"),50);
  imagenes.forEach(url=>{ let img=document.createElement("img"); img.src=url; div.appendChild(img); });
  c.scroll({top:c.scrollHeight,behavior:"smooth"});
  if(cls==="ai") hablarTexto(msg,div);
  return div;
}

function checkDailyLimit(){
  if(!isPremium && !isSuper && preguntasHoy >= MAX_NO_PREMIUM){
    alert(`⚠️ Has alcanzado el límite de ${MAX_NO_PREMIUM} preguntas diarias. Pasá a Premium para más.`);
    return;
  }

  enviar();

  if(!isPremium){
    preguntasHoy++;
    localStorage.setItem("preguntasHoy_" + hoy, preguntasHoy);
  }
}

function enviar(){
  let msg=document.getElementById("mensaje").value.trim(); 
  if(!msg) return;

  agregar(msg,"user"); 

  document.getElementById("mensaje").value="";
    // ============================
  // ❌ SALIR DEL MODO DOCUMENTO
  // ============================

  if(
    msg.toLowerCase().includes("salir del documento") ||
    msg.toLowerCase().includes("cerrar archivo") ||
    msg.toLowerCase().includes("modo normal")
  ){

    salirModoDocumento();

    return;
  }

  fetch("/preguntar",{
    method:"POST",
    headers:{
      "Content-Type":"application/json"
    },
    body:JSON.stringify({
      mensaje: msg,
      usuario_id: usuario_id,
      doc_id: documentoActual,
      preguntar_doc: modoPreguntasDocumento
    })
  })

  .then(r=>r.json())

  .then(data=>{

    agregar(data.texto,"ai",data.imagenes);

    if(data.borrar_historial){
      document.getElementById("chat").innerHTML="";
    }

  })

  .catch(e=>{

    agregar("Error al comunicarse con el servidor.","ai");

    console.error(e);

  });
}

document.getElementById("mensaje").addEventListener("keydown",e=>{ if(e.key==="Enter"){ e.preventDefault(); checkDailyLimit(); } });

function hablarTexto(texto, div=null){

  if(!vozActiva) return;

  // 🛑 detener escucha solo si está en modo conversación
  if(modoConversacion && recognitionConversacion){
    recognitionConversacion.stop();
  }

  detenerVoz();

  if(mensajeActual) mensajeActual.classList.remove("playing");
  if(div) div.classList.add("playing");
  mensajeActual = div;

  audioActual = new Audio("/tts?texto=" + encodeURIComponent(texto));
  audioActual.playbackRate = 1.25;

  audioActual.onended = () => {

    if(mensajeActual) mensajeActual.classList.remove("playing");
    mensajeActual = null;

    // 🎤 volver a escuchar cuando termina
    if(modoConversacion && recognitionConversacion){
      recognitionConversacion.start();
    }

  };

  audioActual.play();
}

function togglePremiumMenu(){
  if(isPremium) return;

  const menu = document.getElementById("premiumMenu");
  if(!menu) return;

  menu.style.display = (menu.style.display === "block") ? "none" : "block";

  if(menu.style.display === "block"){
    setTimeout(() => {
      window.addEventListener("click", closePremiumMenuOnClickOutside);
    }, 50);
  }
}

function closePremiumMenuOnClickOutside(e){
  const menu = document.getElementById("premiumMenu");
  const btn = document.getElementById("premiumBtn");
  if(!menu.contains(e.target) && !btn.contains(e.target)){
    menu.style.display="none";
    window.removeEventListener('click', closePremiumMenuOnClickOutside);
  }
}

function irPremium(tipo){
  fetch(`/premium?tipo=${tipo}`)
    .then(r => {
      if(r.status === 401){
        openAuth();
        return null;
      }
      return r.json();
    })
    .then(data => {
      if(!data) return;
      if(data.init_point){
        window.location.href = data.init_point;
      }
    })
    .catch(err => console.error(err));
}

function checkPremium(tipo){
  if(!isPremium){
    alert("⚠️ Esta función requiere Premium. Pasá a Premium para usarla.");
    return;
  }
  if(tipo==='audio') document.getElementById('audioInput').click();
  if(tipo==='doc') document.getElementById('archivo_pdf_word').click();
}

function toggleAdjuntosMenu(){
  const m = document.getElementById("adjuntos_menu");
  m.style.display = m.style.display === "block" ? "none" : "block";
  if(m.style.display==="block"){ setTimeout(()=>window.addEventListener('click', closeMenuOnClickOutside),50); }
}
function closeMenuOnClickOutside(e){
  const menu = document.getElementById("adjuntos_menu");
  const clip = document.getElementById("clipBtn");
  if(!menu.contains(e.target) && !clip.contains(e.target)){ menu.style.display="none"; window.removeEventListener('click', closeMenuOnClickOutside); }
}
function abrirDictadoDesdeMenu(){
  document.getElementById("adjuntos_menu").style.display = "none";
  window.removeEventListener('click', closeMenuOnClickOutside);
  toggleDictado();
}

function verHistorial(){
  fetch("/historial/"+usuario_id).then(r=>r.json()).then(data=>{
    document.getElementById("chat").innerHTML="";
    if(data.length===0){agregar("No hay historial todavía.","ai");return;}
    data.slice(-20).forEach(e=>{ agregar(`<small>${e.fecha}</small><br>${e.usuario}`,"user"); agregar(`<small>${e.fecha}</small><br>${e.foschi}`,"ai"); });
  });
}

function borrarPantalla(){
    detenerVoz(); 
    document.getElementById("chat").innerHTML = ""; 
}

function openAuth() {
  document.getElementById("authModal").style.display = "block";
}

function closeAuth() {
  document.getElementById("authModal").style.display = "none";
}

async function login() {
  const email = authEmail.value;
  const password = authPassword.value;

  const r = await fetch("/auth/login", {
    method: "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify({email, password})
  });

  const j = await r.json();
  if (j.ok) location.reload();
  else authMsg.innerText = j.msg;
}

async function register() {
  const email = authEmail.value;
  const password = authPassword.value;

  const r = await fetch("/auth/register", {
    method: "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify({email, password})
  });

  const j = await r.json();
  if (j.ok) location.reload();
  else authMsg.innerText = j.msg;
}

function hablar(){
  if('webkitSpeechRecognition' in window || 'SpeechRecognition' in window){

    const Rec = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new Rec();

    recognition.lang='es-AR';
    recognition.continuous=false;
    recognition.interimResults=false;

    recognition.onresult = function(event){

      let textoReconocido = event.results[0][0].transcript;
      let txt = textoReconocido.toLowerCase();

      // 👉 COMANDOS DE VOZ PARA DICTADO PREMIUM
      if(txt.includes("activar dictado")){
        iniciarDictado();
        return;
      }

      if(txt.includes("desactivar dictado")){
        detenerDictado();
        return;
      }

      // 👉 comportamiento normal
      document.getElementById("mensaje").value = txt;
      checkDailyLimit();
    };

    recognition.onerror = function(e){
      console.log(e);
      alert("Error reconocimiento de voz: " + e.error);
    }

    recognition.start();

  }else{
    alert("Tu navegador no soporta reconocimiento de voz.");
  }
}

function chequearRecordatorios(){
  fetch("/avisos",{ method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({usuario_id}) })
  .then(r=>r.json()).then(data=>{ if(Array.isArray(data) && data.length>0){ data.forEach(r=>{ agregar(`⏰ Tenés un recordatorio: ${r.motivo||"(sin motivo)"}`,"ai"); }); } }).catch(e=>console.error(e));
}
setInterval(chequearRecordatorios,10000);

/* --- SALUDO INICIAL --- */
window.onload = function() {
    agregar("👋 ¡Hola! Bienvenido a Foschi IA","ai");
    let saludoAudio = new Audio("/tts?texto=👋 ¡Hola! Bienvenido a Foschi IA");
    saludoAudio.playbackRate = 1.25;
    saludoAudio.play();
};
/* =============================== */
/* === BOTÓN MODO DAY / NIGHT ==== */
/* =============================== */
function toggleDayNight(){
  const body = document.body;
  body.classList.toggle("day");

  const btn = document.getElementById("dayNightBtn");
  if(btn){
    btn.textContent = body.classList.contains("day") ? "☀️" : "🌙";
  }
}
// =====================
// 🎤 DICTADO PRO
// =====================

let dictadoActivo = false;
let dictadoPausado = false;
let reconocimiento = null;
let textoDictado = localStorage.getItem("dictado_guardado") || "";
let ultimoTexto = "";
let reinicioDictado = false;

// Crea el panel de previsualización una sola vez
function getPanelDictado(){
  let p = document.getElementById("dictadoPanel");
  if(!p){
    p = document.createElement("div");
    p.id = "dictadoPanel";
    document.body.appendChild(p);
  }
  return p;
}

// Refresca lo que se ve en el panel:
// texto confirmado (blanco) + lo que se está diciendo ahora (gris)
function actualizarPanel(parcial){
  const panel = getPanelDictado();
  const enCurso = parcial
    ? '<span style="color:#888">' + parcial + '</span>'
    : "";
  panel.innerHTML = textoDictado + enCurso;
  panel.scrollTop = panel.scrollHeight;
}

function _resetUI(){
  document.getElementById("dictadoEstado").style.display = "none";
  document.getElementById("clipBtn").style.display = "flex";
  document.getElementById("botonesNormales").style.display = "flex";
  document.getElementById("botonesDictado").style.display = "none";
  document.getElementById("mensaje").value = "";
  document.getElementById("mensaje").placeholder = "Escribí tu mensaje o hablá";
  const panel = getPanelDictado();
  panel.style.display = "none";
  panel.innerHTML = "";
}

function toggleDictado(){
  if(!isPremium && !isSuper){
    alert("🔒 Esta función es solo Premium");
    return;
  }
  if(!dictadoActivo){ iniciarDictado(); return; }
  if(dictadoActivo && !dictadoPausado){ pausarDictado(); return; }
  if(dictadoActivo && dictadoPausado){ continuarDictado(); }
}

function iniciarDictado(){

  const SpeechRecognition =
    window.SpeechRecognition || window.webkitSpeechRecognition;

  if(!SpeechRecognition){
    alert("Tu navegador no soporta dictado");
    return;
  }

  reconocimiento = new SpeechRecognition();
  reconocimiento.lang = "es-AR";
  reconocimiento.continuous = true;
  reconocimiento.interimResults = true;
  reconocimiento.maxAlternatives = 1;

  dictadoActivo = true;
  dictadoPausado = false;
  reinicioDictado = true;
  if(!textoDictado) textoDictado = "";
  ultimoTexto = "";

  // UI: estado visible, clip+botones normales ocultos, botones dictado visibles
  document.getElementById("dictadoEstado").style.display = "block";
  document.getElementById("dictadoEstado").innerText = "🎤 Dictando...";
  document.getElementById("clipBtn").style.display = "none";
  document.getElementById("botonesNormales").style.display = "none";
  document.getElementById("botonesDictado").style.display = "flex";
  document.getElementById("adjuntos_menu").style.display = "none";
  document.getElementById("dictadoBtn").classList.add("activo");
  document.getElementById("dictadoBtn").innerText = "⏸️ Pausar";

  // Mostrar panel y limpiar input
  const panel = getPanelDictado();
  panel.style.display = "block";
  actualizarPanel("");
  document.getElementById("mensaje").value = "";
  document.getElementById("mensaje").placeholder = "🎤 Dictando...";

 reconocimiento.onresult = function(event){

    let parcial = "";

    for(let i = event.resultIndex; i < event.results.length; i++){

      let trans = event.results[i][0].transcript.trim();

      if(!trans) continue;

      let txt = trans.toLowerCase();

      // ============================
      // 🗑️ BORRAR PALABRAS
      // ============================

      // borrar eso
if(
  txt.includes("borrar eso") ||
  txt.includes("borrar esa palabra")
){

  let palabras = textoDictado.trim().split(" ");

  palabras.pop();

  textoDictado =
    palabras.join(" ").trim() + " ";

  localStorage.setItem(
    "dictado_guardado",
    textoDictado
  );

  document.getElementById("mensaje").value =
    textoDictado.trim();

  return;
}

// ============================
// 🗑️ BORRAR X PALABRAS
// ============================

if(
  txt.includes("borrar") &&
  txt.includes("palabras")
){

  let numero = 1;

  // números escritos
  if(txt.includes("dos")) numero = 2;
  else if(txt.includes("tres")) numero = 3;
  else if(txt.includes("cuatro")) numero = 4;
  else if(txt.includes("cinco")) numero = 5;
  else if(txt.includes("seis")) numero = 6;
  else if(txt.includes("siete")) numero = 7;
  else if(txt.includes("ocho")) numero = 8;
  else if(txt.includes("nueve")) numero = 9;
  else if(txt.includes("diez")) numero = 10;

  // números normales
  let match = txt.match(/\d+/);

  if(match){
    numero = parseInt(match[0]);
  }

  let palabras = textoDictado.trim().split(/\s+/);

palabras.splice(-numero);

textoDictado =
  palabras.join(" ").trim() + " ";

localStorage.setItem(
  "dictado_guardado",
  textoDictado
);

document.getElementById("mensaje").value =
  textoDictado.trim();

return;

      // ============================
      // 🎤 COMANDOS DE VOZ
      // ============================

      if(txt.includes("pausar dictado"))   {
        pausarDictado();
        return;
      }

      if(txt.includes("continuar dictado")){
        continuarDictado();
        return;
      }

      if(txt.includes("finalizar dictado")){
        finalizarDictado();
        return;
      }

      if(
        txt.includes("cancelar dictado") ||
        txt.includes("borrar dictado") ||
        txt.includes("borrar todo")
      ){
        cancelarDictado();
        return;
      }

      trans = mejorarTextoDictado(trans);

      if(event.results[i].isFinal){

        // Evitar duplicado del último fragmento final
        if(trans !== ultimoTexto){

          ultimoTexto = trans;

          textoDictado += trans + " ";

          localStorage.setItem(
            "dictado_guardado",
            textoDictado
          );
        }

      } else {

        parcial += trans + " ";
      }
    }

    // Refrescar panel con acumulado + parcial en gris
    actualizarPanel(parcial);

    // El input solo muestra conteo para no distraer
    const palabras = textoDictado.trim().split(/\s+/).filter(Boolean).length;
    document.getElementById("mensaje").placeholder =
      "🎤 " + palabras + " palabra" + (palabras !== 1 ? "s" : "") + " dictada" + (palabras !== 1 ? "s" : "");
  };

  reconocimiento.onerror = function(e){
    console.log("Error dictado:", e.error);
    if(e.error === "not-allowed"){
      alert("Micrófono bloqueado");
      finalizarDictado();
    }
  };

  reconocimiento.onend = function(){
    if(dictadoActivo && !dictadoPausado && reinicioDictado){
      try{ reconocimiento.start(); }catch(err){ console.log("Reinicio:", err); }
    }
  };

  reconocimiento.start();
}

function pausarDictado(){
  dictadoPausado = true;
  if(reconocimiento){ reinicioDictado = false; reconocimiento.stop(); }
  document.getElementById("dictadoEstado").innerText = "⏸️ Dictado pausado";
  document.getElementById("dictadoBtn").innerText = "▶️ Continuar";
}

function continuarDictado(){
  if(!dictadoActivo) return;
  dictadoPausado = false;
  reinicioDictado = true;
  try{ reconocimiento.start(); }catch(err){ console.log("Continuar:", err); }
  document.getElementById("dictadoEstado").innerText = "🎤 Dictando...";
  document.getElementById("dictadoBtn").innerText = "⏸️ Pausar";
}

function finalizarDictado(){
  dictadoActivo = false;
  dictadoPausado = false;
  reinicioDictado = false;

  if(reconocimiento){ reconocimiento.stop(); reconocimiento = null; }

  // ⚠️ Guardar el texto ANTES de limpiar las variables
  const textoFinal = textoDictado.trim();
  textoDictado = "";
  ultimoTexto = "";
  localStorage.removeItem("dictado_guardado");

  _resetUI();

  if(textoFinal.length > 0){
    descargarWordDictado(textoFinal);
  } else {
    alert("No hay texto para guardar");
  }
}

function finalizarDictadoManual(){
  if(!textoDictado.trim()){ alert("No hay texto para guardar"); return; }
  finalizarDictado();
}

function detenerDictado(){ finalizarDictado(); }

function cancelarDictado(){
  if(reconocimiento){ reconocimiento.stop(); }
  dictadoActivo = false;
  dictadoPausado = false;
  reinicioDictado = false;
  textoDictado = "";
  ultimoTexto = "";
  localStorage.removeItem("dictado_guardado");
  _resetUI();
  agregar("🗑️ Dictado cancelado", "ai");
}

// =====================
// MEJORADOR DE TEXTO
// =====================

function mejorarTextoDictado(texto){

  texto = texto.trim();

  // =========================
  // PUNTUACIÓN
  // =========================

  texto = texto.replace(/\scoma\s/gi, ", ");
  texto = texto.replace(/\spunto y coma\s/gi, "; ");
  texto = texto.replace(/\sdos puntos\s/gi, ": ");
  texto = texto.replace(/\spunto aparte\s/gi, ". <br><br> ");
  texto = texto.replace(/\spunto seguido\s/gi, ". ");
  texto = texto.replace(/\spunto\s/gi, ". ");

  // =========================
  // PREGUNTAS
  // =========================

  texto = texto.replace(/\sabrir pregunta\s/gi, " ¿");
  texto = texto.replace(/\scerrar pregunta\s/gi, "? ");

  // =========================
  // ADMIRACIÓN
  // =========================

  texto = texto.replace(/\sabrir admiración\s/gi, " ¡");
  texto = texto.replace(/\scerrar admiración\s/gi, "! ");

  // =========================
  // PARÉNTESIS
  // =========================

  texto = texto.replace(/\sabrir paréntesis\s/gi, " (");
  texto = texto.replace(/\scerrar paréntesis\s/gi, ") ");

  // =========================
  // NUEVO PÁRRAFO
  // =========================

  texto = texto.replace(/\snuevo párrafo\s/gi, " <br><br> ");

  // =========================
  // ELIMINAR ESPACIOS DOBLES
  // =========================

  texto = texto.replace(/\s{2,}/g, " ");

// =========================
// MAYÚSCULAS INTELIGENTES
// =========================

// Solo usar mayúscula:
// 1. al inicio real
// 2. después de punto
// 3. después de ? o !

if(
  textoDictado.trim() === "" ||
  /[.!?]\s*$/.test(textoDictado.trim())
){

  texto =
    texto.charAt(0).toUpperCase() +
    texto.slice(1);

}

  // =========================
  // MAYÚSCULA DESPUÉS DE PUNTO
  // =========================

  texto = texto.replace(/([.!?]\s*)([a-z])/gi,
    function(match, p1, p2){
      return p1 + p2.toUpperCase();
    }
  );

  return texto;
}

async function descargarWordDictado(texto){

  try{

    const r = await fetch("/dictado_word",{
      method:"POST",
      headers:{
        "Content-Type":"application/json"
      },
      body:JSON.stringify({
        texto:texto
      })
    });

    if(!r.ok){

      let errorTexto = await r.text();

      console.log(errorTexto);

      alert("Error generando Word");

      return;
    }

    const blob = await r.blob();

    const url =
      window.URL.createObjectURL(blob);

    const a = document.createElement("a");

    a.href = url;

    a.download =
      "dictado_foschi.docx";

    document.body.appendChild(a);

    a.click();

    a.remove();

    window.URL.revokeObjectURL(url);

    // ✅ LIMPIAR SOLO DESPUÉS
    localStorage.removeItem(
      "dictado_guardado"
    );

  }catch(err){

    console.log(err);

    alert("Error descargando Word");
  }
}

// ===============================
// 🎵 AUDIO A TEXTO (WORD)
// ===============================

document.getElementById("audioInput")
.addEventListener("change", async function(e){

  const file = e.target.files[0];
  if(!file) return;

  agregar("🎵 Transcribiendo audio, esperá un momento...","ai");

  let formData = new FormData();
  formData.append("audio", file);
  formData.append("usuario_id", usuario_id);

  try{

    const r = await fetch("/upload_audio",{
      method:"POST",
      body:formData
    });

    if(!r.ok){
      let txt = await r.text();
      agregar("❌ Error en transcripción: " + txt, "ai");
      e.target.value = "";
      return;
    }

    const blob = await r.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = file.name.replace(/\.[^.]+$/, "") + "_transcripcion.docx";
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);

    agregar("✅ Transcripción lista. Se descargó el Word con el texto.", "ai");

  }catch(err){
    console.log(err);
    agregar("❌ Error procesando el audio.", "ai");
  }

  e.target.value = ""; // reset para poder subir el mismo archivo de nuevo

});

// ===============================
// 📄 SUBIR PDF / WORD
// ===============================

document.getElementById("archivo_pdf_word")
.addEventListener("change", async function(e){

  const file = e.target.files[0];

  if(!file) return;

  agregar("📄 Subiendo documento...","ai");

  let formData = new FormData();

  formData.append("archivo", file);
  formData.append("usuario_id", usuario_id);

  try{

    const r = await fetch("/upload_doc",{
      method:"POST",
      body:formData
    });

    if(!r.ok){
      let txt = await r.text();
      agregar("❌ Error: " + txt,"ai");
      return;
    }

    const data = await r.json();

    documentoActual = data.doc_id;
    textoDocumento = data.snippet || "";

    agregar(
      `✅ Documento cargado: ${data.name}
      <br><br>
      📌 Elegí una opción:
      <br><br>
      <button onclick="resumirDocumento('breve')">📄 Resumen breve</button>
      <button onclick="resumirDocumento('normal')">📘 Resumen normal</button>
      <button onclick="resumirDocumento('profundo')">📚 Resumen profundo</button>
      <button onclick="activarPreguntasDocumento()">❓ Preguntar al documento</button>
      `,
      "ai"
    );

  }catch(err){

    console.log(err);

    agregar(
      "❌ Error subiendo documento",
      "ai"
    );
  }

});

// ===============================
// 📘 RESUMIR DOCUMENTO
// ===============================

async function resumirDocumento(tipo){

  if(!documentoActual){
    agregar("❌ No hay documento cargado","ai");
    return;
  }

  agregar("🧠 Generando resumen...","ai");

  try{

    const r = await fetch("/resumir_doc",{
      method:"POST",
      headers:{
        "Content-Type":"application/json"
      },
      body:JSON.stringify({
        doc_id: documentoActual,
        modo: tipo,
        usuario_id: usuario_id
      })
    });

    if(!r.ok){

      let txt = await r.text();

      agregar("❌ Error: " + txt,"ai");

      return;
    }

    const blob = await r.blob();

    const url = window.URL.createObjectURL(blob);

    const a = document.createElement("a");

    a.href = url;

    a.download = "resumen_foschi.docx";

    document.body.appendChild(a);

    a.click();

    a.remove();

    agregar("✅ Resumen generado","ai");

  }catch(err){

    console.log(err);

    agregar("❌ Error generando resumen","ai");
  }
}

// ===============================
// ❓ PREGUNTAS SOBRE DOCUMENTO
// ===============================

let modoPreguntasDocumento = false;

function activarPreguntasDocumento(){

  modoPreguntasDocumento = true;

  agregar(
    "📄 Modo documento ACTIVADO. Ahora podés hacer preguntas sobre el archivo.",
    "ai"
  );

  // ============================
  // CREAR BOTÓN FLOTANTE
  // ============================

  if(!document.getElementById("btnSalirDocumento")){

    let btn = document.createElement("button");

    btn.id = "btnSalirDocumento";

    btn.innerHTML = "❌ Salir del documento";

    btn.onclick = salirModoDocumento;

    btn.style.position = "fixed";

    btn.style.bottom = "90px";

    btn.style.right = "20px";

    btn.style.zIndex = "9999";

    btn.style.padding = "12px 18px";

    btn.style.borderRadius = "14px";

    btn.style.border = "none";

    btn.style.cursor = "pointer";

    btn.style.fontWeight = "bold";

    btn.style.background = "#ff0033";

    btn.style.color = "white";

    btn.style.boxShadow = "0 0 15px rgba(255,0,0,0.5)";

    document.body.appendChild(btn);
  }
}

function salirModoDocumento(){

  modoPreguntasDocumento = false;

  documentoActual = null;

  textoDocumento = "";

  let btn = document.getElementById("btnSalirDocumento");

  if(btn){
    btn.remove();
  }

  agregar(
    "✅ Saliste del modo documento. Foschi IA volvió al modo normal.",
    "ai"
  );
}
</script>

<div id="authModal" style="display:none; position:fixed; inset:0; background:rgba(0,0,0,.85); z-index:9999;">
  <div style="max-width:360px; margin:10% auto; background:#001d3d; padding:20px; border-radius:12px; color:#00eaff;">
    
    <h3>Ingresar</h3>

    <div class="form-premium">

      <input id="authEmail" type="email" placeholder="Email">

      <input id="authPassword" type="password" placeholder="Contraseña">

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

# ---------------- RUTAS ----------------
import mercadopago

sdk = mercadopago.SDK(os.getenv("MP_ACCESS_TOKEN"))

@app.route("/auth/register", methods=["POST"])
def register():
    data = request.get_json()

    email = data.get("email", "").lower().strip()
    password = data.get("password", "")

    ok, msg = registrar_usuario(email, password)
    if not ok:
        return jsonify({"ok": False, "msg": msg})

    # login automático
    session["user_email"] = email
    return jsonify({"ok": True})

@app.route("/auth/login", methods=["POST"])
def login():
    data = request.get_json()

    email = data.get("email", "").lower().strip()
    password = data.get("password", "")

    if not autenticar_usuario(email, password):
        return jsonify({"ok": False, "msg": "Credenciales incorrectas"})

    session["user_email"] = email
    return jsonify({"ok": True})

@app.route("/auth/logout")
def logout():
    session.pop("user_email", None)
    return redirect("/")

@app.route("/premium")
def premium():

    # 1️⃣ Verificar login
    usuario = session.get("user_email")
    if not usuario:
        return jsonify({"error": "No logueado"}), 401

    # 2️⃣ Determinar tipo de plan
    tipo = request.args.get("tipo", "mensual")

    if tipo == "anual":
        titulo = "Foschi IA Premium Anual (12 meses PAGA 10)"
        precio = 100000   # 🔥 10 meses pagos
    else:
        titulo = "Foschi IA Premium Mensual"
        precio = 10000

    # 3️⃣ Crear preferencia MercadoPago
    pref = {
        "items": [{
            "title": titulo,
            "quantity": 1,
            "unit_price": precio
        }],
        "external_reference": usuario,
        "notification_url": "https://foschi-ia.onrender.com/webhook/mp"
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
    info = payment.get("response", {})

    # 🔐 VALIDAR QUE EL PAGO SEA TUYO
    if info.get("merchant_account_id") != os.getenv("MP_MERCHANT_ID"):
        return "ok"

    if info.get("status") != "approved":
        return "ok"

    usuario = info.get("external_reference")
    if not usuario:
        return "ok"

    from pagos import pago_ya_registrado, registrar_pago
    if pago_ya_registrado(str(payment_id)):
        return "ok"

    items = info.get("additional_info", {}).get("items", [])
    titulo = items[0]["title"] if items else ""
    plan = "anual" if "12" in titulo or "Anual" in titulo else "mensual"

    monto = info.get("transaction_amount", 0)

    activar_premium(usuario, plan)

    registrar_pago(
        usuario=usuario,
        monto=monto,
        plan=plan,
        payment_id=str(payment_id)
    )

    return "ok"

@app.route("/")
def index():
    if "usuario_id" not in session:
        session["usuario_id"] = str(uuid.uuid4())

    usuario = session.get("user_email") or session["usuario_id"]

    premium = usuario_premium(usuario)

    is_super = es_superusuario(usuario)
    rol = rol_superusuario(usuario)
    nivel = nivel_superusuario(usuario)

    return render_template_string(
        HTML_TEMPLATE,
        APP_NAME=APP_NAME,
        usuario_id=usuario,
        premium=premium,
        is_super=is_super,
        rol=rol,
        nivel=nivel
    )

@app.route("/preguntar", methods=["POST"])
def preguntar():

    data = request.get_json()

    mensaje = data.get("mensaje", "")

    doc_id = data.get("doc_id")

    preguntar_doc = data.get("preguntar_doc", False)
    
    # 1️⃣ Asegurar UUID en sesión (NO se borra nunca)
    if "usuario_id" not in session:
        session["usuario_id"] = str(uuid.uuid4())

    # 2️⃣ Identidad activa:
    #    email si está logueado
    #    UUID si no
    usuario = session.get("user_email") or session["usuario_id"]

    lat = data.get("lat")
    lon = data.get("lon")
    tz  = data.get("timeZone") or data.get("time_zone") or None

     # ============================
    # 📄 PREGUNTAS SOBRE DOCUMENTO
    # ============================

    if preguntar_doc and doc_id:

        txt_path = os.path.join(TEMP_DIR, f"{doc_id}.txt")

        if os.path.exists(txt_path):

            with open(txt_path, "r", encoding="utf-8") as f:
                contenido_doc = f.read()

            try:

                client = OpenAI(api_key=OPENAI_API_KEY)

                prompt = f"""
Sos Foschi IA.

Respondé usando SOLAMENTE el contenido del documento.

DOCUMENTO:
{contenido_doc[:12000]}

PREGUNTA:
{mensaje}
"""

                resp = client.chat.completions.create(
                    model="gpt-4-turbo",
                    messages=[
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.2,
                    max_tokens=700
                )

                texto = resp.choices[0].message.content.strip()

                return jsonify({
                    "texto": texto,
                    "imagenes": [],
                    "borrar_historial": False
                })

            except Exception as e:

                return jsonify({
                    "texto": f"Error analizando documento: {e}",
                    "imagenes": [],
                    "borrar_historial": False
                })

    # 3️⃣ Generar respuesta con identidad correcta
    respuesta = generar_respuesta(
        mensaje,
        usuario,
        lat=lat,
        lon=lon,
        tz=tz
    )

    # 4️⃣ Guardar historial con la MISMA identidad
    texto_para_hist = (
        respuesta["texto"]
        if isinstance(respuesta, dict) and "texto" in respuesta
        else str(respuesta)
    )

    guardar_en_historial(usuario, mensaje, texto_para_hist)

    return jsonify(respuesta)

@app.route("/historial/<usuario_id>")
def historial(usuario_id):
    return jsonify(cargar_historial(usuario_id))

@app.route("/tts")
def tts():
    texto = request.args.get("texto","")
    try:
        tts_obj = gTTS(text=texto, lang="es", slow=False, tld="com.mx")
        archivo = io.BytesIO()
        tts_obj.write_to_fp(archivo)
        archivo.seek(0)
        return send_file(archivo, mimetype="audio/mpeg")
    except Exception as e:
        return f"Error TTS: {e}", 500

@app.route("/clima")
def clima():
    lat = request.args.get("lat")
    lon = request.args.get("lon")
    ciudad = request.args.get("ciudad")
    return obtener_clima(ciudad=ciudad, lat=lat, lon=lon)

@app.route('/favicon.ico')
def favicon():
    ico = os.path.join(STATIC_DIR, 'favicon.ico')
    if os.path.exists(ico):
        return send_file(ico)
    return "", 204

@app.route("/avisos", methods=["POST"])
def avisos():
    usuario = request.json.get("usuario_id", "anon")
    lista = load_recordatorios()
    ahora = datetime.now(TZ)
    vencidos = []
    restantes = []
    for r in lista:
        when = TZ.localize(datetime.strptime(r["cuando"], "%Y-%m-%d %H:%M:%S"))
        if when <= ahora and r["usuario"] == usuario:
            vencidos.append(r)
        else:
            restantes.append(r)
    save_recordatorios(restantes)
    return jsonify(vencidos)

@app.route("/admin/pagos")
def admin_pagos():
    import json, os

    # 🔐 clave simple (después se mejora)
    if request.args.get("key") != "foschi_admin_2026":
        return "Acceso denegado", 403

    archivo = "data/pagos.json"
    if not os.path.exists(archivo):
        return "<h2>No hay pagos todavía</h2>"

    pagos = json.load(open(archivo))

    html = """
    <h2>💎 Pagos Foschi IA</h2>
    <table border="1" cellpadding="8">
      <tr>
        <th>Usuario</th>
        <th>Plan</th>
        <th>Fecha</th>
        <th>Payment ID</th>
        <th>Status</th>
      </tr>
    """

    for u, p in pagos.items():
        html += f"""
        <tr>
          <td>{u}</td>
          <td>{p['plan']}</td>
          <td>{p['fecha']}</td>
          <td>{p['payment_id']}</td>
          <td>{p['status']}</td>
        </tr>
        """

    html += "</table>"
    return html

# ---------------- AUDIO A WORD DOCX ----------------
from werkzeug.utils import secure_filename

@app.route("/upload_audio", methods=["POST"])
def upload_audio():
    if "audio" not in request.files:
        return "No se envió archivo", 400
    
    file = request.files["audio"]
    usuario_id = request.form.get("usuario_id", "anon")

    # Guardar archivo temporal
    filename = secure_filename(file.filename)
    if not filename:
        return "Nombre de archivo inválido", 400
    temp_path = os.path.join("temp", f"{uuid.uuid4()}_{filename}")
    os.makedirs("temp", exist_ok=True)
    file.save(temp_path)

    docx_path = None  # PREVENIR ERROR EN finally

    try:
        # ---- TRANSCRIPCIÓN OPENAI ----
        with open(temp_path, "rb") as f:
            transcript = client.audio.transcriptions.create(
                model="gpt-4o-transcribe",
                file=f,
            )

        texto_transcrito = transcript.text if hasattr(transcript, "text") else str(transcript)

        # ---- CREAR DOCX ----
        nombre_docx = filename.rsplit(".", 1)[0] + ".docx"
        docx_path = os.path.join("temp", nombre_docx)

        doc = DocxDocument()
        doc.add_heading("Transcripción de audio", level=1)
        doc.add_paragraph(texto_transcrito)
        doc.add_page_break()
        doc.save(docx_path)

        # --- programar limpieza después de responder ---
        @after_this_request
        def _cleanup(response):
            try:
                if os.path.exists(docx_path):
                    os.remove(docx_path)
            except Exception:
                pass
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            except Exception:
                pass
            return response

        # ---- ENVIAR DOCX ----
        return send_file(
            docx_path,
            as_attachment=True,
            mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            download_name=nombre_docx
        )

    except Exception as e:
        # intentar limpiar si algo quedó
        try:
            if docx_path and os.path.exists(docx_path):
                os.remove(docx_path)
        except:
            pass
        try:
            if os.path.exists(temp_path):
                os.remove(temp_path)
        except:
            pass
        return f"Error en transcripción: {str(e)}", 500

# ---------------- NUEVOS ENDPOINTS: subir documento (extraer texto) y resumir (crear .docx) ----------------
def extract_text_from_pdf(path):
    text = ""
    try:
        with open(path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                try:
                    p = page.extract_text()
                    if p:
                        text += p + "\n"
                except:
                    continue
    except Exception as e:
        print("Error leyendo PDF:", e)
    return text

def extract_text_from_docx(path):
    text = ""
    try:
        doc = docx_reader.Document(path)
        for p in doc.paragraphs:
            if p.text:
                text += p.text + "\n"
    except Exception as e:
        print("Error leyendo DOCX:", e)
    return text

@app.route("/upload_doc", methods=["POST"])
def upload_doc():
    """Recibe PDF o DOCX, extrae texto y guarda temporalmente. Devuelve doc_id que luego se usa para pedir resumen."""
    if "archivo" not in request.files:
        return "No se envió archivo", 400
    file = request.files["archivo"]
    usuario_id = request.form.get("usuario_id", "anon")
    filename = secure_filename(file.filename)
    if filename == "":
        return "Archivo sin nombre", 400
    ext = filename.rsplit(".",1)[-1].lower()
    if ext not in ["pdf", "docx"]:
        return "Formato no permitido. Solo PDF o DOCX.", 400

    doc_id = str(uuid.uuid4())
    saved_name = f"{doc_id}_{filename}"
    temp_path = os.path.join(TEMP_DIR, saved_name)
    try:
        file.save(temp_path)
    except Exception as e:
        return f"Error guardando archivo temporal: {e}", 500

    # extraer texto
    if ext == "pdf":
        text = extract_text_from_pdf(temp_path)
    else:
        text = extract_text_from_docx(temp_path)

    if not text or len(text.strip()) == 0:
        # limpiar archivo
        try:
            os.remove(temp_path)
        except:
            pass
        return "No pude extraer texto del documento.", 400

    # guardar texto en fichero temporal .txt
    txt_path = os.path.join(TEMP_DIR, f"{doc_id}.txt")
    try:
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(text)
    except Exception as e:
        # limpiar archivo original
        try:
            os.remove(temp_path)
        except:
            pass
        return f"Error guardando texto temporal: {e}", 500

    # devolvemos doc_id y un snippet para mostrar
    snippet = text[:800].replace("\n"," ") + ("..." if len(text)>800 else "")
    return jsonify({"doc_id": doc_id, "name": filename, "snippet": snippet})

@app.route("/resumir_doc", methods=["POST"])
def resumir_doc():

    data = request.get_json()

    doc_id = data.get("doc_id")

    modo = data.get("modo", "normal")

    txt_path = os.path.join(TEMP_DIR, f"{doc_id}.txt")

    if not os.path.exists(txt_path):
        return "Documento no encontrado", 404

    with open(txt_path, "r", encoding="utf-8") as f:
        texto = f.read()

    # ============================
    # TIPOS DE RESUMEN
    # ============================

    if modo == "breve":

        instrucciones = (
            "Hacé un resumen breve y directo "
            "del siguiente documento."
        )

    elif modo == "profundo":

        instrucciones = (
            "Hacé un resumen MUY detallado "
            "del siguiente documento. "
            "Separá por temas y explicá bien."
        )

    else:

        instrucciones = (
            "Resumí el siguiente texto "
            "de forma clara, ordenada y completa. "
            "Usá títulos y viñetas si hace falta."
        )

    # ============================
    # GENERAR RESUMEN IA
    # ============================

    try:

        client = OpenAI(api_key=OPENAI_API_KEY)

        prompt = f"""
{instrucciones}

TEXTO:
{texto[:15000]}
"""

        resp = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.4,
            max_tokens=1500
        )

        resumen = resp.choices[0].message.content.strip()

    except Exception as e:

        return f"Error generando resumen: {e}", 500

    # ============================
    # CREAR WORD
    # ============================

    nombre_doc = f"resumen_{doc_id}.docx"

    ruta_doc = os.path.join(TEMP_DIR, nombre_doc)

    doc = DocxDocument()

    doc.add_heading(
        "Resumen generado por Foschi IA",
        level=1
    )

    doc.add_paragraph(resumen)

    doc.save(ruta_doc)

    @after_this_request
    def cleanup(response):

        try:

            if os.path.exists(ruta_doc):
                os.remove(ruta_doc)

        except:
            pass

        return response

    return send_file(
        ruta_doc,
        as_attachment=True,
        download_name="resumen_foschi.docx"
    )

# ---------------- RUN ----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)