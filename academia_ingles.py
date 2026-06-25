#!/usr/bin/env python3
# coding: utf-8
"""
academia_ingles.py — Academia de Inglés Foschi IA
Reemplaza a profesor_ingles.py
Integra modo Adultos y modo Niños con IA, pronunciación, juegos y seguimiento.
"""

import os
import json
from flask import request, jsonify, render_template_string, session
from openai import OpenAI

client = OpenAI()

# ──────────────────────────────────────────────
#  HTML DE LA ACADEMIA (página única completa)
# ──────────────────────────────────────────────
ACADEMIA_HTML = r"""
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>🎓 Academia Foschi IA</title>
<style>
  :root {
    --primary: #6c3fc5;
    --primary-light: #8b5cf6;
    --secondary: #f59e0b;
    --kids-bg: #fff7ed;
    --adult-bg: #f0f4ff;
    --green: #10b981;
    --red: #ef4444;
    --card: #ffffff;
    --radius: 16px;
    --shadow: 0 4px 24px rgba(108,63,197,.15);
  }

  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: 'Segoe UI', sans-serif; background: #f8f6ff; min-height: 100vh; }

  /* HEADER */
  .header {
    background: linear-gradient(135deg, #6c3fc5 0%, #a855f7 100%);
    color: white; text-align: center; padding: 18px 20px 14px;
    box-shadow: 0 4px 20px rgba(108,63,197,.4);
    position: sticky; top: 0; z-index: 100;
  }
  .header h1 { font-size: 1.6rem; font-weight: 800; letter-spacing: 1px; }
  .header p { font-size: .85rem; opacity: .85; margin-top: 2px; }

  /* SELECTOR DE MODO */
  .mode-selector {
    display: flex; justify-content: center; gap: 16px;
    padding: 24px 20px 10px;
  }
  .mode-btn {
    flex: 1; max-width: 200px; padding: 18px 12px;
    border-radius: var(--radius); border: 3px solid transparent;
    cursor: pointer; font-size: 1rem; font-weight: 700;
    transition: all .25s; text-align: center;
    box-shadow: var(--shadow);
  }
  .mode-btn.adult { background: var(--adult-bg); color: var(--primary); border-color: var(--primary); }
  .mode-btn.kids  { background: var(--kids-bg);  color: #d97706;         border-color: #f59e0b;       }
  .mode-btn.active { transform: scale(1.05); }
  .mode-btn.adult.active { background: var(--primary); color: white; }
  .mode-btn.kids.active  { background: var(--secondary); color: white; }
  .mode-btn .emoji { font-size: 2.2rem; display: block; margin-bottom: 6px; }

  /* CONTENEDOR PRINCIPAL */
  .main { max-width: 900px; margin: 0 auto; padding: 10px 16px 40px; }

  /* TABS INTERNOS */
  .tabs { display: flex; gap: 8px; flex-wrap: wrap; margin: 16px 0 12px; }
  .tab {
    padding: 8px 16px; border-radius: 30px; border: 2px solid var(--primary);
    background: white; color: var(--primary); font-weight: 600; cursor: pointer;
    font-size: .85rem; transition: all .2s;
  }
  .tab.active { background: var(--primary); color: white; }
  .tab:hover:not(.active) { background: #ede9fe; }

  /* CARDS */
  .card {
    background: var(--card); border-radius: var(--radius);
    padding: 22px; box-shadow: var(--shadow); margin-bottom: 16px;
  }
  .card h2 { color: var(--primary); font-size: 1.1rem; margin-bottom: 14px; }

  /* CHAT */
  #chatBox {
    height: 320px; overflow-y: auto; background: #f1f0f7; border-radius: 12px;
    padding: 14px; display: flex; flex-direction: column; gap: 10px;
    margin-bottom: 12px;
  }
  .msg { max-width: 80%; padding: 10px 14px; border-radius: 12px; line-height: 1.5; font-size: .93rem; }
  .msg.ai   { background: white; border: 1.5px solid #e0d6fa; align-self: flex-start; color: #2d1b69; }
  .msg.user { background: var(--primary); color: white; align-self: flex-end; }
  .msg.correction { background: #fffbeb; border: 1.5px solid #f59e0b; color: #78350f; align-self: flex-start; }

  .chat-input-row { display: flex; gap: 8px; }
  .chat-input-row input {
    flex: 1; padding: 10px 14px; border-radius: 30px;
    border: 2px solid #d1c4e9; font-size: .95rem; outline: none;
    transition: border .2s;
  }
  .chat-input-row input:focus { border-color: var(--primary); }
  .btn {
    padding: 10px 20px; border-radius: 30px; border: none;
    background: var(--primary); color: white; font-weight: 700;
    cursor: pointer; font-size: .9rem; transition: background .2s;
    white-space: nowrap;
  }
  .btn:hover { background: var(--primary-light); }
  .btn.green  { background: var(--green); }
  .btn.orange { background: #f59e0b; color: white; }
  .btn.red    { background: var(--red); }
  .btn:disabled { opacity: .5; cursor: default; }

  /* PRONUNCIACIÓN */
  .pron-word {
    font-size: 2.2rem; font-weight: 800; color: var(--primary);
    text-align: center; padding: 20px; letter-spacing: 2px;
  }
  .pron-emoji { font-size: 3.5rem; text-align: center; display: block; margin-bottom: 8px; }
  .score-bar-wrap { background: #e5e7eb; border-radius: 30px; height: 18px; overflow: hidden; margin: 8px 0; }
  .score-bar { height: 100%; border-radius: 30px; transition: width .6s; background: var(--green); }
  .score-label { font-weight: 700; color: var(--primary); }

  /* SELECTOR DE TEMA */
  .topic-grid { display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 16px; }
  .topic-chip {
    padding: 8px 16px; border-radius: 30px; border: 2px solid #d1c4e9;
    background: white; cursor: pointer; font-weight: 600; color: #4c1d95;
    transition: all .2s; font-size: .85rem;
  }
  .topic-chip.active, .topic-chip:hover { background: var(--primary); color: white; border-color: var(--primary); }

  /* PROGRESO */
  .progress-item { margin-bottom: 14px; }
  .progress-item .label { display: flex; justify-content: space-between; margin-bottom: 4px; font-size: .88rem; }
  .progress-item .label .topic-name { font-weight: 600; color: #374151; }
  .progress-item .label .pct { font-weight: 700; }
  .pct.good { color: var(--green); }
  .pct.mid  { color: #f59e0b; }
  .pct.low  { color: var(--red); }
  .repaso-badge { background: #fef3c7; color: #92400e; font-size: .75rem; padding: 2px 8px; border-radius: 10px; margin-left: 6px; }

  /* CORRECTOR */
  textarea {
    width: 100%; padding: 12px; border-radius: 12px; border: 2px solid #d1c4e9;
    font-size: .95rem; resize: vertical; min-height: 80px; outline: none;
    font-family: inherit; transition: border .2s;
  }
  textarea:focus { border-color: var(--primary); }
  .correction-box {
    background: #f0fdf4; border: 1.5px solid #a7f3d0;
    border-radius: 12px; padding: 14px; margin-top: 12px;
    color: #065f46; line-height: 1.6; white-space: pre-wrap;
  }
  .error-box { background: #fff1f2; border-color: #fecdd3; color: #881337; }

  /* ── MODO NIÑOS ── */
  .kids-section { background: var(--kids-bg); border-radius: var(--radius); padding: 20px; }
  .kids-tab { border-color: #f59e0b; color: #92400e; }
  .kids-tab.active { background: #f59e0b; color: white; }

  .game-emoji-big { font-size: 5rem; text-align: center; display: block; margin: 10px 0; }
  .game-question  { font-size: 1.2rem; font-weight: 700; text-align: center; color: #92400e; margin-bottom: 16px; }

  .options-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
  .option-btn {
    padding: 14px; border-radius: 14px; border: 3px solid #fed7aa;
    background: white; font-size: 1.05rem; font-weight: 700;
    cursor: pointer; transition: all .2s; color: #78350f;
    text-align: center;
  }
  .option-btn:hover { background: #fff7ed; border-color: #f59e0b; transform: scale(1.03); }
  .option-btn.correct { background: #d1fae5; border-color: var(--green); color: #065f46; }
  .option-btn.wrong   { background: #fee2e2; border-color: var(--red);   color: #7f1d1d; }

  /* Recompensas */
  .stars-bar { text-align: right; font-size: 1rem; font-weight: 700; color: #92400e; padding: 4px 0 10px; }

  .reward-popup {
    position: fixed; top: 50%; left: 50%; transform: translate(-50%,-50%) scale(0);
    background: white; border-radius: 24px; padding: 32px 40px;
    box-shadow: 0 20px 60px rgba(0,0,0,.25); z-index: 9999;
    text-align: center; transition: transform .3s cubic-bezier(.34,1.56,.64,1);
  }
  .reward-popup.show { transform: translate(-50%,-50%) scale(1); }
  .reward-popup .big-emoji { font-size: 4rem; display: block; margin-bottom: 8px; }
  .reward-popup h3 { font-size: 1.5rem; color: var(--primary); }
  .reward-popup p  { color: #6b7280; margin-top: 4px; }

  /* Memotest */
  .memo-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; }
  .memo-card {
    aspect-ratio: 1; border-radius: 12px; background: var(--primary);
    display: flex; align-items: center; justify-content: center;
    font-size: 1.6rem; cursor: pointer; transition: all .3s;
    user-select: none; border: 3px solid transparent;
  }
  .memo-card:hover:not(.flipped):not(.matched) { background: var(--primary-light); }
  .memo-card.matched { background: #d1fae5; border-color: var(--green); pointer-events: none; }

  /* spinner */
  .spinner { display: inline-block; width: 20px; height: 20px; border: 3px solid rgba(255,255,255,.3); border-top-color: white; border-radius: 50%; animation: spin .6s linear infinite; margin-right: 6px; vertical-align: middle; }
  @keyframes spin { to { transform: rotate(360deg); } }

  /* Responsive */
  @media (max-width: 600px) {
    .mode-selector { flex-direction: column; align-items: center; }
    .mode-btn { max-width: 320px; }
    .memo-grid { grid-template-columns: repeat(3, 1fr); }
    .options-grid { grid-template-columns: 1fr; }
  }

  /* Ocultar secciones */
  .section { display: none; }
  .section.active { display: block; }
  .loading-msg { color: #7c3aed; font-style: italic; font-size: .9rem; padding: 6px 0; }
</style>
</head>
<body>

<div class="header">
  <h1>🎓 Academia de Inglés Foschi IA</h1>
  <p>Tu profesor personal — adaptado a vos</p>
</div>

<!-- SELECTOR MODO -->
<div class="mode-selector">
  <button class="mode-btn adult active" id="btnAdult" onclick="setMode('adult')">
    <span class="emoji">🧑</span> Adultos
  </button>
  <button class="mode-btn kids" id="btnKids" onclick="setMode('kids')">
    <span class="emoji">👶</span> Niños
  </button>
</div>

<div class="main">

  <!-- ══════════════ ADULTOS ══════════════ -->
  <div id="modeAdult">

    <!-- TABS ADULTOS -->
    <div class="tabs">
      <button class="tab active" onclick="showAdultTab('conversation')">💬 Conversación</button>
      <button class="tab" onclick="showAdultTab('pronunciation')">🎤 Pronunciación</button>
      <button class="tab" onclick="showAdultTab('corrector')">✍️ Corrector</button>
      <button class="tab" onclick="showAdultTab('progress')">📈 Mi Progreso</button>
    </div>

    <!-- ── CONVERSACIÓN ── -->
    <div id="tab-conversation" class="section active">
      <div class="card">
        <h2>💬 Conversá con el Profesor</h2>
        <div class="topic-grid">
          <div class="topic-chip active" data-topic="greetings" onclick="setTopic(this,'greetings')">👋 Saludos</div>
          <div class="topic-chip" data-topic="work"      onclick="setTopic(this,'work')">💼 Trabajo</div>
          <div class="topic-chip" data-topic="travel"    onclick="setTopic(this,'travel')">✈️ Viajes</div>
          <div class="topic-chip" data-topic="family"    onclick="setTopic(this,'family')">👨‍👩‍👧 Familia</div>
          <div class="topic-chip" data-topic="free"      onclick="setTopic(this,'free')">🗣️ Libre</div>
        </div>
        <div id="chatBox"></div>
        <div class="chat-input-row">
          <input id="chatInput" type="text" placeholder="Escribí en inglés..." onkeydown="if(event.key==='Enter')sendChat()" />
          <button class="btn" onclick="sendChat()" id="btnSend">Enviar</button>
        </div>
      </div>
    </div>

    <!-- ── PRONUNCIACIÓN ── -->
    <div id="tab-pronunciation" class="section">
      <div class="card">
        <h2>🎤 Practicá tu Pronunciación</h2>
        <div id="pronEmojiWrap"></div>
        <div class="pron-word" id="pronWord">---</div>
        <div style="text-align:center;margin:10px 0;color:#6b7280;font-size:.9rem">
          Escuchá la palabra y luego repetila
        </div>
        <div style="display:flex;gap:10px;justify-content:center;flex-wrap:wrap;margin-bottom:14px">
          <button class="btn orange" onclick="listenWord()">🔊 Escuchar</button>
          <button class="btn green"  onclick="startPron()" id="btnPron">🎤 Hablar</button>
          <button class="btn"        onclick="nextPronWord()">Siguiente ➜</button>
        </div>
        <div id="pronResult"></div>
      </div>
    </div>

    <!-- ── CORRECTOR ── -->
    <div id="tab-corrector" class="section">
      <div class="card">
        <h2>✍️ Corrector de Inglés</h2>
        <p style="color:#6b7280;font-size:.88rem;margin-bottom:12px">
          Escribí una frase, párrafo o texto en inglés. El profesor lo corrige y explica.
        </p>
        <textarea id="correctorText" placeholder="Ej: I have 30 years old. Yesterday I go to school..."></textarea>
        <button class="btn" style="margin-top:10px;width:100%" onclick="correctText()" id="btnCorrect">
          🔍 Corregir
        </button>
        <div id="correctorResult"></div>
      </div>
    </div>

    <!-- ── PROGRESO ── -->
    <div id="tab-progress" class="section">
      <div class="card">
        <h2>📈 Tu Progreso</h2>
        <p style="color:#6b7280;font-size:.88rem;margin-bottom:16px">
          Los temas por debajo del 80% necesitan repaso. Foschi IA los reforzará automáticamente.
        </p>
        <div id="progressList"></div>
        <button class="btn" style="margin-top:14px" onclick="loadProgress()">🔄 Actualizar</button>
      </div>
    </div>

  </div><!-- fin modeAdult -->

  <!-- ══════════════ NIÑOS ══════════════ -->
  <div id="modeKids" style="display:none">
    <div class="kids-section">

      <div class="stars-bar">⭐ <span id="starCount">0</span> puntos</div>

      <div class="tabs">
        <button class="tab kids-tab active" onclick="showKidsTab('games')">🎮 Juegos</button>
        <button class="tab kids-tab" onclick="showKidsTab('memo')">🃏 Memotest</button>
        <button class="tab kids-tab" onclick="showKidsTab('pronKids')">🎤 Pronunciación</button>
        <button class="tab kids-tab" onclick="showKidsTab('chatKids')">🧑‍🏫 Chat Profe</button>
        <button class="tab kids-tab" onclick="showKidsTab('badges')">🏆 Logros</button>
      </div>

      <!-- ── JUEGOS ── -->
      <div id="tab-games" class="section active">
        <div class="card">
          <h2>🎮 ¿Qué es esto?</h2>
          <div class="topic-grid">
            <div class="topic-chip active kids-topic" data-topic="animals"  onclick="setKidsTopic(this,'animals')">🐶 Animales</div>
            <div class="topic-chip kids-topic"         data-topic="colors"   onclick="setKidsTopic(this,'colors')">🎨 Colores</div>
            <div class="topic-chip kids-topic"         data-topic="fruits"   onclick="setKidsTopic(this,'fruits')">🍎 Frutas</div>
            <div class="topic-chip kids-topic"         data-topic="numbers"  onclick="setKidsTopic(this,'numbers')">🔢 Números</div>
            <div class="topic-chip kids-topic"         data-topic="body"     onclick="setKidsTopic(this,'body')">🦴 Cuerpo</div>
          </div>
          <span class="game-emoji-big" id="gameEmoji">🐶</span>
          <div class="game-question" id="gameQuestion">What animal is this?</div>
          <div class="options-grid" id="optionsGrid"></div>
          <div style="text-align:center;margin-top:14px">
            <button class="btn orange" onclick="nextGameQuestion()">➜ Siguiente</button>
          </div>
        </div>
      </div>

      <!-- ── MEMOTEST ── -->
      <div id="tab-memo" class="section">
        <div class="card">
          <h2>🃏 Memotest</h2>
          <p style="color:#6b7280;font-size:.88rem;margin-bottom:12px">
            Encontrá cada emoji con su palabra en inglés. ¡A jugar!
          </p>
          <div class="memo-grid" id="memoGrid"></div>
          <button class="btn" style="margin-top:14px;width:100%" onclick="initMemo()">🔄 Nuevo juego</button>
        </div>
      </div>

      <!-- ── PRONUNCIACIÓN NIÑOS ── -->
      <div id="tab-pronKids" class="section">
        <div class="card" style="text-align:center">
          <h2>🎤 ¡Aprendé a decirlo!</h2>
          <span class="game-emoji-big" id="kidsEmoji">🍎</span>
          <div class="pron-word" id="kidsWord">Apple</div>
          <p style="color:#6b7280;font-size:.9rem;margin:8px 0 16px">
            Escuchá y luego decilo vos 😄
          </p>
          <div style="display:flex;gap:10px;justify-content:center;flex-wrap:wrap;margin-bottom:16px">
            <button class="btn orange" onclick="kidsListen()">🔊 Escuchar</button>
            <button class="btn green"  onclick="kidsSpeak()" id="btnKidsSpeak">🎤 ¡Hablo yo!</button>
            <button class="btn"        onclick="nextKidsWord()">Siguiente ➜</button>
          </div>
          <div id="kidsVoiceResult"></div>
        </div>
      </div>

      <!-- ── CHAT NIÑOS ── -->
      <div id="tab-chatKids" class="section">
        <div class="card">
          <h2>🧑‍🏫 Hablá con el Profe</h2>
          <div id="kidsChatBox" style="height:260px;overflow-y:auto;background:#fff7ed;border-radius:12px;padding:14px;display:flex;flex-direction:column;gap:10px;margin-bottom:12px"></div>
          <div class="chat-input-row">
            <input id="kidsChatInput" type="text" placeholder="Escribí en inglés..." onkeydown="if(event.key==='Enter')sendKidsChat()" />
            <button class="btn orange" onclick="sendKidsChat()">Enviar</button>
          </div>
        </div>
      </div>

      <!-- ── LOGROS ── -->
      <div id="tab-badges" class="section">
        <div class="card">
          <h2>🏆 Tus Logros</h2>
          <div id="badgesList" style="display:flex;flex-wrap:wrap;gap:14px;margin-top:8px"></div>
        </div>
      </div>

    </div>
  </div><!-- fin modeKids -->

</div><!-- fin main -->

<!-- REWARD POPUP -->
<div class="reward-popup" id="rewardPopup">
  <span class="big-emoji" id="rewardEmoji">⭐</span>
  <h3 id="rewardTitle">¡Muy bien!</h3>
  <p id="rewardMsg">Ganaste 10 puntos</p>
</div>

<audio id="audioPlayer"></audio>

<script>
// ═══════════════════════════════════════════════
//  DATOS DE VOCABULARIO
// ═══════════════════════════════════════════════
const VOCAB = {
  animals:  [{e:"🐶",w:"Dog"},{e:"🐱",w:"Cat"},{e:"🐦",w:"Bird"},{e:"🐟",w:"Fish"},{e:"🐘",w:"Elephant"},{e:"🦁",w:"Lion"},{e:"🐻",w:"Bear"},{e:"🐰",w:"Rabbit"}],
  colors:   [{e:"🔴",w:"Red"},{e:"🔵",w:"Blue"},{e:"🟡",w:"Yellow"},{e:"🟢",w:"Green"},{e:"⚫",w:"Black"},{e:"⚪",w:"White"},{e:"🟠",w:"Orange"},{e:"🟣",w:"Purple"}],
  fruits:   [{e:"🍎",w:"Apple"},{e:"🍌",w:"Banana"},{e:"🍇",w:"Grapes"},{e:"🍓",w:"Strawberry"},{e:"🍊",w:"Orange"},{e:"🍋",w:"Lemon"},{e:"🍑",w:"Peach"},{e:"🍉",w:"Watermelon"}],
  numbers:  [{e:"1️⃣",w:"One"},{e:"2️⃣",w:"Two"},{e:"3️⃣",w:"Three"},{e:"4️⃣",w:"Four"},{e:"5️⃣",w:"Five"},{e:"6️⃣",w:"Six"},{e:"7️⃣",w:"Seven"},{e:"8️⃣",w:"Eight"}],
  body:     [{e:"👁️",w:"Eye"},{e:"👂",w:"Ear"},{e:"👃",w:"Nose"},{e:"👄",w:"Mouth"},{e:"🦷",w:"Tooth"},{e:"🦴",w:"Bone"},{e:"💪",w:"Arm"},{e:"🦵",w:"Leg"}]
};

const PRON_WORDS = [
  {e:"🍎",w:"Apple"},{e:"🐶",w:"Dog"},{e:"📚",w:"Book"},{e:"🏠",w:"House"},
  {e:"🚗",w:"Car"},{e:"🌳",w:"Tree"},{e:"🍕",w:"Pizza"},{e:"☀️",w:"Sun"},
  {e:"🎵",w:"Music"},{e:"💻",w:"Computer"},{e:"✈️",w:"Airplane"},{e:"🌊",w:"Ocean"}
];

// ═══════════════════════════════════════════════
//  ESTADO
// ═══════════════════════════════════════════════
let currentMode  = 'adult';
let adultTopic   = 'greetings';
let kidsTopic    = 'animals';
let chatHistory  = [];
let kidsChatHistory = [];
let pronIdx      = 0;
let kidsWordIdx  = 0;
let kidsGameIdx  = 0;
let stars        = parseInt(localStorage.getItem('foschi_stars') || '0');
let unlockedBadges = JSON.parse(localStorage.getItem('foschi_badges') || '[]');

let progress = JSON.parse(localStorage.getItem('foschi_progress') || JSON.stringify({
  greetings: 0, work: 0, travel: 0, family: 0, free: 0,
  pronunciation: 0, corrector: 0
}));

// ═══════════════════════════════════════════════
//  MODO
// ═══════════════════════════════════════════════
function setMode(mode) {
  currentMode = mode;
  document.getElementById('modeAdult').style.display = mode === 'adult' ? 'block' : 'none';
  document.getElementById('modeKids').style.display  = mode === 'kids'  ? 'block' : 'none';
  document.getElementById('btnAdult').classList.toggle('active', mode === 'adult');
  document.getElementById('btnKids').classList.toggle('active',  mode === 'kids');
  if (mode === 'kids') {
    updateStars();
    renderBadges();
    nextGameQuestion();
    if (!document.getElementById('kidsChatBox').children.length) startKidsChat();
  } else {
    loadProgress();
    if (!document.getElementById('chatBox').children.length) startAdultChat();
    nextPronWord();
  }
}

// ═══════════════════════════════════════════════
//  TABS
// ═══════════════════════════════════════════════
function showAdultTab(name) {
  document.querySelectorAll('#modeAdult .section').forEach(s => s.classList.remove('active'));
  document.getElementById('tab-'+name).classList.add('active');
  document.querySelectorAll('#modeAdult .tab').forEach(t => t.classList.remove('active'));
  event.target.classList.add('active');
  if (name === 'progress') loadProgress();
}

function showKidsTab(name) {
  document.querySelectorAll('#modeKids .section').forEach(s => s.classList.remove('active'));
  document.getElementById('tab-'+name).classList.add('active');
  document.querySelectorAll('#modeKids .tab').forEach(t => t.classList.remove('active'));
  event.target.classList.add('active');
  if (name === 'memo') initMemo();
  if (name === 'pronKids') nextKidsWord();
  if (name === 'badges') renderBadges();
}

// ═══════════════════════════════════════════════
//  CHAT ADULTOS
// ═══════════════════════════════════════════════
function setTopic(el, topic) {
  document.querySelectorAll('.topic-chip:not(.kids-topic)').forEach(c => c.classList.remove('active'));
  el.classList.add('active');
  adultTopic = topic;
  chatHistory = [];
  document.getElementById('chatBox').innerHTML = '';
  startAdultChat();
}

async function startAdultChat() {
  const greet = {
    greetings: "Hello! I'm your English teacher. Today we'll practice **greetings and introductions**. Let's start simple: How are you?",
    work:      "Welcome! Let's talk about **work and jobs**. Tell me: What do you do for a living?",
    travel:    "Great choice! We'll practice **travel English**. Imagine you're at the airport. You need to check in. What do you say to the agent?",
    family:    "Wonderful topic! Let's talk about **family**. Tell me: How many people are in your family?",
    free:      "Perfect! Let's have a **free conversation in English**. Tell me something about yourself — anything you like!"
  };
  addMsg(greet[adultTopic] || greet.free, 'ai');
  chatHistory.push({role:'assistant', content: greet[adultTopic] || greet.free});
}

async function sendChat() {
  const input = document.getElementById('chatInput');
  const text  = input.value.trim();
  if (!text) return;
  input.value = '';
  addMsg(text, 'user');
  chatHistory.push({role:'user', content: text});

  const btn = document.getElementById('btnSend');
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span>Pensando...';

  addMsg('...', 'ai', 'loadingMsg');

  try {
    const res = await fetch('/academia/chat', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({ history: chatHistory, topic: adultTopic })
    });
    const data = await res.json();
    document.getElementById('loadingMsg')?.remove();

    if (data.reply)      addMsg(data.reply, 'ai');
    if (data.correction) addMsg(data.correction, 'correction');

    chatHistory.push({role:'assistant', content: data.reply || ''});

    // actualizar progreso
    if (data.score) updateProgress(adultTopic, data.score);

  } catch(e) {
    document.getElementById('loadingMsg')?.remove();
    addMsg('❌ Error de conexión. Intentá de nuevo.', 'ai');
  }
  btn.disabled = false;
  btn.textContent = 'Enviar';
}

function addMsg(text, cls, id) {
  const box = document.getElementById('chatBox');
  const div = document.createElement('div');
  div.className = 'msg ' + cls;
  if (id) div.id = id;
  div.innerHTML = text.replace(/\*\*(.*?)\*\*/g,'<strong>$1</strong>');
  box.appendChild(div);
  box.scrollTop = box.scrollHeight;
}

// ═══════════════════════════════════════════════
//  PRONUNCIACIÓN ADULTOS
// ═══════════════════════════════════════════════
function nextPronWord() {
  pronIdx = (pronIdx + 1) % PRON_WORDS.length;
  const item = PRON_WORDS[pronIdx];
  document.getElementById('pronWord').textContent = item.w;
  const wrap = document.getElementById('pronEmojiWrap');
  wrap.innerHTML = `<span class="pron-emoji">${item.e}</span>`;
  document.getElementById('pronResult').innerHTML = '';
}

function listenWord() {
  const word = PRON_WORDS[pronIdx].w;
  const utter = new SpeechSynthesisUtterance(word);
  utter.lang = 'en-US'; utter.rate = 0.85;
  window.speechSynthesis.speak(utter);
}

function startPron() {
  if (!('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {
    document.getElementById('pronResult').innerHTML =
      '<p style="color:#ef4444">⚠️ Tu navegador no soporta reconocimiento de voz. Usá Chrome.</p>';
    return;
  }
  const expected = PRON_WORDS[pronIdx].w.toLowerCase();
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  const rec = new SR();
  rec.lang = 'en-US'; rec.interimResults = false;

  const btn = document.getElementById('btnPron');
  btn.textContent = '🔴 Grabando...'; btn.style.background='#ef4444';

  rec.onresult = e => {
    const spoken = e.results[0][0].transcript.toLowerCase().trim();
    const confidence = Math.round(e.results[0][0].confidence * 100);
    showPronScore(expected, spoken, confidence);
    btn.textContent = '🎤 Hablar'; btn.style.background='';
    updateProgress('pronunciation', confidence);
  };
  rec.onerror = () => {
    document.getElementById('pronResult').innerHTML =
      '<p style="color:#ef4444">❌ No se detectó audio. Intentá de nuevo.</p>';
    btn.textContent = '🎤 Hablar'; btn.style.background='';
  };
  rec.start();
}

function showPronScore(expected, spoken, confidence) {
  const match = spoken.includes(expected) || expected.includes(spoken);
  const color = confidence >= 80 ? '#10b981' : confidence >= 60 ? '#f59e0b' : '#ef4444';
  const emoji = confidence >= 80 ? '🌟' : confidence >= 60 ? '👍' : '💪';
  const msg   = confidence >= 80 ? '¡Excelente pronunciación!' : confidence >= 60 ? 'Bien, pero podés mejorar.' : 'Seguí practicando — ¡vas a lograrlo!';
  document.getElementById('pronResult').innerHTML = `
    <div style="padding:14px;background:#f9fafb;border-radius:12px;margin-top:8px">
      <p style="margin-bottom:8px"><strong>Dijiste:</strong> "${spoken}"</p>
      <p style="margin-bottom:8px"><strong>Esperado:</strong> "${expected}"</p>
      <div class="score-bar-wrap">
        <div class="score-bar" style="width:${confidence}%;background:${color}"></div>
      </div>
      <p class="score-label">${emoji} ${confidence}% — ${msg}</p>
    </div>`;
}

// ═══════════════════════════════════════════════
//  CORRECTOR
// ═══════════════════════════════════════════════
async function correctText() {
  const text = document.getElementById('correctorText').value.trim();
  if (!text) return;
  const btn = document.getElementById('btnCorrect');
  btn.disabled = true; btn.innerHTML = '<span class="spinner"></span> Corrigiendo...';
  document.getElementById('correctorResult').innerHTML = '';

  try {
    const res = await fetch('/academia/correct', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({ text })
    });
    const data = await res.json();
    const cls  = data.has_errors ? '' : 'correction-box';
    document.getElementById('correctorResult').innerHTML =
      `<div class="correction-box ${cls}" style="margin-top:12px">${data.result}</div>`;
    updateProgress('corrector', data.score || 70);
  } catch(e) {
    document.getElementById('correctorResult').innerHTML =
      '<div class="correction-box error-box">❌ Error de conexión.</div>';
  }
  btn.disabled = false; btn.textContent = '🔍 Corregir';
}

// ═══════════════════════════════════════════════
//  PROGRESO
// ═══════════════════════════════════════════════
function updateProgress(topic, score) {
  if (!progress[topic]) progress[topic] = 0;
  progress[topic] = Math.round(progress[topic] * 0.7 + score * 0.3);
  localStorage.setItem('foschi_progress', JSON.stringify(progress));
}

function loadProgress() {
  const topics = {
    greetings:'👋 Saludos', work:'💼 Trabajo', travel:'✈️ Viajes',
    family:'👨‍👩‍👧 Familia', free:'🗣️ Conversación libre',
    pronunciation:'🎤 Pronunciación', corrector:'✍️ Corrector'
  };
  const list = document.getElementById('progressList');
  list.innerHTML = '';
  Object.entries(topics).forEach(([key, label]) => {
    const pct  = progress[key] || 0;
    const cls  = pct >= 80 ? 'good' : pct >= 50 ? 'mid' : 'low';
    const rep  = pct < 80 && pct > 0 ? '<span class="repaso-badge">↩ Necesita repaso</span>' : '';
    const bar  = pct >= 80 ? '#10b981' : pct >= 50 ? '#f59e0b' : '#ef4444';
    list.innerHTML += `
      <div class="progress-item">
        <div class="label">
          <span class="topic-name">${label}${rep}</span>
          <span class="pct ${cls}">${pct}%</span>
        </div>
        <div class="score-bar-wrap">
          <div class="score-bar" style="width:${pct}%;background:${bar}"></div>
        </div>
      </div>`;
  });
}

// ═══════════════════════════════════════════════
//  MODO NIÑOS — JUEGOS
// ═══════════════════════════════════════════════
function setKidsTopic(el, topic) {
  document.querySelectorAll('.kids-topic').forEach(c => c.classList.remove('active'));
  el.classList.add('active');
  kidsTopic = topic;
  nextGameQuestion();
}

function nextGameQuestion() {
  const items = VOCAB[kidsTopic];
  kidsGameIdx = Math.floor(Math.random() * items.length);
  const correct = items[kidsGameIdx];

  document.getElementById('gameEmoji').textContent = correct.e;
  const topicQ = { animals:'animal', colors:'color', fruits:'fruit', numbers:'number', body:'body part' };
  document.getElementById('gameQuestion').textContent = `What ${topicQ[kidsTopic]||'word'} is this?`;

  // 4 opciones (1 correcta + 3 wrongas)
  const shuffled = items.filter((_,i) => i !== kidsGameIdx).sort(()=>Math.random()-.5).slice(0,3);
  const opts = [correct, ...shuffled].sort(()=>Math.random()-.5);

  const grid = document.getElementById('optionsGrid');
  grid.innerHTML = '';
  opts.forEach(opt => {
    const btn = document.createElement('button');
    btn.className = 'option-btn';
    btn.textContent = opt.w;
    btn.onclick = () => checkAnswer(btn, opt.w, correct.w);
    grid.appendChild(btn);
  });
}

function checkAnswer(btn, chosen, correct) {
  const all = document.querySelectorAll('.option-btn');
  all.forEach(b => b.disabled = true);

  if (chosen === correct) {
    btn.classList.add('correct');
    addStars(10);
    showReward('⭐', '¡Excelente!', '+10 puntos');
    checkBadge();
  } else {
    btn.classList.add('wrong');
    all.forEach(b => { if (b.textContent === correct) b.classList.add('correct'); });
    showReward('💪', '¡Casi!', `La respuesta era: ${correct}`);
  }
}

// ═══════════════════════════════════════════════
//  MEMOTEST
// ═══════════════════════════════════════════════
let memoCards = [], memoFlipped = [], memoMatched = 0;

function initMemo() {
  const items = VOCAB['animals'].slice(0,4);
  const pairs = [...items.map(i=>({type:'emoji',val:i.e,pair:i.w})),
                  ...items.map(i=>({type:'word', val:i.w,pair:i.e}))];
  memoCards = pairs.sort(()=>Math.random()-.5);
  memoFlipped = []; memoMatched = 0;

  const grid = document.getElementById('memoGrid');
  grid.innerHTML = '';
  memoCards.forEach((card, idx) => {
    const div = document.createElement('div');
    div.className = 'memo-card';
    div.dataset.idx = idx;
    div.dataset.val = card.val;
    div.dataset.pair = card.pair;
    div.textContent = '?';
    div.onclick = () => flipMemo(div, idx);
    grid.appendChild(div);
  });
}

function flipMemo(div, idx) {
  if (memoFlipped.length >= 2 || div.classList.contains('matched')) return;
  div.textContent = memoCards[idx].val;
  memoFlipped.push(div);

  if (memoFlipped.length === 2) {
    const [a, b] = memoFlipped;
    const match = a.dataset.pair === b.dataset.val || b.dataset.pair === a.dataset.val;
    setTimeout(() => {
      if (match) {
        a.classList.add('matched'); b.classList.add('matched');
        memoMatched += 2; addStars(20);
        if (memoMatched === memoCards.length) showReward('🎉','¡Ganaste!','¡Completaste el Memotest! +20 pts');
      } else {
        a.textContent = '?'; b.textContent = '?';
      }
      memoFlipped = [];
    }, 800);
  }
}

// ═══════════════════════════════════════════════
//  PRONUNCIACIÓN NIÑOS
// ═══════════════════════════════════════════════
const KIDS_WORDS = PRON_WORDS;

function nextKidsWord() {
  kidsWordIdx = (kidsWordIdx + 1) % KIDS_WORDS.length;
  const item = KIDS_WORDS[kidsWordIdx];
  document.getElementById('kidsEmoji').textContent = item.e;
  document.getElementById('kidsWord').textContent  = item.w;
  document.getElementById('kidsVoiceResult').innerHTML = '';
}

function kidsListen() {
  const word = KIDS_WORDS[kidsWordIdx].w;
  const utter = new SpeechSynthesisUtterance(word);
  utter.lang = 'en-US'; utter.rate = 0.75;
  window.speechSynthesis.speak(utter);
}

function kidsSpeak() {
  if (!('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {
    document.getElementById('kidsVoiceResult').innerHTML =
      '<p style="color:#ef4444">⚠️ Usá Chrome para poder hablar 🎤</p>';
    return;
  }
  const expected = KIDS_WORDS[kidsWordIdx].w.toLowerCase();
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  const rec = new SR();
  rec.lang = 'en-US'; rec.interimResults = false;

  const btn = document.getElementById('btnKidsSpeak');
  btn.textContent = '🔴 Escuchando...'; btn.style.background = '#ef4444';

  rec.onresult = e => {
    const spoken = e.results[0][0].transcript.toLowerCase().trim();
    const confidence = Math.round(e.results[0][0].confidence * 100);
    const ok = spoken.includes(expected) || confidence >= 70;

    if (ok) {
      document.getElementById('kidsVoiceResult').innerHTML =
        `<div style="text-align:center;font-size:1.4rem;color:#10b981;font-weight:800">🌟 ¡Perfecto! ¡Muy bien!</div>`;
      addStars(15); showReward('🌟','¡Excelente!','¡Dijiste la palabra perfecto!');
    } else {
      document.getElementById('kidsVoiceResult').innerHTML =
        `<div style="text-align:center;font-size:1rem;color:#f59e0b;font-weight:700">
          Dijiste: "${spoken}"<br>Intentalo de nuevo 💪
        </div>`;
    }
    btn.textContent = '🎤 ¡Hablo yo!'; btn.style.background = '';
  };
  rec.onerror = () => { btn.textContent = '🎤 ¡Hablo yo!'; btn.style.background = ''; };
  rec.start();
}

// ═══════════════════════════════════════════════
//  CHAT NIÑOS
// ═══════════════════════════════════════════════
async function startKidsChat() {
  const msg = "Hi! I'm your English teacher! 😊 Today we're going to learn together! Are you ready? Say: Yes, I'm ready! 🎉";
  addKidsMsg(msg, 'ai');
  kidsChatHistory.push({role:'assistant', content: msg});
}

async function sendKidsChat() {
  const input = document.getElementById('kidsChatInput');
  const text  = input.value.trim();
  if (!text) return;
  input.value = '';
  addKidsMsg(text, 'user');
  kidsChatHistory.push({role:'user', content: text});

  try {
    const res = await fetch('/academia/chat-kids', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({ history: kidsChatHistory })
    });
    const data = await res.json();
    if (data.reply) { addKidsMsg(data.reply, 'ai'); kidsChatHistory.push({role:'assistant', content: data.reply}); }
  } catch(e) {
    addKidsMsg('❌ Sin conexión. Intentá de nuevo.', 'ai');
  }
}

function addKidsMsg(text, cls) {
  const box = document.getElementById('kidsChatBox');
  const div = document.createElement('div');
  div.className = 'msg ' + (cls === 'ai' ? '' : 'user');
  div.style.background = cls === 'ai' ? '#fff3e0' : '#6c3fc5';
  div.style.color       = cls === 'ai' ? '#78350f' : 'white';
  div.style.alignSelf   = cls === 'ai' ? 'flex-start' : 'flex-end';
  div.style.border      = cls === 'ai' ? '1.5px solid #fed7aa' : 'none';
  div.textContent = text;
  box.appendChild(div);
  box.scrollTop = box.scrollHeight;
}

// ═══════════════════════════════════════════════
//  ESTRELLAS Y LOGROS
// ═══════════════════════════════════════════════
const BADGES = [
  {id:'first10',    emoji:'🌟', name:'First Star',      desc:'Primeros 10 puntos',    needed: 10},
  {id:'animal',     emoji:'🐾', name:'Animal Master',   desc:'Completá 5 preguntas de animales', needed: 50},
  {id:'voice',      emoji:'🎤', name:'Voice Hero',      desc:'Pronunciá 3 palabras bien',        needed: 45},
  {id:'memo',       emoji:'🃏', name:'Memory King',     desc:'Completá el Memotest',             needed: 80},
  {id:'champion',   emoji:'🏆', name:'English Champion',desc:'Alcanzá 200 puntos',               needed:200},
];

function addStars(n) {
  stars += n;
  localStorage.setItem('foschi_stars', stars);
  updateStars();
  checkBadge();
}

function updateStars() {
  document.getElementById('starCount').textContent = stars;
}

function checkBadge() {
  BADGES.forEach(b => {
    if (!unlockedBadges.includes(b.id) && stars >= b.needed) {
      unlockedBadges.push(b.id);
      localStorage.setItem('foschi_badges', JSON.stringify(unlockedBadges));
      showReward(b.emoji, b.name, b.desc);
    }
  });
}

function renderBadges() {
  const list = document.getElementById('badgesList');
  list.innerHTML = '';
  BADGES.forEach(b => {
    const locked = !unlockedBadges.includes(b.id);
    list.innerHTML += `
      <div style="text-align:center;width:100px;opacity:${locked?0.35:1}">
        <div style="font-size:2.8rem">${b.emoji}</div>
        <div style="font-weight:700;font-size:.78rem;color:#4c1d95">${b.name}</div>
        <div style="font-size:.7rem;color:#6b7280">${locked ? '🔒 Bloqueado' : '✅ Ganado'}</div>
      </div>`;
  });
}

// ═══════════════════════════════════════════════
//  REWARD POPUP
// ═══════════════════════════════════════════════
function showReward(emoji, title, msg) {
  document.getElementById('rewardEmoji').textContent = emoji;
  document.getElementById('rewardTitle').textContent = title;
  document.getElementById('rewardMsg').textContent   = msg;
  const popup = document.getElementById('rewardPopup');
  popup.classList.add('show');
  setTimeout(() => popup.classList.remove('show'), 2200);
}

// ═══════════════════════════════════════════════
//  INIT
// ═══════════════════════════════════════════════
window.onload = () => {
  updateStars();
  startAdultChat();
  nextPronWord();
  loadProgress();
};
</script>
</body>
</html>
"""

