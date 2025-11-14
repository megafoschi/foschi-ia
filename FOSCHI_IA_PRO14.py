from flask import Flask, render_template_string, request, jsonify, session, send_file
from flask_session import Session
import os
import uuid
import json
import io
from datetime import datetime
import pytz
from gtts import gTTS
import requests
import urllib.parse
from openai import OpenAI
from werkzeug.utils import secure_filename
import whisper
from docx import Document
import tempfile

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

    # (Aquí podés mantener el resto de tus reglas y llamadas a OpenAI)
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

    except Exception as e:
        texto = f"No pude generar respuesta: {e}"

    texto = hacer_links_clicleables(texto)
    learn_from_message(usuario, mensaje, texto)
    return {"texto": texto, "imagenes": [], "borrar_historial": False}

# --------- CARGAR WHISPER UNA VEZ ---------
print("Cargando modelo Whisper base (solo una vez)...")
WHISPER_MODEL = whisper.load_model("base")
print("Whisper cargado.")

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

@app.route("/subir_audio", methods=["POST"])
def subir_audio():
    if "audio" not in request.files:
        return "No se envió archivo de audio", 400

    archivo = request.files["audio"]
    if archivo.filename == "":
        return "Archivo inválido", 400

    # Asegurar nombre seguro y crear temporales
    original_name = secure_filename(archivo.filename)
    # Creamos temp file para guardar el audio
    tmp_audio = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(original_name)[1] or ".mp3")
    tmp_docx = tempfile.NamedTemporaryFile(delete=False, suffix=".docx")
    try:
        archivo.save(tmp_audio.name)

        # Transcribir con el modelo ya cargado
        result = WHISPER_MODEL.transcribe(tmp_audio.name)
        texto = result.get("text", "").strip()

        # Crear documento Word
        doc = Document()
        doc.add_heading("Transcripción de Audio", level=1)
        doc.add_paragraph(texto)
        doc.save(tmp_docx.name)

        # Leer docx a bytes y devolverlo con nombre original.docx
        with open(tmp_docx.name, "rb") as f:
            data = f.read()

        download_name = os.path.splitext(original_name)[0] + ".docx"
        return send_file(
            io.BytesIO(data),
            as_attachment=True,
            download_name=download_name,
            mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

    except Exception as e:
        return f"Error al procesar audio: {e}", 500

    finally:
        # Limpiar temporales si existen
        try:
            if os.path.exists(tmp_audio.name):
                os.remove(tmp_audio.name)
        except:
            pass
        try:
            if os.path.exists(tmp_docx.name):
                os.remove(tmp_docx.name)
        except:
            pass

# ---------------- HTML ----------------
# (Tu HTML original aquí — lo dejé intacto para no romper tu UI)
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
#vozBtn,#borrarBtn{float:right;margin-right:20px;}
#logo{width:50px;vertical-align:middle;cursor:pointer;transition: transform 0.5s;}
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
</h2>

<div id="chat" role="log" aria-live="polite"></div>
<div style="padding:10px;">
<input type="text" id="mensaje" placeholder="Escribí tu mensaje o hablá" />
<button onclick="enviar()">Enviar</button>
<button onclick="hablar()">🎤 Hablar</button>
<button onclick="verHistorial()">🗂️ Ver historial</button>
</div>

<div style="padding:10px;">
<input type="file" id="audioFile" accept="audio/*">
<button onclick="subirAudio()">🎧 Subir audio</button>

<script>
// --- JS del chat ---
let usuario_id="{{usuario_id}}";
let vozActiva=true,audioActual=null,mensajeActual=null;

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

function subirAudio(){
    let archivo = document.getElementById("audioFile").files[0];
    if(!archivo){
        alert("Seleccioná un archivo de audio primero.");
        return;
    }

    let formData = new FormData();
    formData.append("audio", archivo);

    fetch("/subir_audio", {
        method: "POST",
        body: formData
    })
    .then(resp => {
        if(resp.ok) return resp.blob();
        else throw new Error("Error al procesar el audio");
    })
    .then(blob => {
        let url = window.URL.createObjectURL(blob);
        let a = document.createElement("a");
        a.href = url;
        a.download = archivo.name.split('.').slice(0, -1).join('.') + ".docx";
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);
    })
    .catch(err => alert("Error: " + err));
}
</script>
</body>
</html>
"""

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
