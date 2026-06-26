#!/usr/bin/env python3
# coding: utf-8
"""
academia_ingles.py — Academia de Inglés Foschi IA v2
Mejoras v2:
  - 🎙️ Voz bidireccional: el alumno habla y la IA responde con voz
  - 🔁 Repetición obligatoria: no avanza hasta corregir el error
  - 🧠 Memoria de errores: el profesor recuerda qué falla el alumno
  - 🗣️ Situaciones reales: restaurante, aeropuerto, hotel, médico, etc.
  - 📊 Nivel adaptativo: bilingüismo ajustado por nivel del alumno
Requiere: pip install flask anthropic
Configurar: variable de entorno ANTHROPIC_API_KEY
"""

import os
import json
import re
from flask import request, jsonify, render_template_string

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
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Segoe UI',sans-serif;background:#f0f4ff;min-height:100vh;overflow-x:hidden}
:root{
  --pur:#6c3fc5;--pur2:#a78bfa;--pur3:#ede9fe;
  --kids-bg:#fff7ed;--kids-acc:#f59e0b;
  --grn:#10b981;--red:#ef4444;
  --rad:14px;--shadow:0 2px 16px rgba(108,63,197,.13);
}
.header{background:linear-gradient(135deg,#6c3fc5,#a855f7);color:#fff;text-align:center;padding:14px 16px 10px;position:sticky;top:0;z-index:50}
.header h1{font-size:1.5rem;font-weight:800;letter-spacing:.5px}
.header p{font-size:.8rem;opacity:.85;margin-top:2px}
.mode-bar{display:flex;gap:12px;justify-content:center;padding:18px 16px 6px}
.mbtn{flex:1;max-width:180px;padding:14px 10px;border-radius:var(--rad);border:2.5px solid transparent;cursor:pointer;font-weight:700;font-size:.95rem;text-align:center;transition:all .2s;box-shadow:var(--shadow)}
.mbtn.adult{background:#f0f4ff;color:var(--pur);border-color:var(--pur)}
.mbtn.kids{background:var(--kids-bg);color:#d97706;border-color:var(--kids-acc)}
.mbtn.adult.on{background:var(--pur);color:#fff}
.mbtn.kids.on{background:var(--kids-acc);color:#fff}
.mbtn .ico{font-size:1.8rem;display:block;margin-bottom:4px}
.main{max-width:860px;margin:0 auto;padding:8px 14px 40px}
.tabs{display:flex;gap:6px;flex-wrap:wrap;margin:14px 0 10px}
.tab{padding:7px 14px;border-radius:30px;border:2px solid var(--pur);background:#fff;color:var(--pur);font-weight:600;cursor:pointer;font-size:.82rem;transition:all .2s}
.tab.on{background:var(--pur);color:#fff}
.ktab{border-color:var(--kids-acc);color:#92400e}
.ktab.on{background:var(--kids-acc);color:#fff}
.card{background:#fff;border-radius:var(--rad);padding:18px;box-shadow:var(--shadow);margin-bottom:14px}
.card h2{color:var(--pur);font-size:1rem;margin-bottom:12px}
.sec{display:none}.sec.on{display:block}
#chatBox,#kidsChatBox{height:300px;overflow-y:auto;background:#f5f3ff;border-radius:10px;padding:12px;display:flex;flex-direction:column;gap:8px;margin-bottom:10px}
#kidsChatBox{background:#fff7ed}
.msg{max-width:82%;padding:9px 13px;border-radius:10px;line-height:1.5;font-size:.88rem}
.msg.ai{background:#fff;border:1.5px solid #e0d6fa;align-self:flex-start;color:#2d1b69}
.msg.usr{background:var(--pur);color:#fff;align-self:flex-end}
.msg.corr{background:#fff8e1;border:1.5px solid #f59e0b;color:#78350f;align-self:flex-start;font-size:.82rem;font-weight:600}
.msg.repeat-req{background:#fff1f2;border:2px solid #ef4444;color:#881337;align-self:flex-start;font-size:.85rem;font-weight:700;border-radius:10px;padding:10px 14px}
.msg.kid-ai{background:#fff3e0;border:1.5px solid #fed7aa;align-self:flex-start;color:#78350f}
.row{display:flex;gap:8px;align-items:center}
.row input{flex:1;padding:9px 13px;border-radius:30px;border:2px solid #d1c4e9;font-size:.9rem;outline:none;transition:border .2s;font-family:inherit}
.row input:focus{border-color:var(--pur)}
.row input:disabled{background:#f3f4f6;color:#9ca3af;cursor:not-allowed}
.btn{padding:9px 18px;border-radius:30px;border:none;background:var(--pur);color:#fff;font-weight:700;cursor:pointer;font-size:.85rem;transition:background .2s;white-space:nowrap}
.btn:hover{opacity:.9}.btn:disabled{opacity:.5;cursor:default}
.btn.grn{background:var(--grn)}.btn.org{background:#f59e0b;color:#fff}.btn.red{background:var(--red)}
.btn-mic{width:46px;height:46px;border-radius:50%;border:none;background:var(--grn);color:#fff;font-size:1.2rem;cursor:pointer;flex-shrink:0;transition:all .2s;display:flex;align-items:center;justify-content:center}
.btn-mic:hover{opacity:.9}
.btn-mic.recording{background:var(--red);animation:pulse 1s infinite}
.btn-mic:disabled{opacity:.5;cursor:default}
@keyframes pulse{0%,100%{transform:scale(1)}50%{transform:scale(1.08)}}
.mic-hint{font-size:.7rem;color:#9ca3af;text-align:center;margin-top:3px}
.voice-badge{display:inline-block;background:#d1fae5;color:#065f46;border-radius:20px;padding:2px 8px;font-size:.72rem;font-weight:700;margin-left:6px;vertical-align:middle}
.pronword{font-size:2rem;font-weight:800;color:var(--pur);text-align:center;padding:16px;letter-spacing:2px}
.pronemi{font-size:3rem;text-align:center;display:block;margin:6px 0}
.bar-wrap{background:#e5e7eb;border-radius:30px;height:14px;overflow:hidden;margin:6px 0}
.bar{height:100%;border-radius:30px;transition:width .5s;background:var(--grn)}
.chips{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:12px}
.chip{padding:6px 14px;border-radius:30px;border:2px solid #d1c4e9;background:#fff;cursor:pointer;font-weight:600;color:#4c1d95;font-size:.8rem;transition:all .2s}
.chip.on,.chip:hover{background:var(--pur);color:#fff;border-color:var(--pur)}
.kchip.on,.kchip:hover{background:var(--kids-acc);color:#fff;border-color:var(--kids-acc)}
.kchip{color:#92400e;border-color:var(--kids-acc)}
.kidsec{background:#fff7ed;border-radius:var(--rad);padding:16px}
.star-bar{text-align:right;font-weight:700;color:#92400e;font-size:.9rem;padding:2px 0 10px}
.big-emi{font-size:4.5rem;text-align:center;display:block;margin:8px 0}
.gq{font-size:1.1rem;font-weight:700;text-align:center;color:#92400e;margin-bottom:14px}
.opts{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.opt{padding:12px;border-radius:12px;border:2.5px solid #fed7aa;background:#fff;font-size:.98rem;font-weight:700;cursor:pointer;transition:all .2s;color:#78350f;text-align:center}
.opt:hover{background:#fff7ed;border-color:var(--kids-acc);transform:scale(1.02)}
.opt.ok{background:#d1fae5;border-color:var(--grn);color:#065f46}
.opt.ng{background:#fee2e2;border-color:var(--red);color:#7f1d1d}
.memo-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:8px}
.mc{aspect-ratio:1;border-radius:10px;background:var(--pur);display:flex;align-items:center;justify-content:center;font-size:1.4rem;cursor:pointer;transition:all .2s;user-select:none;border:2.5px solid transparent;color:#fff;font-weight:700}
.mc:hover:not(.flipped):not(.match){background:var(--pur2)}
.mc.match{background:#d1fae5;border-color:var(--grn);pointer-events:none;color:#065f46}
.popup{position:fixed;top:50%;left:50%;transform:translate(-50%,-50%) scale(0);background:#fff;border-radius:20px;padding:26px 32px;box-shadow:0 16px 50px rgba(0,0,0,.22);z-index:9999;text-align:center;transition:transform .28s cubic-bezier(.34,1.56,.64,1)}
.popup.show{transform:translate(-50%,-50%) scale(1)}
.popup .pe{font-size:3.5rem;display:block;margin-bottom:6px}
.popup h3{font-size:1.3rem;color:var(--pur)}
.popup p{color:#6b7280;margin-top:3px;font-size:.88rem}
.prog-item{margin-bottom:12px}
.prog-item .lbl{display:flex;justify-content:space-between;margin-bottom:3px;font-size:.85rem}
.pct-g{color:var(--grn);font-weight:700}.pct-m{color:#f59e0b;font-weight:700}.pct-l{color:var(--red);font-weight:700}
.rb{background:#fef3c7;color:#92400e;font-size:.72rem;padding:2px 6px;border-radius:8px;margin-left:4px}
textarea{width:100%;padding:10px;border-radius:10px;border:2px solid #d1c4e9;font-size:.9rem;resize:vertical;min-height:75px;outline:none;font-family:inherit;transition:border .2s}
textarea:focus{border-color:var(--pur)}
.corr-box{background:#f0fdf4;border:1.5px solid #a7f3d0;border-radius:10px;padding:12px;margin-top:10px;color:#065f46;line-height:1.6;white-space:pre-wrap;font-size:.88rem}
.err-box{background:#fff1f2;border-color:#fecdd3;color:#881337}
.spin{display:inline-block;width:16px;height:16px;border:2.5px solid rgba(255,255,255,.3);border-top-color:#fff;border-radius:50%;animation:spin .5s linear infinite;margin-right:5px;vertical-align:middle}
@keyframes spin{to{transform:rotate(360deg)}}
.bdg-grid{display:flex;flex-wrap:wrap;gap:12px;margin-top:6px}
.bdg{text-align:center;width:90px}
.bdg .be{font-size:2.4rem}
.bdg .bn{font-weight:700;font-size:.72rem;color:#4c1d95;margin-top:2px}
.bdg .bl{font-size:.65rem;color:#6b7280}
.level-bar{display:flex;gap:4px;margin-bottom:14px;flex-wrap:wrap}
.lvl{padding:5px 12px;border-radius:20px;border:2px solid #d1c4e9;font-size:.78rem;font-weight:700;cursor:pointer;color:#6b7280;transition:all .2s}
.lvl.on{background:var(--pur);color:#fff;border-color:var(--pur)}
.abc-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(56px,1fr));gap:6px;margin-bottom:14px}
.abc-btn{padding:8px 4px;border-radius:8px;background:var(--pur3);border:2px solid #c4b5fd;font-size:.95rem;font-weight:700;cursor:pointer;color:var(--pur);text-align:center;transition:all .2s}
.abc-btn:hover{background:var(--pur2);color:#fff}
.word-card{background:var(--pur3);border-radius:var(--rad);padding:20px;text-align:center;margin-bottom:14px}
.word-card .word-en{font-size:2.2rem;font-weight:800;color:var(--pur)}
.word-card .word-es{font-size:1rem;color:#7c3aed;margin-top:4px}
.word-card .word-ipa{font-size:.9rem;color:#a78bfa;margin-top:2px}
.error-mem{background:#fff8e1;border-radius:10px;padding:10px 14px;font-size:.78rem;color:#78350f;margin-bottom:10px;border:1px solid #f59e0b}
.error-mem strong{color:#92400e}
.situation-chips{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:14px}
.sit-chip{padding:7px 12px;border-radius:30px;border:2px solid #d1c4e9;background:#fff;cursor:pointer;font-weight:600;color:#4c1d95;font-size:.78rem;transition:all .2s}
.sit-chip.on,.sit-chip:hover{background:var(--pur);color:#fff;border-color:var(--pur)}
.level-selector{display:flex;gap:6px;margin-bottom:10px;flex-wrap:wrap;align-items:center}
.level-selector span{font-size:.8rem;color:#6b7280;font-weight:600}
.nlvl{padding:4px 12px;border-radius:20px;border:2px solid #d1c4e9;font-size:.75rem;font-weight:700;cursor:pointer;color:#6b7280;transition:all .2s}
.nlvl.on{background:var(--pur);color:#fff;border-color:var(--pur)}
@media(max-width:580px){.opts{grid-template-columns:1fr}.memo-grid{grid-template-columns:repeat(3,1fr)}.mbtn{max-width:100%;width:100%}.mode-bar{flex-direction:column;align-items:center}}
</style>
</head>
<body>

<div class="header">
  <h1>🎓 Academia Foschi IA</h1>
  <p>Aprendé inglés de verdad — desde cero hasta avanzado</p>
  <div style="margin-top:8px;display:flex;gap:8px;justify-content:center;flex-wrap:wrap">
    <button onclick="window.history.back()" style="background:rgba(255,255,255,0.18);border:1.5px solid rgba(255,255,255,0.5);color:#fff;border-radius:20px;padding:5px 14px;font-size:.78rem;font-weight:700;cursor:pointer">⬅ Volver a Foschi IA</button>
    <span style="background:rgba(255,255,255,0.18);border:1.5px solid rgba(255,255,255,0.5);color:#fff;border-radius:20px;padding:5px 14px;font-size:.78rem;font-weight:700">🎙️ ¡Usá el micrófono para hablar en todo momento!</span>
  </div>
</div>

<div class="mode-bar">
  <button class="mbtn adult on" id="btnA" onclick="setMode('adult')"><span class="ico">🧑</span>Adultos</button>
  <button class="mbtn kids" id="btnK" onclick="setMode('kids')"><span class="ico">👶</span>Niños</button>
</div>

<div class="main">

<!-- ═══ ADULTOS ═══ -->
<div id="mAdult">
  <div class="tabs">
    <button class="tab on" onclick="aTab('conv',this)">💬 Conversación</button>
    <button class="tab" onclick="aTab('situaciones',this)">🎭 Situaciones</button>
    <button class="tab" onclick="aTab('lecciones',this)">📖 Lecciones</button>
    <button class="tab" onclick="aTab('temario',this)">📋 Temario</button>
    <button class="tab" onclick="aTab('oral',this)">🗣️ Práctica Oral</button>
    <button class="tab" onclick="aTab('pron',this)">🎤 Pronunciación</button>
    <button class="tab" onclick="aTab('corrector',this)">✍️ Corrector</button>
    <button class="tab" onclick="aTab('prog',this)">📈 Progreso</button>
  </div>

  <div id="t-conv" class="sec on">
    <div class="card">
      <h2>💬 Conversá con tu Profe</h2>

      <!-- Selector de nivel -->
      <div class="level-selector">
        <span>Mi nivel:</span>
        <div class="nlvl on" onclick="setNivel(this,1)" id="nl1">🌱 Básico</div>
        <div class="nlvl" onclick="setNivel(this,2)" id="nl2">📘 Intermedio</div>
        <div class="nlvl" onclick="setNivel(this,3)" id="nl3">🚀 Avanzado</div>
      </div>

      <!-- Temas -->
      <div class="chips" id="topicChips">
        <div class="chip on" onclick="setTopic(this,'greetings')">👋 Saludos</div>
        <div class="chip" onclick="setTopic(this,'work')">💼 Trabajo</div>
        <div class="chip" onclick="setTopic(this,'travel')">✈️ Viajes</div>
        <div class="chip" onclick="setTopic(this,'family')">👨‍👩‍👧 Familia</div>
        <div class="chip" onclick="setTopic(this,'shopping')">🛒 Compras</div>
        <div class="chip" onclick="setTopic(this,'free')">🗣️ Libre</div>
      </div>

      <!-- Memoria de errores visible -->
      <div id="errorMemBox" style="display:none" class="error-mem">
        🧠 <strong>Tu profe recuerda:</strong> <span id="errorMemTxt"></span>
      </div>

      <div id="chatBox"></div>

      <!-- Input con mic -->
      <div class="row" id="chatInputRow">
        <button class="btn-mic" id="btnMic" onclick="toggleMic()" title="Hablar con el profe">🎤</button>
        <input id="chatIn" placeholder="Escribí o usá el micrófono 🎤..." onkeydown="if(event.key==='Enter'&&!chatBlocked)sendChat()"/>
        <button class="btn" onclick="sendChat()" id="btnSend">Enviar</button>
      </div>
      <div class="mic-hint" id="micHint">Presioná 🎤 para hablar con el profe</div>
    </div>
  </div>

  <!-- ═══ TAB SITUACIONES ═══ -->
  <div id="t-situaciones" class="sec">
    <div class="card">
      <h2>🎭 Conversaciones por Situación</h2>
      <p style="color:#6b7280;font-size:.82rem;margin-bottom:12px">Practicá inglés en situaciones reales. La IA toma el rol del personaje.</p>
      <div class="situation-chips" id="sitChips">
        <div class="sit-chip on" onclick="setSit(this,'restaurant')">🍽️ Restaurante</div>
        <div class="sit-chip" onclick="setSit(this,'airport')">✈️ Aeropuerto</div>
        <div class="sit-chip" onclick="setSit(this,'hotel')">🏨 Hotel</div>
        <div class="sit-chip" onclick="setSit(this,'doctor')">🏥 Médico</div>
        <div class="sit-chip" onclick="setSit(this,'interview')">💼 Entrevista</div>
        <div class="sit-chip" onclick="setSit(this,'police')">👮 Policía</div>
        <div class="sit-chip" onclick="setSit(this,'pharmacy')">💊 Farmacia</div>
        <div class="sit-chip" onclick="setSit(this,'bank')">🏦 Banco</div>
      </div>
      <div id="sitDesc" style="background:#f0f4ff;border-radius:10px;padding:10px;margin-bottom:12px;font-size:.82rem;color:#4c1d95"></div>
      <div id="sitBox" style="height:280px;overflow-y:auto;background:#f5f3ff;border-radius:10px;padding:12px;display:flex;flex-direction:column;gap:8px;margin-bottom:10px"></div>
      <div class="row">
        <button class="btn-mic" id="btnMicSit" onclick="toggleMicSit()" title="Hablar">🎤</button>
        <input id="sitIn" placeholder="Respondé al personaje..." onkeydown="if(event.key==='Enter')sendSit()"/>
        <button class="btn" onclick="sendSit()">Enviar</button>
      </div>
      <div class="mic-hint">Presioná 🎤 para hablar en la situación</div>
    </div>
  </div>

  <div id="t-lecciones" class="sec">
    <div class="card">
      <h2>📖 Lecciones — Elegí tu nivel</h2>
      <div class="level-bar">
        <div class="lvl on" onclick="setLvl(this,0)">🌱 Cero</div>
        <div class="lvl" onclick="setLvl(this,1)">🔤 Básico</div>
        <div class="lvl" onclick="setLvl(this,2)">📘 Intermedio</div>
        <div class="lvl" onclick="setLvl(this,3)">🚀 Avanzado</div>
      </div>
      <div id="lessonArea"></div>
    </div>
  </div>

  <div id="t-pron" class="sec">
    <div class="card">
      <h2>🎤 Pronunciación</h2>
      <span class="pronemi" id="pronEmi">🍎</span>
      <div class="pronword" id="pronW">Apple</div>
      <div style="text-align:center;color:#6b7280;font-size:.82rem;margin-bottom:12px">Escuchá → repetí → compará</div>
      <div style="display:flex;gap:8px;justify-content:center;flex-wrap:wrap;margin-bottom:12px">
        <button class="btn org" onclick="listenWord()">🔊 Escuchar</button>
        <button class="btn grn" onclick="startPron()" id="btnPron">🎤 Hablar</button>
        <button class="btn" onclick="nextPron()">Siguiente ➜</button>
      </div>
      <div id="pronRes"></div>
    </div>
  </div>

  <div id="t-corrector" class="sec">
    <div class="card">
      <h2>✍️ Corrector de Inglés</h2>
      <p style="color:#6b7280;font-size:.82rem;margin-bottom:10px">Escribí cualquier texto en inglés. El profe lo corrige y explica cada error en español.</p>
      <textarea id="corrTxt" placeholder="Ej: I have 25 years old. Yesterday I go to the market..."></textarea>
      <button class="btn" style="margin-top:8px;width:100%" onclick="correctText()" id="btnCorr">🔍 Corregir</button>
      <div id="corrRes"></div>
    </div>
  </div>

  <div id="t-temario" class="sec">
    <div class="card">
      <h2>📋 Temario Completo — 6 Niveles</h2>
      <p style="color:#6b7280;font-size:.82rem;margin-bottom:14px">Hacé clic en cualquier nivel para ver el contenido y escuchar la explicación en español.</p>
      <div id="temarioList"></div>
    </div>
  </div>

  <div id="t-oral" class="sec">
    <div class="card">
      <h2>🗣️ Práctica Oral Guiada</h2>
      <p style="color:#6b7280;font-size:.82rem;margin-bottom:10px">El profe te hace preguntas en voz alta. ¡Respondé hablando! Presioná 🎤 cuando quieras hablar.</p>
      <div class="level-selector" style="margin-bottom:12px">
        <span>Nivel:</span>
        <div class="nlvl on" onclick="setOralNivel(this,1)" id="onl1">🌱 Básico</div>
        <div class="nlvl" onclick="setOralNivel(this,2)" id="onl2">📘 Intermedio</div>
        <div class="nlvl" onclick="setOralNivel(this,3)" id="onl3">🚀 Avanzado</div>
      </div>
      <div class="chips" id="oralTopics">
        <div class="chip on" onclick="setOralTopic(this,'presentacion')">👋 Presentación</div>
        <div class="chip" onclick="setOralTopic(this,'rutina')">⏰ Rutina diaria</div>
        <div class="chip" onclick="setOralTopic(this,'familia')">👨‍👩‍👧 Familia</div>
        <div class="chip" onclick="setOralTopic(this,'trabajo')">💼 Trabajo</div>
        <div class="chip" onclick="setOralTopic(this,'viaje')">✈️ Viaje</div>
        <div class="chip" onclick="setOralTopic(this,'libre')">🎲 Libre</div>
      </div>
      <div id="oralBox" style="height:280px;overflow-y:auto;background:#f5f3ff;border-radius:10px;padding:12px;display:flex;flex-direction:column;gap:8px;margin-bottom:10px"></div>
      <div style="background:#fef3c7;border-radius:10px;padding:10px;margin-bottom:10px;font-size:.82rem;color:#92400e">
        💡 <strong>Tip:</strong> El profe habla primero en español (nivel básico) y después en inglés. ¡Respondé hablando!
      </div>
      <div class="row">
        <button class="btn-mic" id="btnMicOral" onclick="toggleMicOral()" title="Hablar con el profe oral">🎤</button>
        <input id="oralIn" placeholder="O escribí tu respuesta aquí..." onkeydown="if(event.key==='Enter')sendOral()"/>
        <button class="btn grn" onclick="sendOral()">Responder</button>
      </div>
      <div class="mic-hint" id="oralMicHint">Presioná 🎤 para responder hablando — ¡el profe escucha!</div>
    </div>
  </div>


    <div class="card">
      <h2>📈 Tu Progreso</h2>
      <p style="color:#6b7280;font-size:.82rem;margin-bottom:14px">Temas bajo 80% necesitan repaso.</p>
      <div id="progList"></div>
      <div id="errorProgBox" style="margin-top:14px"></div>
      <button class="btn" style="margin-top:12px" onclick="loadProg()">🔄 Actualizar</button>
    </div>
  </div>
</div>

<!-- ═══ NIÑOS ═══ -->
<div id="mKids" style="display:none">
  <div class="kidsec">
    <div class="star-bar">⭐ <span id="stC">0</span> puntos</div>
    <div class="tabs">
      <button class="tab ktab on" onclick="kTab('abcLearn',this)">🔤 ABC</button>
      <button class="tab ktab" onclick="kTab('games',this)">🎮 Juegos</button>
      <button class="tab ktab" onclick="kTab('memo',this)">🃏 Memotest</button>
      <button class="tab ktab" onclick="kTab('kpron',this)">🎤 Pronunciar</button>
      <button class="tab ktab" onclick="kTab('kchat',this)">🧑‍🏫 Profe</button>
      <button class="tab ktab" onclick="kTab('badges',this)">🏆 Logros</button>
    </div>

    <div id="t-abcLearn" class="sec on">
      <div class="card">
        <h2>🔤 Aprendé el Abecedario en Inglés</h2>
        <p style="color:#6b7280;font-size:.82rem;margin-bottom:12px">Tocá una letra para escucharla y aprender palabras 🎵</p>
        <div class="abc-grid" id="abcGrid"></div>
        <div id="letterInfo" style="display:none">
          <div class="word-card">
            <div class="word-en" id="liLetter">A</div>
            <div class="word-es" id="liWord">Apple 🍎</div>
            <div class="word-ipa" id="liIpa">/ˈæpəl/</div>
          </div>
          <div style="display:flex;gap:8px;justify-content:center;flex-wrap:wrap;margin-bottom:8px">
            <button class="btn org" onclick="speakLetter()">🔊 Escuchar</button>
            <button class="btn grn" onclick="kidsSpeak2()" id="btnKSpk2">🎤 Repetir</button>
          </div>
          <div id="letterResult"></div>
        </div>
      </div>
    </div>

    <div id="t-games" class="sec">
      <div class="card">
        <h2>🎮 ¿Qué es esto?</h2>
        <div class="chips">
          <div class="chip kchip on" onclick="setKTopic(this,'animals')">🐶 Animales</div>
          <div class="chip kchip" onclick="setKTopic(this,'colors')">🎨 Colores</div>
          <div class="chip kchip" onclick="setKTopic(this,'fruits')">🍎 Frutas</div>
          <div class="chip kchip" onclick="setKTopic(this,'numbers')">🔢 Números</div>
          <div class="chip kchip" onclick="setKTopic(this,'body')">🦴 Cuerpo</div>
          <div class="chip kchip" onclick="setKTopic(this,'clothes')">👕 Ropa</div>
        </div>
        <span class="big-emi" id="gEmi">🐶</span>
        <div class="gq" id="gQ">What animal is this?</div>
        <div class="opts" id="optsGrid"></div>
        <div style="text-align:center;margin-top:12px">
          <button class="btn org" onclick="nextGame()">➜ Siguiente</button>
          <button class="btn" onclick="kidsHearWord()" style="margin-left:6px">🔊 Escuchar</button>
        </div>
      </div>
    </div>

    <div id="t-memo" class="sec">
      <div class="card">
        <h2>🃏 Memotest</h2>
        <p style="color:#6b7280;font-size:.82rem;margin-bottom:10px">Emparejá el emoji con su palabra en inglés.</p>
        <div class="memo-grid" id="memoGrid"></div>
        <button class="btn" style="margin-top:12px;width:100%" onclick="initMemo()">🔄 Nuevo juego</button>
      </div>
    </div>

    <div id="t-kpron" class="sec">
      <div class="card" style="text-align:center">
        <h2>🎤 ¡Aprendé a decirlo!</h2>
        <span class="big-emi" id="kpEmi">🍎</span>
        <div class="pronword" id="kpW">Apple</div>
        <p style="color:#6b7280;font-size:.82rem;margin:6px 0 14px">Primero escuchá, después decilo vos 😄</p>
        <div style="display:flex;gap:8px;justify-content:center;flex-wrap:wrap;margin-bottom:14px">
          <button class="btn org" onclick="kListen()">🔊 Escuchar</button>
          <button class="btn grn" onclick="kSpeak()" id="btnKS">🎤 ¡Lo digo yo!</button>
          <button class="btn" onclick="nextKWord()">Siguiente ➜</button>
        </div>
        <div id="kVR"></div>
      </div>
    </div>

    <div id="t-kchat" class="sec">
      <div class="card">
        <h2>🧑‍🏫 Hablá con el Profe</h2>
        <div id="kidsChatBox"></div>
        <div class="row">
          <button class="btn-mic" id="btnMicKids" onclick="toggleMicKids()" title="Hablar">🎤</button>
          <input id="kChatIn" placeholder="Escribí o usá el micrófono 🎤..." onkeydown="if(event.key==='Enter')sendKChat()"/>
          <button class="btn org" onclick="sendKChat()">Enviar</button>
        </div>
        <div class="mic-hint">Presioná 🎤 para hablar con el profe</div>
      </div>
    </div>

    <div id="t-badges" class="sec">
      <div class="card">
        <h2>🏆 Tus Logros</h2>
        <div class="bdg-grid" id="bdgList"></div>
      </div>
    </div>
  </div>
</div>

</div><!-- main -->

<!-- 🎤 Botón flotante de micrófono siempre visible -->
<div id="floatMicWrap" style="position:fixed;bottom:24px;right:20px;z-index:999;display:flex;flex-direction:column;align-items:center;gap:4px">
  <button id="floatMicBtn" onclick="activateFloatMic()" style="width:58px;height:58px;border-radius:50%;border:none;background:#10b981;color:#fff;font-size:1.5rem;cursor:pointer;box-shadow:0 4px 18px rgba(16,185,129,0.45);transition:all .2s" title="Hablar en cualquier momento">🎤</button>
  <span style="font-size:.6rem;color:#6b7280;font-weight:700;text-align:center;max-width:60px">Hablar</span>
</div>

<!-- 🤖 FOSCHI IA — Chat flotante dentro de la academia -->
<div id="foschiPanel" style="position:fixed;bottom:24px;left:16px;z-index:1000;width:320px;display:none;flex-direction:column;border-radius:18px;overflow:hidden;box-shadow:0 8px 36px rgba(0,0,0,.25);border:2px solid #00ff8844;font-family:'Segoe UI',sans-serif">
  <!-- Header -->
  <div style="background:linear-gradient(135deg,#001800,#003300);color:#00ff88;padding:11px 14px;display:flex;align-items:center;justify-content:space-between">
    <div style="display:flex;align-items:center;gap:8px">
      <span style="font-size:1.5rem">🤖</span>
      <div>
        <div style="font-weight:800;font-size:.92rem;letter-spacing:.3px">FOSCHI IA</div>
        <div style="font-size:.68rem;opacity:.7">Consultas extras · Siempre disponible</div>
      </div>
    </div>
    <div style="display:flex;gap:6px;align-items:center">
      <a href="/" target="_blank" style="background:rgba(0,255,136,.15);border:1px solid #00ff8844;color:#00ff88;border-radius:12px;padding:3px 8px;font-size:.68rem;font-weight:700;text-decoration:none">🏠 Ir a Foschi IA</a>
      <button onclick="toggleFoschiPanel()" style="background:none;border:none;color:#00ff88;font-size:1.1rem;cursor:pointer;opacity:.7">✕</button>
    </div>
  </div>
  <!-- Chat box -->
  <div id="foschiChatBox" style="height:260px;overflow-y:auto;background:#0a0f0a;padding:10px;display:flex;flex-direction:column;gap:7px"></div>
  <!-- Input -->
  <div style="background:#0d150d;padding:8px 10px;border-top:1px solid #00ff8822;display:flex;gap:6px;align-items:center">
    <button id="btnMicFoschi" onclick="toggleMicFoschi()" style="width:36px;height:36px;border-radius:50%;border:1px solid #00ff8844;background:#001a00;color:#00ff88;font-size:.9rem;cursor:pointer;flex-shrink:0">🎤</button>
    <input id="foschiIn" placeholder="Preguntale algo a Foschi IA..." onkeydown="if(event.key==='Enter')sendFoschi()" style="flex:1;padding:7px 12px;border-radius:20px;border:1px solid #00ff8833;background:#001a00;color:#00ff88;font-size:.8rem;outline:none;font-family:inherit"/>
    <button onclick="sendFoschi()" style="padding:7px 13px;border-radius:20px;border:1px solid #00ff8844;background:linear-gradient(135deg,#003300,#005500);color:#00ff88;font-weight:700;font-size:.78rem;cursor:pointer">→</button>
  </div>
</div>
<!-- Botón para abrir Foschi IA panel -->
<button onclick="toggleFoschiPanel()" style="position:fixed;bottom:24px;left:20px;z-index:1001;width:58px;height:58px;border-radius:50%;border:2px solid #00ff8866;background:linear-gradient(135deg,#001a00,#003300);color:#00ff88;font-size:1.4rem;cursor:pointer;box-shadow:0 4px 18px rgba(0,255,136,.25);transition:all .2s" title="Abrir Foschi IA">🤖</button>

<!-- 🙋 Preguntas al profe — siempre visible -->
<div id="askTeacherPanel" style="position:fixed;bottom:96px;right:16px;z-index:998;width:300px;display:none;background:#fff;border-radius:16px;box-shadow:0 8px 32px rgba(108,63,197,.22);border:2px solid #ede9fe">
  <div style="background:linear-gradient(135deg,#6c3fc5,#a855f7);color:#fff;padding:10px 14px;border-radius:14px 14px 0 0;display:flex;justify-content:space-between;align-items:center">
    <span style="font-weight:800;font-size:.9rem">🙋 Preguntá al Profe</span>
    <button onclick="document.getElementById('askTeacherPanel').style.display='none'" style="background:none;border:none;color:#fff;font-size:1.1rem;cursor:pointer">✕</button>
  </div>
  <div id="askBox" style="height:160px;overflow-y:auto;padding:10px;display:flex;flex-direction:column;gap:6px"></div>
  <div style="padding:8px 10px;border-top:1px solid #ede9fe">
    <div style="display:flex;gap:6px;align-items:center">
      <button id="btnMicAsk" onclick="toggleMicAsk()" style="width:38px;height:38px;border-radius:50%;border:none;background:#10b981;color:#fff;font-size:1rem;cursor:pointer;flex-shrink:0">🎤</button>
      <input id="askIn" placeholder="¿Tenés una duda? Escribila o hablá..." style="flex:1;padding:7px 12px;border-radius:20px;border:2px solid #d1c4e9;font-size:.82rem;outline:none;font-family:inherit" onkeydown="if(event.key==='Enter')sendAsk()"/>
      <button onclick="sendAsk()" style="padding:7px 12px;border-radius:20px;border:none;background:#6c3fc5;color:#fff;font-weight:700;font-size:.78rem;cursor:pointer">→</button>
    </div>
  </div>
</div>
<button onclick="toggleAskPanel()" style="position:fixed;bottom:92px;right:84px;z-index:998;width:52px;height:52px;border-radius:50%;border:none;background:#6c3fc5;color:#fff;font-size:1.2rem;cursor:pointer;box-shadow:0 4px 16px rgba(108,63,197,.4)" title="Preguntá al profe">🙋</button>


  <span class="pe" id="pEmi">⭐</span>
  <h3 id="pTit">¡Muy bien!</h3>
  <p id="pMsg">+10 puntos</p>
</div>

<script>
const VOCAB = {
  animals:[{e:"🐶",w:"Dog",es:"perro"},{e:"🐱",w:"Cat",es:"gato"},{e:"🐦",w:"Bird",es:"pájaro"},{e:"🐟",w:"Fish",es:"pez"},{e:"🐘",w:"Elephant",es:"elefante"},{e:"🦁",w:"Lion",es:"león"},{e:"🐻",w:"Bear",es:"oso"},{e:"🐰",w:"Rabbit",es:"conejo"},{e:"🦊",w:"Fox",es:"zorro"},{e:"🐸",w:"Frog",es:"rana"}],
  colors:[{e:"🔴",w:"Red",es:"rojo"},{e:"🔵",w:"Blue",es:"azul"},{e:"🟡",w:"Yellow",es:"amarillo"},{e:"🟢",w:"Green",es:"verde"},{e:"⚫",w:"Black",es:"negro"},{e:"⚪",w:"White",es:"blanco"},{e:"🟠",w:"Orange",es:"naranja"},{e:"🟣",w:"Purple",es:"morado"}],
  fruits:[{e:"🍎",w:"Apple",es:"manzana"},{e:"🍌",w:"Banana",es:"banana"},{e:"🍇",w:"Grapes",es:"uvas"},{e:"🍓",w:"Strawberry",es:"frutilla"},{e:"🍊",w:"Orange",es:"naranja"},{e:"🍋",w:"Lemon",es:"limón"},{e:"🍑",w:"Peach",es:"durazno"},{e:"🍉",w:"Watermelon",es:"sandía"}],
  numbers:[{e:"1️⃣",w:"One",es:"uno"},{e:"2️⃣",w:"Two",es:"dos"},{e:"3️⃣",w:"Three",es:"tres"},{e:"4️⃣",w:"Four",es:"cuatro"},{e:"5️⃣",w:"Five",es:"cinco"},{e:"6️⃣",w:"Six",es:"seis"},{e:"7️⃣",w:"Seven",es:"siete"},{e:"8️⃣",w:"Eight",es:"ocho"},{e:"9️⃣",w:"Nine",es:"nueve"},{e:"🔟",w:"Ten",es:"diez"}],
  body:[{e:"👁️",w:"Eye",es:"ojo"},{e:"👂",w:"Ear",es:"oreja"},{e:"👃",w:"Nose",es:"nariz"},{e:"👄",w:"Mouth",es:"boca"},{e:"🦷",w:"Tooth",es:"diente"},{e:"🦴",w:"Bone",es:"hueso"},{e:"💪",w:"Arm",es:"brazo"},{e:"🦵",w:"Leg",es:"pierna"},{e:"🖐️",w:"Hand",es:"mano"},{e:"👣",w:"Foot",es:"pie"}],
  clothes:[{e:"👕",w:"T-shirt",es:"remera"},{e:"👖",w:"Pants",es:"pantalón"},{e:"👟",w:"Shoes",es:"zapatillas"},{e:"🧤",w:"Gloves",es:"guantes"},{e:"🎩",w:"Hat",es:"sombrero"},{e:"🧣",w:"Scarf",es:"bufanda"},{e:"👗",w:"Dress",es:"vestido"},{e:"🧦",w:"Socks",es:"medias"}]
};

const PRON_WORDS=[
  {e:"🍎",w:"Apple"},{e:"🐶",w:"Dog"},{e:"📚",w:"Book"},{e:"🏠",w:"House"},
  {e:"🚗",w:"Car"},{e:"🌳",w:"Tree"},{e:"🍕",w:"Pizza"},{e:"☀️",w:"Sun"},
  {e:"🎵",w:"Music"},{e:"💻",w:"Computer"},{e:"✈️",w:"Airplane"},{e:"🌊",w:"Ocean"},
  {e:"🌙",w:"Moon"},{e:"⭐",w:"Star"},{e:"🐱",w:"Cat"},{e:"🍌",w:"Banana"}
];

const ABC_DATA={
  A:{word:"Apple",ipa:"/ˈæpəl/",es:"Manzana 🍎"},B:{word:"Ball",ipa:"/bɔːl/",es:"Pelota ⚽"},
  C:{word:"Cat",ipa:"/kæt/",es:"Gato 🐱"},D:{word:"Dog",ipa:"/dɒɡ/",es:"Perro 🐶"},
  E:{word:"Egg",ipa:"/ɛɡ/",es:"Huevo 🥚"},F:{word:"Fish",ipa:"/fɪʃ/",es:"Pez 🐟"},
  G:{word:"Girl",ipa:"/ɡɜːrl/",es:"Niña 👧"},H:{word:"Hat",ipa:"/hæt/",es:"Sombrero 🎩"},
  I:{word:"Ice cream",ipa:"/aɪs kriːm/",es:"Helado 🍦"},J:{word:"Juice",ipa:"/dʒuːs/",es:"Jugo 🧃"},
  K:{word:"Kite",ipa:"/kaɪt/",es:"Cometa 🪁"},L:{word:"Lion",ipa:"/ˈlaɪən/",es:"León 🦁"},
  M:{word:"Moon",ipa:"/muːn/",es:"Luna 🌙"},N:{word:"Nose",ipa:"/noʊz/",es:"Nariz 👃"},
  O:{word:"Orange",ipa:"/ˈɒrɪndʒ/",es:"Naranja 🍊"},P:{word:"Pizza",ipa:"/ˈpiːtsə/",es:"Pizza 🍕"},
  Q:{word:"Queen",ipa:"/kwiːn/",es:"Reina 👑"},R:{word:"Rainbow",ipa:"/ˈreɪnboʊ/",es:"Arcoíris 🌈"},
  S:{word:"Sun",ipa:"/sʌn/",es:"Sol ☀️"},T:{word:"Tree",ipa:"/triː/",es:"Árbol 🌳"},
  U:{word:"Umbrella",ipa:"/ʌmˈbrɛlə/",es:"Paraguas ☂️"},V:{word:"Violin",ipa:"/ˌvaɪəˈlɪn/",es:"Violín 🎻"},
  W:{word:"Water",ipa:"/ˈwɔːtər/",es:"Agua 💧"},X:{word:"Xylophone",ipa:"/ˈzaɪləfoʊn/",es:"Xilófono 🎵"},
  Y:{word:"Yellow",ipa:"/ˈjɛloʊ/",es:"Amarillo 🟡"},Z:{word:"Zebra",ipa:"/ˈziːbrə/",es:"Cebra 🦓"}
};

const BADGES=[
  {id:"first",e:"🌟",n:"Primera Estrella",d:"Primeros 10 puntos",pts:10},
  {id:"star50",e:"⭐",n:"Coleccionista",d:"50 puntos",pts:50},
  {id:"voice",e:"🎤",n:"Voz de Oro",d:"Pronunciá 5 palabras",pts:0,voiceCount:5},
  {id:"champ",e:"🏆",n:"Campeón",d:"200 puntos",pts:200},
  {id:"master",e:"🎓",n:"Maestro",d:"500 puntos",pts:500},
];

const SIT_DATA = {
  restaurant:{icon:'🍽️',role:'Waiter/Waitress',desc:'Practicá pedir comida y hablar en un restaurante. La IA es el/la mesero/a.',start:"Hello! Welcome to La Bella Italia. How many people are dining with us today?"},
  airport:{icon:'✈️',role:'Check-in Agent',desc:'Practicá hacer el check-in y moverse por el aeropuerto. La IA es el/la agente.',start:"Good morning! Welcome to the airport. May I see your passport and booking confirmation, please?"},
  hotel:{icon:'🏨',role:'Receptionist',desc:'Practicá hacer el check-in y pedir cosas en un hotel. La IA es el/la recepcionista.',start:"Good evening! Welcome to the Grand Hotel. Do you have a reservation with us?"},
  doctor:{icon:'🏥',role:'Doctor',desc:'Practicá describir síntomas y hablar con un médico. La IA es el/la doctor/a.',start:"Hello! I'm Dr. Smith. Please, have a seat. What brings you in today? What seems to be the problem?"},
  interview:{icon:'💼',role:'Interviewer',desc:'Practicá una entrevista laboral en inglés. La IA es el/la entrevistador/a.',start:"Good morning! Please, sit down. I'm the HR Manager. Can you start by telling me a little about yourself?"},
  police:{icon:'👮',role:'Police Officer',desc:'Practicá hablar con un policía (por ejemplo, si te para en la calle). La IA es el/la oficial.',start:"Good evening, sir/ma\'am. I\'m Officer Johnson. May I see your ID, please?"},
  pharmacy:{icon:'💊',role:'Pharmacist',desc:'Practicá comprar medicamentos y explicar síntomas en una farmacia.',start:"Hello! How can I help you today? Are you looking for something specific, or do you need some advice?"},
  bank:{icon:'🏦',role:'Bank Teller',desc:'Practicá hacer trámites bancarios en inglés. La IA es el/la cajero/a.',start:"Good morning! Welcome to City Bank. How can I assist you today?"}
};

// ─── ESTADO GLOBAL ───
let mode='adult',topic='greetings',kTopic='animals';
let chatHist=[],kChatHist=[],sitHist=[];
let pronIdx=0,kWordIdx=0,kGIdx=0,lvl=0;
let stars=parseInt(localStorage.getItem('fa_stars')||'0');
let badges=JSON.parse(localStorage.getItem('fa_badges')||'[]');
let voiceCount=parseInt(localStorage.getItem('fa_vc')||'0');
let memoFlipped=[],memoMatched=0,memoCards=[];
let curLetter='A';
let curSit='restaurant';
let nivelAlumno=1; // 1=básico, 2=intermedio, 3=avanzado

// ─── MEMORIA DE ERRORES ───
// Estructura: {past_simple:5, articles:3, to_be:2, spelling:1, ...}
let errorMemory=JSON.parse(localStorage.getItem('fa_errors')||'{}');

let progress=JSON.parse(localStorage.getItem('fa_prog')||JSON.stringify({
  greetings:0,work:0,travel:0,family:0,shopping:0,free:0,pronunciation:0,corrector:0,
  restaurant:0,airport:0,hotel:0,doctor:0,interview:0,police:0,pharmacy:0,bank:0
}));

// ─── CONTROL DE REPETICIÓN OBLIGATORIA ───
let chatBlocked = false; // true cuando esperamos que el alumno corrija
let repeatTarget = '';   // la frase que debe repetir

// ─── SPEECH RECOGNITION GLOBAL ───
let micRecognizer = null;
let micActive = false;
let micSitActive = false;
let micKidsActive = false;

function speak(text,rate,lang){
  rate=rate||0.85;lang=lang||'en-US';
  window.speechSynthesis.cancel();
  var u=new SpeechSynthesisUtterance(text);
  u.lang=lang;u.rate=rate;
  window.speechSynthesis.speak(u);
}

// ─── HELPER: crear reconocedor de voz ───
function createRecognizer(lang, onResult, onEnd){
  if(!('webkitSpeechRecognition' in window||'SpeechRecognition' in window)) return null;
  var SR=window.SpeechRecognition||window.webkitSpeechRecognition;
  var rec=new SR();
  rec.lang=lang||'en-US';
  rec.interimResults=false;
  rec.continuous=false;
  rec.onresult=function(e){
    var transcript=e.results[0][0].transcript.trim();
    onResult(transcript);
  };
  rec.onerror=function(e){console.log('mic error',e.error);if(onEnd)onEnd();};
  rec.onend=function(){if(onEnd)onEnd();};
  return rec;
}

// ─── MIC CONVERSACIÓN ADULTOS ───
function toggleMic(){
  if(!('webkitSpeechRecognition' in window||'SpeechRecognition' in window)){
    document.getElementById('micHint').textContent='⚠️ Tu navegador no soporta micrófono. Usá Chrome.';
    return;
  }
  if(chatBlocked){
    document.getElementById('micHint').textContent='⚠️ Primero corregí el error antes de continuar.';
    return;
  }
  if(micActive){
    micActive=false;
    if(micRecognizer){try{micRecognizer.stop();}catch(e){}}
    setBtnMic('btnMic',false);
    return;
  }
  micActive=true;
  setBtnMic('btnMic',true);
  document.getElementById('micHint').textContent='🔴 Escuchando... hablá en inglés';
  micRecognizer=createRecognizer('en-US',function(txt){
    document.getElementById('chatIn').value=txt;
    micActive=false;
    setBtnMic('btnMic',false);
    document.getElementById('micHint').textContent='✅ Escuché: "'+txt+'" — enviando...';
    setTimeout(sendChat,400);
  },function(){
    micActive=false;
    setBtnMic('btnMic',false);
    document.getElementById('micHint').textContent='Presioná 🎤 para hablar con el profe';
  });
  try{micRecognizer.start();}catch(e){micActive=false;setBtnMic('btnMic',false);}
}

// ─── MIC SITUACIONES ───
function toggleMicSit(){
  if(!('webkitSpeechRecognition' in window||'SpeechRecognition' in window)) return;
  if(micSitActive){
    micSitActive=false;setBtnMic('btnMicSit',false);
    if(micRecognizer){try{micRecognizer.stop();}catch(e){}}
    return;
  }
  micSitActive=true;setBtnMic('btnMicSit',true);
  micRecognizer=createRecognizer('en-US',function(txt){
    document.getElementById('sitIn').value=txt;
    micSitActive=false;setBtnMic('btnMicSit',false);
    setTimeout(sendSit,400);
  },function(){micSitActive=false;setBtnMic('btnMicSit',false);});
  try{micRecognizer.start();}catch(e){micSitActive=false;setBtnMic('btnMicSit',false);}
}

// ─── MIC KIDS ───
function toggleMicKids(){
  if(!('webkitSpeechRecognition' in window||'SpeechRecognition' in window)) return;
  if(micKidsActive){
    micKidsActive=false;setBtnMic('btnMicKids',false);
    if(micRecognizer){try{micRecognizer.stop();}catch(e){}}
    return;
  }
  micKidsActive=true;setBtnMic('btnMicKids',true);
  micRecognizer=createRecognizer('en-US',function(txt){
    document.getElementById('kChatIn').value=txt;
    micKidsActive=false;setBtnMic('btnMicKids',false);
    setTimeout(sendKChat,400);
  },function(){micKidsActive=false;setBtnMic('btnMicKids',false);});
  try{micRecognizer.start();}catch(e){micKidsActive=false;setBtnMic('btnMicKids',false);}
}

function setBtnMic(id,active){
  var b=document.getElementById(id);if(!b)return;
  if(active){b.classList.add('recording');b.textContent='🔴';}
  else{b.classList.remove('recording');b.textContent='🎤';}
}

// ─── MODO ───
function setMode(m){
  mode=m;
  document.getElementById('mAdult').style.display=m==='adult'?'block':'none';
  document.getElementById('mKids').style.display=m==='kids'?'block':'none';
  document.getElementById('btnA').className='mbtn adult'+(m==='adult'?' on':'');
  document.getElementById('btnK').className='mbtn kids'+(m==='kids'?' on':'');
  if(m==='kids'){updateStars();renderBadges();buildABC();nextGame();if(!document.getElementById('kidsChatBox').children.length)startKChat();}
  else{loadProg();if(!document.getElementById('chatBox').children.length)startChat();nextPron();}
}

function aTab(n,el){
  document.querySelectorAll('#mAdult .sec').forEach(function(s){s.classList.remove('on');});
  document.getElementById('t-'+n).classList.add('on');
  document.querySelectorAll('#mAdult .tab').forEach(function(t){t.classList.remove('on');});
  el.classList.add('on');
  if(n==='prog')loadProg();
  if(n==='lecciones')loadLesson();
  if(n==='situaciones'){setSit(document.querySelector('.sit-chip.on')||document.querySelector('.sit-chip'),'restaurant',true);}
}
function kTab(n,el){
  document.querySelectorAll('#mKids .sec').forEach(function(s){s.classList.remove('on');});
  document.getElementById('t-'+n).classList.add('on');
  document.querySelectorAll('.ktab').forEach(function(t){t.classList.remove('on');});
  el.classList.add('on');
  if(n==='memo')initMemo();
  if(n==='kpron')nextKWord();
  if(n==='badges')renderBadges();
  if(n==='abcLearn')buildABC();
}

// ─── NIVEL DEL ALUMNO ───
function setNivel(el,n){
  document.querySelectorAll('.nlvl').forEach(function(x){x.classList.remove('on');});
  el.classList.add('on');nivelAlumno=n;
}

// ─── MEMORIA ERRORES UI ───
function updateErrorMemUI(){
  var box=document.getElementById('errorMemBox');
  var txt=document.getElementById('errorMemTxt');
  var keys=Object.keys(errorMemory).filter(function(k){return errorMemory[k]>0;});
  if(keys.length===0){box.style.display='none';return;}
  var sorted=keys.sort(function(a,b){return errorMemory[b]-errorMemory[a];}).slice(0,3);
  txt.textContent=sorted.map(function(k){return k+' (×'+errorMemory[k]+')';}).join(' · ');
  box.style.display='block';
}

function saveError(type){
  if(!type)return;
  errorMemory[type]=(errorMemory[type]||0)+1;
  localStorage.setItem('fa_errors',JSON.stringify(errorMemory));
  updateErrorMemUI();
}

// ─── CHAT ADULTOS ───
function setTopic(el,t){
  document.querySelectorAll('#topicChips .chip').forEach(function(c){c.classList.remove('on');});
  el.classList.add('on');topic=t;chatHist=[];chatBlocked=false;repeatTarget='';
  document.getElementById('chatBox').innerHTML='';
  unblockInput();
  startChat();
}

function startChat(){
  var greets={
    greetings:"Hello! I'm your English teacher at Academia Foschi! 😊 Today we practice greetings. Let's begin: Can you say 'Hello, my name is...'? Try it!",
    work:"Welcome! Let's practice work vocabulary. Tell me: What do you do for work? Don't worry if it's not perfect — I'll help you!",
    travel:"Great! Travel English is super useful! Imagine you're at the airport. The agent asks: 'Where are you flying today?' What do you answer?",
    family:"Wonderful! Let's talk about family. Start simple: How many people are in your family? Say it in English!",
    shopping:"Let's practice shopping English! Imagine you're in a store. The clerk says: 'Can I help you?' How do you answer?",
    free:"Perfect! Let's have a free conversation. Tell me one thing about yourself in English — anything! I'll help you if you get stuck."
  };
  addMsg(greets[topic]||greets.free,'ai');
  chatHist.push({role:'assistant',content:greets[topic]||greets.free});
  speak((greets[topic]||greets.free).split('?')[0]);
  updateErrorMemUI();
}

function blockInput(target){
  chatBlocked=true;repeatTarget=target||'';
  var inp=document.getElementById('chatIn');
  inp.disabled=false; // sigue habilitado para escribir la repetición
  inp.placeholder='✍️ Repetí la frase correcta arriba...';
  inp.style.borderColor='#ef4444';
  document.getElementById('btnSend').textContent='Corregir ↩';
}
function unblockInput(){
  chatBlocked=false;repeatTarget='';
  var inp=document.getElementById('chatIn');
  inp.disabled=false;
  inp.placeholder='Escribí o usá el micrófono 🎤...';
  inp.style.borderColor='';
  document.getElementById('btnSend').textContent='Enviar';
}

function sendChat(){
  var inp=document.getElementById('chatIn');
  var txt=inp.value.trim();if(!txt)return;

  // Si estamos bloqueados, verificar si el alumno repitió bien
  if(chatBlocked && repeatTarget){
    var clean=function(s){return s.toLowerCase().replace(/[^a-z0-9 ']/g,'').trim();};
    var similarity=clean(txt)===clean(repeatTarget);
    inp.value='';
    addMsg(txt,'usr');
    if(similarity){
      unblockInput();
      addMsg('✅ Perfect! Well done! Now let\'s continue. 🌟','ai');
      speak('Perfect! Well done! Now let us continue.');
      chatHist.push({role:'user',content:txt});
      chatHist.push({role:'assistant',content:'Perfect! Well done! Let\'s continue.'});
      return;
    } else {
      addMsg('🔁 Almost! Please try again. Repeat exactly:\n👉 '+repeatTarget,'repeat-req');
      speak('Try again. Repeat: '+repeatTarget,0.8);
      return;
    }
  }

  inp.value='';
  addMsg(txt,'usr');
  chatHist.push({role:'user',content:txt});
  var btn=document.getElementById('btnSend');
  btn.disabled=true;btn.innerHTML='<span class="spin"></span>Pensando...';
  addMsg('...','ai','loadingA');

  // Armar contexto de errores para el backend
  var errCtx='';
  var topErrors=Object.keys(errorMemory).sort(function(a,b){return errorMemory[b]-errorMemory[a];}).slice(0,3);
  if(topErrors.length)errCtx=topErrors.join(', ');

  fetch('/academia/chat',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({history:chatHist.slice(-12),topic:topic,nivel:nivelAlumno,error_memory:errCtx})})
  .then(function(r){return r.json();})
  .then(function(data){
    var el=document.getElementById('loadingA');if(el)el.remove();
    if(data.reply){
      addMsg(data.reply,'ai');
      // Hablar solo la parte en inglés (antes de [)
      var toSpeak=data.reply.replace(/\[✅[^\]]+\]/g,'').replace(/\*\*/g,'').split('[')[0].trim();
      speak(toSpeak);
    }
    if(data.correction){
      addMsg(data.correction,'corr');
    }
    // Si hay error que requiere repetición
    if(data.repeat_target){
      blockInput(data.repeat_target);
      addMsg('🔁 Antes de continuar, repetí esta frase:\n👉 '+data.repeat_target,'repeat-req');
      speak('Before we continue, please repeat: '+data.repeat_target,0.85);
    }
    // Guardar errores en memoria
    if(data.error_type){
      saveError(data.error_type);
    }
    chatHist.push({role:'assistant',content:data.reply||''});
    if(data.score)updateProg(topic,data.score);
    btn.disabled=false;
    btn.textContent=chatBlocked?'Corregir ↩':'Enviar';
  })
  .catch(function(){
    var el=document.getElementById('loadingA');if(el)el.remove();
    addMsg('❌ Error de conexión. Intentá de nuevo.','ai');
    btn.disabled=false;btn.textContent='Enviar';
  });
}

function addMsg(txt,cls,id){
  var box=document.getElementById('chatBox');
  var d=document.createElement('div');d.className='msg '+cls;
  if(id)d.id=id;
  d.innerHTML=txt.replace(/\*\*(.*?)\*\*/g,'<strong>$1</strong>').replace(/\n/g,'<br>');
  box.appendChild(d);box.scrollTop=box.scrollHeight;
}

// ─── SITUACIONES REALES ───
function setSit(el,sitKey,skipClear){
  if(!sitKey){sitKey='restaurant';}
  document.querySelectorAll('.sit-chip').forEach(function(c){c.classList.remove('on');});
  if(el)el.classList.add('on');
  curSit=sitKey;
  sitHist=[];
  var s=SIT_DATA[sitKey];
  if(!s)return;
  document.getElementById('sitDesc').innerHTML='<strong>'+s.icon+' '+s.role+'</strong> — '+s.desc;
  var box=document.getElementById('sitBox');box.innerHTML='';
  addSitMsg(s.start,'ai');
  sitHist.push({role:'assistant',content:s.start});
  speak(s.start,0.85);
}

function sendSit(){
  var inp=document.getElementById('sitIn');
  var txt=inp.value.trim();if(!txt)return;
  inp.value='';
  addSitMsg(txt,'usr');
  sitHist.push({role:'user',content:txt});
  fetch('/academia/chat-sit',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({history:sitHist.slice(-14),situation:curSit,nivel:nivelAlumno})})
  .then(function(r){return r.json();})
  .then(function(data){
    var reply=data.reply||'I see. Please go on.';
    addSitMsg(reply,'ai');
    sitHist.push({role:'assistant',content:reply});
    speak(reply.split('[')[0].trim());
    if(data.correction)addSitMsg(data.correction,'corr');
    if(data.score)updateProg(curSit,data.score);
  })
  .catch(function(){addSitMsg('❌ Error. Intentá de nuevo.','ai');});
}

function addSitMsg(txt,cls){
  var box=document.getElementById('sitBox');
  var d=document.createElement('div');
  d.className='msg '+(cls==='ai'?'ai':cls==='usr'?'usr':'corr');
  d.innerHTML=txt.replace(/\n/g,'<br>');
  box.appendChild(d);box.scrollTop=box.scrollHeight;
}

// ─── LECCIONES ───
var LESSONS=[
  {level:0,title:"🌱 Absoluto Cero — Primeras Palabras",content:'<div class="word-card"><div class="word-en" style="font-size:1.3rem">Bienvenido al inglés desde cero ✅</div><div class="word-es" style="margin-top:8px">Estas son las 8 palabras más importantes para comenzar</div></div><div style="display:grid;grid-template-columns:1fr 1fr;gap:8px">'+[['Hello','Hola'],['Goodbye','Adiós'],['Yes','Sí'],['No','No'],['Please','Por favor'],['Thank you','Gracias'],['Sorry','Perdón'],['Help','Ayuda']].map(function(x){return '<div style="background:#ede9fe;border-radius:10px;padding:10px"><div style="font-weight:800;font-size:1.1rem;color:#6c3fc5">'+x[0]+'</div><div style="color:#7c3aed;font-size:.88rem">'+x[1]+'</div></div>';}).join('')+'</div><button class="btn" style="margin-top:14px;width:100%" onclick="practiceWords([\'Hello\',\'Goodbye\',\'Yes\',\'No\',\'Please\',\'Thank you\',\'Sorry\',\'Help\'])">🔊 Escuchar todas</button>'},
  {level:1,title:"🔤 Básico — Presentarte",content:'<div class="word-card"><div class="word-en">My name is...</div><div class="word-es">Me llamo...</div><div class="word-ipa">/maɪ neɪm ɪz.../</div></div><div style="display:flex;flex-direction:column;gap:8px">'+[['My name is [nombre]','Me llamo [nombre]'],['I am [edad] years old','Tengo [edad] años'],['I am from Argentina','Soy de Argentina'],['I live in Buenos Aires','Vivo en Buenos Aires'],['Nice to meet you','Mucho gusto'],['I speak a little English','Hablo un poco de inglés']].map(function(x){return '<div style="background:#f0f4ff;border-radius:10px;padding:10px;display:flex;justify-content:space-between;align-items:center;gap:8px"><div><div style="font-weight:700;color:#4c1d95">'+x[0]+'</div><div style="color:#7c3aed;font-size:.82rem">'+x[1]+'</div></div><button class="btn" style="padding:5px 10px;font-size:.75rem" onclick="speak(\''+x[0]+'\')">🔊</button></div>';}).join('')+'</div>'},
  {level:2,title:"📘 Intermedio — Tiempos Verbales",content:'<div class="word-card"><div class="word-en">The Verb "To Be"</div><div class="word-es">El verbo Ser/Estar — el más importante</div></div><div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:14px">'+[['I am','Yo soy/estoy'],['You are','Vos sos/estás'],['He/She is','Él/Ella es/está'],['We are','Nosotros somos'],['They are','Ellos son/están']].map(function(x){return '<div style="background:#ede9fe;border-radius:10px;padding:10px"><div style="font-weight:800;color:#6c3fc5">'+x[0]+'</div><div style="color:#7c3aed;font-size:.82rem">'+x[1]+'</div></div>';}).join('')+'</div><div style="background:#f0fdf4;border-radius:10px;padding:12px;font-size:.88rem;line-height:1.8"><strong>I work</strong> → Trabajo (presente)<br><strong>I worked</strong> → Trabajé (pasado)<br><strong>I will work</strong> → Voy a trabajar (futuro)</div>'},
  {level:3,title:"🚀 Avanzado — Modales y Condicionales",content:'<div class="word-card"><div class="word-en">Modal Verbs</div><div class="word-es">Posibilidad, obligación, permiso</div></div><div style="display:flex;flex-direction:column;gap:8px;margin-bottom:14px">'+[['Can / Could','Puedo / Podría'],['Must / Have to','Debo / Tengo que'],['Should','Debería'],['Would','Haría / Gustaría'],['May / Might','Puedo / Podría — permiso']].map(function(x){return '<div style="background:#f0f4ff;border-radius:10px;padding:10px"><div style="font-weight:800;color:#4c1d95">'+x[0]+'</div><div style="color:#7c3aed;font-size:.82rem">'+x[1]+'</div></div>';}).join('')+'</div><div style="background:#fef9c3;border-radius:10px;padding:12px;font-size:.85rem;line-height:2"><strong>If I study, I will pass.</strong> → real<br><strong>If I studied, I would pass.</strong> → hipotético<br><strong>If I had studied, I would have passed.</strong> → irreal pasado</div>'}
];

function setLvl(el,n){
  document.querySelectorAll('.lvl').forEach(function(l){l.classList.remove('on');});
  el.classList.add('on');lvl=n;loadLesson();
}
function loadLesson(){
  var l=LESSONS[lvl];if(!l)return;
  document.getElementById('lessonArea').innerHTML='<h3 style="color:#6c3fc5;margin-bottom:12px;font-size:1rem">'+l.title+'</h3>'+l.content+'<div style="margin-top:14px;padding:12px;background:#fef3c7;border-radius:10px"><p style="font-size:.82rem;color:#92400e">💡 <strong>Ejercicio:</strong> Andá a 💬 Conversación y practicá este tema con el profe.</p></div>';
}
function practiceWords(words){words.forEach(function(w,i){setTimeout(function(){speak(w);},i*1200);});}

// ─── PRONUNCIACIÓN ADULTOS ───
function nextPron(){
  pronIdx=(pronIdx+1)%PRON_WORDS.length;
  var it=PRON_WORDS[pronIdx];
  document.getElementById('pronW').textContent=it.w;
  document.getElementById('pronEmi').textContent=it.e;
  document.getElementById('pronRes').innerHTML='';
}
function listenWord(){speak(PRON_WORDS[pronIdx].w,0.8);}
function startPron(){
  if(!('webkitSpeechRecognition' in window||'SpeechRecognition' in window)){
    document.getElementById('pronRes').innerHTML='<p style="color:#ef4444">⚠️ Usá Chrome para grabarte 🎤</p>';return;
  }
  var exp=PRON_WORDS[pronIdx].w.toLowerCase();
  var SR=window.SpeechRecognition||window.webkitSpeechRecognition;
  var rec=new SR();rec.lang='en-US';rec.interimResults=false;
  var btn=document.getElementById('btnPron');
  btn.textContent='🔴 Grabando...';btn.style.background='#ef4444';
  rec.onresult=function(e){
    var sp=e.results[0][0].transcript.toLowerCase().trim();
    var conf=Math.round(e.results[0][0].confidence*100);
    showPronScore(exp,sp,conf);
    btn.textContent='🎤 Hablar';btn.style.background='';
    updateProg('pronunciation',conf);
    voiceCount++;localStorage.setItem('fa_vc',voiceCount);
    checkBadges();
  };
  rec.onerror=function(){btn.textContent='🎤 Hablar';btn.style.background='';};
  rec.start();
}
function showPronScore(exp,sp,conf){
  var col=conf>=80?'#10b981':conf>=60?'#f59e0b':'#ef4444';
  var emi=conf>=80?'🌟':conf>=60?'👍':'💪';
  var msg=conf>=80?'¡Excelente pronunciación!':conf>=60?'Bien, podés mejorar.':'¡Seguí practicando!';
  if(conf>=80)speak('Excellent! Perfect pronunciation!');
  else if(conf>=60)speak('Good job! Keep practicing!');
  else speak('Keep trying! You can do it!');
  document.getElementById('pronRes').innerHTML='<div style="padding:12px;background:#f9fafb;border-radius:10px;margin-top:8px"><p style="margin-bottom:6px;font-size:.85rem"><strong>Dijiste:</strong> "'+sp+'"</p><p style="margin-bottom:6px;font-size:.85rem"><strong>Esperado:</strong> "'+exp+'"</p><div class="bar-wrap"><div class="bar" style="width:'+conf+'%;background:'+col+'"></div></div><p style="font-weight:700;color:'+col+';font-size:.88rem">'+emi+' '+conf+'% — '+msg+'</p></div>';
}

// ─── CORRECTOR ───
function correctText(){
  var txt=document.getElementById('corrTxt').value.trim();if(!txt)return;
  var btn=document.getElementById('btnCorr');
  btn.disabled=true;btn.innerHTML='<span class="spin"></span>Corrigiendo...';
  document.getElementById('corrRes').innerHTML='';
  fetch('/academia/correct',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text:txt})})
  .then(function(r){return r.json();})
  .then(function(data){
    document.getElementById('corrRes').innerHTML='<div class="corr-box">'+data.result.replace(/\n/g,'<br>')+'</div>';
    updateProg('corrector',data.score||70);
    if((data.score||0)>=90)speak('Excellent! Your English is very good!');
    else speak('Good effort! Keep practicing!');
    // Guardar tipo de error si vino del corrector
    if(data.error_type)saveError(data.error_type);
    btn.disabled=false;btn.textContent='🔍 Corregir';
  })
  .catch(function(){
    document.getElementById('corrRes').innerHTML='<div class="corr-box err-box">❌ Error de conexión.</div>';
    btn.disabled=false;btn.textContent='🔍 Corregir';
  });
}

// ─── PROGRESO ───
function updateProg(t,s){
  if(!progress[t])progress[t]=0;
  progress[t]=Math.round(progress[t]*0.7+s*0.3);
  localStorage.setItem('fa_prog',JSON.stringify(progress));
}
function loadProg(){
  var topics={greetings:'👋 Saludos',work:'💼 Trabajo',travel:'✈️ Viajes',family:'👨‍👩‍👧 Familia',shopping:'🛒 Compras',free:'🗣️ Libre',pronunciation:'🎤 Pronunciación',corrector:'✍️ Corrector',restaurant:'🍽️ Restaurante',airport:'✈️ Aeropuerto',hotel:'🏨 Hotel',doctor:'🏥 Médico'};
  var list=document.getElementById('progList');list.innerHTML='';
  Object.keys(topics).forEach(function(k){
    var p=progress[k]||0;if(!p)return;
    var lbl=topics[k];
    var cls=p>=80?'pct-g':p>=50?'pct-m':'pct-l';
    var rep=p<80&&p>0?'<span class="rb">↩ Repaso</span>':'';
    var col=p>=80?'#10b981':p>=50?'#f59e0b':'#ef4444';
    list.innerHTML+='<div class="prog-item"><div class="lbl"><span style="font-size:.85rem;font-weight:600">'+lbl+rep+'</span><span class="'+cls+'">'+p+'%</span></div><div class="bar-wrap"><div class="bar" style="width:'+p+'%;background:'+col+'"></div></div></div>';
  });

  // Mostrar errores frecuentes en progreso
  var errBox=document.getElementById('errorProgBox');
  var topE=Object.keys(errorMemory).filter(function(k){return errorMemory[k]>0;}).sort(function(a,b){return errorMemory[b]-errorMemory[a];});
  if(topE.length){
    errBox.innerHTML='<div class="error-mem"><strong>🧠 Errores frecuentes del profe:</strong><br>'+topE.map(function(k){return '&bull; '+k+': '+errorMemory[k]+' veces';}).join('<br>')+'<br><button class="btn" style="margin-top:8px;padding:5px 12px;font-size:.75rem;background:#ef4444" onclick="clearErrors()">🗑️ Limpiar historial</button></div>';
  } else {
    errBox.innerHTML='';
  }
}

function clearErrors(){
  errorMemory={};localStorage.setItem('fa_errors','{}');
  loadProg();updateErrorMemUI();
}

// ─── ABC NIÑOS ───
function buildABC(){
  var g=document.getElementById('abcGrid');g.innerHTML='';
  Object.keys(ABC_DATA).forEach(function(l){
    var b=document.createElement('button');
    b.className='abc-btn';b.textContent=l;
    b.onclick=function(){showLetter(l);};
    g.appendChild(b);
  });
}
function showLetter(l){
  curLetter=l;var d=ABC_DATA[l];
  document.getElementById('letterInfo').style.display='block';
  document.getElementById('liLetter').textContent=l+' / '+l.toLowerCase();
  document.getElementById('liWord').textContent=d.word+' — '+d.es;
  document.getElementById('liIpa').textContent=d.ipa;
  document.getElementById('letterResult').innerHTML='';
  speak(l+'. '+d.word,0.75);
  setTimeout(function(){speak('Great! The letter '+l+' is for '+d.word+'!',0.8);},1500);
}
function speakLetter(){var d=ABC_DATA[curLetter];speak(curLetter+'. '+d.word,0.75);}
function kidsSpeak2(){
  if(!('webkitSpeechRecognition' in window||'SpeechRecognition' in window)){
    document.getElementById('letterResult').innerHTML='<p style="color:#ef4444;text-align:center">⚠️ Usá Chrome 🎤</p>';return;
  }
  var exp=ABC_DATA[curLetter].word.toLowerCase();
  var SR=window.SpeechRecognition||window.webkitSpeechRecognition;
  var rec=new SR();rec.lang='en-US';rec.interimResults=false;
  var btn=document.getElementById('btnKSpk2');
  btn.textContent='🔴 Escuchando...';btn.style.background='#ef4444';
  rec.onresult=function(e){
    var sp=e.results[0][0].transcript.toLowerCase().trim();
    var conf=e.results[0][0].confidence;
    var ok=sp.includes(exp)||conf>0.65;
    if(ok){
      document.getElementById('letterResult').innerHTML='<div style="text-align:center;font-size:1.3rem;color:#10b981;font-weight:800;padding:8px">🌟 ¡Perfecto! ¡Lo dijiste genial!</div>';
      addKidsStars(15);
      speak('Wow! Perfect! You said it perfectly! You are amazing!',0.85);
      showPopup('🌟','¡Perfecto!','¡Dijiste la palabra genial!');
    }else{
      document.getElementById('letterResult').innerHTML='<div style="text-align:center;color:#f59e0b;font-weight:700;padding:8px">Dijiste: "'+sp+'"<br>¡Intentalo de nuevo! 💪</div>';
      speak('Good try! Say it again: '+exp,0.8);
    }
    btn.textContent='🎤 Repetir';btn.style.background='';
    voiceCount++;localStorage.setItem('fa_vc',voiceCount);checkBadges();
  };
  rec.onerror=function(){btn.textContent='🎤 Repetir';btn.style.background='';};
  rec.start();
}

// ─── JUEGOS NIÑOS ───
function setKTopic(el,t){
  document.querySelectorAll('.kchip').forEach(function(c){c.classList.remove('on');});
  el.classList.add('on');kTopic=t;nextGame();
}
function nextGame(){
  var items=VOCAB[kTopic];
  kGIdx=Math.floor(Math.random()*items.length);
  var cor=items[kGIdx];
  document.getElementById('gEmi').textContent=cor.e;
  var qMap={animals:'animal',colors:'color',fruits:'fruit',numbers:'number',body:'body part',clothes:'clothing'};
  document.getElementById('gQ').textContent='What '+( qMap[kTopic]||'word')+' is this?';
  var wr=items.filter(function(_,i){return i!==kGIdx;}).sort(function(){return Math.random()-.5;}).slice(0,3);
  var opts=[cor].concat(wr).sort(function(){return Math.random()-.5;});
  var grid=document.getElementById('optsGrid');grid.innerHTML='';
  opts.forEach(function(o){
    var b=document.createElement('button');
    b.className='opt';b.textContent=o.w;
    b.onclick=function(){checkAns(b,o.w,cor.w,cor.es);};
    grid.appendChild(b);
  });
}
function checkAns(btn,chosen,cor,corEs){
  document.querySelectorAll('.opt').forEach(function(b){b.disabled=true;});
  if(chosen===cor){
    btn.classList.add('ok');addKidsStars(10);
    speak('Yes! Correct! '+cor+' means '+corEs+' in Spanish. Excellent!',0.85);
    showPopup('⭐','¡Correcto!',cor+' = '+corEs+' 🎉 +10 puntos');checkBadges();
  }else{
    btn.classList.add('ng');
    document.querySelectorAll('.opt').forEach(function(b){if(b.textContent===cor)b.classList.add('ok');});
    speak('The correct answer is '+cor+'. '+cor+' means '+corEs+' in Spanish. Don\'t give up!',0.85);
    showPopup('💪','¡Casi!','La respuesta era: '+cor+' ('+corEs+')');
  }
}
function kidsHearWord(){speak(VOCAB[kTopic][kGIdx].w,0.8);}

// ─── MEMOTEST ───
function initMemo(){
  var items=VOCAB['animals'].slice(0,4);
  var pairs=items.map(function(i){return {type:'emoji',val:i.e,pair:i.w};}).concat(items.map(function(i){return {type:'word',val:i.w,pair:i.e};}));
  memoCards=pairs.sort(function(){return Math.random()-.5;});
  memoFlipped=[];memoMatched=0;
  var grid=document.getElementById('memoGrid');grid.innerHTML='';
  memoCards.forEach(function(card,idx){
    var d=document.createElement('div');
    d.className='mc';d.dataset.idx=idx;d.dataset.val=card.val;d.dataset.pair=card.pair;
    d.textContent='?';d.onclick=function(){flipMemo(d,idx);};
    grid.appendChild(d);
  });
}
function flipMemo(div,idx){
  if(memoFlipped.length>=2||div.classList.contains('match'))return;
  div.textContent=memoCards[idx].val;memoFlipped.push(div);
  if(memoFlipped.length===2){
    var a=memoFlipped[0],b=memoFlipped[1];
    var match=a.dataset.pair===b.dataset.val||b.dataset.pair===a.dataset.val;
    setTimeout(function(){
      if(match){
        a.classList.add('match');b.classList.add('match');memoMatched+=2;addKidsStars(20);
        if(memoMatched===memoCards.length){speak('Amazing! You matched all the cards! You are a memory champion!',0.85);showPopup('🎉','¡Ganaste!','¡Completaste el Memotest! +20 pts');}
        else speak('Great match!',0.9);
      }else{a.textContent='?';b.textContent='?';}
      memoFlipped=[];
    },800);
  }
}

// ─── PRONUNCIACIÓN NIÑOS ───
function nextKWord(){
  kWordIdx=(kWordIdx+1)%PRON_WORDS.length;
  var it=PRON_WORDS[kWordIdx];
  document.getElementById('kpEmi').textContent=it.e;
  document.getElementById('kpW').textContent=it.w;
  document.getElementById('kVR').innerHTML='';
}
function kListen(){speak(PRON_WORDS[kWordIdx].w,0.75);}
function kSpeak(){
  if(!('webkitSpeechRecognition' in window||'SpeechRecognition' in window)){
    document.getElementById('kVR').innerHTML='<p style="color:#ef4444">⚠️ Usá Chrome 🎤</p>';return;
  }
  var exp=PRON_WORDS[kWordIdx].w.toLowerCase();
  var SR=window.SpeechRecognition||window.webkitSpeechRecognition;
  var rec=new SR();rec.lang='en-US';rec.interimResults=false;
  var btn=document.getElementById('btnKS');
  btn.textContent='🔴 Escuchando...';btn.style.background='#ef4444';
  rec.onresult=function(e){
    var sp=e.results[0][0].transcript.toLowerCase().trim();
    var conf=e.results[0][0].confidence;
    var ok=sp.includes(exp)||conf>0.65;
    if(ok){
      document.getElementById('kVR').innerHTML='<div style="text-align:center;font-size:1.3rem;color:#10b981;font-weight:800;padding:10px">🌟 ¡PERFECTO! ¡Sos una estrella!</div>';
      addKidsStars(15);speak('Wow! That was perfect! You are a superstar! Amazing!',0.85);
      showPopup('🌟','¡Perfecto!','¡Lo dijiste perfecto! +15 pts');
    }else{
      document.getElementById('kVR').innerHTML='<div style="text-align:center;color:#f59e0b;font-weight:700;padding:8px">Dijiste: "'+sp+'"<br>¡Intentalo otra vez! 💪</div>';
      speak('Good try! Listen again and say: '+exp,0.8);
    }
    btn.textContent='🎤 ¡Lo digo yo!';btn.style.background='';
    voiceCount++;localStorage.setItem('fa_vc',voiceCount);checkBadges();
  };
  rec.onerror=function(){btn.textContent='🎤 ¡Lo digo yo!';btn.style.background='';};
  rec.start();
}

// ─── CHAT NIÑOS ───
function startKChat(){
  var msg="Hi there! I'm your English teacher! 🌟 Welcome to English class! Today we're going to have fun and learn together! Are you ready? Say: YES, I'M READY! 🎉";
  addKMsg(msg,'ai');kChatHist.push({role:'assistant',content:msg});speak(msg,0.82);
}
function sendKChat(){
  var inp=document.getElementById('kChatIn');
  var txt=inp.value.trim();if(!txt)return;
  inp.value='';addKMsg(txt,'usr');kChatHist.push({role:'user',content:txt});
  fetch('/academia/chat-kids',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({history:kChatHist.slice(-10)})})
  .then(function(r){return r.json();})
  .then(function(data){
    var reply=data.reply||'¡Muy bien! 🌟';
    addKMsg(reply,'ai');kChatHist.push({role:'assistant',content:reply});
    speak(reply.replace(/[\u{1F600}-\u{1FFFF}]/gu,'').trim(),0.82);
    addKidsStars(5);checkBadges();
  })
  .catch(function(){addKMsg('❌ Error. Intentá de nuevo.','ai');});
}
function addKMsg(txt,cls){
  var box=document.getElementById('kidsChatBox');
  var d=document.createElement('div');
  d.className='msg '+(cls==='ai'?'kid-ai':'usr');
  d.textContent=txt;box.appendChild(d);box.scrollTop=box.scrollHeight;
}

// ─── ESTRELLAS Y LOGROS ───
function addKidsStars(n){stars+=n;localStorage.setItem('fa_stars',stars);updateStars();}
function updateStars(){document.getElementById('stC').textContent=stars;}
function checkBadges(){
  BADGES.forEach(function(b){
    if(badges.indexOf(b.id)>=0)return;
    var earn=(b.pts>0&&stars>=b.pts)||(b.voiceCount&&voiceCount>=b.voiceCount);
    if(earn){
      badges.push(b.id);localStorage.setItem('fa_badges',JSON.stringify(badges));
      showPopup(b.e,b.n,'🏆 '+b.d);
      speak('Congratulations! You earned the '+b.n+' badge! You are amazing!',0.85);
    }
  });
}
function renderBadges(){
  var list=document.getElementById('bdgList');list.innerHTML='';
  BADGES.forEach(function(b){
    var locked=badges.indexOf(b.id)<0;
    list.innerHTML+='<div class="bdg" style="opacity:'+(locked?0.35:1)+'"><div class="be">'+b.e+'</div><div class="bn">'+b.n+'</div><div class="bl">'+(locked?'🔒 Bloqueado':'✅ Ganado')+'</div></div>';
  });
}

function showPopup(emi,tit,msg){
  document.getElementById('pEmi').textContent=emi;
  document.getElementById('pTit').textContent=tit;
  document.getElementById('pMsg').textContent=msg;
  var p=document.getElementById('popup');p.classList.add('show');
  setTimeout(function(){p.classList.remove('show');},2500);
}


// ──────────────────────────────────────────
// 📋 TEMARIO COMPLETO 6 NIVELES
// ──────────────────────────────────────────
const TEMARIO = [
  {nivel:"A1", titulo:"🌱 Nivel 1 — Principiante Absoluto (A1)", color:"#d1fae5", colorT:"#065f46", temas:[
    {t:"🔤 Abecedario", d:"Pronunciación de letras y deletreo. Cómo se lee cada letra en inglés."},
    {t:"👋 Presentaciones", d:"Saludos, despedidas y frases de cortesía esenciales."},
    {t:"🔵 Verbo To Be", d:"Ser/Estar: I am, you are, he is — afirmación, negación y preguntas."},
    {t:"👤 Pronombres personales", d:"I, you, he, she, it, we, they — quién es quién."},
    {t:"🔢 Vocabulario inicial", d:"Números 1-100, colores, días de la semana y meses del año."},
    {t:"📌 Artículos y demostrativos", d:"a, an, the, this, that, these, those — señalar cosas."},
    {t:"⏱️ Presente Simple", d:"Estructura básica y la regla de la tercera persona (-s/-es)."},
    {t:"❓ Preguntas básicas", d:"Who, What, Where, When, Why, How — las 6 preguntas clave."},
  ]},
  {nivel:"A2", titulo:"📗 Nivel 2 — Principiante Intermedio (A2)", color:"#dbeafe", colorT:"#1e40af", temas:[
    {t:"⏰ Rutinas diarias", d:"Adverbios de frecuencia: always, sometimes, usually, never."},
    {t:"🔄 Presente Continuo", d:"Acciones que ocurren ahora mismo: I am working, she is eating."},
    {t:"📍 Preposiciones", d:"In, on, at para tiempo y lugar — cuándo y dónde."},
    {t:"📅 Pasado Simple", d:"Verbos regulares (-ed) e irregulares: go→went, see→saw."},
    {t:"⏪ Pasado Continuo", d:"Acciones que estaban pasando cuando algo las interrumpió."},
    {t:"🔮 Futuro básico", d:"Planes (be going to) vs decisiones espontáneas (will)."},
    {t:"📦 Sustantivos contables", d:"many, much, some, any, a lot of — cuánto y cuántos."},
  ]},
  {nivel:"B1", titulo:"📘 Nivel 3 — Intermedio Bajo (B1)", color:"#ede9fe", colorT:"#4c1d95", temas:[
    {t:"✅ Presente Perfecto", d:"Acciones pasadas relevantes hoy: ever, never, already, yet, since, for."},
    {t:"📊 Comparativos y superlativos", d:"Bigger, the biggest — comparar cosas y personas."},
    {t:"🎯 Verbos modales I", d:"Can, could, may, must, should — habilidad, permiso, obligación."},
    {t:"📐 Condicionales 0 y 1", d:"Verdades generales y situaciones futuras reales probables."},
    {t:"➕ Gerundios e infinitivos", d:"Cuándo usar -ing (enjoying) o to (to enjoy)."},
    {t:"🔗 Pronombres relativos", d:"Who, which, that, where — conectar frases y dar más información."},
  ]},
  {nivel:"B2", titulo:"📙 Nivel 4 — Intermedio Alto (B2)", color:"#fef3c7", colorT:"#92400e", temas:[
    {t:"⬅️ Pasado Perfecto", d:"Acciones que ocurrieron antes de otro momento pasado."},
    {t:"🔭 Futuro Continuo y Perfecto", d:"Eventos en progreso o terminados en el futuro."},
    {t:"🔄 Voz Pasiva", d:"The book was written — el foco está en el objeto, no en quien actúa."},
    {t:"💭 Condicionales 2 y 3", d:"Hipotéticos del presente y arrepentimientos del pasado."},
    {t:"🧩 Verbos modales II", d:"Must have, might have, can't be — deducción y especulación."},
    {t:"🔧 Phrasal Verbs", d:"Get up, look for, turn off — verbos compuestos del día a día."},
  ]},
  {nivel:"C1", titulo:"🚀 Nivel 5 — Avanzado Operativo (C1)", color:"#fee2e2", colorT:"#7f1d1d", temas:[
    {t:"🔃 Inversión gramatical", d:"Estructuras formales para énfasis: Seldom have I seen..."},
    {t:"💬 Estilo Indirecto Avanzado", d:"Reported Speech: órdenes, sugerencias y peticiones."},
    {t:"🌀 Condicionales mixtos", d:"Condiciones pasadas con consecuencias presentes (y viceversa)."},
    {t:"📢 Voz Pasiva Avanzada", d:"It is said that... — verbos de opinión en voz pasiva."},
    {t:"🔀 Conectores discursivos", d:"Nevertheless, furthermore, whereas — conectar ideas complejas."},
    {t:"✂️ Cleft Sentences", d:"What I need is... — oraciones hendidas para enfatizar ideas."},
  ]},
  {nivel:"C2", titulo:"🎓 Nivel 6 — Maestría y Fluidez Nativa (C2)", color:"#f0fdf4", colorT:"#14532d", temas:[
    {t:"🗣️ Idioms y Modismos", d:"Expresiones culturales y lenguaje metafórico avanzado."},
    {t:"🎯 Verbos modales complejos", d:"Should have, needn't have — matices de probabilidad y pasado."},
    {t:"📜 Subjuntivo en inglés", d:"I insist that he be present — deseos formales e importancia."},
    {t:"📚 Matices de vocabulario", d:"Sinónimos exactos para registro literario, legal y académico."},
    {t:"✂️ Estructuras elípticas", d:"Omisión de palabras obvias para mayor fluidez nativa."},
    {t:"🎵 Reducción y acento", d:"Comprensión de la entonación y el inglés conectado conversacional."},
  ]},
];

function buildTemario(){
  var el=document.getElementById('temarioList');
  if(!el)return;
  el.innerHTML='';
  TEMARIO.forEach(function(niv){
    var sec=document.createElement('div');
    sec.style.cssText='margin-bottom:14px;border-radius:12px;overflow:hidden;border:2px solid '+niv.color;
    var hdr=document.createElement('div');
    hdr.style.cssText='background:'+niv.color+';padding:12px 16px;cursor:pointer;display:flex;justify-content:space-between;align-items:center';
    hdr.innerHTML='<span style="font-weight:800;color:'+niv.colorT+';font-size:.95rem">'+niv.titulo+'</span>'
      +'<div style="display:flex;gap:8px;align-items:center">'
      +'<button onclick="speakTemario(\''+niv.nivel+'\',event)" style="background:rgba(0,0,0,.1);border:none;border-radius:20px;padding:4px 10px;font-size:.75rem;font-weight:700;cursor:pointer;color:'+niv.colorT+'">🔊 Escuchar</button>'
      +'<span style="color:'+niv.colorT+'">▼</span></div>';
    var body=document.createElement('div');
    body.style.cssText='display:none;padding:12px 16px;background:#fff';
    body.id='temBody_'+niv.nivel;
    niv.temas.forEach(function(t){
      body.innerHTML+='<div style="padding:8px 0;border-bottom:1px solid #f3f4f6">'
        +'<div style="font-weight:700;color:#4c1d95;font-size:.88rem">'+t.t+'</div>'
        +'<div style="color:#6b7280;font-size:.82rem;margin-top:2px">'+t.d+'</div>'
        +'</div>';
    });
    body.innerHTML+='<button class="btn" style="margin-top:10px;width:100%;font-size:.82rem" onclick="practicarNivel(\''+niv.nivel+'\')">💬 Practicar este nivel ahora</button>';
    hdr.onclick=function(e){
      if(e.target.tagName==='BUTTON')return;
      var vis=body.style.display==='block';body.style.display=vis?'none':'block';
      hdr.querySelector('span:last-child').textContent=vis?'▼':'▲';
    };
    sec.appendChild(hdr);sec.appendChild(body);el.appendChild(sec);
  });
}

function speakTemario(nivel,e){
  e.stopPropagation();
  var niv=TEMARIO.find(function(n){return n.nivel===nivel;});
  if(!niv)return;
  var txt='Nivel '+niv.nivel+'. '+niv.titulo.replace(/[🌱📗📘📙🚀🎓]/g,'')+'. Los temas de este nivel son: ';
  txt+=niv.temas.map(function(t){return t.t.replace(/[🔤👋🔵👤🔢📌⏱️❓⏰🔄📍📅⏪🔮📦✅📊🎯📐➕🔗⬅️🔭🔄💭🧩🔧🔃💬🌀📢🔀✂️🗣️🎯📜📚✂️🎵]/g,'').trim();}).join(', ');
  speak(txt, 0.8, 'es-AR');
}

function practicarNivel(nivel){
  var mapa={A1:1,A2:1,B1:2,B2:2,C1:3,C2:3};
  var n=mapa[nivel]||1;
  // Cambiar al tab de conversación con ese nivel
  document.querySelectorAll('#mAdult .nlvl').forEach(function(x){x.classList.remove('on');});
  var nl=document.getElementById('nl'+n);if(nl)nl.classList.add('on');
  nivelAlumno=n;
  // Activar tab conversación
  var convTab=document.querySelector('#mAdult .tab');
  aTab('conv',convTab);
  convTab.classList.add('on');
}

// ──────────────────────────────────────────
// 🗣️ PRÁCTICA ORAL GUIADA
// ──────────────────────────────────────────
var oralTopic='presentacion';
var oralNivel=1;
var oralHist=[];
var micOralActive=false;

function setOralNivel(el,n){
  document.querySelectorAll('#t-oral .nlvl').forEach(function(x){x.classList.remove('on');});
  el.classList.add('on');oralNivel=n;
  oralHist=[];document.getElementById('oralBox').innerHTML='';
  startOral();
}
function setOralTopic(el,t){
  document.querySelectorAll('#oralTopics .chip').forEach(function(c){c.classList.remove('on');});
  el.classList.add('on');oralTopic=t;oralHist=[];
  document.getElementById('oralBox').innerHTML='';
  startOral();
}
function startOral(){
  var preguntas={
    presentacion:{1:"¡Hola! Soy tu profe. Empecemos. En inglés, ¿cómo decís 'Me llamo...'? — In English: Can you say your name? 😊",2:"Hello! Let's practice introductions. Tell me your name, where you're from, and what you do.",3:"Hello! Let's start with a full self-introduction — name, background, profession and one interesting fact about yourself."},
    rutina:{1:"Bien. Hablemos de tu día. ¿Qué hacés todos los días por la mañana? — In English: What do you do every morning?",2:"Let's talk about your daily routine! What time do you usually wake up and what's the first thing you do?",3:"Describe your typical weekday from morning to night. Use a variety of time expressions."},
    familia:{1:"Genial. Tu familia. ¿Cuántas personas hay en tu familia? — In English: How many people are in your family?",2:"Tell me about your family — how many people, names, and what they do.",3:"Describe your family dynamics — who you're closest to and why."},
    trabajo:{1:"Hablemos del trabajo. ¿A qué te dedicás? — In English: What do you do for work?",2:"Tell me about your job. What do you do, where do you work, and do you like it?",3:"Describe your professional background, your current role, and your career goals."},
    viaje:{1:"¡Viajes! ¿Fuiste a algún lugar interesante? — In English: Have you been anywhere interesting?",2:"Tell me about a trip you took. Where did you go, when, and what did you do?",3:"Describe the most memorable trip you've ever taken and explain what made it special."},
    libre:{1:"Genial, conversación libre. Contame algo sobre vos en inglés. ¡Yo te ayudo! — Something about yourself in English 😊",2:"Let's just talk! Tell me something interesting that happened to you recently.",3:"Let's have a free conversation. Start with any topic you find interesting."},
  };
  var msg=preguntas[oralTopic]?preguntas[oralTopic][oralNivel]||preguntas[oralTopic][1]:"Let's practice! Tell me something in English.";
  addOralMsg(msg,'ai');
  oralHist.push({role:'assistant',content:msg});
  // En nivel básico: hablar primero en español
  if(oralNivel===1){
    var esMsg=msg.split('—')[0].trim();
    speak(esMsg,0.82,'es-AR');
    setTimeout(function(){
      var enMsg=msg.includes('—')?msg.split('—')[1].trim():msg;
      speak(enMsg,0.82,'en-US');
    },2200);
  } else {
    speak(msg,0.85,'en-US');
  }
}

function sendOral(){
  var inp=document.getElementById('oralIn');
  var txt=inp.value.trim();if(!txt)return;
  inp.value='';
  addOralMsg(txt,'usr');
  oralHist.push({role:'user',content:txt});
  var btn=document.querySelector('#t-oral .btn.grn');
  if(btn){btn.disabled=true;btn.innerHTML='<span class="spin"></span>...';}
  fetch('/academia/chat',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({history:oralHist.slice(-10),topic:oralTopic,nivel:oralNivel,error_memory:''})})
  .then(function(r){return r.json();})
  .then(function(data){
    var reply=data.reply||'Good! Keep going!';
    addOralMsg(reply,'ai');
    oralHist.push({role:'assistant',content:reply});
    if(data.correction)addOralMsg(data.correction,'corr');
    if(data.repeat_target){
      addOralMsg('🔁 Decilo en voz alta: 👉 '+data.repeat_target,'repeat-req');
      if(oralNivel===1){
        speak('Repetí en voz alta: ',0.82,'es-AR');
        setTimeout(function(){speak(data.repeat_target,0.82,'en-US');},1500);
      } else {
        speak('Please say out loud: '+data.repeat_target,0.82,'en-US');
      }
    } else {
      var toSpeak=reply.replace(/\[✅[^\]]+\]/g,'').split('[')[0].trim();
      if(oralNivel===1 && reply.includes('[')){
        var espart=reply.match(/\[([^\]]+)\]/);
        if(espart)speak(espart[1],0.82,'es-AR');
        setTimeout(function(){speak(toSpeak,0.82,'en-US');},1800);
      } else {
        speak(toSpeak,0.82,'en-US');
      }
    }
    if(btn){btn.disabled=false;btn.textContent='Responder';}
  })
  .catch(function(){
    addOralMsg('❌ Error. Intentá de nuevo.','ai');
    if(btn){btn.disabled=false;btn.textContent='Responder';}
  });
}

function addOralMsg(txt,cls){
  var box=document.getElementById('oralBox');
  var d=document.createElement('div');d.className='msg '+cls;
  d.innerHTML=txt.replace(/\*\*(.*?)\*\*/g,'<strong>$1</strong>').replace(/\n/g,'<br>');
  box.appendChild(d);box.scrollTop=box.scrollHeight;
}

function toggleMicOral(){
  if(!('webkitSpeechRecognition' in window||'SpeechRecognition' in window)){
    document.getElementById('oralMicHint').textContent='⚠️ Usá Chrome para hablar 🎤';return;
  }
  if(micOralActive){
    micOralActive=false;setBtnMic('btnMicOral',false);
    if(micRecognizer){try{micRecognizer.stop();}catch(e){}}
    return;
  }
  micOralActive=true;setBtnMic('btnMicOral',true);
  document.getElementById('oralMicHint').textContent='🔴 Escuchando... ¡hablá en inglés!';
  micRecognizer=createRecognizer('en-US',function(txt){
    document.getElementById('oralIn').value=txt;
    micOralActive=false;setBtnMic('btnMicOral',false);
    document.getElementById('oralMicHint').textContent='✅ Escuché: "'+txt+'"';
    setTimeout(sendOral,400);
  },function(){
    micOralActive=false;setBtnMic('btnMicOral',false);
    document.getElementById('oralMicHint').textContent='Presioná 🎤 para responder hablando';
  });
  try{micRecognizer.start();}catch(e){micOralActive=false;setBtnMic('btnMicOral',false);}
}

// ──────────────────────────────────────────
// 🎤 MICRÓFONO FLOTANTE (siempre visible)
// ──────────────────────────────────────────
var floatMicActive=false;
function activateFloatMic(){
  if(!('webkitSpeechRecognition' in window||'SpeechRecognition' in window)){
    alert('Tu navegador no soporta micrófono. Usá Google Chrome.');return;
  }
  if(floatMicActive){
    floatMicActive=false;
    if(micRecognizer){try{micRecognizer.stop();}catch(e){}}
    document.getElementById('floatMicBtn').style.background='#10b981';
    document.getElementById('floatMicBtn').textContent='🎤';
    return;
  }
  floatMicActive=true;
  document.getElementById('floatMicBtn').style.background='#ef4444';
  document.getElementById('floatMicBtn').textContent='🔴';
  // Detectar qué sección está activa y enviar ahí
  var activeTab=document.querySelector('#mAdult .sec.on');
  var tabId=activeTab?activeTab.id:'t-conv';
  micRecognizer=createRecognizer('en-US',function(txt){
    floatMicActive=false;
    document.getElementById('floatMicBtn').style.background='#10b981';
    document.getElementById('floatMicBtn').textContent='🎤';
    // Mandar al input correcto según el tab activo
    if(tabId==='t-oral'){
      document.getElementById('oralIn').value=txt;sendOral();
    } else if(tabId==='t-situaciones'){
      document.getElementById('sitIn').value=txt;sendSit();
    } else {
      document.getElementById('chatIn').value=txt;sendChat();
    }
  },function(){
    floatMicActive=false;
    document.getElementById('floatMicBtn').style.background='#10b981';
    document.getElementById('floatMicBtn').textContent='🎤';
  });
  try{micRecognizer.start();}catch(e){floatMicActive=false;}
}

// ──────────────────────────────────────────
// 🤖 FOSCHI IA — CHAT DENTRO DE LA ACADEMIA
// ──────────────────────────────────────────
var foschiOpen=false;
var foschiBienvenida=false;
var micFoschiActive=false;

function toggleFoschiPanel(){
  foschiOpen=!foschiOpen;
  document.getElementById('foschiPanel').style.display=foschiOpen?'flex':'none';
  if(foschiOpen && !foschiBienvenida){
    foschiBienvenida=true;
    addFoschiMsg('ai','¡Hola! Soy <strong>Foschi IA</strong> 🤖<br>Podés preguntarme cualquier cosa — no solo inglés. Clima, noticias, ayuda con documentos, lo que necesites.<br><small style="opacity:.6">También podés ir a la app completa ↗️</small>');
  }
}

function sendFoschi(){
  var inp=document.getElementById('foschiIn');
  var txt=inp.value.trim();if(!txt)return;
  inp.value='';
  addFoschiMsg('usr',txt);
  var box=document.getElementById('foschiChatBox');
  var loading=document.createElement('div');
  loading.id='foschiLoading';
  loading.style.cssText='color:#00ff8866;font-size:.78rem;padding:4px 8px';
  loading.textContent='⏳ Pensando...';
  box.appendChild(loading);box.scrollTop=box.scrollHeight;

  fetch('/academia/foschi-chat',{
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify({mensaje:txt})
  })
  .then(function(r){return r.json();})
  .then(function(data){
    var el=document.getElementById('foschiLoading');if(el)el.remove();
    var reply=data.texto||data.reply||'No pude responder. Intentá de nuevo.';
    addFoschiMsg('ai',reply.replace(/\n/g,'<br>'));
  })
  .catch(function(){
    var el=document.getElementById('foschiLoading');if(el)el.remove();
    addFoschiMsg('ai','❌ Error de conexión. Verificá que Foschi IA esté activa.');
  });
}

function addFoschiMsg(cls,html){
  var box=document.getElementById('foschiChatBox');
  var d=document.createElement('div');
  var isAI=cls==='ai';
  d.style.cssText='max-width:90%;padding:8px 11px;border-radius:12px;font-size:.79rem;line-height:1.5;'
    +(isAI?'background:#001a00;border:1px solid #00ff8822;color:#b0ffb0;align-self:flex-start'
           :'background:#003300;color:#00ff88;align-self:flex-end;margin-left:auto');
  d.innerHTML=html;
  box.appendChild(d);box.scrollTop=box.scrollHeight;
}

function toggleMicFoschi(){
  if(!('webkitSpeechRecognition' in window||'SpeechRecognition' in window))return;
  if(micFoschiActive){
    micFoschiActive=false;
    document.getElementById('btnMicFoschi').textContent='🎤';
    document.getElementById('btnMicFoschi').style.color='#00ff88';
    if(micRecognizer){try{micRecognizer.stop();}catch(e){}}
    return;
  }
  micFoschiActive=true;
  document.getElementById('btnMicFoschi').textContent='🔴';
  document.getElementById('btnMicFoschi').style.color='#ef4444';
  micRecognizer=createRecognizer('es-AR',function(txt){
    document.getElementById('foschiIn').value=txt;
    micFoschiActive=false;
    document.getElementById('btnMicFoschi').textContent='🎤';
    document.getElementById('btnMicFoschi').style.color='#00ff88';
    setTimeout(sendFoschi,400);
  },function(){
    micFoschiActive=false;
    document.getElementById('btnMicFoschi').textContent='🎤';
    document.getElementById('btnMicFoschi').style.color='#00ff88';
  });
  try{micRecognizer.start();}catch(e){micFoschiActive=false;}
}

// ─── PANEL PREGUNTÁ AL PROFE ───
var micAskActive=false;
var askHist=[];

function toggleAskPanel(){
  var p=document.getElementById('askTeacherPanel');
  var vis=p.style.display==='block';
  p.style.display=vis?'none':'block';
  if(!vis && askHist.length===0){
    var bienvenida='¡Hola! Podés preguntarme cualquier cosa sobre inglés — gramática, vocabulario, pronunciación, lo que quieras. ¡Hablar también! 🎤';
    addAskMsg(bienvenida,'ai');
    speak(bienvenida,0.82,'es-AR');
  }
}

function sendAsk(){
  var inp=document.getElementById('askIn');
  var txt=inp.value.trim();if(!txt)return;
  inp.value='';
  addAskMsg(txt,'usr');
  askHist.push({role:'user',content:txt});
  fetch('/academia/preguntar',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({pregunta:txt,nivel:nivelAlumno})})
  .then(function(r){return r.json();})
  .then(function(data){
    var reply=data.reply||'¡Buena pregunta!';
    addAskMsg(reply,'ai');
    askHist.push({role:'assistant',content:reply});
    speak(reply.split('\n')[0],0.82,'es-AR');
  })
  .catch(function(){addAskMsg('❌ Error. Intentá de nuevo.','ai');});
}

function addAskMsg(txt,cls){
  var box=document.getElementById('askBox');
  var d=document.createElement('div');
  d.style.cssText='max-width:92%;padding:7px 10px;border-radius:10px;font-size:.78rem;line-height:1.4;'+(cls==='ai'?'background:#f0f4ff;align-self:flex-start;border:1px solid #d1c4e9':'background:#6c3fc5;color:#fff;align-self:flex-end;margin-left:auto');
  d.textContent=txt;
  box.appendChild(d);box.scrollTop=box.scrollHeight;
}

function toggleMicAsk(){
  if(!('webkitSpeechRecognition' in window||'SpeechRecognition' in window))return;
  if(micAskActive){
    micAskActive=false;setBtnMic('btnMicAsk',false);
    if(micRecognizer){try{micRecognizer.stop();}catch(e){}}
    return;
  }
  micAskActive=true;setBtnMic('btnMicAsk',true);
  micRecognizer=createRecognizer('es-AR',function(txt){
    document.getElementById('askIn').value=txt;
    micAskActive=false;setBtnMic('btnMicAsk',false);
    setTimeout(sendAsk,400);
  },function(){micAskActive=false;setBtnMic('btnMicAsk',false);});
  try{micRecognizer.start();}catch(e){micAskActive=false;setBtnMic('btnMicAsk',false);}
}


var _origATab=aTab;
function aTab(n,el){
  document.querySelectorAll('#mAdult .sec').forEach(function(s){s.classList.remove('on');});
  document.getElementById('t-'+n).classList.add('on');
  document.querySelectorAll('#mAdult .tab').forEach(function(t){t.classList.remove('on');});
  el.classList.add('on');
  if(n==='prog')loadProg();
  if(n==='lecciones')loadLesson();
  if(n==='situaciones'){setSit(document.querySelector('.sit-chip.on')||document.querySelector('.sit-chip'),'restaurant',true);}
  if(n==='temario')buildTemario();
  if(n==='oral'){oralHist=[];document.getElementById('oralBox').innerHTML='';startOral();}
}


  updateStars();startChat();nextPron();loadProg();loadLesson();updateErrorMemUI();
};
</script>
</body>
</html>
"""

# ──────────────────────────────────────────────
#  PROMPTS DE SISTEMA
# ──────────────────────────────────────────────

SYSTEM_ADULT = """Sos el Profesor de Inglés de la Academia Foschi IA.
Tu filosofía: si el alumno no aprende, es responsabilidad del docente, no del alumno.

NIVEL DEL ALUMNO: {nivel}
(1=Básico: explicá TODA regla gramatical en ESPAÑOL claro entre [corchetes]. Usá frases muy cortas. Invitá SIEMPRE a responder con el micrófono.
 2=Intermedio: solo los errores los explicás en español. El resto en inglés.
 3=Avanzado: todo en inglés.)

ERRORES FRECUENTES DE ESTE ALUMNO: {error_memory}
(Si hay errores listados, prestalés atención especial y no avancés hasta que los supere.)

REGLAS ESTRICTAS:
1. Respondés en inglés. En nivel 1, SIEMPRE agregás traducción/explicación en español entre [corchetes] al final.
2. En nivel 1, SIEMPRE terminás tu respuesta invitando a hablar: "[🎤 Ahora respondé vos — podés usar el micrófono!]"
3. Si hay un error gramatical, lo corregís y ponés: [✅ Corrección: decimos "..." no "..." — REGLA en español: ...]
4. Si hay un error, OBLIGATORIAMENTE emitís: REPEAT_TARGET:"<frase correcta completa>"
   Ej: REPEAT_TARGET:"I went to work yesterday."
   Esto hace que el alumno deba repetir esa frase (hablando o escribiendo) antes de continuar.
5. Si hay error, también emitís: ERROR_TYPE:<categoría>
   Categorías: past_simple, present_simple, articles, to_be, pronouns, spelling, word_order, vocabulary, plural
6. Si no hay error, NO emitís REPEAT_TARGET ni ERROR_TYPE.
7. Hacés UNA pregunta de seguimiento para continuar la práctica. NUNCA dos preguntas.
8. Sos MUY paciente y motivador. Celebrás el esfuerzo siempre.
9. Si escribe en español, respondés en inglés y le pedís amablemente que lo intente en inglés.
10. Al final de tu respuesta escribí exactamente: SCORE:{"score":85}
    (número 0-100 según el dominio demostrado por el alumno)
11. En nivel 1, preferís preguntas ORALES simples que el alumno pueda responder hablando.

Tema actual: {topic}"""

SYSTEM_KIDS = """Sos el Profesor de Inglés para niños de la Academia Foschi IA.
REGLAS FUNDAMENTALES:
1. Usás palabras MUY simples y frases CORTAS (máximo 3 frases por respuesta).
2. Siempre usás emojis para hacer la clase divertida 🎉🌟😊.
3. PRIMERO celebrás al niño, aunque se equivoque: "¡Muy bien por intentarlo! 🌟"
4. Si escribe en español, respondés en español Y enseñás la palabra en inglés.
5. Enseñás UNA cosa por vez, muy despacio, con ejemplos simples.
6. Hacés preguntas muy fáciles: colores, animales, números, frutas.
7. Sos como un amigo mayor que ama enseñar, no un profesor serio.
8. Terminás siempre con una frase de aliento."""

SYSTEM_CORRECTOR = """Sos un corrector experto de inglés de la Academia Foschi IA.
Tu tarea:
1. Analizás el texto recibido con atención.
2. Mostrás el texto CORREGIDO completo.
3. Explicás CADA error en español, de forma didáctica: indicás qué estaba mal, cuál es la regla gramatical y cómo se dice correctamente.
4. Terminás con motivación y un consejo práctico para no repetir los errores.
5. Al final escribís exactamente en una línea: SCORE:{"score":85,"has_errors":true}
   donde score = 0-100 (100 = texto perfecto) y has_errors = true/false.
6. Si hay un tipo de error dominante, indicalo con: ERROR_TYPE:<categoría>
   Categorías: past_simple, present_simple, articles, to_be, pronouns, spelling, word_order, vocabulary, plural"""

SYSTEM_SITUATION = """Sos un personaje en una simulación de conversación en inglés real.
Tu rol: {role}
Situación: {situation}

REGLAS:
1. Actuás COMPLETAMENTE como el personaje — no sos un profesor, sos el personaje.
2. Respondés de forma natural y realista, como en una situación real.
3. Después de tu respuesta como personaje, añadís una línea separada en español con corrección si hubo error:
   [✅ Corrección: decimos "..." no "..." — REGLA: ...]
4. Si el alumno cometió un error, añadís: REPEAT_TARGET:"<frase correcta>"
5. Si no hay error, añadís solo: SCORE:{"score":90}
6. En nivel {nivel} (1=básico), SIEMPRE añadís traducción al español de lo que dijiste: [🇪🇸 Español: ...]
7. En nivel 1, terminás con: [🎤 Respondé con el micrófono!] para animarlos a hablar.
8. Mantené la conversación realista: pedís lo que un {role} real pediría."""


# ──────────────────────────────────────────────
#  FUNCIÓN DE INICIALIZACIÓN DE RUTAS
# ──────────────────────────────────────────────
def init_academia_ingles(app):
    """
    Registra las rutas de la Academia de Inglés Foschi IA en la app Flask.
    Usa la API de Anthropic (claude-sonnet-4-6).

    Requiere:
        pip install anthropic flask
        Variable de entorno: ANTHROPIC_API_KEY
    """
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    except ImportError:
        raise RuntimeError("Instalá anthropic: pip install anthropic")

    MODEL = "claude-sonnet-4-6"
    MAX_TOKENS = 1000

    def call_claude(system_prompt, messages, max_tokens=MAX_TOKENS):
        """Llamada centralizada a la API de Anthropic."""
        response = client.messages.create(
            model=MODEL,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=messages,
        )
        return response.content[0].text if response.content else ""

    @app.route("/ingles")
    @app.route("/academia")
    def academia_view():
        return render_template_string(ACADEMIA_HTML)

    @app.route("/academia/chat", methods=["POST"])
    def academia_chat():
        data = request.get_json(force=True)
        history = data.get("history", [])
        topic = data.get("topic", "free")
        nivel = data.get("nivel", 1)
        error_memory = data.get("error_memory", "")

        system = (SYSTEM_ADULT
                  .replace("{topic}", topic)
                  .replace("{nivel}", str(nivel))
                  .replace("{error_memory}", error_memory or "ninguno"))

        messages = [{"role": m["role"], "content": m["content"]} for m in history[-12:]]

        try:
            full = call_claude(system, messages)

            score_val = 70
            correction = None
            repeat_target = None
            error_type = None
            reply_text = full

            # Extraer SCORE
            score_match = re.search(r'SCORE:\{"score":(\d+)\}', full)
            if score_match:
                score_val = int(score_match.group(1))
                reply_text = full[:score_match.start()].strip()

            # Extraer REPEAT_TARGET
            repeat_match = re.search(r'REPEAT_TARGET:"([^"]+)"', reply_text)
            if repeat_match:
                repeat_target = repeat_match.group(1)
                reply_text = reply_text[:repeat_match.start()].strip()

            # Extraer ERROR_TYPE
            error_match = re.search(r'ERROR_TYPE:(\w+)', reply_text)
            if error_match:
                error_type = error_match.group(1)
                reply_text = reply_text[:error_match.start()].strip()

            # Extraer corrección inline
            corr_match = re.search(r'\[✅[^\]]+\]', reply_text)
            if corr_match:
                correction = corr_match.group(0)

            return jsonify({
                "reply": reply_text,
                "correction": correction,
                "score": score_val,
                "repeat_target": repeat_target,
                "error_type": error_type,
            })

        except Exception as e:
            return jsonify({"error": str(e), "reply": "Lo siento, hubo un error. Intentá de nuevo."}), 500

    @app.route("/academia/chat-sit", methods=["POST"])
    def academia_chat_sit():
        """Endpoint para conversaciones por situación."""
        data = request.get_json(force=True)
        history = data.get("history", [])
        situation = data.get("situation", "restaurant")
        nivel = data.get("nivel", 1)

        sit_roles = {
            "restaurant": "Waiter/Waitress at an Italian restaurant",
            "airport": "Check-in Agent at an international airport",
            "hotel": "Hotel Receptionist at a 4-star hotel",
            "doctor": "Doctor at a medical clinic",
            "interview": "HR Manager conducting a job interview",
            "police": "Police Officer on a routine stop",
            "pharmacy": "Pharmacist at a local pharmacy",
            "bank": "Bank Teller at City Bank",
        }
        role = sit_roles.get(situation, "Staff member")

        system = (SYSTEM_SITUATION
                  .replace("{role}", role)
                  .replace("{situation}", situation)
                  .replace("{nivel}", str(nivel)))

        messages = [{"role": m["role"], "content": m["content"]} for m in history[-14:]]

        try:
            full = call_claude(system, messages)

            score_val = 80
            correction = None
            repeat_target = None
            reply_text = full

            score_match = re.search(r'SCORE:\{"score":(\d+)\}', full)
            if score_match:
                score_val = int(score_match.group(1))
                reply_text = full[:score_match.start()].strip()

            repeat_match = re.search(r'REPEAT_TARGET:"([^"]+)"', reply_text)
            if repeat_match:
                repeat_target = repeat_match.group(1)
                reply_text = reply_text[:repeat_match.start()].strip()

            corr_match = re.search(r'\[✅[^\]]+\]', reply_text)
            if corr_match:
                correction = corr_match.group(0)

            return jsonify({
                "reply": reply_text,
                "correction": correction,
                "score": score_val,
                "repeat_target": repeat_target,
            })

        except Exception as e:
            return jsonify({"error": str(e), "reply": "Error. Try again."}), 500

    @app.route("/academia/chat-kids", methods=["POST"])
    def academia_chat_kids():
        data = request.get_json(force=True)
        history = data.get("history", [])
        messages = [{"role": m["role"], "content": m["content"]} for m in history[-10:]]

        try:
            reply = call_claude(SYSTEM_KIDS, messages, max_tokens=400)
            return jsonify({"reply": reply or "¡Muy bien! 🌟 Keep going!"})

        except Exception as e:
            return jsonify({"error": str(e), "reply": "❌ Error. Intentá de nuevo."}), 500

    @app.route("/academia/foschi-chat", methods=["POST"])
    def academia_foschi_chat():
        """
        Proxy: recibe consultas desde la Academia y las reenvía al endpoint
        principal /preguntar de Foschi IA, usando la sesión activa del usuario.
        Si por algún motivo no puede conectarse, responde con Claude directamente.
        """
        import requests as req_lib
        data = request.get_json(force=True)
        mensaje = data.get("mensaje", "").strip()
        if not mensaje:
            return jsonify({"texto": "¿Qué querés consultarme?"})

        # Intentar llamar al /preguntar interno de Foschi IA
        try:
            # Llamada interna a la misma app Flask (mismo proceso)
            with app.test_client() as c:
                # Pasar las cookies de sesión para mantener identidad del usuario
                resp = c.post(
                    "/preguntar",
                    json={"mensaje": mensaje},
                    headers={"Content-Type": "application/json"}
                )
                if resp.status_code == 200:
                    return jsonify(resp.get_json())
        except Exception:
            pass

        # Fallback: Claude responde como Foschi IA si el proxy falla
        try:
            SYSTEM_FOSCHI = """Sos FOSCHI IA, una inteligencia amable, directa y con humor ligero.
Sos el asistente general de la plataforma educativa de Gustavo Foschi.
Respondé de forma clara y natural en español argentino.
El usuario te escribe desde la Academia de Inglés — podés ayudar con cualquier consulta,
no solo inglés. Sé conciso (máximo 150 palabras)."""
            full = call_claude(
                SYSTEM_FOSCHI,
                [{"role": "user", "content": mensaje}],
                max_tokens=600
            )
            return jsonify({"texto": full or "¡Preguntame lo que necesites!"})
        except Exception as e:
            return jsonify({"texto": f"Error al conectar con Foschi IA: {e}"}), 500


    def academia_preguntar():
        """Endpoint para preguntas libres del alumno en cualquier momento."""
        data = request.get_json(force=True)
        pregunta = data.get("pregunta", "").strip()
        nivel = data.get("nivel", 1)
        if not pregunta:
            return jsonify({"reply": "¿Cuál es tu pregunta? Escribila o usá el micrófono."})

        system = """Sos el Profesor de Inglés de la Academia Foschi IA.
El alumno tiene una pregunta libre sobre inglés. Respondé de forma clara y didáctica.
NIVEL: {nivel}
En nivel 1: respondé SIEMPRE en español primero, luego dá el ejemplo en inglés.
En nivel 2: mezcl español e inglés.
En nivel 3: respondé en inglés con algún ejemplo.
Sé conciso, práctico y usa ejemplos reales. No más de 150 palabras.""".replace("{nivel}", str(nivel))

        try:
            reply = call_claude(system, [{"role": "user", "content": pregunta}], max_tokens=600)
            return jsonify({"reply": reply or "¡Buena pregunta! Intentalo de nuevo."})
        except Exception as e:
            return jsonify({"reply": f"Error: {str(e)}"}), 500


    def academia_correct():
        data = request.get_json(force=True)
        text = data.get("text", "").strip()
        if not text:
            return jsonify({"result": "No enviaste texto.", "score": 0, "has_errors": False})

        try:
            full = call_claude(
                SYSTEM_CORRECTOR,
                [{"role": "user", "content": text}],
                max_tokens=MAX_TOKENS
            )

            score_val = 70
            has_errors = True
            error_type = None

            score_match = re.search(r'SCORE:\{"score":(\d+),"has_errors":(true|false)\}', full)
            if score_match:
                score_val = int(score_match.group(1))
                has_errors = score_match.group(2) == "true"
                full = full[:score_match.start()].strip()

            error_match = re.search(r'ERROR_TYPE:(\w+)', full)
            if error_match:
                error_type = error_match.group(1)
                full = full[:error_match.start()].strip()

            return jsonify({
                "result": full,
                "score": score_val,
                "has_errors": has_errors,
                "error_type": error_type,
            })

        except Exception as e:
            return jsonify({"result": f"Error: {str(e)}", "score": 0, "has_errors": True}), 500