# ──────────────────────────────────────────────
#  PROMPTS DE SISTEMA
# ──────────────────────────────────────────────
SYSTEM_ADULT = """Sos el Profesor de Inglés de la Academia Foschi IA.
Tu filosofía: un alumno que no aprende es responsabilidad del docente, no del alumno.
Tus reglas:
1. Conversás en inglés con el alumno.
2. Si el alumno comete un error gramatical, primero respondés naturalmente en inglés y LUEGO agregás una corrección breve en español entre corchetes, ej: [✅ Corrección: en inglés decimos "I am 30 years old", no "I have 30 years"].
3. Hacés preguntas de seguimiento para que el alumno practique más.
4. Sos paciente, motivador, con buen humor.
5. Si el alumno escribe en español, le respondés en inglés y le pedís amablemente que lo intente en inglés.
6. Adaptás la dificultad al nivel del alumno.
7. NO avanzás a otro tema hasta que el alumno demuestre comprensión.
8. Al final de tu respuesta, incluí un JSON en una línea separada así:
SCORE:{"score":85}
donde el número representa cuánto dominó el alumno el tema en este intercambio (0-100).
Tema actual: {topic}"""

SYSTEM_KIDS = """Sos el Profesor de Inglés para niños de la Academia Foschi IA.
Reglas fundamentales:
1. Usás palabras MUY simples, frases cortas.
2. Siempre usás emojis para hacer la clase divertida 🎉🌟😊.
3. Celebrás CADA respuesta del niño, aunque esté mal — primero motivás, luego corregís suave.
4. Preguntás cosas fáciles: colores, animales, números, frutas.
5. Si el niño escribe en español, le respondés también en español pero le enseñás la palabra en inglés.
6. Nunca hacés clases largas — frases cortas, muchos emojis, mucha alegría.
7. Sos como un amigo mayor, no un profesor serio."""

