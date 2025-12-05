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

from flask import Flask, render_template_string, request, jsonify, session, send_file
from flask_session import Session
from gtts import gTTS
import requests
import urllib.parse
from openai import OpenAI

# ---------------- CONFIG ----------------
APP_NAME = "FOSCHI IA WEB"
CREADOR = "Gustavo Enrique Foschi"
DATA_DIR = "data"
STATIC_DIR = "static"
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)

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

# ---------------- RESPUESTA IA ----------------
def generar_respuesta(mensaje, usuario, lat=None, lon=None, tz=None, max_hist=5):
    # Asegurar que mensaje sea str
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
    learn_from_message(usuario, mensaje, texto)
    return {"texto": texto, "imagenes": [], "borrar_historial": False}

HTML_TEMPLATE = """  
<!doctype html>
<html>
<head>
<title>{{APP_NAME}}</title>
<meta name="viewport" content="width=device-width, initial-scale=1">

<style>
body{
 font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
 background:#000814;
 color:#00eaff;
 margin:0;
 padding:0;
 text-shadow:0 0 6px #00eaff;
}

#chat{
 width:100%;
 height:70vh;
 overflow-y:auto;
 padding:10px;
 background: linear-gradient(#00111a,#000814);
 border-top:2px solid #00eaff44;
 border-bottom:2px solid #00eaff44;
 box-shadow: inset 0 0 15px #00eaff55;
}

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

a{
 color:#00eaff;
 text-decoration:underline;
}

img{
 max-width:300px;
 border-radius:10px;
 margin:5px 0;
 box-shadow:0 0 10px #00eaff88;
 border:1px solid #00eaff55;
}

input,button{
 padding:10px;
 font-size:16px;
 margin:5px;
 border:none;
 border-radius:5px;
 outline:none;
}

input[type=text]{
 width:70%;
 background:#00121d;
 color:#00eaff;
 border:1px solid #003344;
 box-shadow:0 0 6px #00eaff55 inset;
}

button{
 background:#001f2e;
 color:#00eaff;
 cursor:pointer;
 border:1px solid #006688;
 text-shadow:0 0 4px #00eaff;
 box-shadow:0 0 8px #0099bb;
 transition:0.25s;
}

button:hover{
 background:#003547;
 box-shadow:0 0 14px #00eaff;
}

#vozBtn,#borrarBtn{
 float:right;
 margin-right:20px;
}

#logo{
 width:50px;
 vertical-align:middle;
 cursor:pointer;
 transition: transform 0.5s, filter 0.5s;
 filter: drop-shadow(0 0 8px #00eaff);
}

#logo:hover{
 transform:scale(1.15) rotate(6deg);
 filter:drop-shadow(0 0 14px #00eaff);
}

#nombre{
 font-weight:bold;
 margin-left:10px;
 cursor:pointer;
 font-size:24px;
 letter-spacing:1px;
 color:#00eaff;
 text-shadow:0 0 12px #00eaff;
}

small{ color:#7ddfff; }
.playing{ outline:2px solid #00eaff; box-shadow:0 0 14px #00eaff; }

/* Estilos para el clip a la izquierda */
#inputBar {
  display:flex;
  align-items:center;
  gap:6px;
  padding:10px;
}
#clipBtn {
  width:44px;
  height:44px;
  border-radius:8px;
  background:#001f2e;
  border:1px solid #006688;
  display:flex;
  align-items:center;
  justify-content:center;
  cursor:pointer;
  box-shadow:0 0 8px #0099bb;
  font-size:20px;
}
#clipBtn:hover{ background:#003547; }
#audioInput {
  display:none;
}
</style>
</head>

<body>
<h2 style="text-align:center;margin:10px 0; text-shadow:0 0 12px #00eaff;">
<img src="/static/logo.png" id="logo" onclick="logoClick()" alt="logo">
<span id="nombre" onclick="logoClick()">FOSCHI IA</span>
<button onclick="detenerVoz()" style="margin-left:10px;">⏹️ Detener voz</button>
<button id="vozBtn" onclick="toggleVoz()">🔊 Voz activada</button>
<button id="borrarBtn" onclick="borrarPantalla()">🧹 Borrar pantalla</button>
</h2>

<div id="chat" role="log" aria-live="polite"></div>

<!-- Barra de entrada: clip a la izquierda, input central, botones a la derecha -->
<div id="inputBar">
  <!-- Clip (izquierda) -->
  <div id="clipBtn" title="Adjuntar audio (mp3 / wav)" onclick="document.getElementById('audioInput').click();">📎</div>
  <input id="audioInput" type="file" accept=".mp3,audio/*,.wav" />

  <!-- Campo de texto (igual que antes) -->
  <input type="text" id="mensaje" placeholder="Escribí tu mensaje o hablá" />
  <button onclick="enviar()">Enviar</button>
  <button onclick="hablar()">🎤 Hablar</button>
  <button onclick="verHistorial()">🗂️ Ver historial</button>
</div>

<script>
let usuario_id="{{usuario_id}}";
let vozActiva=true,audioActual=null,mensajeActual=null;

function logoClick(){ alert("FOSCHI NUNCA MUERE, TRASCIENDE..."); }

function hablarTexto(texto, div=null){
  if(!vozActiva) return;
  detenerVoz();
  if(mensajeActual) mensajeActual.classList.remove("playing");
  if(div) div.classList.add("playing");
  mensajeActual = div;
  audioActual = new Audio("/tts?texto=" + encodeURIComponent(texto));
  audioActual.playbackRate = 1.25;
  audioActual.onended = () => {
    if(mensajeActual) mensajeActual.classList.remove("playing");
    mensajeActual = null;
  };
  audioActual.play();
}

function detenerVoz(){ if(audioActual){ try{audioActual.pause(); audioActual.currentTime=0; audioActual.src=""; audioActual.load(); audioActual=null; if(mensajeActual) mensajeActual.classList.remove("playing"); mensajeActual=null;}catch(e){console.log(e);}} }

function toggleVoz(estado=null){ vozActiva=estado!==null?estado:!vozActiva; document.getElementById("vozBtn").textContent=vozActiva?"🔊 Voz activada":"🔇 Silenciada"; }

function agregar(msg,cls,imagenes=[]){
  let c=document.getElementById("chat"),div=document.createElement("div");
  div.className="message "+cls; div.innerHTML=msg;
  c.appendChild(div);
  setTimeout(()=>div.classList.add("show"),50);
  imagenes.forEach(url=>{ let img=document.createElement("img"); img.src=url; div.appendChild(img); });
  c.scroll({top:c.scrollHeight,behavior:"smooth"});
  if(cls==="ai") hablarTexto(msg,div);
}

function enviar(){
  let msg=document.getElementById("mensaje").value.trim(); if(!msg) return;
  agregar(msg,"user"); document.getElementById("mensaje").value="";
  fetch("/preguntar",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({mensaje: msg, usuario_id: usuario_id})})
  .then(r=>r.json()).then(data=>{ agregar(data.texto,"ai",data.imagenes); if(data.borrar_historial){document.getElementById("chat").innerHTML="";} })
  .catch(e=>{ agregar("Error al comunicarse con el servidor.","ai"); console.error(e); });
}

document.getElementById("mensaje").addEventListener("keydown",e=>{ if(e.key==="Enter"){ e.preventDefault(); enviar(); } });

function hablar(){
  if('webkitSpeechRecognition' in window || 'SpeechRecognition' in window){
    const Rec = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new Rec();
    recognition.lang='es-AR'; recognition.continuous=false; recognition.interimResults=false;
    recognition.onresult=function(event){ document.getElementById("mensaje").value=event.results[0][0].transcript.toLowerCase(); enviar(); }
    recognition.onerror=function(e){console.log(e); alert("Error reconocimiento de voz: " + e.error); }
    recognition.start();
  }else{alert("Tu navegador no soporta reconocimiento de voz.");}
}

function verHistorial(){
  fetch("/historial/"+usuario_id).then(r=>r.json()).then(data=>{
    document.getElementById("chat").innerHTML="";
    if(data.length===0){agregar("No hay historial todavía.","ai");return;}
    data.slice(-20).forEach(e=>{ agregar(`<small>${e.fecha}</small><br>${e.usuario}`,"user"); agregar(`<small>${e.fecha}</small><br>${e.foschi}`,"ai"); });
  });
}

function borrarPantalla(){ document.getElementById("chat").innerHTML=""; }

window.onload=function(){
  agregar("👋 Hola, soy FOSCHI IA. Obteniendo tu ubicación...","ai");
  if(navigator.geolocation){
    navigator.geolocation.getCurrentPosition(pos=>{
      fetch(`/clima?lat=${pos.coords.latitude}&lon=${pos.coords.longitude}`)
      .then(r=>r.text()).then(clima=>{ agregar(`🌤️ ${clima}`,"ai"); })
      .catch(e=>{ agregar("No pude obtener el clima automáticamente.","ai"); console.error(e); });
    },()=>{ agregar("No pude obtener tu ubicación (permiso denegado o error).","ai"); }, {timeout:8000});
  } else { agregar("Tu navegador no soporta geolocalización.","ai"); }
};

// --- NUEVO: manejar subida automática del audio, transcribir y forzar descarga del .docx ---
document.getElementById("audioInput").addEventListener("change", async (ev) => {
  const file = ev.target.files[0];
  if(!file) return;
  // mostrar mensaje en chat
  agregar(`Subiendo y transcribiendo: <b>${file.name}</b> ...`, "user");
  try {
    const fd = new FormData();
    fd.append("audio", file);
    fd.append("usuario_id", usuario_id);
    const resp = await fetch("/upload_audio", { method: "POST", body: fd });
    if(!resp.ok){
      const txt = await resp.text();
      agregar("Error en transcripción: " + txt, "ai");
      return;
    }
    const blob = await resp.blob();

    // intentar obtener filename desde headers
    let filename = file.name.replace(/\\.[^.]+$/, '') + ".docx";
    const cd = resp.headers.get("Content-Disposition");
    if(cd){
      const m = cd.match(/filename\\*=UTF-8''([^;]+)|filename=\\"?([^\\";]+)\\"?/);
      if(m){
        filename = decodeURIComponent(m[1] || m[2] || filename);
      }
    }

    // forzar descarga automática
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);

    agregar(`✅ Transcripción lista: <b>${filename}</b> (descargada)`, "ai");

  } catch (e){
    console.error(e);
    agregar("Error al subir/transcribir el audio.", "ai");
  } finally {
    // limpiar input para permitir re-subir mismo archivo si hace falta
    ev.target.value = "";
  }
});
// --- fin nuevo ---

function chequearRecordatorios() {
  fetch("/avisos", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({ usuario_id: usuario_id })
  })
  .then(r => r.json())
  .then(data => {
    if (Array.isArray(data) && data.length > 0) {
      data.forEach(r => {
        const motivo = r.motivo || "(sin motivo)";
        agregar(`⏰ Tenés un recordatorio: ${motivo}`, "ai");
        mostrarNotificacion(`⏰ Tenés un recordatorio`, motivo);
      });
    }
  })
  .catch(e => console.error("Error avisos:", e));
}

function mostrarNotificacion(titulo, cuerpo) {
  if (!("Notification" in window)) return;
  if (Notification.permission === "granted") {
    new Notification(titulo, { body: cuerpo });
  } else if (Notification.permission !== "denied") {
    Notification.requestPermission().then(perm => {
      if (perm === "granted") {
        new Notification(titulo, { body: cuerpo });
      }
    });
  }
}

setInterval(chequearRecordatorios, 10000);
</script>
</body>
</html>
"""

# ---------------- RUTAS ----------------
@app.route("/")
def index():
    if "usuario_id" not in session:
        session["usuario_id"]=str(uuid.uuid4())
    return render_template_string(HTML_TEMPLATE, APP_NAME=APP_NAME, usuario_id=session["usuario_id"])

@app.route("/preguntar", methods=["POST"])
def preguntar():
    data = request.get_json()
    mensaje = data.get("mensaje","")
    usuario_id = data.get("usuario_id", str(uuid.uuid4()))
    lat = data.get("lat")
    lon = data.get("lon")
    tz = data.get("timeZone") or data.get("time_zone") or None
    respuesta = generar_respuesta(mensaje, usuario_id, lat=lat, lon=lon, tz=tz)
    texto_para_hist = respuesta["texto"] if isinstance(respuesta, dict) and "texto" in respuesta else str(respuesta)
    guardar_en_historial(usuario_id, mensaje, texto_para_hist)
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

# ---------------- RUN ----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
