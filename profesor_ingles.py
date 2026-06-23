# profesor_ingles.py
# Módulo del Modo Profesor de Inglés para FOSCHI IA

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
        "modo_activo": None,    # None | "conversacion" | "leccion" | "escenario"
        "escenario_activo": None,
    }

# ──────────────────────────────────────────────
#  API PÚBLICA
# ──────────────────────────────────────────────

def obtener_perfil(usuario):
    data = _load()
    if usuario not in data:
        data[usuario] = _perfil_default()
        _save(data)
    return data[usuario]


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
        pass  # ya estudió hoy
    elif ultimo == str(date.fromordinal(date.today().toordinal() - 1)):
        perfil["racha_dias"] = perfil.get("racha_dias", 0) + 1
    else:
        perfil["racha_dias"] = 1  # racha cortada

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
    perfil["errores_frecuentes"] = errores[-20:]  # últimos 20
    data[usuario] = perfil
    _save(data)


def completar_leccion(usuario):
    data = _load()
    perfil = data.get(usuario, _perfil_default())
    perfil["lecciones_completadas"] = perfil.get("lecciones_completadas", 0) + 1
    data[usuario] = perfil
    _save(data)
    _verificar_logros(usuario)


def _verificar_logros(usuario):
    data = _load()
    perfil = data.get(usuario, _perfil_default())
    logros = set(perfil.get("logros", []))
    lecciones = perfil.get("lecciones_completadas", 0)
    racha = perfil.get("racha_dias", 0)
    palabras = perfil.get("palabras_aprendidas", 0)

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
🏆 Logros: **{len(logros)}** desbloqueados
━━━━━━━━━━━━━━━━━━━━━━━━━━━
""".strip()


# ──────────────────────────────────────────────
#  PROMPTS DE SISTEMA POR MODO
# ──────────────────────────────────────────────

def prompt_conversacion_basica(nivel, perfil):
    return f"""
Sos FOSCHI IA en modo **Profesor de Inglés** (conversación básica).

Nivel del alumno: {nivel} — {NIVELES.get(nivel, {}).get('nombre', '')}

REGLAS ESTRICTAS:
1. Respondé SIEMPRE en inglés primero.
2. Si el usuario comete un error gramatical o de vocabulario, mostrá:
   ✅ Correcto: [la versión corregida]
   💡 Explicación: [por qué en español, de forma clara y breve]
3. Continuá la conversación de forma natural después de la corrección.
4. Adaptá el vocabulario y la complejidad al nivel {nivel}.
5. Sé amable, alentador y paciente. Nunca hagas sentir mal al alumno.
6. Si el alumno escribe todo bien, felicitalo brevemente y continuá.
7. Al final de cada respuesta, si corresponde, enseñá UNA palabra nueva útil para su nivel con su traducción.

Errores frecuentes de este alumno: {', '.join(perfil.get('errores_frecuentes', [])[-5:]) or 'ninguno registrado aún'}.
""".strip()


def prompt_leccion(nivel):
    return f"""
Sos FOSCHI IA en modo **Profesor de Inglés** — dando una clase estructurada nivel {nivel}.

ESTRUCTURA DE LA CLASE:
1. Empezá con una breve explicación del tema (2-3 oraciones en español + ejemplo en inglés).
2. Dá 3 ejercicios prácticos (frases para completar o traducir).
3. Esperá la respuesta del alumno y corregí cada ejercicio.
4. Al terminar los 3 ejercicios, dá un puntaje del 0 al 100 y un mensaje motivador.
5. Preguntá si quiere continuar con otro tema o hacer un repaso.

TONO: Didáctico, claro, motivador. Explicá siempre en español. Los ejemplos y ejercicios en inglés.
""".strip()


def prompt_escenario(escenario_key, nivel):
    esc = ESCENARIOS.get(escenario_key, {})
    return f"""
Sos FOSCHI IA en modo **Conversación Real** — simulando el escenario: {esc.get('nombre', escenario_key)}.

INSTRUCCIONES:
1. Interpretá tu rol de forma natural y realista.
2. Usá vocabulario típico de ese contexto real.
3. Después de cada respuesta del alumno:
   - Si hubo errores: mostrá la corrección con ✅ y 💡 explicación en español.
   - Si estuvo bien: felicitalo brevemente y continuá el escenario.
4. Adaptá la dificultad al nivel {nivel} del alumno.
5. Hacé que la conversación avance de forma realista (no repetís la misma pregunta).
6. Cuando el escenario llegue a un punto natural de cierre, ofrecé un resumen del desempeño.

IMPORTANTE: El alumno es argentino, explicá las correcciones siempre en español.
""".strip()