SYSTEM_CORRECTOR = """Sos un corrector experto de inglés de la Academia Foschi IA.
Tu tarea:
1. Analizás el texto que te dan.
2. Identificás TODOS los errores gramaticales, de vocabulario y de puntuación.
3. Mostrás el texto CORREGIDO.
4. Explicás cada corrección en español, en forma clara y didáctica.
5. Terminás con una nota de aliento.
6. Al final incluí una línea: SCORE:{"score":85,"has_errors":true}
   donde score = porcentaje de corrección del texto original (100 = perfecto)."""

# ──────────────────────────────────────────────
#  RUTAS
# ──────────────────────────────────────────────
def init_academia_ingles(app):

    @app.route("/ingles")
    @app.route("/academia")
    def academia_view():
        return render_template_string(ACADEMIA_HTML)

    @app.route("/academia/chat", methods=["POST"])
    def academia_chat():
        data    = request.get_json(force=True)
        history = data.get("history", [])
        topic   = data.get("topic", "free")

        system = SYSTEM_ADULT.replace("{topic}", topic)
        msgs   = [{"role": m["role"], "content": m["content"]} for m in history[-12:]]

        try:
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "system", "content": system}] + msgs,
                max_tokens=400,
                temperature=0.7,
            )
            full = resp.choices[0].message.content or ""

            # Separar score del reply
            score_val = 70
            correction = None
            reply_text = full

            import re
            score_match = re.search(r'SCORE:\{"score":(\d+)\}', full)
            if score_match:
                score_val  = int(score_match.group(1))
                reply_text = full[:score_match.start()].strip()

            # Separar corrección si está entre corchetes
            corr_match = re.search(r'\[✅[^\]]+\]', reply_text)
            if corr_match:
                correction = corr_match.group(0)

            return jsonify({"reply": reply_text, "correction": correction, "score": score_val})

        except Exception as e:
            return jsonify({"error": str(e), "reply": "Lo siento, hubo un error. Intentá de nuevo."}), 500

    @app.route("/academia/chat-kids", methods=["POST"])
    def academia_chat_kids():
        data    = request.get_json(force=True)
        history = data.get("history", [])

        msgs = [{"role": m["role"], "content": m["content"]} for m in history[-10:]]

        try:
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "system", "content": SYSTEM_KIDS}] + msgs,
                max_tokens=200,
                temperature=0.8,
            )
            reply = resp.choices[0].message.content or "Let's learn! 😊"
            return jsonify({"reply": reply})

        except Exception as e:
            return jsonify({"error": str(e), "reply": "❌ Error. Intentá de nuevo."}), 500

    @app.route("/academia/correct", methods=["POST"])
    def academia_correct():
        data = request.get_json(force=True)
        text = data.get("text", "").strip()
        if not text:
            return jsonify({"result": "No enviaste texto.", "score": 0, "has_errors": False})

        try:
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": SYSTEM_CORRECTOR},
                    {"role": "user",   "content": text}
                ],
                max_tokens=600,
                temperature=0.3,
            )
            full = resp.choices[0].message.content or ""

            import re
            score_val  = 70
            has_errors = True
            score_match = re.search(r'SCORE:\{"score":(\d+),"has_errors":(true|false)\}', full)
            if score_match:
                score_val  = int(score_match.group(1))
                has_errors = score_match.group(2) == 'true'
                full = full[:score_match.start()].strip()

            return jsonify({"result": full, "score": score_val, "has_errors": has_errors})

        except Exception as e:
            return jsonify({"result": f"Error: {str(e)}", "score": 0, "has_errors": True}), 500
