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
    data = request.json
    texto = data.get("texto", "").strip()

    if not texto:
        return jsonify({"ok": False, "error": "Texto vacío"})

    nombre = f"dictado_{uuid.uuid4().hex}.docx"
    ruta = os.path.join(TEMP_DIR, nombre)

    doc = DocxDocument()
    doc.add_heading("Dictado Foschi IA", 0)
    doc.add_paragraph(texto)

    doc.save(ruta)

    @after_this_request
    def remove_file(response):
        try:
            os.remove(ruta)
        except:
            pass
        return response

    return send_file(ruta, as_attachment=True)

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

/* --- MENÚ DE ADJUNTOS --- */
#adjuntos_menu{
 position:absolute;
 left:0;
 bottom:50px;   /* se abre hacia arriba del clip */
 display:none;
 background:#001f2e;
 border:1px solid #003547;
 padding:8px;
 border-radius:8px;
 box-shadow:0 6px 16px rgba(0,0,0,0.6);
 z-index:999;
 max-width:90vw;   /* evita que se corte en móviles */
}
#adjuntos_menu button{ display:block; width:160px; margin:6px; text-align:left; }
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
<!-- BARRA DE ENTRADA -->
<div id="inputBar">
  <div style="position:relative;">
    <div id="clipBtn" title="Adjuntar" onclick="toggleAdjuntosMenu()">📎</div>
    <div id="adjuntos_menu" aria-hidden="true">
  <button onclick="checkPremium('audio')">🎵 Audio (mp3/wav) a Texto</button>
  <button onclick="checkPremium('doc')">📄 Resumir PDF / WORD</button>
  <button onclick="toggleDictado()">🎤 Dictado por voz</button>
</div>
  </div>
  <input id="audioInput" class="hidden_file_input" type="file" accept=".mp3,audio/*,.wav" />
  <input id="archivo_pdf_word" class="hidden_file_input" type="file" accept=".pdf,.docx" />
  <input type="text" id="mensaje" placeholder="Escribí tu mensaje o hablá" />
  <button onclick="checkDailyLimit()">Enviar</button>
  <button onclick="hablar()">🎤 Hablar</button>
</div>

<script>
// --- Variables y funciones generales ---
let usuario_id="{{usuario_id}}";
let vozActiva=true,audioActual=null,mensajeActual=null;
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
  let msg=document.getElementById("mensaje").value.trim(); if(!msg) return;
  agregar(msg,"user"); document.getElementById("mensaje").value="";
  fetch("/preguntar",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({mensaje: msg, usuario_id: usuario_id})})
  .then(r=>r.json()).then(data=>{ agregar(data.texto,"ai",data.imagenes); if(data.borrar_historial){document.getElementById("chat").innerHTML="";} })
  .catch(e=>{ agregar("Error al comunicarse con el servidor.","ai"); console.error(e); });
}

document.getElementById("mensaje").addEventListener("keydown",e=>{ if(e.key==="Enter"){ e.preventDefault(); checkDailyLimit(); } });

