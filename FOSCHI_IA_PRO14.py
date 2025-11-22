from flask import Flask, render_template_string, request, jsonify, session, send_file
from flask_session import Session
import os, uuid, json, io, time, threading
from datetime import datetime
import pytz
from gtts import gTTS
import requests
import urllib.parse
from openai import OpenAI
from concurrent.futures import ThreadPoolExecutor

# ---------------- CONFIG ----------------
APP_NAME = "FOSCHI IA WEB"
CREADOR = "Gustavo Enrique Foschi"
DATA_DIR = "data"
STATIC_DIR = "static"
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)

# ---------------- KEYS ----------------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")
OWM_API_KEY = os.getenv("OWM_API_KEY")

# ---------------- APP ----------------
app = Flask(__name__)
app.secret_key = "FoschiWebKey"
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# ---------------- MEMORIA ----------------
MEMORY_FILE = os.path.join(DATA_DIR, "memory.json")
CACHE = {}
CACHE_LOCK = threading.Lock()
CACHE_TTL = 300  # 5 minutos de validez

def load_json(path):
    if not os.path.exists(path): return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def fecha_hora_en_es():
    tz = pytz.timezone("America/Argentina/Buenos_Aires")
    ahora = datetime.now(tz)
    meses = ["enero","febrero","marzo","abril","mayo","junio","julio","agosto","septiembre","octubre","noviembre","diciembre"]
    dias = ["lunes","martes","miércoles","jueves","viernes","sábado","domingo"]
    dia_semana = dias[ahora.weekday()]
    mes = meses[ahora.month-1]
    return f"{dia_semana}, {ahora.day} de {mes} de {ahora.year}, {ahora.hour:02d}:{ahora.minute:02d}"

def learn_from_message(usuario, mensaje, respuesta):
    memory = load_json(MEMORY_FILE)
    if usuario not in memory:
        memory[usuario] = {"temas": {}, "mensajes": [], "ultima_interaccion": None}
    memory[usuario]["mensajes"].append({"usuario": mensaje, "foschi": respuesta})
    ahora = datetime.now(pytz.timezone("America/Argentina/Buenos_Aires"))
    memory[usuario]["ultima_interaccion"] = ahora.strftime("%d/%m/%Y %H:%M:%S")
    memory[usuario]["temas"].update({palabra: memory[usuario]["temas"].get(palabra,0)+1
                                     for palabra in mensaje.lower().split() if len(palabra)>3})
    save_json(MEMORY_FILE, memory)

def hacer_links_clicleables(texto):
    import re
    return re.sub(r'(https?://[^\s]+)', r'<a href="\1" target="_blank" style="color:#ff0000;">\1</a>', texto)

def obtener_clima(ciudad=None, lat=None, lon=None):
    if not OWM_API_KEY:
        return "No está configurada la API de clima (OWM_API_KEY)."
    try:
        if lat and lon:
            url = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OWM_API_KEY}&units=metric&lang=es"
        else:
            ciudad = ciudad if ciudad else "Buenos Aires"
            url = f"http://api.openweathermap.org/data/2.5/weather?q={ciudad}&appid={OWM_API_KEY}&units=metric&lang=es"
        r = requests.get(url, timeout=6)
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

def guardar_en_historial(usuario, entrada, respuesta):
    path = os.path.join(DATA_DIR, f"{usuario}.json")
    datos = []
    if os.path.exists(path):
        with open(path,"r",encoding="utf-8") as f:
            try: datos = json.load(f)
            except: datos = []
    datos.append({"fecha":datetime.now(pytz.timezone("America/Argentina/Buenos_Aires")).strftime("%d/%m/%Y %H:%M:%S"),
                  "usuario":entrada,"foschi":respuesta})
    with open(path,"w",encoding="utf-8") as f:
        json.dump(datos,f,ensure_ascii=False,indent=2)

def cargar_historial(usuario):
    path = os.path.join(DATA_DIR, f"{usuario}.json")
    if not os.path.exists(path): return []
    with open(path,"r",encoding="utf-8") as f:
        try: return json.load(f)
        except: return []

# ---------------- CACHE ----------------
def get_cached(query):
    with CACHE_LOCK:
        entry = CACHE.get(query)
        if entry and (time.time() - entry["ts"] < CACHE_TTL):
            return entry["result"]
        return None

def set_cache(query, result):
    with CACHE_LOCK:
        CACHE[query] = {"result": result, "ts": time.time()}

def buscar_google(query, max_results=5):
    cached = get_cached(query)
    if cached: return cached
    resultados = []
    if GOOGLE_API_KEY and GOOGLE_CSE_ID:
        try:
            url = (
                f"https://www.googleapis.com/customsearch/v1"
                f"?key={GOOGLE_API_KEY}&cx={GOOGLE_CSE_ID}"
                f"&q={urllib.parse.quote(query)}&sort=date"
            )
            r = requests.get(url, timeout=3)
            data = r.json()
            for item in data.get("items", [])[:max_results]:
                snippet = item.get("snippet", "").strip()
                if snippet and snippet not in resultados:
                    resultados.append(snippet)
        except Exception as e:
            print("Error al obtener Google Search:", e)
    set_cache(query, resultados)
    return resultados

