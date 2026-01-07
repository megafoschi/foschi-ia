#!/usr/bin/env python3
# coding: utf-8

import os, uuid, json, io, time
from datetime import datetime
from flask import Flask, request, jsonify, session, send_file, render_template_string, after_this_request
from flask_session import Session
from werkzeug.utils import secure_filename
from gtts import gTTS
from openai import OpenAI
import mercadopago
import PyPDF2
import docx as docx_reader
from docx import Document as DocxDocument
from werkzeug.security import generate_password_hash, check_password_hash

# ---------------- CONFIG ----------------
APP_NAME = "Foschi IA"
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
TEMP_DIR = "temp"
STATIC_DIR = "static"
USUARIOS_FILE = "usuarios.json"
PAGOS_FILE = "pagos.json"

os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)

app = Flask(__name__)
app.secret_key = str(uuid.uuid4())
Session(app)

client = OpenAI(api_key=OPENAI_API_KEY)

# ---------------- MERCADOPAGO ----------------
sdk = mercadopago.SDK(
    "APP_USR-5793113592542665-010411-d99204938ad36578d1c7d45ef1e352e1-3111235582"
)

# ---------------- FUNCIONES AUXILIARES ----------------
def cargar_usuarios():
    if os.path.exists(USUARIOS_FILE):
        with open(USUARIOS_FILE,"r",encoding="utf-8") as f:
            return json.load(f)
    return {}

def guardar_usuarios(usuarios):
    with open(USUARIOS_FILE,"w",encoding="utf-8") as f:
        json.dump(usuarios,f,indent=2)

def usuario_premium(usuario_id):
    usuarios = cargar_usuarios()
    user = usuarios.get(usuario_id)
    return bool(user and user.get("premium", False))

def activar_premium(usuario_id, plan="mensual", payment_id=None):
    usuarios = cargar_usuarios()
    if usuario_id not in usuarios:
        usuarios[usuario_id] = {"premium": True, "creado": datetime.now().isoformat()}
    else:
        usuarios[usuario_id]["premium"] = True
    usuarios[usuario_id]["plan"] = plan
    usuarios[usuario_id]["payment_id"] = payment_id
    guardar_usuarios(usuarios)

def registrar_pago(usuario_id, monto, plan, payment_id):
    pagos = {}
    if os.path.exists(PAGOS_FILE):
        with open(PAGOS_FILE,"r",encoding="utf-8") as f:
            pagos = json.load(f)
    pagos[usuario_id] = {
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "plan": plan,
        "monto": monto,
        "payment_id": str(payment_id),
        "status":"approved"
    }
    with open(PAGOS_FILE,"w",encoding="utf-8") as f:
        json.dump(pagos,f,indent=2)

# ---------------- DOCUMENTOS ----------------
def extract_text_from_pdf(path):
    text=""
    try:
        with open(path,"rb") as f:
            reader=PyPDF2.PdfReader(f)
            for page in reader.pages:
                t=page.extract_text()
                if t: text+=t+"\n"
    except: pass
    return text

def extract_text_from_docx(path):
    text=""
    try:
        doc = docx_reader.Document(path)
        for p in doc.paragraphs:
            if p.text: text+=p.text+"\n"
    except: pass
    return text

# ---------------- CHAT ----------------
DOCUMENTOS_ACTIVOS = {}  # opcional, si se usan
MAX_NO_PREMIUM = 5
PREGUNTAS_HOY = {}

def generar_respuesta(mensaje, usuario_id, lat=None, lon=None, tz=None):
    # ejemplo simple
    return {"texto": f"Respondí a '{mensaje}'", "imagenes":[]}

def guardar_en_historial(usuario_id, usuario_msg, foschi_msg):
    pass  # implementa si quieres

def cargar_historial(usuario_id):
    return []


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
 left:6px; top:-120px;
 display:none;
 background:#001f2e;
 border:1px solid #003547;
 padding:8px;
 border-radius:8px;
 box-shadow:0 6px 16px rgba(0,0,0,0.6);
 z-index:50;
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
      <button id="premiumBtn" onclick="togglePremiumMenu()">💎 Pasar a Premium</button>
      <div id="premiumMenu" style="display:none;position:absolute;top:36px;left:0;background:#001f2e;border:1px solid #003547;border-radius:6px;padding:6px;box-shadow:0 6px 16px rgba(0,0,0,0.6);z-index:100;">
        <button onclick="irPremium('mensual')">💎 Pago Mensual</button>
        <button onclick="irPremium('anual')">💎 Pago Anual</button>
      </div>
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

