# --- FOSCHI IA - Código completo con todas las funciones solicitadas ---
from flask import Flask, render_template_string, request, jsonify, session, send_file, Response
from flask_session import Session
import os, io, uuid, json, tempfile, shutil, hashlib
from datetime import datetime
import pytz
from werkzeug.utils import secure_filename

# opcionales
try:
    from gtts import gTTS
except Exception:
    gTTS = None

try:
    import whisper
except Exception:
    whisper = None

try:
    from docx import Document
except Exception:
    Document = None

try:
    import PyPDF2
except Exception:
    PyPDF2 = None

try:
    from moviepy.editor import VideoFileClip
except Exception:
    VideoFileClip = None

# opcionales para aceleración de audio y OCR
try:
    from pydub import AudioSegment
    from pydub.effects import speedup
    PYDUB_AVAILABLE = True
except Exception:
    PYDUB_AVAILABLE = False

try:
    import pytesseract
    from PIL import Image
    TESSERACT_AVAILABLE = True
except Exception:
    TESSERACT_AVAILABLE = False

# OpenAI client (opcional / para TTS premium)
USE_OPENAI_TTS = os.getenv("USE_OPENAI_TTS", "0") in ("1", "true", "True", "TRUE")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if USE_OPENAI_TTS and OPENAI_API_KEY:
    try:
        from openai import OpenAI
        openai_client = OpenAI(api_key=OPENAI_API_KEY)
    except Exception:
        openai_client = None
else:
    openai_client = None

# Google CSE config (opcional)
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")

# ---------------- CONFIG ----------------
APP_NAME = "FOSCHI IA WEB"
CREADOR = "Gustavo Enrique Foschi"
DATA_DIR = "data"
STATIC_DIR = "static"
TTS_CACHE_DIR = os.path.join(DATA_DIR, "tts_cache")
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(TTS_CACHE_DIR, exist_ok=True)

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

# ---------------- helpers ----------------
def fecha_hora_en_es():
    tz = pytz.timezone("America/Argentina/Buenos_Aires")
    ahora = datetime.now(tz)
    meses = ["enero","febrero","marzo","abril","mayo","junio","julio","agosto","septiembre","octubre","noviembre","diciembre"]
    dias = ["lunes","martes","miércoles","jueves","viernes","sábado","domingo"]
    dia_semana = dias[ahora.weekday()]
    mes = meses[ahora.month-1]
    return f"{dia_semana}, {ahora.day} de {mes} de {ahora.year}, {ahora.hour:02d}:{ahora.minute:02d}"

def make_docx_from_text(texto, title="Documento"):
    if Document is None:
        raise RuntimeError("python-docx no está instalado.")
    doc = Document()
    doc.add_heading(title, level=1)
    for line in texto.splitlines():
        doc.add_paragraph(line)
    bio = io.BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio

def tts_cache_path(texto, speed, voice):
    key = hashlib.sha256((texto + f"|{speed}" + f"|{voice}").encode("utf-8")).hexdigest()
    return os.path.join(TTS_CACHE_DIR, f"{key}.mp3")

# ---------------- Whisper (cargar una vez) ----------------
WHISPER_MODEL = None
if whisper is not None:
    try:
        # modelo "small" balance velocidad/calidad
        WHISPER_MODEL = whisper.load_model(os.getenv("WHISPER_MODEL", "small"))
        print("Whisper cargado.")
    except Exception as e:
        print("No pude cargar Whisper:", e)
        WHISPER_MODEL = None
else:
    print("Whisper no está disponible (no instalado).")

# ---------------- RUTAS BASE ----------------
@app.route("/")
def index():
    if "usuario_id" not in session:
        session["usuario_id"] = str(uuid.uuid4())
    return render_template_string(HTML_TEMPLATE, APP_NAME=APP_NAME, usuario_id=session["usuario_id"])

