# FOSCHI_IA_PRO_FINAL.py
from flask import Flask, render_template_string, request, jsonify, session, send_file
from flask_session import Session
import os, uuid, json, io
from datetime import datetime
import pytz
from gtts import gTTS
import requests
import urllib.parse

# OpenAI modern client
try:
    from openai import OpenAI
except Exception:
    OpenAI = None

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

# ---------------- OPENAI CLIENT ----------------
client = None
if OpenAI is not None and OPENAI_API_KEY:
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
    except Exception:
        client = None

# ---------------- APP ----------------
app = Flask(__name__)
app.secret_key = "FoschiWebKey"
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# ---------------- MEMORIA ----------------
MEMORY_FILE = os.path.join(DATA_DIR, "memory.json")

def load_json(path):
    if not os.path.exists(path):
        return {}
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
    for palabra in mensaje.lower().split():
        if len(palabra) > 3:
            memory[usuario]["temas"][palabra] = memory[usuario]["temas"].get(palabra, 0) + 1
    save_json(MEMORY_FILE, memory)

def save_last_sources(usuario, fuentes_list):
    memory = load_json(MEMORY_FILE)
    if usuario not in memory:
        memory[usuario] = {"temas": {}, "mensajes": [], "ultima_interaccion": None}
    memory[usuario]["ultimas_fuentes"] = fuentes_list
    save_json(MEMORY_FILE, memory)

def get_last_sources(usuario):
    memory = load_json(MEMORY_FILE)
    return memory.get(usuario, {}).get("ultimas_fuentes", [])

def hacer_links_clicleables(texto):
    import re
    return re.sub(r'(https?://[^\s]+)', r'<a href="\1" target="_blank" style="color:#ff0000;">\1</a>', texto)

# ---------------- BÚSQUEDAS ----------------
def buscar_google_con_links(query, max_results=3):
    """
    Devuelve (snippets, links) usando Google Custom Search.
    snippets: lista de textos (sin títulos ni links)
    links: lista de URLs (strings) o strings con título + url para mostrar si se piden fuentes.
    """
    snippets = []
    links = []
    if GOOGLE_API_KEY and GOOGLE_CSE_ID:
        try:
            url = f"https://www.googleapis.com/customsearch/v1?key={GOOGLE_API_KEY}&cx={GOOGLE_CSE_ID}&q={urllib.parse.quote(query)}&sort=date"
            r = requests.get(url, timeout=6)
            data = r.json()
            for item in data.get("items", [])[:max_results]:
                snippet = item.get("snippet", "").strip()
                link = item.get("link", "").strip()
                title = item.get("title", "").strip()
                if snippet:
                    snippets.append(snippet)
                if link:
                    # guardamos texto amigable + url para mostrar cuando se pida
                    if title:
                        links.append(f"{title} — {link}")
                    else:
                        links.append(link)
        except Exception:
            pass
    return snippets, links

# Respaldos simples (Bing RSS + DuckDuckGo scraping ligero) para cuando Google no devuelva nada
import re
def buscar_respaldo(query, max_results=4):
    resultados = []
    links = []
    try:
        # Bing News RSS (puede devolver títulos)
        url_bing = f"https://www.bing.com/news/search?q={urllib.parse.quote(query)}&format=rss"
        r_bing = requests.get(url_bing, timeout=6)
        titles = re.findall(r"<title>(.*?)</title>", r_bing.text)
        # ignorar los primeros 1-2 que son encabezados
        for t in titles[2:2+max_results]:
            resultados.append(t)
        # DuckDuckGo (HTML)
        url_duck = f"https://duckduckgo.com/html/?q={urllib.parse.quote(query)}"
        r_duck = requests.get(url_duck, timeout=6, headers={"User-Agent": "Mozilla/5.0"})
        matches = re.findall(r'<a rel="nofollow" class="result__a" href="([^"]+)">([^<]+)</a>', r_duck.text)
        for href, text in matches[:max_results]:
            resultados.append(text)
            links.append(href)
    except Exception:
        pass
    return resultados[:max_results], links

def buscar_info_actual(query, max_results=3):
    """
    Devuelve (snippets, links). Por defecto intenta Google Custom Search; si no hay resultados
    usa buscadores de respaldo. Los 'snippets' son solo texto para resumir; los 'links' se
    guardan en memoria y se muestran solo si el usuario lo pide.
    """
    snippets, links = buscar_google_con_links(query, max_results=max_results)
    if not snippets:
        snippets, links = buscar_respaldo(query, max_results=max_results)
    if not snippets:
        snippets = ["No se encontró información reciente sobre ese tema."]
    return snippets, links

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
        r = requests.get(url, timeout=6)
        data = r.json()
        if r.status_code != 200:
            return "No pude obtener el clima en este momento."
        desc = data.get("weather", [{}])[0].get("description", "Sin descripción").capitalize()
        temp = data.get("main", {}).get("temp")
        hum = data.get("main", {}).get("humidity")
        parts = [f"{desc}"]
        if temp is not None:
            parts.append(f"Temperatura {round(temp)}°C")
        if hum is not None:
            parts.append(f"Humedad {hum}%")
        return ", ".join(parts) + "."
    except:
        return "No pude obtener el clima."