<!-- BARRA DE ENTRADA -->
<div id="inputBar">
  <div style="position:relative;">
    <div id="clipBtn" title="Adjuntar" onclick="toggleAdjuntosMenu()">📎</div>
    <div id="adjuntos_menu" aria-hidden="true">
      <button onclick="checkPremium('audio')">🎵 Subir Audio (mp3/wav)</button>
      <button onclick="checkPremium('doc')">📄 Subir PDF / WORD</button>
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
let preguntasHoy = 0; 
let isPremium = false; 

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
  if(!isPremium && preguntasHoy>=MAX_NO_PREMIUM){
    alert(`⚠️ Has alcanzado el límite de ${MAX_NO_PREMIUM} preguntas diarias. Pasá a Premium para más.`);
    return;
  }
  enviar();
  if(!isPremium) preguntasHoy++;
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
  const menu = document.getElementById("premiumMenu");
  menu.style.display = (menu.style.display === "block") ? "none" : "block";
  if(menu.style.display==="block"){ setTimeout(()=>window.addEventListener('click', closePremiumMenuOnClickOutside),50); }
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
  fetch(`/premium?usuario_id=${usuario_id}&tipo=${tipo}`)
    .then(r=>r.json())
    .then(d=>{
      window.open(d.qr,"_blank");
      document.getElementById("premiumMenu").style.display="none";
    });
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

