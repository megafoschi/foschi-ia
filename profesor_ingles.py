#!/usr/bin/env python3
# coding: utf-8
# ============================================================
#  FOSCHI IA — PROFESOR DE INGLÉS
#  Módulo independiente. No modifica FOSCHI_IA_PRO14.py
#  Registrar en app principal: from profesor_ingles import init_profesor_ingles
# ============================================================

import os
import json
import uuid
import re
from datetime import datetime, date

import pytz
from flask import (
    Blueprint,
    request,
    session,
    jsonify,
    render_template_string,
    send_file,
    after_this_request
)
from openai import OpenAI

# ---------- Config ----------
DATA_DIR       = "data"
INGLES_DIR     = os.path.join(DATA_DIR, "ingles")
PROGRESO_FILE  = os.path.join(INGLES_DIR, "ingles_progreso.json")
TZ             = pytz.timezone("America/Argentina/Buenos_Aires")

os.makedirs(INGLES_DIR, exist_ok=True)

# ---- Blueprint ----
profesor_bp = Blueprint("profesor_ingles", __name__)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client_ia = OpenAI(api_key=OPENAI_API_KEY)


# ============================================================
# DATOS DE NIVELES Y LECCIONES
# ============================================================

NIVELES = [
    {"codigo": "A0", "nombre": "Principiante absoluto"},
    {"codigo": "A1", "nombre": "Básico"},
    {"codigo": "A2", "nombre": "Elemental"},
    {"codigo": "B1", "nombre": "Intermedio"},
    {"codigo": "B2", "nombre": "Intermedio Alto"},
    {"codigo": "C1", "nombre": "Avanzado"},
    {"codigo": "C2", "nombre": "Experto"},
]

INDICE_NIVEL = {n["codigo"]: i for i, n in enumerate(NIVELES)}

# Lecciones por nivel — con nombre, modo (adultos/niños/ambos)
LECCIONES = {
    "A0": [
        {"id": "A0_L1", "titulo": "El abecedario", "modo": "ambos"},
        {"id": "A0_L2", "titulo": "Números del 1 al 20", "modo": "ambos"},
        {"id": "A0_L3", "titulo": "Colores", "modo": "ambos"},
        {"id": "A0_L4", "titulo": "Animales básicos", "modo": "ninos"},
        {"id": "A0_L5", "titulo": "Saludos y despedidas", "modo": "ambos"},
        {"id": "A0_L6", "titulo": "La familia", "modo": "ambos"},
    ],
    "A1": [
        {"id": "A1_L1", "titulo": "Presentarse", "modo": "ambos"},
        {"id": "A1_L2", "titulo": "El cuerpo humano", "modo": "ambos"},
        {"id": "A1_L3", "titulo": "Comida y bebida", "modo": "ambos"},
        {"id": "A1_L4", "titulo": "Los días y los meses", "modo": "ambos"},
        {"id": "A1_L5", "titulo": "Objetos de la casa", "modo": "ninos"},
        {"id": "A1_L6", "titulo": "Verbo TO BE — presente", "modo": "ambos"},
    ],
    "A2": [
        {"id": "A2_L1", "titulo": "Presente simple", "modo": "ambos"},
        {"id": "A2_L2", "titulo": "Presente continuo", "modo": "ambos"},
        {"id": "A2_L3", "titulo": "Vocabulario de trabajo", "modo": "adultos"},
        {"id": "A2_L4", "titulo": "Viajes y transporte", "modo": "ambos"},
        {"id": "A2_L5", "titulo": "En el restaurante", "modo": "adultos"},
        {"id": "A2_L6", "titulo": "Preguntar y responder", "modo": "ambos"},
    ],
    "B1": [
        {"id": "B1_L1", "titulo": "Pasado simple", "modo": "ambos"},
        {"id": "B1_L2", "titulo": "Pasado continuo", "modo": "ambos"},
        {"id": "B1_L3", "titulo": "Inglés para entrevistas laborales", "modo": "adultos"},
        {"id": "B1_L4", "titulo": "Vocabulario técnico: informática", "modo": "adultos"},
        {"id": "B1_L5", "titulo": "Conversación cotidiana", "modo": "ambos"},
        {"id": "B1_L6", "titulo": "Condicionales (if)", "modo": "ambos"},
    ],
    "B2": [
        {"id": "B2_L1", "titulo": "Tiempos perfectos", "modo": "ambos"},
        {"id": "B2_L2", "titulo": "Voz pasiva", "modo": "ambos"},
        {"id": "B2_L3", "titulo": "Inglés de negocios", "modo": "adultos"},
        {"id": "B2_L4", "titulo": "Phrasal verbs comunes", "modo": "ambos"},
        {"id": "B2_L5", "titulo": "Debate y opinión", "modo": "ambos"},
        {"id": "B2_L6", "titulo": "Escritura formal (emails)", "modo": "adultos"},
    ],
    "C1": [
        {"id": "C1_L1", "titulo": "Subjuntivo avanzado", "modo": "adultos"},
        {"id": "C1_L2", "titulo": "Vocabulario académico", "modo": "adultos"},
        {"id": "C1_L3", "titulo": "Presentaciones en inglés", "modo": "adultos"},
        {"id": "C1_L4", "titulo": "Phrasal verbs avanzados", "modo": "adultos"},
        {"id": "C1_L5", "titulo": "Idioms and expressions", "modo": "adultos"},
        {"id": "C1_L6", "titulo": "Comprensión de texto literario", "modo": "adultos"},
    ],
    "C2": [
        {"id": "C2_L1", "titulo": "Inglés técnico y científico", "modo": "adultos"},
        {"id": "C2_L2", "titulo": "Escritura creativa", "modo": "adultos"},
        {"id": "C2_L3", "titulo": "Acento y pronunciación avanzada", "modo": "adultos"},
        {"id": "C2_L4", "titulo": "Debate de nivel nativo", "modo": "adultos"},
        {"id": "C2_L5", "titulo": "Comprensión auditiva avanzada", "modo": "adultos"},
        {"id": "C2_L6", "titulo": "Preparación exámenes internacionales (IELTS / TOEFL)", "modo": "adultos"},
    ],
}

# ============================================================
# PROGRESO — guardar / cargar
# ============================================================

def _cargar_progreso():
    if not os.path.exists(PROGRESO_FILE):
        return {}
    try:
        with open(PROGRESO_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}