# ---------- Endpoint /preguntar (sin streaming, seguro) ----------
@app.route("/preguntar", methods=["POST"])
def preguntar():
    data = request.get_json()
    mensaje = data.get("mensaje","")
    usuario_id = data.get("usuario_id", str(uuid.uuid4()))
    # aquí podrías llamar a OpenAI o tu lógica local
    # simple eco si no hay API configurada
    resp_text = f"Recibí: {mensaje}"
    # guardar en historial simple
    hist = load_json(MEMORY_FILE)
    if usuario_id not in hist:
        hist[usuario_id] = {"mensajes": []}
    hist[usuario_id]["mensajes"].append({"usuario":mensaje, "foschi":resp_text, "fecha": fecha_hora_en_es()})
    save_json(MEMORY_FILE, hist)
    # devolver
    return jsonify({"texto": resp_text, "imagenes": [], "borrar_historial": False})

@app.route("/historial/<usuario_id>")
def historial(usuario_id):
    path = os.path.join(DATA_DIR, f"{usuario_id}.json")
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return jsonify(json.load(f))
        except:
            return jsonify([])
    # fallback: from memory file
    mem = load_json(MEMORY_FILE).get(usuario_id, {}).get("mensajes", [])
    return jsonify(mem)

# ---------------- TTS mejorado (OpenAI TTS opcional o gTTS fallback) ----------------
@app.route("/tts")
def tts():
    texto = request.args.get("texto","")
    voice = request.args.get("voice","female")  # "male" or "female"
    speed = float(request.args.get("speed", "1.0"))
    if not texto:
        return "Texto vacío", 400

    cache_path = tts_cache_path(texto, speed, voice)
    if os.path.exists(cache_path):
        return send_file(cache_path, mimetype="audio/mpeg")

    # Si OpenAI TTS está activado y el cliente está disponible, usarlo
    if USE_OPENAI_TTS and openai_client is not None:
        try:
            # Intentamos crear audio con OpenAI (este bloque puede necesitar adaptación según SDK)
            # Nota: el siguiente llamado es genérico; ajustá si tu versión del SDK difiere.
            # Generamos wav/mp3 bytes
            audio_resp = openai_client.audio.speech.create(
                model="gpt-4o-mini-tts",
                voice="alloy" if voice == "male" else "verse",  # ejemplo; ajustá voces disponibles
                input=texto
            )
            # audio_resp podría devolver bytes o base64; esto depende del SDK y versión.
            # Intentamos escribir el contenido a un archivo si viene en .read()
            try:
                b = audio_resp.read()
                with open(cache_path, "wb") as f:
                    f.write(b)
                return send_file(cache_path, mimetype="audio/mpeg")
            except Exception:
                # fallback: intentar tratar audio_resp como JSON con 'audio' base64
                import base64
                data = getattr(audio_resp, "audio", None) or audio_resp.get("audio") if isinstance(audio_resp, dict) else None
                if data:
                    raw = base64.b64decode(data)
                    with open(cache_path, "wb") as f:
                        f.write(raw)
                    return send_file(cache_path, mimetype="audio/mpeg")
        except Exception as e:
            print("OpenAI TTS falló:", e)
            # seguimos a fallback gTTS

    # gTTS fallback
    if gTTS is None:
        return "gTTS no está instalado y OpenAI TTS no está disponible.", 500

    try:
        # generar mp3 temporal
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        gTTS(text=texto, lang="es", slow=False).save(tmp.name)
        tmp.close()

        # si pydub está disponible y speed != 1.0, aplicamos speedup en servidor
        if PYDUB_AVAILABLE and abs(speed - 1.0) > 0.01:
            audio = AudioSegment.from_file(tmp.name)
            # speedup puede chocar si speed < 0.5 o > 2.0; manejamos límites
            spd = max(0.5, min(2.0, float(speed)))
            faster = speedup(audio, playback_speed=spd)
            faster.export(cache_path, format="mp3")
            try: os.remove(tmp.name)
            except: pass
            return send_file(cache_path, mimetype="audio/mpeg")
        else:
            # si no hay pydub o speed == 1: movemos a cache y devolvemos
            shutil.move(tmp.name, cache_path)
            return send_file(cache_path, mimetype="audio/mpeg")
    except Exception as e:
        print("Error generando gTTS:", e)
        # intentar generar en memoria como fallback
        try:
            buf = io.BytesIO()
            gTTS(text=texto, lang="es", slow=False).write_to_fp(buf)
            buf.seek(0)
            return send_file(buf, mimetype="audio/mpeg")
        except Exception as e2:
            return f"Error generando TTS: {e} / {e2}", 500