function hablar(){
  if('webkitSpeechRecognition' in window || 'SpeechRecognition' in window){
    const Rec = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new Rec();
    recognition.lang='es-AR'; recognition.continuous=false; recognition.interimResults=false;
    recognition.onresult=function(event){ document.getElementById("mensaje").value=event.results[0][0].transcript.toLowerCase(); checkDailyLimit(); }
    recognition.onerror=function(e){console.log(e); alert("Error reconocimiento de voz: " + e.error);}
    recognition.start();
  }else{alert("Tu navegador no soporta reconocimiento de voz.");}
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
fetch("/estado_premium?usuario_id=" + usuario_id)
  .then(r => r.json())
  .then(d => {
    isPremium = d.premium;
    if(isPremium){
      document.getElementById("premiumBtn").textContent = "💎 Premium activo";
    }
  });

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

@app.route("/premium")
def premium():
    usuario = request.args.get("usuario_id")
    tipo = request.args.get("tipo","mensual")
    if tipo=="mensual":
        pref = {
            "items":[{"title":"Foschi IA Premium – 30 días","quantity":1,"unit_price":5000}],
            "external_reference":usuario,
            "notification_url":"https://foschi-ia.onrender.com/webhook/mp"
        }
    else:  # anual
        pref = {
            "items":[{"title":"Foschi IA Premium – 12 meses","quantity":1,"unit_price":48000}],
            "external_reference":usuario,
            "notification_url":"https://foschi-ia.onrender.com/webhook/mp"
        }
    res = sdk.preference().create(pref)
    return jsonify({"qr": res["response"]["init_point"]})

@app.route("/webhook/mp", methods=["POST"])
def webhook_mp():
    data = request.json
    if not data or "data" not in data: return "ok"
    payment_id = data["data"].get("id")
    if not payment_id: return "ok"

    payment = sdk.payment().get(payment_id)
    info = payment["response"]
    if info.get("status")=="approved":
        usuario = info.get("external_reference")
        monto = info.get("transaction_amount",0)
        plan = "anual" if monto>=30000 else "mensual"
        activar_premium(usuario, plan, payment_id)
        registrar_pago(usuario, monto, plan, payment_id)
    return "ok"

@app.route("/estado_premium")
def estado_premium():
    usuario = request.args.get("usuario_id")
    return jsonify({"premium": usuario_premium(usuario)})

@app.route("/preguntar", methods=["POST"])
def preguntar():
    data = request.get_json()
    mensaje = data.get("mensaje","")
    usuario_id = data.get("usuario_id", str(uuid.uuid4()))
    lat = data.get("lat")
    lon = data.get("lon")
    tz = data.get("timeZone") or data.get("time_zone") or None
    respuesta = generar_respuesta(mensaje, usuario_id, lat=lat, lon=lon, tz=tz)
    texto_para_hist = respuesta["texto"] if isinstance(respuesta, dict) else str(respuesta)
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
        return f"Error TTS: {e}",500

# ---------------- USUARIOS ----------------
@app.route("/registro", methods=["POST"])
def registro():
    email = request.form.get("email")
    password = request.form.get("password")
    usuarios = cargar_usuarios()
    if email in usuarios: return "❌ Email ya registrado"
    usuarios[email] = {"password": generate_password_hash(password), "premium":False, "creado":datetime.now().isoformat()}
    guardar_usuarios(usuarios)
    return "✅ Usuario creado"

@app.route("/login", methods=["POST"])
def login():
    email = request.form.get("email")
    password = request.form.get("password")
    usuarios = cargar_usuarios()
    user = usuarios.get(email)
    if not user or not check_password_hash(user["password"], password):
        return "❌ Credenciales incorrectas"
    session["usuario_id"]=email
    session["premium"]=user.get("premium",False)
    return "✅ Login correcto"

@app.route("/logout")
def logout():
    session.clear()
    return "👋 Sesión cerrada"

# ---------------- UPLOAD Y RESUMEN DOC ----------------
@app.route("/upload_doc", methods=["POST"])
def upload_doc():
    if "archivo" not in request.files: return "No se envió archivo", 400
    file = request.files["archivo"]
    usuario_id = request.form.get("usuario_id","anon")
    filename = secure_filename(file.filename)
    if not filename: return "Archivo sin nombre", 400
    ext = filename.rsplit(".",1)[-1].lower()
    if ext not in ["pdf","docx"]: return "Formato no permitido",400
    doc_id = str(uuid.uuid4())
    saved_name = f"{doc_id}_{filename}"
    temp_path = os.path.join(TEMP_DIR,saved_name)
    file.save(temp_path)
    # extraer texto
    text = extract_text_from_pdf(temp_path) if ext=="pdf" else extract_text_from_docx(temp_path)
    if not text.strip():
        os.remove(temp_path)
        return "No pude extraer texto del documento.",400
    txt_path = os.path.join(TEMP_DIR,f"{doc_id}.txt")
    with open(txt_path,"w",encoding="utf-8") as f: f.write(text)
    snippet = text[:800].replace("\n"," ") + ("..." if len(text)>800 else "")
    return jsonify({"doc_id":doc_id,"name":filename,"snippet":snippet})

@app.route("/resumir_doc", methods=["POST"])
def resumir_doc():
    data = request.get_json() or {}
    doc_id = data.get("doc_id")
    modo = data.get("modo","normal")
    usuario_id = data.get("usuario_id","anon")
    if not doc_id: return "Falta doc_id",400
    txt_path = os.path.join(TEMP_DIR,f"{doc_id}.txt")
    if not os.path.exists(txt_path): return "Documento temporal no encontrado",404
    with open(txt_path,"r",encoding="utf-8") as f: texto=f.read()
    if modo=="breve":
        instrucciones="Resumí el texto en 4-6 líneas muy concisas, puntos numerados si aplica."
    elif modo=="profundo":
        instrucciones="Resumen detallado con subtítulos y viñetas, estilo formal."
    else:
        instrucciones="Resumí en puntos claros y ordenados, destacando ideas y conclusiones."
    prompt=f"{instrucciones}\n\n--- TEXTO A RESUMIR ---\n\n{texto[:120000]}"
    try:
        resp=client.chat.completions.create(model="gpt-4-turbo",messages=[{"role":"user","content":prompt}],temperature=0.3,max_tokens=1000)
        resumen=resp.choices[0].message.content.strip()
    except Exception as e: return f"No pude generar el resumen: {e}",500
    fecha=datetime.now().strftime("%Y-%m-%d")
    resumen_filename=f"Resumen_{fecha}.docx"
    resumen_path=os.path.join(TEMP_DIR,f"{doc_id}_resumen_{fecha}.docx")
    doc = DocxDocument()
    doc.add_heading("Resumen del Documento",level=1)
    for linea in resumen.split("\n"):
        doc.add_paragraph(linea if linea.strip()!="" else "")
    doc.save(resumen_path)
    @after_this_request
    def _cleanup(response):
        for f in [resumen_path, txt_path]:
            try: os.remove(f)
            except: pass
        for f in os.listdir(TEMP_DIR):
            if f.startswith(doc_id+"_"):
                try: os.remove(os.path.join(TEMP_DIR,f))
                except: pass
        return response
    return send_file(resumen_path, as_attachment=True, mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document", download_name=resumen_filename)

# ---------------- RUN ----------------
if __name__=="__main__":
    port=int(os.environ.get("PORT",8080))
    app.run(host="0.0.0.0",port=port)