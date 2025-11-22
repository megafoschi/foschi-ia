from flask import Flask, render_template_string, request, jsonify, session, send_file
from flask_session import Session
import os
import uuid
import json
import io
from datetime import datetime
import pytz
from openai import OpenAI
from werkzeug.utils import secure_filename
from docx import Document
import tempfile
import PyPDF2
import hashlib
import shutil

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

@app.route("/clima")
def clima():
    lat = request.args.get("lat")
    lon = request.args.get("lon")
    ciudad = request.args.get("ciudad")
    return obtener_clima(ciudad=ciudad, lat=lat, lon=lon)

@app.route('/favicon.ico')
def favicon():
    return send_file(os.path.join(STATIC_DIR, 'favicon.ico'))

# ------------------ NUEVAS RUTAS DE SUBIDA ------------------

def make_docx_from_text(texto, title="Documento"):
    doc = Document()
    doc.add_heading(title, level=1)
    # añadir por párrafos (respetando saltos de línea)
    for line in texto.splitlines():
        doc.add_paragraph(line)
    bio = io.BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio

@app.route("/subir_pdf", methods=["POST"])
def subir_pdf():
    if "pdf" not in request.files:
        return "No se envió archivo PDF", 400
    archivo = request.files["pdf"]
    if archivo.filename == "":
        return "Archivo inválido", 400
    original_name = secure_filename(archivo.filename)
    tmp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    try:
        archivo.save(tmp_pdf.name)
        texto = ""
        with open(tmp_pdf.name, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                try:
                    page_text = page.extract_text() or ""
                except:
                    page_text = ""
                texto += page_text + "\n"
        if not texto.strip():
            texto = "No se pudo extraer texto del PDF o está vacío."
        doc_bio = make_docx_from_text(texto, title=f"Texto extraído - {original_name}")
        return send_file(
            doc_bio,
            as_attachment=True,
            download_name=os.path.splitext(original_name)[0] + ".docx",
            mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
    except Exception as e:
        return f"Error al procesar PDF: {e}", 500
    finally:
        try:
            if os.path.exists(tmp_pdf.name): os.remove(tmp_pdf.name)
        except: pass

@app.route("/subir_archivo", methods=["POST"])
def subir_archivo():
    # genérico: acepta txt, docx, pdf; devuelve docx con texto
    if "file" not in request.files:
        return "No se envió archivo", 400
    archivo = request.files["file"]
    if archivo.filename == "":
        return "Archivo inválido", 400
    original_name = secure_filename(archivo.filename)
    ext = os.path.splitext(original_name)[1].lower()
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
    try:
        archivo.save(tmp.name)
        texto = ""
        if ext in [".txt", ".md"]:
            with open(tmp.name, "r", encoding="utf-8", errors="ignore") as f:
                texto = f.read()
        elif ext in [".docx"]:
            # leer con python-docx
            doc = Document(tmp.name)
            partes = []
            for p in doc.paragraphs:
                partes.append(p.text)
            texto = "\n".join(partes)
        elif ext in [".pdf"]:
            with open(tmp.name, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    try:
                        page_text = page.extract_text() or ""
                    except:
                        page_text = ""
                    texto += page_text + "\n"
        else:
            texto = "Tipo de archivo no soportado en /subir_archivo."
        if not texto.strip():
            texto = "No se pudo extraer texto del archivo o está vacío."
        doc_bio = make_docx_from_text(texto, title=f"Conversión - {original_name}")
        return send_file(
            doc_bio,
            as_attachment=True,
            download_name=os.path.splitext(original_name)[0] + ".docx",
            mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
    except Exception as e:
        return f"Error al procesar archivo: {e}", 500
    finally:
        try:
            if os.path.exists(tmp.name): os.remove(tmp.name)
        except: pass

@app.route("/subir_docx", methods=["POST"])
def subir_docx():
    # Recibe un docx y devuelve una versión "limpia" (por ejemplo, normalizar saltos)
    if "docx" not in request.files:
        return "No se envió archivo DOCX", 400
    archivo = request.files["docx"]
    if archivo.filename == "":
        return "Archivo inválido", 400
    original_name = secure_filename(archivo.filename)
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".docx")
    try:
        archivo.save(tmp.name)
        # abrir y reescribir para normalizar
        doc = Document(tmp.name)
        bio = io.BytesIO()
        # (aqui podrías agregar limpieza adicional si querés)
        doc.save(bio)
        bio.seek(0)
        return send_file(
            bio,
            as_attachment=True,
            download_name=os.path.splitext(original_name)[0] + "_limpio.docx",
            mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
    except Exception as e:
        return f"Error al procesar docx: {e}", 500
    finally:
        try:
            if os.path.exists(tmp.name): os.remove(tmp.name)
        except: pass

# ---------------- HTML ----------------
# Menú lateral moderno (panel desde la izquierda). El input principal mantiene su aspecto.
HTML_TEMPLATE = """  
<!doctype html>
<html>
<head>
<title>{{APP_NAME}}</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
:root{
  --bg:#0b0b0b; --panel:#0f1720; --accent:#06b6d4; --muted:#94a3b8; --card:#0b1220;
  --glass: rgba(255,255,255,0.03);
  font-family: Inter, system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial;
}
*{box-sizing:border-box}
body{background:var(--bg);color:#e6eef2;margin:0;padding:0}
.header{display:flex;align-items:center;gap:12px;padding:14px 18px;border-bottom:1px solid rgba(255,255,255,0.03)}
#logo{width:46px;height:46px;border-radius:10px;background:linear-gradient(135deg,#0ea5a4,#06b6d4);display:flex;align-items:center;justify-content:center;font-weight:700;cursor:pointer;box-shadow:0 6px 18px rgba(2,6,23,0.6)}
.header h1{margin:0;font-size:18px}
.controls{margin-left:auto;display:flex;gap:8px;align-items:center}
button.small{background:transparent;border:1px solid rgba(255,255,255,0.04);padding:8px 10px;border-radius:8px;color:var(--muted);cursor:pointer}
.container{display:flex;height:calc(100vh - 66px);gap:20px;padding:18px}
.chat-area{flex:1;display:flex;flex-direction:column;gap:12px}
#chat{flex:1;overflow:auto;padding:16px;border-radius:14px;background:linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01));box-shadow:inset 0 1px 0 rgba(255,255,255,0.02)}
.message{max-width:78%;padding:12px 14px;border-radius:12px;margin:8px 0;word-wrap:break-word;opacity:0;transform:translateY(6px);transition:all .28s}
.message.show{opacity:1;transform:none}
.user{margin-left:auto;background:linear-gradient(90deg,#0b1220,#081423);border:1px solid rgba(255,255,255,0.02)}
.ai{margin-right:auto;background:linear-gradient(90deg,#062022,#04212a);border:1px solid rgba(255,255,255,0.02)}
.input-row{display:flex;gap:10px;align-items:center;padding:6px 0}
.attach-btn{width:44px;height:44px;border-radius:10px;background:var(--glass);display:flex;align-items:center;justify-content:center;border:1px solid rgba(255,255,255,0.03);cursor:pointer}
.input{flex:1;display:flex;gap:8px;align-items:center;background:#07121a;padding:8px;border-radius:12px;border:1px solid rgba(255,255,255,0.03)}
.input input[type=text]{flex:1;background:transparent;border:none;color:#e6eef2;font-size:15px;padding:8px;outline:none}
.input button{background:var(--accent);color:#002;border:none;padding:10px 14px;border-radius:10px;cursor:pointer}
.small-muted{font-size:12px;color:var(--muted)}
/* LATERAL PANEL */
.side-panel{position:fixed;left:0;top:66px;width:320px;height:calc(100vh - 66px);background:linear-gradient(180deg,#041021,#031018);box-shadow:2px 0 30px rgba(0,0,0,0.7);transform:translateX(-100%);transition:transform .32s ease-in-out;padding:18px;z-index:60;border-right:1px solid rgba(255,255,255,0.03)}
.side-panel.open{transform:translateX(0)}
.side-panel h3{margin:0 0 12px 0}
.menu-item{display:flex;align-items:center;gap:12px;padding:12px;border-radius:10px;cursor:pointer;margin-bottom:8px;border:1px solid rgba(255,255,255,0.02)}
.menu-item:hover{background:rgba(255,255,255,0.02)}
.menu-item .kbd{padding:6px 8px;border-radius:6px;background:#071728;border:1px solid rgba(255,255,255,0.02);font-size:13px;color:var(--muted)}
.footer-note{position:absolute;bottom:18px;left:18px;color:var(--muted);font-size:12px}

/* responsive */
@media(max-width:700px){
  .side-panel{width:100%;top:56px;height:calc(100vh - 56px)}
  .container{padding:12px}
}
</style>
</head>
<body>
<div class="header">
  <div id="logo" onclick="logoClick()">F</div>
  <h1>FOSCHI IA</h1>
  <div class="controls">
    <button class="small" onclick="borrarPantalla()">🧹</button>
  </div>
</div>

<div class="container">
  <div class="chat-area">
    <div id="chat" role="log" aria-live="polite"></div>

    <div class="input-row">
      <div class="attach-btn" id="attachBtn" title="Adjuntar archivo (PDF, DOCX,...)" onclick="togglePanel()">
        📎
      </div>

      <div class="input" role="search">
        <input type="text" id="mensaje" placeholder="Escribí tu mensaje" aria-label="mensaje">
        <button onclick="enviar()">Enviar</button>
      </div>
    </div>
    <div style="display:flex;gap:8px;margin-top:8px;">
      <button onclick="verHistorial()" class="small">🗂️ Historial</button>
    </div>
  </div>

  <!-- Side panel (deslizante moderno) -->
  <div class="side-panel" id="sidePanel" aria-hidden="true">
    <h3>Adjuntar — opciones</h3>

    <div class="menu-item" onclick="triggerFile('pdf')">
      <div class="kbd">📄</div><div>PDF → Texto / DOCX</div>
    </div>

    <div class="menu-item" onclick="triggerFile('file')">
      <div class="kbd">🗂️</div><div>Archivo genérico (txt, docx, pdf)</div>
    </div>

    <div class="menu-item" onclick="triggerFile('docx')">
      <div class="kbd">✳️</div><div>Reprocesar DOCX</div>
    </div>

    <div class="footer-note">Los archivos se procesan y se eliminan del servidor automáticamente.</div>
  </div>
</div>

<!-- Hidden inputs para cada tipo (son disparadas por JS) -->
<input id="in_pdf" type="file" accept="application/pdf" style="display:none"/>
<input id="in_file" type="file" accept=".txt,.md,.pdf,.docx" style="display:none"/>
<input id="in_docx" type="file" accept=".docx" style="display:none"/>

<script>
// --- JS del chat / UI ---
let usuario_id="{{usuario_id}}";

function logoClick(){ alert("FOSCHI IA — listo para ayudar 🤖"); }

function agregar(msg,cls,imagenes=[]){
  let c=document.getElementById("chat"),div=document.createElement("div");
  div.className="message "+cls; div.innerHTML=msg;
  c.appendChild(div);
  setTimeout(()=>div.classList.add("show"),50);
  imagenes.forEach(url=>{ let img=document.createElement("img"); img.src=url; img.style.maxWidth="200px"; img.style.borderRadius="8px"; div.appendChild(img); });
  c.scroll({top:c.scrollHeight,behavior:"smooth"});
}

function stripHtml(html){
  let tmp = document.createElement("div"); tmp.innerHTML = html; return tmp.textContent || tmp.innerText || "";
}

function enviar(){
  let msg=document.getElementById("mensaje").value.trim(); if(!msg) return;
  agregar(msg,"user"); document.getElementById("mensaje").value="";
  fetch("/preguntar",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({mensaje: msg, usuario_id: usuario_id})})
  .then(r=>r.json()).then(data=>{ agregar(data.texto,"ai",data.imagenes); if(data.borrar_historial){document.getElementById("chat").innerHTML="";} })
  .catch(e=>{ agregar("Error al comunicarse con el servidor.","ai"); console.error(e); });
}

document.getElementById("mensaje").addEventListener("keydown",e=>{ if(e.key==="Enter"){ e.preventDefault(); enviar(); } });

function verHistorial(){
  fetch("/historial/"+usuario_id).then(r=>r.json()).then(data=>{
    document.getElementById("chat").innerHTML="";
    if(data.length===0){agregar("No hay historial todavía.","ai");return;}
    data.slice(-20).forEach(e=>{ agregar(`<small>${e.fecha}</small><br>${escapeHtml(e.usuario)}`,"user"); agregar(`<small>${e.fecha}</small><br>${escapeHtml(e.foschi)}`,"ai"); });
  });
}

function borrarPantalla(){ document.getElementById("chat").innerHTML=""; }

window.onload=function(){
  agregar("👋 Hola, soy FOSCHI IA.","ai");
  if(navigator.geolocation){
    navigator.geolocation.getCurrentPosition(pos=>{
      fetch(`/clima?lat=${pos.coords.latitude}&lon=${pos.coords.longitude}`)
      .then(r=>r.text()).then(clima=>{ agregar(`🌤️ ${clima}`,"ai"); })
      .catch(e=>{ agregar("No pude obtener el clima automáticamente.","ai"); console.error(e); });
    },()=>{ agregar("No pude obtener tu ubicación (permiso denegado o error).","ai"); }, {timeout:8000});
  } else { agregar("Tu navegador no soporta geolocalización.","ai"); }
};

function escapeHtml(text){ var map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' }; return text.replace(/[&<>"']/g, function(m){ return map[m]; }); }

// --- PANEL LATERAL & subida de archivos ---
const sidePanel = document.getElementById("sidePanel");
function togglePanel(open){
  if(open===undefined) sidePanel.classList.toggle("open");
  else if(open) sidePanel.classList.add("open"); else sidePanel.classList.remove("open");
}

// map tipo -> input id and endpoint
const uploadMap = {
  pdf:   {input: "in_pdf", endpoint: "/subir_pdf", nameKey: "pdf"},
  file:  {input: "in_file", endpoint: "/subir_archivo", nameKey: "file"},
  docx:  {input: "in_docx", endpoint: "/subir_docx", nameKey: "docx"}
};

function triggerFile(tipo){
  togglePanel(false); // cerrar panel para mejor UX
  const map = uploadMap[tipo];
  if(!map) return alert("Tipo no soportado");
  const input = document.getElementById(map.input);
  input.value = null;
  input.click();
  input.onchange = ()=> {
    const file = input.files[0];
    if(!file) return;
    // mostrar mensaje en chat
    agregar(`📎 Enviando <strong>${file.name}</strong> para procesar (${tipo})...`,"ai");
    const fd = new FormData();
    fd.append(map.nameKey, file);
    fetch(map.endpoint, {method:"POST", body: fd})
      .then(resp => {
        if (resp.ok) return resp.blob();
        return resp.text().then(txt=>{ throw new Error(txt || "Error al procesar"); });
      })
      .then(blob => {
        // descargar archivo devuelto
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        let ext = ".docx";
        a.href = url;
        a.download = file.name.split('.').slice(0,-1).join('.') + ext;
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);
        agregar(`✅ Procesado: <strong>${file.name}</strong> — descarga iniciada.`,"ai");
      })
      .catch(err => {
        console.error(err);
        agregar(`❌ Error procesando ${file.name}: ${err.message || err}`,"ai");
      })
      .finally(()=>{ input.value = null; });
  };
}
</script>
</body>
</html>
"""

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    # threaded=True permite manejar múltiples requests en paralelo en Flask (mejora la latencia)
    app.run(host="0.0.0.0", port=port, threaded=True)