function hablarTexto(texto, div=null){
  if(!vozActiva) return;
  detenerVoz();
  if(mensajeActual) mensajeActual.classList.remove("playing");
  if(div) div.classList.add("playing");
  mensajeActual = div;
  audioActual = new Audio("/tts?texto=" + encodeURIComponent(texto));
  audioActual.playbackRate = 1.25;
  audioActual.onended = () => { if(mensajeActual) mensajeActual.classList.remove("playing"); mensajeActual = null; };
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
// 🎤 DICTADO PREMIUM
// =====================
let dictadoActivo = false;
let reconocimiento = null;
let textoDictado = "";

function toggleDictado(){
  if(!isPremium && !isSuper){
    alert("🔒 Esta función es solo Premium");
    return;
  }

  if(dictadoActivo){
    detenerDictado();
  }else{
    iniciarDictado();
  }
}

function iniciarDictado(){
  if(!('webkitSpeechRecognition' in window)){
    alert("Tu navegador no soporta dictado por voz");
    return;
  }

  reconocimiento = new webkitSpeechRecognition();
  reconocimiento.lang = "es-AR";
  reconocimiento.continuous = true;
  reconocimiento.interimResults = true;

  textoDictado = "";
  dictadoActivo = true;

  document.getElementById("dictadoEstado").style.display = "block";

  reconocimiento.onresult = function(event){
    let parcial = "";
    for(let i=event.resultIndex;i<event.results.length;i++){
      let trans = event.results[i][0].transcript;
      if(event.results[i].isFinal){
        textoDictado += trans + " ";
      }else{
        parcial += trans;
      }
    }
    document.getElementById("mensaje").value = textoDictado + parcial;
  };

  reconocimiento.start();
}

function detenerDictado(){
  dictadoActivo = false;

  if(reconocimiento){
    reconocimiento.stop();
    reconocimiento = null;
  }

  document.getElementById("dictadoEstado").style.display = "none";

  if(textoDictado.trim().length > 0){
    descargarWordDictado(textoDictado);
  }
}

function descargarWordDictado(texto){
  fetch("/dictado_word",{
    method:"POST",
    headers:{"Content-Type":"application/json"},
    body: JSON.stringify({texto: texto})
  })
  .then(r=>r.blob())
  .then(blob=>{
    let url = window.URL.createObjectURL(blob);
    let a = document.createElement("a");
    a.href = url;
    a.download = "dictado_foschi.docx";
    a.click();
  });
}
</script>

<div id="authModal" style="display:none; position:fixed; inset:0; background:rgba(0,0,0,.85); z-index:9999;">
  <div style="max-width:360px; margin:10% auto; background:#001d3d; padding:20px; border-radius:12px; color:#00eaff;">
    <h3>Ingresar</h3>

    <input id="authEmail" type="email" placeholder="Email"
      style="width:100%; padding:10px; margin:8px 0;">

    <input id="authPassword" type="password" placeholder="Contraseña"
      style="width:100%; padding:10px; margin:8px 0;">

    <button onclick="login()" style="width:100%; padding:10px;">Ingresar</button>
    <button onclick="register()" style="width:100%; padding:10px; margin-top:6px;">
      Crear cuenta
    </button>

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
    """
    Recibe JSON { doc_id, modo, usuario_id }.
    modo: 'breve', 'normal', 'profundo'
    Devuelve un .docx con el resumen (send_file).
    """
    data = request.get_json() or {}
    doc_id = data.get("doc_id")
    modo = data.get("modo", "normal")
    usuario_id = data.get("usuario_id", "anon")

    if not doc_id:
        return "Falta doc_id", 400
    txt_path = os.path.join(TEMP_DIR, f"{doc_id}.txt")
    # local file original (para eliminar)
    # any temp saved doc name begins with doc_id_
    try:
        if not os.path.exists(txt_path):
            return "Documento temporal no encontrado (subilo nuevamente).", 404
        with open(txt_path, "r", encoding="utf-8") as f:
            texto = f.read()
    except Exception as e:
        return f"Error leyendo texto temporal: {e}", 500

    # construir prompt según modo
    if modo == "breve":
        instrucciones = "Resumí el siguiente texto en 4-6 líneas muy concisas, en español claro y directo, con puntos numerados si aplica."
    elif modo == "profundo":
        instrucciones = "Hacé un resumen detallado del siguiente texto: explicá los puntos clave, sub-puntos, y posibles conclusiones. Usá viñetas y subtítulos cuando corresponda. Mantené un estilo formal y completo."
    else:  # normal
        instrucciones = "Resumí el siguiente texto en puntos claros y ordenados, abarcando las ideas importantes y destacando conclusiones."

    # acotar texto si es muy largo (mejor enviar en trozos o truncar — aquí hacemos truncamiento prudente)
    max_chars = 120000  # límite prudente para no mandar textos enormes (ajustable)
    if len(texto) > max_chars:
        texto_envio = texto[:max_chars] + "\n\n[El documento original fue truncado por tamaño.]\n"
    else:
        texto_envio = texto

    prompt = f"{instrucciones}\n\n--- TEXTO A RESUMIR ---\n\n{texto_envio}"

    # Llamada a OpenAI
    try:
        client_local = OpenAI(api_key=OPENAI_API_KEY)
        resp = client_local.chat.completions.create(
            model="gpt-4-turbo",
            messages=[{"role":"user","content": prompt}],
            temperature=0.3,
            max_tokens=1000
        )
        resumen = resp.choices[0].message.content.strip()
    except Exception as e:
        return f"No pude generar el resumen: {e}", 500

    # Crear DOCX con el resumen
    fecha = datetime.now().strftime("%Y-%m-%d")
    resumen_filename = f"Resumen_{fecha}.docx"
    resumen_path = os.path.join(TEMP_DIR, f"{doc_id}_resumen_{fecha}.docx")
    try:
        doc = DocxDocument()
        doc.add_heading("Resumen del Documento", level=1)
        # agregar texto manteniendo saltos
        for linea in resumen.split("\n"):
            if linea.strip() == "":
                doc.add_paragraph("")  # separador
            else:
                doc.add_paragraph(linea)
        doc.save(resumen_path)
    except Exception as e:
        return f"Error creando archivo Word: {e}", 500

    # programar limpieza después de la respuesta (resumen, txt y originales)
    @after_this_request
    def _cleanup(response):
        try:
            if os.path.exists(resumen_path):
                os.remove(resumen_path)
        except Exception:
            pass
        # eliminar txt temporal
        try:
            if os.path.exists(txt_path):
                os.remove(txt_path)
        except Exception:
            pass
        # eliminar cualquier archivo original que empiece con doc_id_
        try:
            for f in os.listdir(TEMP_DIR):
                if f.startswith(doc_id + "_"):
                    try:
                        os.remove(os.path.join(TEMP_DIR, f))
                    except Exception:
                        pass
        except Exception:
            pass
        return response

    # Enviar el archivo .docx generado
    return send_file(
        resumen_path,
        as_attachment=True,
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        download_name=resumen_filename
    )

# ---------------- RUN ----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)