# ---------------- Buscar web con Google CSE (opcional) ----------------
@app.route("/buscar_web")
def buscar_web():
    q = request.args.get("q","")
    if not q:
        return jsonify({"error":"Consulta vacía"}), 400
    if not GOOGLE_API_KEY or not GOOGLE_CSE_ID:
        return jsonify({"error":"Google CSE no está configurado (GOOGLE_API_KEY y GOOGLE_CSE_ID)"}), 400
    try:
        import requests
        url = "https://www.googleapis.com/customsearch/v1"
        params = {"key": GOOGLE_API_KEY, "cx": GOOGLE_CSE_ID, "q": q, "lr":"lang_es"}
        r = requests.get(url, params=params, timeout=6)
        data = r.json()
        # devolver resultados básicos
        items = data.get("items", [])
        results = [{"title": it.get("title"), "snippet": it.get("snippet"), "link": it.get("link")} for it in items]
        return jsonify({"results": results})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ---------------- OCR: subir_imagen ----------------
@app.route("/subir_imagen", methods=["POST"])
def subir_imagen():
    if "image" not in request.files:
        return "No se envió imagen", 400
    if not TESSERACT_AVAILABLE:
        return "OCR no disponible. Instalá pytesseract y pillow.", 500
    f = request.files["image"]
    if f.filename == "":
        return "Archivo inválido", 400
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(f.filename)[1] or ".png")
    try:
        f.save(tmp.name)
        text = pytesseract.image_to_string(Image.open(tmp.name), lang='spa+eng')
        if not text.strip():
            text = "No se detectó texto en la imagen."
        doc = make_docx_from_text(text, title=f"OCR - {f.filename}")
        return send_file(doc, as_attachment=True, download_name=os.path.splitext(f.filename)[0] + ".docx",
                         mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    except Exception as e:
        return f"Error OCR: {e}", 500
    finally:
        try: os.remove(tmp.name)
        except: pass

# ---------------- RUTAS de subida ya presentes (audio/pdf/video/file/docx) ----------------
# (estas rutas ya estaban en tu código original; las mantengo con ligeros ajustes)
def safe_remove(path):
    try:
        if os.path.exists(path): os.remove(path)
    except:
        pass

@app.route("/subir_audio", methods=["POST"])
def subir_audio():
    if "audio" not in request.files:
        return "No se envió archivo de audio", 400
    archivo = request.files["audio"]
    if archivo.filename == "":
        return "Archivo inválido", 400
    original_name = secure_filename(archivo.filename)
    tmp_audio = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(original_name)[1] or ".mp3")
    try:
        archivo.save(tmp_audio.name)
        if WHISPER_MODEL is None:
            return "Whisper no está disponible en el servidor.", 500
        result = WHISPER_MODEL.transcribe(tmp_audio.name)
        texto = result.get("text", "").strip()
        doc_bio = make_docx_from_text(texto, title=f"Transcripción - {original_name}")
        return send_file(doc_bio, as_attachment=True, download_name=os.path.splitext(original_name)[0] + ".docx",
                         mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    except Exception as e:
        return f"Error al procesar audio: {e}", 500
    finally:
        safe_remove(tmp_audio.name)

@app.route("/subir_pdf", methods=["POST"])
def subir_pdf():
    if "pdf" not in request.files:
        return "No se envió archivo PDF", 400
    archivo = request.files["pdf"]
    if archivo.filename == "":
        return "Archivo inválido", 400
    if PyPDF2 is None:
        return "PyPDF2 no está instalado en el servidor.", 500
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
        return send_file(doc_bio, as_attachment=True, download_name=os.path.splitext(original_name)[0] + ".docx",
                         mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    except Exception as e:
        return f"Error al procesar PDF: {e}", 500
    finally:
        safe_remove(tmp_pdf.name)

@app.route("/subir_video", methods=["POST"])
def subir_video():
    if "video" not in request.files:
        return "No se envió archivo de video", 400
    archivo = request.files["video"]
    if archivo.filename == "":
        return "Archivo inválido", 400
    if VideoFileClip is None:
        return "moviepy/ffmpeg no está disponible en el servidor.", 500
    original_name = secure_filename(archivo.filename)
    tmp_video = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(original_name)[1] or ".mp4")
    tmp_audio = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    try:
        archivo.save(tmp_video.name)
        clip = VideoFileClip(tmp_video.name)
        clip.audio.write_audiofile(tmp_audio.name, logger=None)
        clip.close()
        if WHISPER_MODEL is None:
            return "Whisper no está disponible en el servidor.", 500
        result = WHISPER_MODEL.transcribe(tmp_audio.name)
        texto = result.get("text", "").strip()
        doc_bio = make_docx_from_text(texto, title=f"Transcripción de video - {original_name}")
        return send_file(doc_bio, as_attachment=True, download_name=os.path.splitext(original_name)[0] + ".docx",
                         mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    except Exception as e:
        return f"Error al procesar video: {e}", 500
    finally:
        safe_remove(tmp_video.name); safe_remove(tmp_audio.name)

@app.route("/subir_archivo", methods=["POST"])
def subir_archivo():
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
            if Document is None:
                return "python-docx no está instalado.", 500
            doc = Document(tmp.name)
            partes = [p.text for p in doc.paragraphs]
            texto = "\n".join(partes)
        elif ext in [".pdf"]:
            if PyPDF2 is None:
                return "PyPDF2 no está instalado.", 500
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
        return send_file(doc_bio, as_attachment=True, download_name=os.path.splitext(original_name)[0] + ".docx",
                         mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    except Exception as e:
        return f"Error al procesar archivo: {e}", 500
    finally:
        safe_remove(tmp.name)

@app.route("/subir_docx", methods=["POST"])
def subir_docx():
    if "docx" not in request.files:
        return "No se envió archivo DOCX", 400
    archivo = request.files["docx"]
    if archivo.filename == "":
        return "Archivo inválido", 400
    if Document is None:
        return "python-docx no está instalado.", 500
    original_name = secure_filename(archivo.filename)
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".docx")
    try:
        archivo.save(tmp.name)
        doc = Document(tmp.name)
        bio = io.BytesIO()
        doc.save(bio)
        bio.seek(0)
        return send_file(bio, as_attachment=True, download_name=os.path.splitext(original_name)[0] + "_limpio.docx",
                         mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    except Exception as e:
        return f"Error al procesar docx: {e}", 500
    finally:
        safe_remove(tmp.name)

# ---------------- HTML (UI mejorada con slider velocidad y selector de voz) ----------------
HTML_TEMPLATE = r"""
<!doctype html>
<html>
<head>
<title>{{APP_NAME}}</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
/* (estilos compactados, idénticos a la versión previa con ajustes para controles) */
:root{--bg:#0b0b0b;--accent:#06b6d4;--muted:#94a3b8}
body{background:var(--bg);color:#e6eef2;font-family:Inter,system-ui,Arial;margin:0}
.header{display:flex;align-items:center;padding:12px;border-bottom:1px solid rgba(255,255,255,0.03)}
#logo{width:44px;height:44px;border-radius:8px;background:linear-gradient(135deg,#0ea5a4,#06b6d4);display:flex;align-items:center;justify-content:center;font-weight:700;margin-right:12px;cursor:pointer}
.container{display:flex;height:calc(100vh - 64px)}
.chat-area{flex:1;display:flex;flex-direction:column;padding:14px;gap:12px}
#chat{flex:1;overflow:auto;background:linear-gradient(180deg,rgba(255,255,255,0.02),rgba(255,255,255,0.01));padding:12px;border-radius:10px}
.input-row{display:flex;gap:10px;align-items:center}
.attach-btn{width:44px;height:44px;border-radius:8px;background:rgba(255,255,255,0.02);display:flex;align-items:center;justify-content:center;cursor:pointer}
.input{flex:1;display:flex;gap:8px;background:#07121a;padding:8px;border-radius:10px}
.input input{flex:1;background:transparent;border:none;color:#e6eef2;padding:8px;outline:none}
.input button{background:var(--accent);border:none;padding:8px 12px;border-radius:8px;cursor:pointer}
.controls{display:flex;gap:8px;align-items:center}
.control-item{background:rgba(255,255,255,0.02);padding:6px;border-radius:8px;font-size:13px}
.side-panel{position:fixed;left:0;top:64px;width:320px;height:calc(100vh - 64px);background:linear-gradient(180deg,#041021,#031018);transform:translateX(-110%);transition:transform .28s;padding:16px;z-index:80}
.side-panel.open{transform:translateX(0)}
.menu-item{display:flex;align-items:center;gap:12px;padding:10px;border-radius:10px;cursor:pointer}
.small{font-size:13px;padding:6px 8px;border-radius:8px}
.message{margin:8px 0;padding:10px;border-radius:10px;background:rgba(255,255,255,0.02)}
.user{align-self:flex-end;background:linear-gradient(90deg,#081423,#0b1220)}
.ai{align-self:flex-start;background:linear-gradient(90deg,#04212a,#062022)}
.play-btn{margin-left:8px;cursor:pointer}
.footer-note{position:fixed;left:20px;bottom:12px;color:#94a3b8;font-size:12px}
</style>
</head>
<body>
<div class="header">
  <div id="logo" onclick="logoClick()">F</div>
  <div>
    <div style="font-weight:700">FOSCHI IA</div>
    <div style="font-size:12px;color:#94a3b8">Tu asistente multimedia</div>
  </div>
  <div style="margin-left:auto;display:flex;gap:8px;align-items:center">
    <div class="control-item">Velocidad: <span id="speedLabel">1.45x</span></div>
    <input id="speedSlider" type="range" min="0.6" max="2.0" step="0.05" value="1.45" style="width:140px">
    <select id="voiceSelect" class="small" style="margin-left:8px">
      <option value="female" selected>Mujer</option>
      <option value="male">Hombre</option>
    </select>
  </div>
</div>

<div class="container">
  <div class="chat-area">
    <div id="chat" role="log" aria-live="polite"></div>

    <div class="input-row">
      <div class="attach-btn" id="attachBtn" title="Adjuntar archivo" onclick="togglePanel()">📎</div>
      <div class="input">
        <input id="mensaje" type="text" placeholder="Escribí tu mensaje o hablá">
        <button onclick="enviar()">Enviar</button>
      </div>
    </div>
    <div style="display:flex;gap:8px">
      <button class="small" onclick="hablar()">🎤 Hablar</button>
      <button class="small" onclick="verHistorial()">🗂️ Historial</button>
      <button class="small" onclick="borrarPantalla()">🧹 Borrar</button>
    </div>
  </div>

  <div class="side-panel" id="sidePanel" aria-hidden="true">
    <h3 style="margin-top:0">Adjuntar — opciones</h3>
    <div class="menu-item" onclick="triggerFile('audio')">🎤 Audio a texto</div>
    <div class="menu-item" onclick="triggerFile('video')">🎥 Video → Texto</div>
    <div class="menu-item" onclick="triggerFile('pdf')">📄 PDF → Texto</div>
    <div class="menu-item" onclick="triggerFile('file')">🗂 Archivo genérico</div>
    <div class="menu-item" onclick="triggerFile('docx')">✳️ Reprocesar DOCX</div>
    <div class="menu-item" onclick="triggerFile('image')">🖼 Imagen → OCR</div>
    <div style="margin-top:12px;color:#94a3b8;font-size:13px">Los archivos se procesan y se eliminan del servidor automáticamente.</div>
  </div>
</div>

<!-- Hidden inputs -->
<input id="in_audio" type="file" accept="audio/*" style="display:none"/>
<input id="in_pdf" type="file" accept="application/pdf" style="display:none"/>
<input id="in_video" type="file" accept="video/*" style="display:none"/>
<input id="in_file" type="file" accept=".txt,.md,.pdf,.docx" style="display:none"/>
<input id="in_docx" type="file" accept=".docx" style="display:none"/>
<input id="in_image" type="file" accept="image/*" style="display:none"/>

<script>
let usuario_id="{{usuario_id}}";
let vozActiva=true,audioActual=null,mensajeActual=null;
let currentPlaybackRate = parseFloat(document.getElementById("speedSlider").value);

// actualizar label slider
document.getElementById("speedSlider").addEventListener("input", (e)=>{
  currentPlaybackRate = parseFloat(e.target.value);
  document.getElementById("speedLabel").textContent = currentPlaybackRate.toFixed(2) + "x";
});

function logoClick(){ alert("FOSCHI IA — listo para ayudar 🤖"); }

function hablarTexto(texto, div=null){
  if(!vozActiva) return;
  detenerVoz();
  if(mensajeActual) mensajeActual.classList.remove("playing");
  if(div) div.classList.add("playing");
  mensajeActual = div;

  // usamos audio del servidor, pero ajustamos playbackRate en cliente si el servidor no aplicó speed
  const voice = document.getElementById("voiceSelect").value;
  audioActual = new Audio("/tts?texto=" + encodeURIComponent(texto) + "&voice=" + encodeURIComponent(voice) + "&speed=" + encodeURIComponent(currentPlaybackRate));
  audioActual.preload = "auto";
  audioActual.playbackRate = currentPlaybackRate;
  try{ audioActual.preservesPitch = true; }catch(e){}
  audioActual.onended = ()=>{ if(mensajeActual) mensajeActual.classList.remove("playing"); mensajeActual = null; };
  audioActual.play().catch(e=>console.warn("Error play audio:", e));
}

function detenerVoz(){ if(audioActual){ try{ audioActual.pause(); audioActual.currentTime=0; audioActual.src=""; audioActual.load(); audioActual=null; if(mensajeActual) mensajeActual.classList.remove("playing"); mensajeActual=null;}catch(e){console.log(e);}} }

function toggleVoz(estado=null){ vozActiva= estado!==null ? estado : !vozActiva; document.getElementById("vozBtn")?.textContent = vozActiva ? "🔊 Voz" : "🔇 Silencio"; }

function agregar(msg,cls,imagenes=[]){
  let c = document.getElementById("chat"), div = document.createElement("div");
  div.className = "message "+cls;
  // añadir botones reproducir / descargar
  let html = `<div>${msg}</div><div style="margin-top:8px">`;
  html += `<button class="small" onclick="reproducirTexto(event, ${JSON.stringify(msg)})">🔊 Reproducir</button>`;
  html += ` <button class="small" onclick="descargarMP3(event, ${JSON.stringify(msg)})">⬇️ MP3</button>`;
  html += `</div>`;
  div.innerHTML = html;
  c.appendChild(div);
  setTimeout(()=>div.classList.add("show"),50);
  imagenes.forEach(url=>{ let img=document.createElement("img"); img.src=url; img.style.maxWidth="200px"; img.style.borderRadius="8px"; div.appendChild(img); });
  c.scroll({top:c.scrollHeight,behavior:"smooth"});
  if(cls==="ai") hablarTexto(stripHtml(msg),div);
}

function reproducirTexto(ev, msg){
  ev.stopPropagation();
  hablarTexto(stripHtml(msg));
}

function descargarMP3(ev, msg){
  ev.stopPropagation();
  const voice = document.getElementById("voiceSelect").value;
  const url = "/tts?texto=" + encodeURIComponent(stripHtml(msg)) + "&voice=" + encodeURIComponent(voice) + "&speed=" + encodeURIComponent(currentPlaybackRate);
  const a = document.createElement("a");
  a.href = url;
  a.download = "foschi.mp3";
  document.body.appendChild(a); a.click(); a.remove();
}

function stripHtml(html){ let tmp=document.createElement("div"); tmp.innerHTML = html; return tmp.textContent || tmp.innerText || ""; }

function enviar(){
  let msg = document.getElementById("mensaje").value.trim(); if(!msg) return;
  agregar(msg,"user");
  document.getElementById("mensaje").value = "";
  fetch("/preguntar",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({mensaje: msg, usuario_id: usuario_id})})
  .then(r=>r.json()).then(data=>{ agregar(data.texto,"ai",data.imagenes || []); })
  .catch(e=>{ agregar("Error al comunicarse con el servidor.","ai"); console.error(e); });
}

document.getElementById("mensaje").addEventListener("keydown", e=>{ if(e.key==="Enter"){ e.preventDefault(); enviar(); } });

function hablar(){
  if('webkitSpeechRecognition' in window || 'SpeechRecognition' in window){
    const Rec = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new Rec();
    recognition.lang='es-AR'; recognition.continuous=false; recognition.interimResults=false;
    recognition.onresult = function(event){ document.getElementById("mensaje").value = event.results[0][0].transcript.toLowerCase(); enviar(); }
    recognition.onerror = function(e){ console.log(e); alert("Error reconocimiento de voz: " + e.error); }
    recognition.start();
  } else alert("Tu navegador no soporta reconocimiento de voz.");
}

function verHistorial(){
  fetch("/historial/"+usuario_id).then(r=>r.json()).then(data=>{
    document.getElementById("chat").innerHTML = "";
    if(!data || data.length === 0){ agregar("No hay historial todavía.","ai"); return; }
    (data.slice ? data.slice(-40) : data).forEach(e=>{
      agregar(`<small>${e.fecha || ''}</small><br>${escapeHtml(e.usuario || '')}`,"user");
      agregar(`<small>${e.fecha || ''}</small><br>${escapeHtml(e.foschi || '')}`,"ai");
    });
  });
}

function borrarPantalla(){ document.getElementById("chat").innerHTML = ""; }

// PANEL LATERAL & subida de archivos
const sidePanel = document.getElementById("sidePanel");
function togglePanel(open){ if(open===undefined) sidePanel.classList.toggle("open"); else if(open) sidePanel.classList.add("open"); else sidePanel.classList.remove("open"); }

const uploadMap = {
  audio: {input: "in_audio", endpoint: "/subir_audio", nameKey: "audio"},
  pdf:   {input: "in_pdf", endpoint: "/subir_pdf", nameKey: "pdf"},
  video: {input: "in_video", endpoint: "/subir_video", nameKey: "video"},
  file:  {input: "in_file", endpoint: "/subir_archivo", nameKey: "file"},
  docx:  {input: "in_docx", endpoint: "/subir_docx", nameKey: "docx"},
  image: {input: "in_image", endpoint: "/subir_imagen", nameKey: "image"}
};

function triggerFile(tipo){
  togglePanel(false);
  const map = uploadMap[tipo];
  if(!map) return alert("Tipo no soportado");
  const input = document.getElementById(map.input);
  input.value = null;
  input.click();
  input.onchange = ()=> {
    const file = input.files[0];
    if(!file) return;
    agregar(`📎 Enviando <strong>${file.name}</strong> para procesar (${tipo})...`,"ai");
    const fd = new FormData();
    fd.append(map.nameKey, file);
    fetch(map.endpoint, {method:"POST", body: fd})
      .then(resp => {
        if (resp.ok) return resp.blob();
        return resp.text().then(txt=>{ throw new Error(txt || "Error al procesar"); });
      })
      .then(blob => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        // filename inferido
        a.download = file.name.split('.').slice(0,-1).join('.') + ".docx";
        document.body.appendChild(a); a.click(); a.remove();
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

function escapeHtml(text){ var map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' }; return (text||'').replace(/[&<>"']/g, function(m){ return map[m]; }); }
</script>
<div class="footer-note">FOSCHI IA • {{APP_NAME}}</div>
</body>
</html>
"""

# ---------------- RUN ----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    # threaded=True permite atender múltiples requests en paralelo
    app.run(host="0.0.0.0", port=port, threaded=True)