# ---------------- RESPUESTA IA ----------------
def generar_respuesta(mensaje, usuario, lat=None, lon=None, tz=None, max_hist=5):
    mensaje_lower = mensaje.lower().strip()

    # Pedir fuentes explícitamente
    if any(w in mensaje_lower for w in ["fuentes", "links", "páginas", "páginas web", "paginas", "referencias", "de dónde", "de donde"]):
        fuentes = get_last_sources(usuario)
        if not fuentes:
            # si no hay guardadas, hacemos una búsqueda rápida (sin resumir) para devolver links
            _, enlaces = buscar_info_actual(mensaje, max_results=5)
            fuentes = enlaces
        if not fuentes:
            return {"texto": "No tengo fuentes guardadas para esta conversación.", "imagenes": []}
        # formatear clickeables
        texto_links = "\n".join([hacer_links_clicleables(e) for e in fuentes])
        return {"texto": "Aquí están las fuentes:\n" + texto_links, "imagenes": []}

    # BORRAR HISTORIAL
    if any(phrase in mensaje_lower for phrase in ["borrar historial", "limpiar historial", "reset historial"]):
        path = os.path.join(DATA_DIR, f"{usuario}.json")
        if os.path.exists(path):
            os.remove(path)
        memory = load_json(MEMORY_FILE)
        if usuario in memory:
            memory[usuario]["mensajes"] = []
            save_json(MEMORY_FILE, memory)
        return {"texto":"✅ Historial borrado correctamente.","imagenes":[],"borrar_historial":True}

    # FECHA/HORA
    if any(phrase in mensaje_lower for phrase in ["qué día", "que día", "qué fecha", "que fecha", "qué hora", "que hora", "día es hoy", "fecha hoy"]):
        texto = fecha_hora_en_es()
        learn_from_message(usuario, mensaje, texto)
        return {"texto":texto,"imagenes":[],"borrar_historial":False}

    # CLIMA
    if "clima" in mensaje_lower:
        import re
        ciudad_match = re.search(r"clima en ([a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+)", mensaje_lower)
        ciudad = ciudad_match.group(1).strip() if ciudad_match else None
        texto = obtener_clima(ciudad=ciudad, lat=lat, lon=lon)
        learn_from_message(usuario, mensaje, texto)
        return {"texto":texto,"imagenes":[],"borrar_historial":False}

    # INFORMACIÓN ACTUAL (resumida y SIN mostrar enlaces)
    if any(word in mensaje_lower for word in ["presidente","actualidad","noticias","quién es","quien es","últimas noticias","evento actual"]):
        snippets, links = buscar_info_actual(mensaje, max_results=3)
        combined = " ".join(snippets)
        # Guardar las fuentes para si el usuario las pide después
        if links:
            save_last_sources(usuario, links)
        # Reescribir naturalmente con OpenAI (si está disponible)
        if client:
            try:
                system_prompt = "Eres Foschi IA, un asistente que resume información actual para el usuario. No menciones ni muestres las fuentes a menos que el usuario lo pida."
                user_prompt = f"Resume brevemente y con lenguaje natural esta información: {combined}. No menciones ni incluyas enlaces o nombres de sitios; solo da el resumen."
                resp = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role":"system","content": system_prompt},
                              {"role":"user","content": user_prompt}],
                    max_tokens=300
                )
                texto = resp.choices[0].message.content.strip()
            except Exception as e:
                texto = combined if combined else "No pude obtener información actual en este momento."
        else:
            texto = combined if combined else "No pude obtener información actual en este momento."
        learn_from_message(usuario, mensaje, texto)
        return {"texto":texto,"imagenes":[],"borrar_historial":False}

    # RESPUESTA IA NORMAL (con contexto)
    try:
        memoria = load_json(MEMORY_FILE)
        historial = memoria.get(usuario, {}).get("mensajes", [])
        prompt_messages = []
        for m in historial[-max_hist:]:
            prompt_messages.append({"role":"user","content": m["usuario"]})
            prompt_messages.append({"role":"assistant","content": m["foschi"]})
        prompt_messages.append({"role":"user","content": mensaje})

        if client:
            resp = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=prompt_messages,
                max_tokens=800
            )
            texto = resp.choices[0].message.content.strip()
        else:
            texto = "El motor de IA no está configurado (falta OPENAI_API_KEY)."
    except Exception as e:
        texto = f"No pude generar respuesta: {e}"

    # Si el usuario pidió "fuentes" en la misma consulta, añadir enlaces (redundancia)
    if any(palabra in mensaje_lower for palabra in ["fuentes","links","paginas web","videos","referencias"]):
        enlaces = get_last_sources(usuario)
        if enlaces:
            texto += "\n\n🔗 Fuentes:\n" + "\n".join([hacer_links_clicleables(e) for e in enlaces])
        else:
            # generar links rápidos si no existen
            _, quick_links = buscar_info_actual(mensaje, max_results=5)
            if quick_links:
                save_last_sources(usuario, quick_links)
                texto += "\n\n🔗 Fuentes:\n" + "\n".join([hacer_links_clicleables(e) for e in quick_links])

    learn_from_message(usuario, mensaje, texto)
    return {"texto":texto,"imagenes":[],"borrar_historial":False}