def _guardar_progreso(data):
    with open(PROGRESO_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _progreso_usuario(usuario):
    prog = _cargar_progreso()
    if usuario not in prog:
        prog[usuario] = {
            "nivel": None,
            "modo": None,
            "lecciones_completadas": [],
            "examenes_aprobados": [],
            "puntaje": 0,
            "racha": 0,
            "ultima_actividad": None,
        }
        _guardar_progreso(prog)
    return prog[usuario]


def _actualizar_progreso(usuario, cambios: dict):
    prog = _cargar_progreso()
    if usuario not in prog:
        _progreso_usuario(usuario)
        prog = _cargar_progreso()
    prog[usuario].update(cambios)
    prog[usuario]["ultima_actividad"] = datetime.now(TZ).strftime("%d/%m/%Y %H:%M")
    _guardar_progreso(prog)


# ============================================================
# IA — funciones de apoyo
# ============================================================

def _ia(prompt: str, max_tokens: int = 900, temperatura: float = 0.6) -> str:
    try:
        resp = client_ia.chat.completions.create(
            model="gpt-4-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=temperatura,
            max_tokens=max_tokens,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        return f"[Error IA: {e}]"


def _ia_json(prompt: str, max_tokens: int = 1200) -> dict | None:
    raw = _ia(prompt, max_tokens=max_tokens, temperatura=0.3)
    raw = re.sub(r"^```(json)?", "", raw.strip())
    raw = re.sub(r"```$", "", raw.strip()).strip()
    inicio = raw.find("{")
    fin    = raw.rfind("}")
    if inicio != -1 and fin != -1:
        raw = raw[inicio:fin + 1]
    try:
        return json.loads(raw)
    except:
        return None


# ============================================================
# EVALUACIÓN INICIAL (diagnóstico de nivel)
# ============================================================

PREGUNTAS_DIAGNOSTICO = [
    {
        "pregunta": "What is the correct sentence?",
        "opciones": ["She go to school", "She goes to school", "She going to school"],
        "correcta": 1,
        "nivel_min": "A1"
    },
    {
        "pregunta": "Complete: I ___ a student.",
        "opciones": ["am", "is", "are"],
        "correcta": 0,
        "nivel_min": "A0"
    },
    {
        "pregunta": "What does 'apple' mean?",
        "opciones": ["Manzana", "Naranja", "Uva"],
        "correcta": 0,
        "nivel_min": "A0"
    },
    {
        "pregunta": "Choose the past tense: 'I ___ to the store yesterday.'",
        "opciones": ["go", "went", "gone"],
        "correcta": 1,
        "nivel_min": "A2"
    },
    {
        "pregunta": "Which sentence uses the present perfect correctly?",
        "opciones": [
            "I have seen that movie last night.",
            "I have never eaten sushi.",
            "She has go to Paris."
        ],
        "correcta": 1,
        "nivel_min": "B1"
    },
    {
        "pregunta": "What is a synonym for 'significant'?",
        "opciones": ["Important", "Ugly", "Fast"],
        "correcta": 0,
        "nivel_min": "B2"
    },
    {
        "pregunta": "Which sentence is grammatically correct?",
        "opciones": [
            "Had she known, she would have came.",
            "Had she known, she would have come.",
            "If she would have known, she would come."
        ],
        "correcta": 1,
        "nivel_min": "C1"
    },
]


def calcular_nivel_diagnostico(respuestas: list) -> str:
    """
    respuestas: lista de índices de opciones elegidas (0,1,2)
    Devuelve el código de nivel calculado.
    """
    correctas = 0
    for i, r in enumerate(respuestas):
        if i < len(PREGUNTAS_DIAGNOSTICO):
            if r == PREGUNTAS_DIAGNOSTICO[i]["correcta"]:
                correctas += 1
    if correctas <= 1:
        return "A0"
    elif correctas == 2:
        return "A1"
    elif correctas == 3:
        return "A2"
    elif correctas == 4:
        return "B1"
    elif correctas == 5:
        return "B2"
    elif correctas == 6:
        return "C1"
    else:
        return "C2"


# ============================================================
# GENERACIÓN DE LECCIÓN CON IA
# ============================================================

def generar_leccion_ia(leccion_id: str, nivel: str, modo: str) -> str:
    """
    Genera el contenido de una lección usando IA.
    Devuelve texto HTML-friendly (con saltos de línea).
    """
    # Buscar título de la lección
    titulo = leccion_id
    for lec in LECCIONES.get(nivel, []):
        if lec["id"] == leccion_id:
            titulo = lec["titulo"]
            break

    es_nino = modo == "ninos"
    tono = (
        "Usá un tono muy amigable, simple y divertido para niños de 5 a 12 años. "
        "Incluí emojis, ejemplos con animales o juguetes, y frases muy cortas."
        if es_nino else
        "Usá un tono profesional y claro, orientado a adultos. "
        "Incluí ejemplos prácticos de la vida cotidiana, laboral o de viajes."
    )

    prompt = f"""
Sos FOSCHI IA, profesor de inglés experto.
Generá una lección completa de inglés sobre: "{titulo}"
Nivel del alumno: {nivel}

{tono}

La lección debe incluir:
1. Título claro
2. Explicación del tema (en español, breve)
3. Vocabulario clave (10 palabras/frases con traducción)
4. Reglas o estructura gramatical (si aplica)
5. 3 ejemplos en inglés con su traducción
6. Un tip o truco fácil de recordar
7. Una frase motivadora al final

Respondé en texto plano con emojis. No uses markdown con asteriscos.
"""
    return _ia(prompt, max_tokens=1000)


# ============================================================
# GENERACIÓN DE EXAMEN CON IA
# ============================================================

def generar_examen_ia(leccion_id: str, nivel: str, modo: str) -> dict | None:
    """
    Genera 5 preguntas de opción múltiple para evaluar una lección.
    Devuelve dict con lista "preguntas" o None si falla.
    """
    titulo = leccion_id
    for lec in LECCIONES.get(nivel, []):
        if lec["id"] == leccion_id:
            titulo = lec["titulo"]
            break

    es_nino = modo == "ninos"
    dificultad = "muy fácil, con oraciones cortas y vocabulario básico" if es_nino else "adecuada para adultos"

    prompt = f"""
Generá un examen de inglés de 5 preguntas de opción múltiple sobre: "{titulo}"
Nivel: {nivel}
Dificultad: {dificultad}

Respondé SOLO con JSON válido, sin texto extra, sin markdown, con esta estructura exacta:

{{
  "titulo": "Examen: {titulo}",
  "preguntas": [
    {{
      "pregunta": "texto de la pregunta en inglés",
      "opciones": ["opción A", "opción B", "opción C"],
      "correcta": 0,
      "explicacion": "Por qué esta es la respuesta correcta (en español)"
    }}
  ]
}}

- "correcta" es el índice (0, 1 o 2) de la opción correcta.
- Generá exactamente 5 preguntas.
"""
    return _ia_json(prompt, max_tokens=1400)


# ============================================================
# CONVERSACIÓN GUIADA CON IA
# ============================================================

def conversar_con_profesor(mensaje: str, nivel: str, modo: str, historial: list) -> str:
    """
    Conversación libre con el profesor de inglés.
    historial: lista de {"rol": "user"|"ai", "texto": "..."}
    """
    es_nino = modo == "ninos"
    personalidad = (
        "Sos un profesor de inglés muy amigable para niños. "
        "Respondé en español con palabras muy simples, incluí emojis y siempre alentá al alumno."
        if es_nino else
        "Sos un profesor de inglés profesional. "
        "Respondé en español, corregí errores gramaticales si el alumno escribe en inglés, "
        "explicá con ejemplos claros y usá un tono motivador pero directo."
    )

    mensajes_ia = [
        {
            "role": "system",
            "content": (
                f"{personalidad} "
                f"El alumno está en nivel {nivel}. "
                "Tu objetivo es ayudarlo a aprender inglés paso a paso."
            )
        }
    ]

    for h in historial[-6:]:
        rol = "user" if h.get("rol") == "user" else "assistant"
        mensajes_ia.append({"role": rol, "content": h.get("texto", "")})

    mensajes_ia.append({"role": "user", "content": mensaje})

    try:
        resp = client_ia.chat.completions.create(
            model="gpt-4-turbo",
            messages=mensajes_ia,
            temperature=0.7,
            max_tokens=500,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        return f"[Error en conversación: {e}]"


# ============================================================
# CERTIFICADO (texto plano, se puede extender a PDF)
# ============================================================

def generar_certificado_texto(usuario: str, nivel: str) -> str:
    nombre_nivel = next((n["nombre"] for n in NIVELES if n["codigo"] == nivel), nivel)
    fecha = datetime.now(TZ).strftime("%d/%m/%Y")
    return (
        f"╔══════════════════════════════════════╗\n"
        f"║      CERTIFICADO FOSCHI IA           ║\n"
        f"╠══════════════════════════════════════╣\n"
        f"║                                      ║\n"
        f"║  Alumno  : {usuario[:28]:<28} ║\n"
        f"║  Nivel   : {nivel} - {nombre_nivel:<23} ║\n"
        f"║  Fecha   : {fecha:<28} ║\n"
        f"║                                      ║\n"
        f"║  🏆 ¡Felicitaciones por completar     ║\n"
        f"║     este nivel de inglés!            ║\n"
        f"║                                      ║\n"
        f"╚══════════════════════════════════════╝\n"
        f"\nFirmado digitalmente por FOSCHI IA\n"
    )


# ============================================================
# HELPER — verificar si el nivel está completado
# ============================================================

def _nivel_completado(usuario: str, nivel: str) -> bool:
    prog = _progreso_usuario(usuario)
    lecciones_nivel = [l["id"] for l in LECCIONES.get(nivel, [])]
    completadas = prog.get("lecciones_completadas", [])
    examenes    = prog.get("examenes_aprobados", [])
    # Necesita completar todas las lecciones y al menos la mitad de los exámenes
    todas_lecciones = all(lid in completadas for lid in lecciones_nivel)
    mitad_examenes  = sum(1 for eid in examenes if eid.startswith(nivel)) >= (len(lecciones_nivel) // 2)
    return todas_lecciones and mitad_examenes


# ============================================================
# RUTAS DEL BLUEPRINT
# ============================================================

@profesor_bp.route("/ingles")
def ingles_home():
    """Página principal del Profesor de Inglés."""
    usuario = session.get("user_email") or session.get("usuario_id", "anonimo")
    prog = _progreso_usuario(usuario)
    return render_template_string(
        HTML_INGLES,
        usuario=usuario,
        prog=prog,
        niveles=NIVELES,
        lecciones=LECCIONES,
        preguntas_diag=PREGUNTAS_DIAGNOSTICO,
    )


@profesor_bp.route("/ingles/api/progreso", methods=["GET"])
def api_progreso():
    usuario = session.get("user_email") or session.get("usuario_id", "anonimo")
    prog = _progreso_usuario(usuario)
    return jsonify({"ok": True, "progreso": prog})


@profesor_bp.route("/ingles/api/set_modo", methods=["POST"])
def api_set_modo():
    data = request.get_json()
    usuario = session.get("user_email") or session.get("usuario_id", "anonimo")
    modo = data.get("modo")  # "ninos" | "adultos"
    if modo not in ("ninos", "adultos"):
        return jsonify({"ok": False, "error": "Modo inválido"})
    _actualizar_progreso(usuario, {"modo": modo})
    return jsonify({"ok": True})


@profesor_bp.route("/ingles/api/diagnostico/responder", methods=["POST"])
def api_diagnostico_responder():
    """Recibe las respuestas del diagnóstico y asigna nivel."""
    data = request.get_json()
    usuario  = session.get("user_email") or session.get("usuario_id", "anonimo")
    respuestas = data.get("respuestas", [])  # lista de índices
    nivel = calcular_nivel_diagnostico(respuestas)
    _actualizar_progreso(usuario, {"nivel": nivel})
    nombre_nivel = next((n["nombre"] for n in NIVELES if n["codigo"] == nivel), nivel)
    return jsonify({
        "ok": True,
        "nivel": nivel,
        "nombre_nivel": nombre_nivel,
        "mensaje": (
            f"✅ Evaluación completada. Tu nivel es {nivel} - {nombre_nivel}. "
            f"¡Vamos a empezar desde ahí!"
        )
    })


@profesor_bp.route("/ingles/api/set_nivel", methods=["POST"])
def api_set_nivel():
    """Permite al usuario elegir su nivel manualmente."""
    data = request.get_json()
    usuario = session.get("user_email") or session.get("usuario_id", "anonimo")
    nivel = data.get("nivel")
    if nivel not in INDICE_NIVEL:
        return jsonify({"ok": False, "error": "Nivel inválido"})
    _actualizar_progreso(usuario, {"nivel": nivel})
    return jsonify({"ok": True, "nivel": nivel})


@profesor_bp.route("/ingles/api/leccion", methods=["POST"])
def api_leccion():
    """Genera y devuelve el contenido de una lección."""
    data      = request.get_json()
    usuario   = session.get("user_email") or session.get("usuario_id", "anonimo")
    leccion_id = data.get("leccion_id")
    prog      = _progreso_usuario(usuario)
    nivel     = prog.get("nivel") or "A0"
    modo      = prog.get("modo") or "adultos"

    contenido = generar_leccion_ia(leccion_id, nivel, modo)

    # Marcar lección como completada
    completadas = prog.get("lecciones_completadas", [])
    if leccion_id not in completadas:
        completadas.append(leccion_id)
        puntaje = prog.get("puntaje", 0) + 10
        _actualizar_progreso(usuario, {"lecciones_completadas": completadas, "puntaje": puntaje})

    return jsonify({"ok": True, "contenido": contenido})


@profesor_bp.route("/ingles/api/examen", methods=["POST"])
def api_examen():
    """Genera un examen de 5 preguntas para una lección."""
    data      = request.get_json()
    usuario   = session.get("user_email") or session.get("usuario_id", "anonimo")
    leccion_id = data.get("leccion_id")
    prog      = _progreso_usuario(usuario)
    nivel     = prog.get("nivel") or "A0"
    modo      = prog.get("modo") or "adultos"

    examen = generar_examen_ia(leccion_id, nivel, modo)
    if not examen:
        return jsonify({"ok": False, "error": "No pude generar el examen. Intentá de nuevo."})

    return jsonify({"ok": True, "examen": examen})


@profesor_bp.route("/ingles/api/examen/calificar", methods=["POST"])
def api_calificar_examen():
    """Recibe respuestas del examen, califica y actualiza progreso."""
    data      = request.get_json()
    usuario   = session.get("user_email") or session.get("usuario_id", "anonimo")
    leccion_id = data.get("leccion_id")
    respuestas = data.get("respuestas", [])   # [{pregunta, elegida, correcta, explicacion}]
    prog      = _progreso_usuario(usuario)

    correctas = sum(1 for r in respuestas if r.get("elegida") == r.get("correcta"))
    total     = len(respuestas)
    puntaje_exam = round((correctas / total) * 100) if total else 0
    aprobado  = puntaje_exam >= 60

    if aprobado:
        examenes = prog.get("examenes_aprobados", [])
        if leccion_id not in examenes:
            examenes.append(leccion_id)
            puntaje_total = prog.get("puntaje", 0) + 20
            _actualizar_progreso(usuario, {"examenes_aprobados": examenes, "puntaje": puntaje_total})

    nivel = prog.get("nivel", "A0")
    cert  = None
    if aprobado and _nivel_completado(usuario, nivel):
        cert = generar_certificado_texto(usuario, nivel)
        # Sugerir subir al siguiente nivel
        idx_actual = INDICE_NIVEL.get(nivel, 0)
        if idx_actual + 1 < len(NIVELES):
            siguiente = NIVELES[idx_actual + 1]["codigo"]
        else:
            siguiente = None
    else:
        siguiente = None

    return jsonify({
        "ok": True,
        "puntaje": puntaje_exam,
        "correctas": correctas,
        "total": total,
        "aprobado": aprobado,
        "certificado": cert,
        "siguiente_nivel": siguiente,
        "detalle": respuestas,
    })


@profesor_bp.route("/ingles/api/conversar", methods=["POST"])
def api_conversar():
    """Conversación libre con el profesor de inglés."""
    data      = request.get_json()
    usuario   = session.get("user_email") or session.get("usuario_id", "anonimo")
    mensaje   = data.get("mensaje", "").strip()
    historial = data.get("historial", [])
    prog      = _progreso_usuario(usuario)
    nivel     = prog.get("nivel") or "A0"
    modo      = prog.get("modo") or "adultos"

    if not mensaje:
        return jsonify({"ok": False, "error": "Mensaje vacío"})

    respuesta = conversar_con_profesor(mensaje, nivel, modo, historial)
    return jsonify({"ok": True, "respuesta": respuesta})


@profesor_bp.route("/ingles/api/subir_nivel", methods=["POST"])
def api_subir_nivel():
    data    = request.get_json()
    usuario = session.get("user_email") or session.get("usuario_id", "anonimo")
    nivel   = data.get("nivel")
    if nivel not in INDICE_NIVEL:
        return jsonify({"ok": False, "error": "Nivel inválido"})
    _actualizar_progreso(usuario, {"nivel": nivel})
    nombre = next((n["nombre"] for n in NIVELES if n["codigo"] == nivel), nivel)
    return jsonify({"ok": True, "mensaje": f"🎉 ¡Pasaste al nivel {nivel} - {nombre}!"})


@profesor_bp.route("/ingles/api/lecciones_nivel", methods=["GET"])
def api_lecciones_nivel():
    usuario = session.get("user_email") or session.get("usuario_id", "anonimo")
    prog    = _progreso_usuario(usuario)
    nivel   = request.args.get("nivel") or prog.get("nivel") or "A0"
    modo    = prog.get("modo") or "adultos"

    lecs = LECCIONES.get(nivel, [])
    # Filtrar por modo (adultos ve todo, niños ve solo "ninos" y "ambos")
    if modo == "ninos":
        lecs = [l for l in lecs if l["modo"] in ("ninos", "ambos")]

    completadas = prog.get("lecciones_completadas", [])
    examenes    = prog.get("examenes_aprobados", [])

    lecs_info = [
        {
            **l,
            "completada": l["id"] in completadas,
            "examen_aprobado": l["id"] in examenes
        }
        for l in lecs
    ]
    return jsonify({"ok": True, "lecciones": lecs_info, "nivel": nivel})


# ============================================================
# FUNCIÓN DE INTEGRACIÓN — llamar desde FOSCHI_IA_PRO14.py
# ============================================================

def init_profesor_ingles(app):
    """
    Registra el blueprint del Profesor de Inglés en la app Flask principal.
    Llamar con: from profesor_ingles import init_profesor_ingles; init_profesor_ingles(app)
    """
    app.register_blueprint(profesor_bp)
    print("✅ Profesor de Inglés IA registrado en /ingles")


# ============================================================
# PLANTILLA HTML — interfaz completa del Profesor de Inglés
# ============================================================

HTML_INGLES = """
<!doctype html>
<html>
<head>
<title>🎓 Profesor de Inglés — Foschi IA</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
*{ box-sizing:border-box; }
body{
  font-family:'Segoe UI',Tahoma,Geneva,Verdana,sans-serif;
  background:#000814;
  color:#00eaff;
  margin:0; padding:0;
  min-height:100vh;
}
#header{
  display:flex; align-items:center; justify-content:space-between;
  padding:10px 20px;
  background:linear-gradient(#000814,#00111a);
  border-bottom:1px solid #00eaff33;
  box-shadow:0 0 12px #00eaff44;
  flex-wrap:wrap; gap:8px;
}
#header h1{ font-size:18px; margin:0; color:#00eaff; text-shadow:0 0 8px #00eaff; }
.back-btn{
  background:#001f2e; color:#00eaff; border:1px solid #006688;
  padding:7px 14px; border-radius:6px; cursor:pointer; font-size:14px;
  text-decoration:none;
}
.back-btn:hover{ background:#003547; }

/* PANEL PRINCIPAL */
#main{ max-width:900px; margin:0 auto; padding:16px; }

/* CARDS */
.card{
  background:rgba(0,30,50,0.85);
  border:1px solid #00eaff33;
  border-radius:14px;
  padding:18px;
  margin-bottom:16px;
  box-shadow:0 0 12px #00eaff22;
}
.card h2{ font-size:16px; color:#00eaff; margin:0 0 12px 0; }

/* BOTONES */
.btn{
  display:inline-block;
  background:#001f2e; color:#00eaff;
  border:1px solid #006688;
  padding:9px 16px; border-radius:8px;
  cursor:pointer; font-size:14px;
  margin:4px 4px 4px 0;
  transition:0.25s;
  text-shadow:0 0 4px #00eaff;
}
.btn:hover{ background:#003547; box-shadow:0 0 12px #00eaff; }
.btn.verde{ border-color:#00ff88; color:#00ff88; }
.btn.verde:hover{ background:#003a22; box-shadow:0 0 12px #00ff88; }
.btn.rojo{ border-color:#ff4444; color:#ff4444; }
.btn.rojo:hover{ background:#3a0000; }
.btn.gold{ border-color:#ffd700; color:#ffd700; animation:neonGold 1.5s infinite alternate; }
@keyframes neonGold{
  0%{ box-shadow:0 0 6px #ffd70066; }
  100%{ box-shadow:0 0 18px #ffd700; }
}

/* NIVELES */
.nivel-grid{ display:flex; flex-wrap:wrap; gap:10px; }
.nivel-btn{
  padding:10px 16px; border-radius:10px;
  border:1px solid #006688; background:#001f2e;
  color:#00eaff; cursor:pointer; font-size:14px;
  transition:0.2s;
}
.nivel-btn:hover{ background:#003547; box-shadow:0 0 10px #00eaff; }
.nivel-btn.activo{ border-color:#ffd700; color:#ffd700; }

/* LECCIONES */
.lec-item{
  display:flex; align-items:center; justify-content:space-between;
  padding:10px 14px; border-radius:10px;
  border:1px solid #00eaff22; background:#001122;
  margin-bottom:8px; flex-wrap:wrap; gap:8px;
}
.lec-titulo{ font-size:14px; }
.badge{
  font-size:11px; padding:2px 8px; border-radius:10px;
  background:#00ff8822; color:#00ff88; border:1px solid #00ff8844;
}
.badge.examen{ background:#ffd70022; color:#ffd700; border-color:#ffd70044; }

/* CONTENIDO LECCIÓN */
#contenidoLeccion{
  white-space:pre-wrap; font-size:14px; line-height:1.7;
  background:#001122; padding:14px; border-radius:10px;
  border:1px solid #00eaff22; min-height:80px;
}

/* EXAMEN */
.pregunta-bloque{ margin-bottom:18px; }
.pregunta-bloque p{ font-size:14px; margin-bottom:8px; }
.opcion{
  display:block; padding:9px 14px; margin-bottom:6px;
  border:1px solid #006688; border-radius:8px;
  background:#001f2e; color:#00eaff;
  cursor:pointer; font-size:14px; transition:0.2s;
}
.opcion:hover{ background:#003547; }
.opcion.correcta{ border-color:#00ff88; color:#00ff88; background:#003a22; }
.opcion.incorrecta{ border-color:#ff4444; color:#ff4444; background:#3a0000; }

/* CONVERSACIÓN */
#chatIngles{
  height:260px; overflow-y:auto;
  background:#001122; border:1px solid #00eaff22;
  border-radius:10px; padding:10px;
  margin-bottom:10px;
}
.msg-user{ text-align:right; color:#b4b7ff; margin:5px 0; font-size:13px; }
.msg-ai{ text-align:left; color:#00eaff; margin:5px 0; font-size:13px; }
#inputConv{ width:100%; padding:10px; background:#001122; color:#00eaff;
  border:1px solid #006688; border-radius:8px; font-size:14px; }

/* PROGRESO */
.prog-bar-wrap{ background:#001122; border-radius:10px; height:12px; overflow:hidden; margin:6px 0; }
.prog-bar{ height:100%; background:linear-gradient(90deg,#00eaff,#0077ff); transition:width 0.5s; }

/* CERTIFICADO */
#certTexto{
  font-family:monospace; white-space:pre; font-size:13px;
  background:#001122; padding:14px; border-radius:10px;
  border:1px solid #ffd70044; color:#ffd700;
}

/* SECCIONES */
.seccion{ display:none; }
.seccion.activa{ display:block; }

/* MODAL MODO */
#modalModo{
  position:fixed; inset:0; background:rgba(0,8,20,0.92);
  display:flex; align-items:center; justify-content:center;
  z-index:9999;
}
.modal-inner{
  background:linear-gradient(135deg,#001a2e,#002a44);
  border:1px solid #00eaff55; border-radius:18px;
  padding:28px; max-width:480px; width:90%;
  text-align:center;
}
.modal-inner h2{ color:#00eaff; font-size:20px; margin-bottom:16px; }
.modo-card{
  padding:18px; border-radius:12px;
  border:1px solid #006688; background:#001f2e;
  margin:8px 0; cursor:pointer; transition:0.25s;
}
.modo-card:hover{ background:#003547; box-shadow:0 0 14px #00eaff; }
.modo-card h3{ margin:0 0 6px 0; font-size:17px; }
.modo-card p{ margin:0; font-size:13px; color:#00eaff99; }

@media(max-width:600px){
  #header h1{ font-size:15px; }
  .btn{ font-size:12px; padding:7px 12px; }
  .nivel-btn{ font-size:12px; padding:8px 12px; }
}
</style>
</head>
<body>

<!-- HEADER -->
<div id="header">
  <h1>🎓 Profesor de Inglés IA — Foschi</h1>
  <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;">
    <span id="usuarioNivel" style="font-size:13px;color:#00eaff88;"></span>
    <a href="/" class="back-btn">← Volver</a>
  </div>
</div>

<!-- MODAL ELECCIÓN DE MODO (1ra vez) -->
<div id="modalModo">
  <div class="modal-inner">
    <h2>👋 ¡Bienvenido al Profesor de Inglés!</h2>
    <p style="color:#00eaff99;font-size:14px;margin-bottom:18px;">¿Cómo querés aprender?</p>
    <div class="modo-card" onclick="elegirModo('ninos')">
      <h3>👶 Modo Niños (5-12 años)</h3>
      <p>Clases simples, divertidas y con emojis 🐶🎨🎵</p>
    </div>
    <div class="modo-card" onclick="elegirModo('adultos')">
      <h3>👨 Modo Adultos</h3>
      <p>Inglés laboral, viajes, entrevistas y conversación real 💼</p>
    </div>
  </div>
</div>

<!-- MAIN -->
<div id="main">

  <!-- NAV SECCIONES -->
  <div style="display:flex;flex-wrap:wrap;gap:8px;margin-bottom:16px;" id="navBar">
    <button class="btn" onclick="irA('secInicio')">🏠 Inicio</button>
    <button class="btn" onclick="irA('secLecciones')">📚 Lecciones</button>
    <button class="btn" onclick="irA('secExamen')">📝 Examen</button>
    <button class="btn" onclick="irA('secConversacion')">💬 Conversar</button>
    <button class="btn" onclick="irA('secProgreso')">📈 Progreso</button>
    <button class="btn" onclick="irA('secDiagnostico')">🔍 Diagnóstico</button>
  </div>

  <!-- INICIO -->
  <div id="secInicio" class="seccion activa">
    <div class="card">
      <h2>🎓 Foschi IA Profesor de Inglés</h2>
      <p style="font-size:14px;color:#00eaff99;line-height:1.7;">
        Aprendé inglés desde cero con lecciones generadas por IA, exámenes, 
        sistema de niveles CEFR (A0 → C2) y seguimiento de tu progreso.<br><br>
        <strong>¿Cómo empezar?</strong><br>
        1️⃣ Hacé el <em>Diagnóstico</em> para que te asignemos tu nivel automáticamente.<br>
        2️⃣ O elegí tu nivel manualmente desde <em>Lecciones</em>.<br>
        3️⃣ Completá lecciones, rendí exámenes y subí de nivel.<br>
        4️⃣ Usá la sección <em>Conversar</em> para practicar con el profesor.
      </p>
      <div id="resumenInicio" style="margin-top:12px;"></div>
    </div>
  </div>

  <!-- DIAGNÓSTICO -->
  <div id="secDiagnostico" class="seccion">
    <div class="card">
      <h2>🔍 Evaluación inicial de nivel</h2>
      <p style="font-size:13px;color:#00eaff88;margin-bottom:14px;">
        Respondé estas 7 preguntas para que Foschi IA determine tu nivel automáticamente.
      </p>
      <div id="diagPreguntas"></div>
      <button class="btn verde" id="btnEnviarDiag" onclick="enviarDiagnostico()" style="display:none;margin-top:10px;">
        ✅ Enviar respuestas
      </button>
      <div id="diagResultado" style="margin-top:14px;font-size:15px;"></div>
    </div>
  </div>

  <!-- LECCIONES -->
  <div id="secLecciones" class="seccion">
    <div class="card">
      <h2>📚 Lecciones</h2>

      <!-- Selector de nivel -->
      <p style="font-size:13px;color:#00eaff88;margin-bottom:10px;">Elegí un nivel:</p>
      <div class="nivel-grid" id="nivelGrid">
        {% for n in niveles %}
        <div class="nivel-btn" id="nbtn_{{n.codigo}}" onclick="setNivel('{{n.codigo}}')">
          {{n.codigo}} — {{n.nombre}}
        </div>
        {% endfor %}
      </div>

      <!-- Lista de lecciones -->
      <div id="listaLecciones" style="margin-top:16px;"></div>
    </div>

    <!-- Contenido lección -->
    <div class="card" id="tarjetaLeccion" style="display:none;">
      <h2 id="tituloLeccion">Lección</h2>
      <div id="contenidoLeccion">Cargando...</div>
      <div style="margin-top:14px;display:flex;gap:8px;flex-wrap:wrap;">
        <button class="btn" onclick="verExamenLeccionActual()">📝 Rendir examen</button>
        <button class="btn rojo" onclick="cerrarLeccion()">✕ Cerrar lección</button>
      </div>
    </div>
  </div>

  <!-- EXAMEN -->
  <div id="secExamen" class="seccion">
    <div class="card">
      <h2>📝 Examen</h2>
      <p style="font-size:13px;color:#00eaff88;" id="examenInfo">
        Primero abrí una lección y hacé clic en "Rendir examen", 
        o seleccioná una lección acá abajo.
      </p>
      <div id="listaLeccionesExamen"></div>
      <div id="bloqueExamen" style="display:none;">
        <h3 id="examenTitulo" style="font-size:15px;margin-bottom:14px;"></h3>
        <div id="preguntasExamen"></div>
        <button class="btn verde" id="btnCalificar" onclick="calificarExamen()" style="display:none;margin-top:10px;">
          ✅ Ver resultado
        </button>
        <div id="resultadoExamen" style="margin-top:14px;"></div>
      </div>
    </div>
  </div>

  <!-- CONVERSACIÓN -->
  <div id="secConversacion" class="seccion">
    <div class="card">
      <h2>💬 Conversación con el Profesor</h2>
      <p style="font-size:13px;color:#00eaff88;margin-bottom:10px;">
        Practicá inglés libremente. Podés escribir en español o en inglés, y el profesor te ayudará.
      </p>
      <div id="chatIngles"></div>
      <div style="display:flex;gap:8px;">
        <input id="inputConv" type="text" placeholder="Escribí tu mensaje..." 
               onkeydown="if(event.key==='Enter') enviarConversacion()">
        <button class="btn verde" onclick="enviarConversacion()">Enviar</button>
      </div>
    </div>
  </div>

  <!-- PROGRESO -->
  <div id="secProgreso" class="seccion">
    <div class="card">
      <h2>📈 Tu progreso</h2>
      <div id="bloqueProgreso">Cargando...</div>
    </div>
    <div class="card" id="bloqueCertificado" style="display:none;">
      <h2>🏆 Certificado</h2>
      <pre id="certTexto"></pre>
    </div>
  </div>

</div><!-- /main -->

<script>
// ===== VARIABLES =====
let historialConv = [];
let leccionActualId = null;
let nivelActual = null;
let modoActual = null;
let examenActual = null;
let respuestasExamen = {};

// ===== INIT =====
window.onload = async function(){
  await cargarProgreso();
};

async function cargarProgreso(){
  const r = await fetch("/ingles/api/progreso");
  const d = await r.json();
  if(!d.ok) return;
  const p = d.progreso;
  nivelActual = p.nivel;
  modoActual  = p.modo;

  if(!modoActual){
    document.getElementById("modalModo").style.display = "flex";
  } else {
    document.getElementById("modalModo").style.display = "none";
  }

  actualizarUIProgreso(p);
  if(nivelActual) cargarLeccionesNivel(nivelActual);
  mostrarResumenInicio(p);
}

function mostrarResumenInicio(p){
  const div = document.getElementById("resumenInicio");
  if(!p.nivel){ div.innerHTML = ""; return; }
  const pct = Math.min(100, Math.round((p.puntaje || 0) / 5));
  div.innerHTML = `
    <p style="font-size:14px;">
      📊 Nivel actual: <strong>${p.nivel}</strong> &nbsp;|&nbsp;
      🏆 Puntaje: <strong>${p.puntaje || 0}</strong> pts &nbsp;|&nbsp;
      📚 Lecciones: <strong>${(p.lecciones_completadas||[]).length}</strong> &nbsp;|&nbsp;
      🎓 Modo: <strong>${p.modo === 'ninos' ? '👶 Niños' : '👨 Adultos'}</strong>
    </p>
    <div class="prog-bar-wrap"><div class="prog-bar" style="width:${pct}%"></div></div>
  `;

  const lbl = document.getElementById("usuarioNivel");
  if(lbl) lbl.textContent = `Nivel: ${p.nivel} | ${p.puntaje||0} pts`;
}

function actualizarUIProgreso(p){
  const div = document.getElementById("bloqueProgreso");
  if(!div) return;
  const completadas = (p.lecciones_completadas||[]).length;
  const examenes    = (p.examenes_aprobados||[]).length;
  div.innerHTML = `
    <p style="font-size:14px;line-height:2;">
      🎯 Nivel: <strong>${p.nivel || "Sin asignar"}</strong><br>
      🎓 Modo: <strong>${p.modo === 'ninos' ? '👶 Niños' : p.modo === 'adultos' ? '👨 Adultos' : 'Sin elegir'}</strong><br>
      📚 Lecciones completadas: <strong>${completadas}</strong><br>
      📝 Exámenes aprobados: <strong>${examenes}</strong><br>
      🏆 Puntaje total: <strong>${p.puntaje || 0} puntos</strong><br>
      🕐 Última actividad: <strong>${p.ultima_actividad || "—"}</strong>
    </p>
    <button class="btn" onclick="cambiarModo()">🔄 Cambiar modo</button>
  `;
  // Actualizar botón nivel activo
  document.querySelectorAll(".nivel-btn").forEach(b => b.classList.remove("activo"));
  if(p.nivel){
    const nb = document.getElementById("nbtn_"+p.nivel);
    if(nb) nb.classList.add("activo");
  }
}

// ===== MODO =====
async function elegirModo(modo){
  await fetch("/ingles/api/set_modo",{
    method:"POST",
    headers:{"Content-Type":"application/json"},
    body:JSON.stringify({modo})
  });
  modoActual = modo;
  document.getElementById("modalModo").style.display = "none";
  await cargarProgreso();
}

function cambiarModo(){
  document.getElementById("modalModo").style.display = "flex";
}

// ===== SECCIONES =====
function irA(id){
  document.querySelectorAll(".seccion").forEach(s => s.classList.remove("activa"));
  document.getElementById(id).classList.add("activa");
  if(id === "secProgreso") cargarVistaProgreso();
  if(id === "secDiagnostico") renderDiagnostico();
  if(id === "secLecciones" && nivelActual) cargarLeccionesNivel(nivelActual);
  if(id === "secExamen") cargarLeccionesParaExamen();
}

// ===== DIAGNÓSTICO =====
const PREGUNTAS_DIAG = {{ preguntas_diag | tojson }};
let respDiag = {};

function renderDiagnostico(){
  const div = document.getElementById("diagPreguntas");
  respDiag = {};
  div.innerHTML = "";
  PREGUNTAS_DIAG.forEach((preg, i) => {
    let ops = preg.opciones.map((op, j) =>
      `<div class="opcion" id="dop_${i}_${j}" onclick="elegirDiag(${i},${j})">${op}</div>`
    ).join("");
    div.innerHTML += `
      <div class="pregunta-bloque">
        <p><strong>${i+1}.</strong> ${preg.pregunta}</p>
        ${ops}
      </div>`;
  });
  document.getElementById("btnEnviarDiag").style.display = "none";
  document.getElementById("diagResultado").innerHTML = "";
}

function elegirDiag(preg, op){
  respDiag[preg] = op;
  // Highlight
  PREGUNTAS_DIAG[preg].opciones.forEach((_, j) => {
    const el = document.getElementById(`dop_${preg}_${j}`);
    el.style.borderColor = j === op ? "#ffd700" : "#006688";
    el.style.color = j === op ? "#ffd700" : "#00eaff";
  });
  if(Object.keys(respDiag).length === PREGUNTAS_DIAG.length)
    document.getElementById("btnEnviarDiag").style.display = "inline-block";
}

async function enviarDiagnostico(){
  const resp = PREGUNTAS_DIAG.map((_,i) => respDiag[i] ?? -1);
  const r = await fetch("/ingles/api/diagnostico/responder",{
    method:"POST", headers:{"Content-Type":"application/json"},
    body:JSON.stringify({respuestas:resp})
  });
  const d = await r.json();
  const div = document.getElementById("diagResultado");
  div.innerHTML = `<p style="color:#00ff88;font-size:15px;">${d.mensaje}</p>`;
  nivelActual = d.nivel;
  await cargarProgreso();
}

// ===== NIVEL / LECCIONES =====
async function setNivel(nivel){
  await fetch("/ingles/api/set_nivel",{
    method:"POST", headers:{"Content-Type":"application/json"},
    body:JSON.stringify({nivel})
  });
  nivelActual = nivel;
  document.querySelectorAll(".nivel-btn").forEach(b => b.classList.remove("activo"));
  const nb = document.getElementById("nbtn_"+nivel);
  if(nb) nb.classList.add("activo");
  await cargarLeccionesNivel(nivel);
  await cargarProgreso();
}

async function cargarLeccionesNivel(nivel){
  const r = await fetch(`/ingles/api/lecciones_nivel?nivel=${nivel}`);
  const d = await r.json();
  if(!d.ok) return;
  const div = document.getElementById("listaLecciones");
  div.innerHTML = `<p style="font-size:13px;color:#00eaff88;margin-bottom:10px;">Nivel ${d.nivel}</p>`;
  d.lecciones.forEach(l => {
    const badgeLec  = l.completada ? '<span class="badge">✅ Completada</span>' : "";
    const badgeExam = l.examen_aprobado ? '<span class="badge examen">🏆 Examen OK</span>' : "";
    div.innerHTML += `
      <div class="lec-item">
        <span class="lec-titulo">📖 ${l.titulo}</span>
        <div style="display:flex;align-items:center;gap:6px;">
          ${badgeLec} ${badgeExam}
          <button class="btn" onclick="abrirLeccion('${l.id}','${l.titulo}')">Ver lección</button>
        </div>
      </div>`;
  });
}

async function abrirLeccion(id, titulo){
  leccionActualId = id;
  document.getElementById("tituloLeccion").textContent = "📖 " + titulo;
  document.getElementById("contenidoLeccion").textContent = "⏳ Generando lección con IA...";
  document.getElementById("tarjetaLeccion").style.display = "block";
  document.getElementById("tarjetaLeccion").scrollIntoView({behavior:"smooth"});

  const r = await fetch("/ingles/api/leccion",{
    method:"POST", headers:{"Content-Type":"application/json"},
    body:JSON.stringify({leccion_id:id})
  });
  const d = await r.json();
  document.getElementById("contenidoLeccion").textContent = d.ok ? d.contenido : "Error cargando lección.";
  await cargarProgreso();
}

function cerrarLeccion(){
  document.getElementById("tarjetaLeccion").style.display = "none";
  leccionActualId = null;
}

function verExamenLeccionActual(){
  if(!leccionActualId){ alert("Abrí una lección primero."); return; }
  irA("secExamen");
  cargarExamen(leccionActualId);
}

// ===== EXAMEN =====
async function cargarLeccionesParaExamen(){
  if(!nivelActual) return;
  const r = await fetch(`/ingles/api/lecciones_nivel?nivel=${nivelActual}`);
  const d = await r.json();
  if(!d.ok) return;
  const div = document.getElementById("listaLeccionesExamen");
  div.innerHTML = '<p style="font-size:13px;color:#00eaff88;margin-bottom:8px;">Elegí una lección para rendir su examen:</p>';
  d.lecciones.forEach(l => {
    const badge = l.examen_aprobado ? '🏆' : '';
    div.innerHTML += `<button class="btn" onclick="cargarExamen('${l.id}')">${badge} ${l.titulo}</button>`;
  });
}

async function cargarExamen(leccionId){
  examenActual = null;
  respuestasExamen = {};
  document.getElementById("bloqueExamen").style.display = "block";
  document.getElementById("examenTitulo").textContent = "⏳ Generando examen con IA...";
  document.getElementById("preguntasExamen").innerHTML = "";
  document.getElementById("btnCalificar").style.display = "none";
  document.getElementById("resultadoExamen").innerHTML = "";
  leccionActualId = leccionId;

  const r = await fetch("/ingles/api/examen",{
    method:"POST", headers:{"Content-Type":"application/json"},
    body:JSON.stringify({leccion_id:leccionId})
  });
  const d = await r.json();
  if(!d.ok){
    document.getElementById("examenTitulo").textContent = "❌ Error generando examen";
    return;
  }
  examenActual = d.examen;
  renderExamen(d.examen);
}

function renderExamen(examen){
  document.getElementById("examenTitulo").textContent = "📝 " + examen.titulo;
  const div = document.getElementById("preguntasExamen");
  div.innerHTML = "";
  examen.preguntas.forEach((preg, i) => {
    let ops = preg.opciones.map((op, j) =>
      `<div class="opcion" id="eop_${i}_${j}" onclick="elegirExamen(${i},${j},${preg.correcta},'${(preg.explicacion||"").replace(/'/g,"\\'")}')">
        ${String.fromCharCode(65+j)}) ${op}
      </div>`
    ).join("");
    div.innerHTML += `
      <div class="pregunta-bloque">
        <p><strong>${i+1}.</strong> ${preg.pregunta}</p>
        ${ops}
      </div>`;
  });
}

function elegirExamen(preg, op, correcta, explicacion){
  respuestasExamen[preg] = op;
  examenActual.preguntas[preg].opciones.forEach((_,j) => {
    const el = document.getElementById(`eop_${preg}_${j}`);
    el.style.borderColor = j === op ? "#ffd700" : "#006688";
    el.style.color = j === op ? "#ffd700" : "#00eaff";
  });
  if(Object.keys(respuestasExamen).length === examenActual.preguntas.length)
    document.getElementById("btnCalificar").style.display = "inline-block";
}

async function calificarExamen(){
  const respuestas = examenActual.preguntas.map((preg, i) => ({
    pregunta: preg.pregunta,
    elegida: respuestasExamen[i] ?? -1,
    correcta: preg.correcta,
    explicacion: preg.explicacion || ""
  }));

  // Marcar visualmente
  examenActual.preguntas.forEach((preg, i) => {
    const elegida = respuestasExamen[i] ?? -1;
    preg.opciones.forEach((_, j) => {
      const el = document.getElementById(`eop_${i}_${j}`);
      if(j === preg.correcta) el.classList.add("correcta");
      else if(j === elegida) el.classList.add("incorrecta");
    });
  });

  const r = await fetch("/ingles/api/examen/calificar",{
    method:"POST", headers:{"Content-Type":"application/json"},
    body:JSON.stringify({leccion_id:leccionActualId, respuestas})
  });
  const d = await r.json();
  const color = d.aprobado ? "#00ff88" : "#ff4444";
  let html = `
    <p style="color:${color};font-size:16px;font-weight:bold;">
      ${d.aprobado ? "🎉 ¡Aprobaste!" : "❌ No aprobaste. ¡Podés intentarlo de nuevo!"}<br>
      Puntaje: ${d.puntaje}% (${d.correctas}/${d.total} correctas)
    </p>`;

  respuestas.forEach((res, i) => {
    html += `<p style="font-size:13px;color:#00eaff88;">
      ${i+1}. ${res.elegida === res.correcta ? "✅" : "❌"} ${res.explicacion}
    </p>`;
  });

  if(d.siguiente_nivel){
    html += `<button class="btn gold" onclick="subirNivel('${d.siguiente_nivel}')">
      🚀 Pasar al nivel ${d.siguiente_nivel}
    </button>`;
  }
  if(d.certificado){
    html += `<div style="margin-top:12px;">
      <button class="btn" onclick="verCertificado(\`${d.certificado.replace(/`/g,"\\`")}\`)">🏆 Ver certificado</button>
    </div>`;
  }
  document.getElementById("resultadoExamen").innerHTML = html;
  document.getElementById("btnCalificar").style.display = "none";
  await cargarProgreso();
}

async function subirNivel(nivel){
  const r = await fetch("/ingles/api/subir_nivel",{
    method:"POST", headers:{"Content-Type":"application/json"},
    body:JSON.stringify({nivel})
  });
  const d = await r.json();
  nivelActual = nivel;
  alert(d.mensaje || "¡Nivel actualizado!");
  await cargarProgreso();
  irA("secLecciones");
}

// ===== CONVERSACIÓN =====
async function enviarConversacion(){
  const inp = document.getElementById("inputConv");
  const msg = inp.value.trim();
  if(!msg) return;
  inp.value = "";
  const chat = document.getElementById("chatIngles");
  chat.innerHTML += `<div class="msg-user">👤 ${msg}</div>`;
  chat.scrollTop = chat.scrollHeight;
  historialConv.push({rol:"user", texto:msg});

  const r = await fetch("/ingles/api/conversar",{
    method:"POST", headers:{"Content-Type":"application/json"},
    body:JSON.stringify({mensaje:msg, historial:historialConv})
  });
  const d = await r.json();
  if(d.ok){
    chat.innerHTML += `<div class="msg-ai">🎓 ${d.respuesta}</div>`;
    historialConv.push({rol:"ai", texto:d.respuesta});
  }
  chat.scrollTop = chat.scrollHeight;
}

// ===== PROGRESO VISTA =====
async function cargarVistaProgreso(){
  const r = await fetch("/ingles/api/progreso");
  const d = await r.json();
  if(d.ok) actualizarUIProgreso(d.progreso);
}

// ===== CERTIFICADO =====
function verCertificado(texto){
  irA("secProgreso");
  document.getElementById("bloqueCertificado").style.display = "block";
  document.getElementById("certTexto").textContent = texto;
}
</script>
</body>
</html>
"""


# ============================================================
# PUNTO DE ENTRADA STANDALONE (prueba local)
# ============================================================
if __name__ == "__main__":
    from flask import Flask, session
    _app = Flask(__name__)
    _app.secret_key = "test_ingles"
    init_profesor_ingles(_app)
    _app.run(debug=True, port=5001)