def responder_con_openai(fragmentos, mensaje, prompt_type="general"):
    if not fragmentos: return None
    texto_bruto = " ".join(fragmentos)
    client = OpenAI(api_key=OPENAI_API_KEY)
    if prompt_type=="deportes":
        prompt = (
            f"Tengo estos fragmentos recientes sobre deportes: {texto_bruto}\n\n"
            f"Respondé brevemente la consulta '{mensaje}' con los resultados deportivos actuales. "
            f"Usá un tono natural, tipo boletín deportivo argentino, sin frases como 'según los textos'. "
            f"Respondé en una sola oración clara."
        )
        max_tokens=150
    else:
        prompt = (
            f"Tengo estos fragmentos de texto recientes: {texto_bruto}\n\n"
            f"Respondé a la pregunta: '{mensaje}'. "
            f"Usá un tono natural y directo en español argentino, sin frases como "
            f"'según los textos', 'según los fragmentos' o 'de acuerdo a las fuentes'. "
            f"Contestá con una sola oración clara y actualizada. Si no hay información suficiente, decílo sin inventar."
        )
        max_tokens=120
    resp = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[{"role":"user","content":prompt}],
        temperature=0.5,
        max_tokens=max_tokens
    )
    return resp.choices[0].message.content.strip()

# ---------------- RESPUESTA IA ----------------
def generar_respuesta(mensaje, usuario, lat=None, lon=None, tz=None, max_hist=5):
    mensaje_lower = mensaje.lower().strip()

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
        import re
        ciudad_match = re.search(r"clima en ([a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+)", mensaje_lower)
        ciudad = ciudad_match.group(1).strip() if ciudad_match else None
        texto = obtener_clima(ciudad=ciudad, lat=lat, lon=lon)
        learn_from_message(usuario, mensaje, texto)
        return {"texto": texto, "imagenes": [], "borrar_historial": False}

    # --- BÚSQUEDAS ACELERADAS ---
    if any(word in mensaje_lower for word in ["presidente", "actualidad", "noticias", "quién es", "últimas noticias", "evento actual"]):
        with ThreadPoolExecutor(max_workers=2) as executor:
            future_google = executor.submit(buscar_google, mensaje)
            resultados = future_google.result(timeout=4)
            texto = responder_con_openai(resultados, mensaje) or "No pude obtener información actualizada en este momento."
        learn_from_message(usuario, mensaje, texto)
        return {"texto": texto, "imagenes": [], "borrar_historial": False}

    if any(p in mensaje_lower for p in ["resultado", "marcador", "ganó", "empató", "perdió",
                                        "partido", "deporte", "fútbol", "futbol", "nba", "tenis", "f1", "formula 1", "motogp"]):
        query = mensaje + " resultados deportivos actualizados"
        with ThreadPoolExecutor(max_workers=2) as executor:
            future_google = executor.submit(buscar_google, query)
            resultados = future_google.result(timeout=4)
            texto = responder_con_openai(resultados, mensaje, prompt_type="deportes") or "No pude encontrar resultados deportivos recientes en este momento."
        learn_from_message(usuario, mensaje, texto)
        return {"texto": texto, "imagenes": [], "borrar_historial": False}

    # --- RESPUESTA GENERAL OPTIMIZADA CON HISTORIAL ---
    historial_cache_key = f"{usuario}_last_{mensaje_lower}"
    cached_resp = get_cached(historial_cache_key)
    if cached_resp:
        return {"texto": cached_resp, "imagenes": [], "borrar_historial": False}

    try:
        memoria = load_json(MEMORY_FILE)
        historial = memoria.get(usuario, {}).get("mensajes", [])[-max_hist:]
        resumen = " ".join([m["usuario"] + ": " + m["foschi"] for m in historial[-3:]])

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
        set_cache(historial_cache_key, texto)
    except Exception as e:
        texto = f"No pude generar respuesta: {e}"

    texto = hacer_links_clicleables(texto)
    learn_from_message(usuario, mensaje, texto)
    return {"texto": texto, "imagenes": [], "borrar_historial": False}

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
    guardar_en_historial(usuario_id, mensaje, respuesta["texto"])
    return jsonify(respuesta)

@app.route("/historial/<usuario_id>")
def historial(usuario_id):
    return jsonify(cargar_historial(usuario_id))

@app.route("/tts")
def tts():
    texto = request.args.get("texto","")
    tts_obj = gTTS(text=texto, lang="es", slow=False, tld="com.mx")
    archivo = io.BytesIO()
    tts_obj.write_to_fp(archivo)
    archivo.seek(0)
    return send_file(archivo, mimetype="audio/mpeg")

@app.route("/clima")
def clima():
    lat = request.args.get("lat")
    lon = request.args.get("lon")
    ciudad = request.args.get("ciudad")
    return obtener_clima(ciudad=ciudad, lat=lat, lon=lon)

@app.route('/favicon.ico')
def favicon():
    return send_file(os.path.join(STATIC_DIR, 'favicon.ico'))

# ---------------- HTML ----------------
HTML_TEMPLATE = """..."""  # Mantén tu template tal cual, no cambia

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
