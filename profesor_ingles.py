# profesor_ingles.py
# Módulo del Modo Profesor de Inglés para FOSCHI IA
# v2 — con examen, diccionario, historial de contexto y prompts mejorados

import json
import os
from datetime import datetime, date

INGLES_FILE = "data/progreso_ingles.json"

# ──────────────────────────────────────────────
#  NIVELES CEFR
# ──────────────────────────────────────────────

NIVELES = {
    "A1": {"nombre": "Principiante",     "orden": 1, "emoji": "🌱"},
    "A2": {"nombre": "Básico",           "orden": 2, "emoji": "📗"},
    "B1": {"nombre": "Intermedio",       "orden": 3, "emoji": "📘"},
    "B2": {"nombre": "Intermedio alto",  "orden": 4, "emoji": "📙"},
    "C1": {"nombre": "Avanzado",         "orden": 5, "emoji": "🏆"},
    "C2": {"nombre": "Experto",          "orden": 6, "emoji": "👑"},
}

# ──────────────────────────────────────────────
#  ESCENARIOS DE CONVERSACIÓN REAL (Nivel 4)
# ──────────────────────────────────────────────

ESCENARIOS = {
    "entrevista": {
        "emoji": "💼",
        "nombre": "Entrevista de trabajo",
        "apertura": "Good morning! Please, have a seat. Tell me a little about yourself and why you're interested in this position.",
    },
    "aeropuerto": {
        "emoji": "✈️",
        "nombre": "Aeropuerto",
        "apertura": "Good afternoon! May I see your passport and boarding pass, please? Where are you travelling to today?",
    },
    "restaurante": {
        "emoji": "🍽️",
        "nombre": "Restaurante",
        "apertura": "Welcome! Do you have a reservation? How many people will be dining with us today?",
    },
    "hotel": {
        "emoji": "🏨",
        "nombre": "Hotel",
        "apertura": "Good evening! Welcome to The Grand Hotel. Do you have a reservation? May I have your name, please?",
    },
    "negocios": {
        "emoji": "🤝",
        "nombre": "Reunión de negocios",
        "apertura": "Good morning, everyone. Let's get started. Today we're here to discuss our Q3 performance and upcoming strategy. Could you introduce yourself briefly?",
    },
    "viaje": {
        "emoji": "🌍",
        "nombre": "Viaje al extranjero",
        "apertura": "Welcome to London! Are you here for tourism or business? How long are you planning to stay?",
    },
    "amigos": {
        "emoji": "👥",
        "nombre": "Conversación con amigos",
        "apertura": "Hey! Long time no see! How have you been? What have you been up to lately?",
    },
    "medico": {
        "emoji": "🏥",
        "nombre": "Médico / Doctor",
        "apertura": "Good morning! I'm Dr. Smith. Please have a seat. What seems to be the problem today?",
    },
    "banco": {
        "emoji": "🏦",
        "nombre": "Banco",
        "apertura": "Good afternoon! Welcome to City Bank. How can I assist you today?",
    },
    "tienda": {
        "emoji": "🛍️",
        "nombre": "Tienda / Shopping",
        "apertura": "Hi there! Welcome to our store. Are you looking for something specific today, or just browsing?",
    },
}

# ──────────────────────────────────────────────
#  TEMAS POR NIVEL (para lecciones)
# ──────────────────────────────────────────────

TEMAS_POR_NIVEL = {
    "A1": ["saludos y presentaciones", "números y colores", "familia y descripción personal", "objetos cotidianos", "días y meses"],
    "A2": ["tiempo libre y hobbies", "ir de compras", "pedir comida", "el cuerpo humano", "viajes cortos"],
    "B1": ["trabajo y profesiones", "planes futuros", "experiencias pasadas", "opiniones y preferencias", "el medio ambiente"],
    "B2": ["debate y argumentación", "noticias y actualidad", "cultura y arte", "tecnología", "economía básica"],
    "C1": ["lenguaje formal e informal", "expresiones idiomáticas", "presentaciones profesionales", "análisis crítico", "literatura"],
    "C2": ["lenguaje académico", "negociación avanzada", "humor y sarcasmo", "discurso político", "filosofía"],
}

# ──────────────────────────────────────────────
#  UTILIDADES DE DATOS
# ──────────────────────────────────────────────