# ---------------- RUTAS ----------------
@app.route("/")
def index():
    if "usuario_id" not in session:
        session["usuario_id"] = str(uuid.uuid4())
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
HTML_TEMPLATE = """  
<!doctype html>
<html>
<head>
<title>{{APP_NAME}}</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body{font-family:Arial,system-ui,-apple-system,Segoe UI,Roboto,Helvetica;background:#000;color:#fff;margin:0;padding:0;}
#chat{width:100%;height:70vh;overflow-y:auto;padding:10px;background:#111;}
.message{margin:5px 0;padding:8px 12px;border-radius:15px;max-width:80%;word-wrap:break-word;opacity:0;transition:opacity 0.5s,border 0.5s;}
.message.show{opacity:1;}
.user{background:#3300ff;color:#fff;margin-left:auto;text-align:right;}
.ai{background:#00ffff;color:#000;margin-right:auto;text-align:left;}
a{color:#fff;text-decoration:underline;}
img{max-width:300px;border-radius:10px;margin:5px 0;}
input,button{padding:10px;font-size:16px;margin:5px;border:none;border-radius:5px;}
input[type=text]{width:70%;background:#222;color:#fff;}
button{background:#333;color:#fff;cursor:pointer;}
button:hover{background:#555;}
#vozBtn,#borrarBtn,#musicaBtn{float:right;margin-right:20px;}
#logo{width:50px;vertical-align:middle;cursor:pointer;transition:transform 0.5s;}
#logo:hover{transform:scale(1.15) rotate(6deg);}
#nombre{font-weight:bold;margin-left:10px;cursor:pointer;}
small{color:#aaa;}
.playing{outline:2px solid #fff;}
</style>
</head>
<body>
<h2 style="text-align:center;margin:10px 0;">
<img src="/static/logo.png" id="logo" onclick="logoClick()" alt="logo">
<span id="nombre" onclick="logoClick()">FOSCHI IA</span>
<button onclick="detenerVoz()" style="margin-left:10px;">⏹️ Detener voz</button>
<button id="vozBtn" onclick="toggleVoz()">🔊 Voz activada</button>
<button id="borrarBtn" onclick="borrarPantalla()">🧹 Borrar pantalla</button>
<button id="musicaBtn" onclick="toggleMusica()">🎵 Detener música</button>
</h2>

<audio id="musicaFondo" autoplay loop>
  <source src="/static/musica.mp3" type="audio/mpeg">
</audio>

<div id="chat" role="log" aria-live="polite"></div>
<div style="padding:10px;">
<input type="text" id="mensaje" placeholder="Escribí tu mensaje o hablá" />
<button onclick="enviar()">Enviar</button>
<button onclick="hablar()">🎤 Hablar</button>
<button onclick="verHistorial()">🗂️ Ver historial</button>
</div>

<script>
let usuario_id="{{usuario_id}}";
let vozActiva=true,audioActual=null,mensajeActual=null;
let musica=document.getElementById("musicaFondo");
let musicaBtn=document.getElementById("musicaBtn");
let musicaActiva=true;

function toggleMusica(){
  if(musicaActiva){musica.pause(); musicaActiva=false; musicaBtn.textContent="🎵 Reproducir música";}
  else{musica.play().catch(()=>{}); musicaActiva=true; musicaBtn.textContent="🎵 Detener música";}
}
document.addEventListener('click',()=>{if(musica.paused) musica.play().catch(()=>{});},{once:true});

function logoClick(){ alert("FOSCHI NUNCA MUERE, TRASCIENDE..."); }

function hablarTexto(texto,div=null){
  if(!vozActiva) return;
  detenerVoz();
  if(mensajeActual) mensajeActual.classList.remove("playing");
  if(div) div.classList.add("playing");
  mensajeActual=div;
  audioActual=new Audio("/tts?texto="+encodeURIComponent(texto));
  audioActual.onended=()=>{ if(mensajeActual) mensajeActual.classList.remove("playing"); mensajeActual=null; };
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
    recognition.onerror=function(e){console.log(e); alert("Error reconocimiento de voz: " + e.error);}
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
</script>
</body>
</html>
"""

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