def _load():
    if not os.path.exists(INGLES_FILE):
        return {}
    try:
        with open(INGLES_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save(data):
    os.makedirs(os.path.dirname(INGLES_FILE), exist_ok=True)
    with open(INGLES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _perfil_default():
    return {
        "nivel": "A1",
        "lecciones_completadas": 0,
        "palabras_aprendidas": 0,
        "puntaje_total": 0,
        "pronunciacion_pct": 0,
        "racha_dias": 0,
        "ultimo_estudio": None,
        "errores_frecuentes": [],
        "logros": [],
        "modo_activo": None,
        "escenario_activo": None,
        "examenes_completados": 0,
        "mejor_puntaje_examen": 0,
    }

# ──────────────────────────────────────────────
#  API PÚBLICA
# ──────────────────────────────────────────────

def obtener_perfil(usuario):
    data = _load()
    if usuario not in data:
        data[usuario] = _perfil_default()
        _save(data)
    # Migrar perfiles viejos
    perfil = data[usuario]
    for k, v in _perfil_default().items():
        if k not in perfil:
            perfil[k] = v
    return perfil


def guardar_perfil(usuario, perfil):
    data = _load()
    data[usuario] = perfil
    _save(data)


def actualizar_racha(usuario):
    """Actualiza la racha de días consecutivos de estudio."""
    data = _load()
    perfil = data.get(usuario, _perfil_default())
    hoy = str(date.today())
    ultimo = perfil.get("ultimo_estudio")
    if ultimo == hoy:
        pass
    elif ultimo == str(date.fromordinal(date.today().toordinal() - 1)):
        perfil["racha_dias"] = perfil.get("racha_dias", 0) + 1
    else:
        perfil["racha_dias"] = 1
    perfil["ultimo_estudio"] = hoy
    data[usuario] = perfil
    _save(data)
    return perfil


def sumar_puntos(usuario, puntos, palabras=0):
    data = _load()
    perfil = data.get(usuario, _perfil_default())
    perfil["puntaje_total"] = perfil.get("puntaje_total", 0) + puntos
    perfil["palabras_aprendidas"] = perfil.get("palabras_aprendidas", 0) + palabras
    data[usuario] = perfil
    _save(data)


def registrar_error(usuario, error):
    """Guarda los errores más frecuentes (máximo 20)."""
    data = _load()
    perfil = data.get(usuario, _perfil_default())
    errores = perfil.get("errores_frecuentes", [])
    errores.append(error)
    perfil["errores_frecuentes"] = errores[-20:]
    data[usuario] = perfil
    _save(data)


def completar_leccion(usuario):
    data = _load()
    perfil = data.get(usuario, _perfil_default())
    perfil["lecciones_completadas"] = perfil.get("lecciones_completadas", 0) + 1
    data[usuario] = perfil
    _save(data)
    return _verificar_logros(usuario)


def registrar_examen(usuario, puntaje):
    """Registra un examen completado y actualiza el mejor puntaje."""
    data = _load()
    perfil = data.get(usuario, _perfil_default())
    perfil["examenes_completados"] = perfil.get("examenes_completados", 0) + 1
    if puntaje > perfil.get("mejor_puntaje_examen", 0):
        perfil["mejor_puntaje_examen"] = puntaje
    perfil["puntaje_total"] = perfil.get("puntaje_total", 0) + puntaje
    data[usuario] = perfil
    _save(data)
    return _verificar_logros(usuario)


def _verificar_logros(usuario):
    data = _load()
    perfil = data.get(usuario, _perfil_default())
    logros = set(perfil.get("logros", []))
    lecciones = perfil.get("lecciones_completadas", 0)
    racha = perfil.get("racha_dias", 0)
    palabras = perfil.get("palabras_aprendidas", 0)
    examenes = perfil.get("examenes_completados", 0)
    mejor_exam = perfil.get("mejor_puntaje_examen", 0)

    nuevos = []
    if lecciones >= 1 and "primera_leccion" not in logros:
        logros.add("primera_leccion"); nuevos.append("🎉 Primera lección completada")
    if lecciones >= 10 and "10_lecciones" not in logros:
        logros.add("10_lecciones"); nuevos.append("🏅 10 lecciones completadas")
    if lecciones >= 50 and "50_lecciones" not in logros:
        logros.add("50_lecciones"); nuevos.append("🥇 50 lecciones completadas")
    if racha >= 7 and "racha_7" not in logros:
        logros.add("racha_7"); nuevos.append("🔥 7 días seguidos estudiando")
    if racha >= 30 and "racha_30" not in logros:
        logros.add("racha_30"); nuevos.append("⚡ 30 días de racha")
    if palabras >= 100 and "100_palabras" not in logros:
        logros.add("100_palabras"); nuevos.append("📖 100 palabras aprendidas")
    if palabras >= 500 and "500_palabras" not in logros:
        logros.add("500_palabras"); nuevos.append("📚 500 palabras aprendidas")
    if examenes >= 1 and "primer_examen" not in logros:
        logros.add("primer_examen"); nuevos.append("📝 Primer examen completado")
    if mejor_exam >= 90 and "examen_90" not in logros:
        logros.add("examen_90"); nuevos.append("⭐ Más de 90 pts en un examen")
    if mejor_exam >= 100 and "examen_perfecto" not in logros:
        logros.add("examen_perfecto"); nuevos.append("💯 ¡Examen perfecto!")

    perfil["logros"] = list(logros)
    data[usuario] = perfil
    _save(data)
    return nuevos


def resumen_progreso(usuario):
    """Devuelve texto formateado del progreso del usuario."""
    perfil = obtener_perfil(usuario)
    nivel = perfil.get("nivel", "A1")
    info_nivel = NIVELES.get(nivel, NIVELES["A1"])
    logros = perfil.get("logros", [])
    racha = perfil.get("racha_dias", 0)
    llama = "🔥" if racha >= 3 else ""

    return f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 **Tu progreso en inglés**
━━━━━━━━━━━━━━━━━━━━━━━━━━━
{info_nivel['emoji']} Nivel: **{nivel} — {info_nivel['nombre']}**
📚 Lecciones completadas: **{perfil.get('lecciones_completadas', 0)}**
📝 Palabras aprendidas: **{perfil.get('palabras_aprendidas', 0)}**
🎯 Pronunciación: **{perfil.get('pronunciacion_pct', 0)}%**
{llama} Racha: **{racha} día{'s' if racha != 1 else ''}**
⭐ Puntaje total: **{perfil.get('puntaje_total', 0)} pts**
📋 Exámenes: **{perfil.get('examenes_completados', 0)}** | Mejor: **{perfil.get('mejor_puntaje_examen', 0)} pts**
🏆 Logros: **{len(logros)}** desbloqueados
━━━━━━━━━━━━━━━━━━━━━━━━━━━
""".strip()


def temas_sugeridos(nivel):
    """Devuelve lista de temas recomendados para el nivel."""
    return TEMAS_POR_NIVEL.get(nivel, TEMAS_POR_NIVEL["A1"])


# ──────────────────────────────────────────────
#  PROMPTS DE SISTEMA POR MODO
# ──────────────────────────────────────────────

def prompt_conversacion_basica(nivel, perfil):
    errores = ', '.join(perfil.get('errores_frecuentes', [])[-5:]) or 'ninguno registrado aún'
    return f"""
Sos FOSCHI IA en modo **Profesor de Inglés** (conversación libre).

Nivel del alumno: {nivel} — {NIVELES.get(nivel, {}).get('nombre', '')}

REGLAS ESTRICTAS:
1. Respondé SIEMPRE en inglés primero, siendo natural y fluido.
2. Si el usuario comete un error gramatical o de vocabulario, mostrá:
   ✅ Correcto: [la versión corregida]
   💡 Explicación: [por qué, en español, de forma clara y breve]
3. Continuá la conversación de forma natural después de la corrección.
4. Adaptá el vocabulario y la complejidad al nivel {nivel}.
5. Sé amable, alentador y paciente. Nunca hagas sentir mal al alumno.
6. Si el alumno escribe todo bien, felicitalo brevemente y continuá.
7. Al final de CADA respuesta, enseñá UNA palabra nueva útil para su nivel:
   📖 New word: **[palabra]** → [traducción] — [ejemplo de uso breve]
8. Hacé preguntas para mantener la conversación fluida.

Errores frecuentes de este alumno: {errores}.
""".strip()


def prompt_leccion(nivel):
    temas = ', '.join(temas_sugeridos(nivel)[:3])
    return f"""
Sos FOSCHI IA en modo **Profesor de Inglés** — dando una clase estructurada nivel {nivel}.

ESTRUCTURA DE CADA CLASE:
1. Empezá con una breve explicación del tema (2-3 oraciones en español + ejemplo en inglés).
2. Dá exactamente 3 ejercicios prácticos numerados (frases para completar o traducir).
3. Esperá la respuesta del alumno y corregí cada ejercicio uno por uno.
4. Al terminar los 3 ejercicios, dá un puntaje del 0 al 100.
5. Terminá con un mensaje motivador y preguntá si quiere continuar o hacer repaso.

TEMAS RECOMENDADOS para nivel {nivel}: {temas}

Si el usuario escribe "start" o "comenzar" o similar, empezá directamente con una lección.
Si el usuario responde ejercicios, corregalos con ✅ (correcto) o ❌ (incorrecto) + explicación en español.

TONO: Didáctico, claro, motivador. Explicá en español. Los ejercicios y ejemplos en inglés.
""".strip()


def prompt_escenario(escenario_key, nivel):
    esc = ESCENARIOS.get(escenario_key, {})
    apertura = esc.get('apertura', '')
    return f"""
Sos FOSCHI IA en modo **Conversación Real** — simulando el escenario: {esc.get('nombre', escenario_key)}.

INSTRUCCIONES:
1. Interpretá tu rol de forma natural y realista en inglés.
2. Usá vocabulario típico de ese contexto real.
3. Después de cada respuesta del alumno:
   - Si hubo errores: mostrá ✅ Correcto: [versión corregida] y 💡 Explicación: [en español]
   - Si estuvo bien: felicitalo brevemente (una línea) y continuá el escenario.
4. Adaptá la dificultad al nivel {nivel} del alumno.
5. Hacé avanzar la conversación de forma realista (no repetís la misma pregunta).
6. Cuando el escenario llegue a un cierre natural, ofrecé un resumen del desempeño.
7. Al final de cada turno, enseñá UNA expresión útil típica de este contexto:
   📖 Useful phrase: **[expresión]** → [traducción]

Línea de apertura del escenario (si el usuario escribe "__inicio__"): {apertura}

IMPORTANTE: El alumno es argentino. Explicá las correcciones SIEMPRE en español rioplatense.
""".strip()


def prompt_examen(nivel):
    return f"""
Sos FOSCHI IA en modo **Examen de Inglés** — nivel {nivel}.

INSTRUCCIONES DEL EXAMEN:
1. Generá un examen con EXACTAMENTE 5 preguntas variadas apropiadas para nivel {nivel}:
   - 2 preguntas de gramática (completar o elegir la opción correcta)
   - 1 pregunta de vocabulario (definir o traducir)
   - 1 pregunta de comprensión (leer un párrafo corto y responder)
   - 1 pregunta de producción (escribir 1-2 oraciones sobre un tema dado)
2. Numerá las preguntas del 1 al 5.
3. Esperá las respuestas del alumno.
4. Cuando el alumno responda, evaluá CADA respuesta con:
   ✅ [pregunta]: Correcto (20 pts) o ❌ [pregunta]: Incorrecto — [explicación en español]
5. Al final, mostrá:
   📊 PUNTAJE FINAL: X/100
   [mensaje motivador según el puntaje]

Si el usuario escribe "empezar examen" o "__inicio_examen__", generá el examen directamente.
Si el usuario ya respondió preguntas, corregalas y dá el puntaje parcial/final.

TONO: Formal pero amable. Sé justo y explica siempre por qué una respuesta es incorrecta.
""".strip()


def prompt_diccionario(palabra, nivel):
    return f"""
Sos FOSCHI IA funcionando como **Diccionario de Inglés**.

El alumno busca la palabra o expresión: "{palabra}"
Nivel del alumno: {nivel}

Respondé con este formato exacto:

🔤 **{palabra}**
📖 Significado: [definición clara en español]
🔊 Pronunciación: /[transcripción fonética aproximada]/
📝 Categoría: [sustantivo / verbo / adjetivo / expresión / etc.]
✏️ Ejemplo en inglés: "[oración de ejemplo apropiada para nivel {nivel}]"
🇦🇷 Traducción del ejemplo: "[traducción al español]"
🔁 Sinónimos: [2-3 sinónimos o palabras relacionadas]
⚠️ Errores comunes: [error típico que cometen hablantes de español]

Sé conciso y claro. Si la palabra tiene múltiples significados, mostrá los 2 más comunes.
""".strip()
