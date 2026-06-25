#!/usr/bin/env python3
# coding: utf-8
"""
academia_ingles.py — Academia de Inglés Foschi IA
Integra modo Adultos y modo Niños con IA Anthropic, pronunciación,
juegos, lecciones desde cero y seguimiento de progreso.
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
#chatBox,#kidsChatBox{height:280px;overflow-y:auto;background:#f5f3ff;border-radius:10px;padding:12px;display:flex;flex-direction:column;gap:8px;margin-bottom:10px}
#kidsChatBox{background:#fff7ed}
.msg{max-width:82%;padding:9px 13px;border-radius:10px;line-height:1.5;font-size:.88rem}
.msg.ai{background:#fff;border:1.5px solid #e0d6fa;align-self:flex-start;color:#2d1b69}
.msg.usr{background:var(--pur);color:#fff;align-self:flex-end}
.msg.corr{background:#fffbeb;border:1.5px solid #f59e0b;color:#78350f;align-self:flex-start;font-size:.82rem}
.msg.kid-ai{background:#fff3e0;border:1.5px solid #fed7aa;align-self:flex-start;color:#78350f}
.row{display:flex;gap:8px}
.row input{flex:1;padding:9px 13px;border-radius:30px;border:2px solid #d1c4e9;font-size:.9rem;outline:none;transition:border .2s;font-family:inherit}
.row input:focus{border-color:var(--pur)}
.btn{padding:9px 18px;border-radius:30px;border:none;background:var(--pur);color:#fff;font-weight:700;cursor:pointer;font-size:.85rem;transition:background .2s;white-space:nowrap}
.btn:hover{opacity:.9}.btn:disabled{opacity:.5;cursor:default}
.btn.grn{background:var(--grn)}.btn.org{background:#f59e0b;color:#fff}.btn.red{background:var(--red)}
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
@media(max-width:580px){.opts{grid-template-columns:1fr}.memo-grid{grid-template-columns:repeat(3,1fr)}.mbtn{max-width:100%;width:100%}.mode-bar{flex-direction:column;align-items:center}}
</style>
</head>
<body>

<div class="header">
  <h1>🎓 Academia Foschi IA</h1>
  <p>Aprendé inglés de verdad — desde cero hasta avanzado</p>
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
    <button class="tab" onclick="aTab('lecciones',this)">📖 Lecciones</button>
    <button class="tab" onclick="aTab('pron',this)">🎤 Pronunciación</button>
    <button class="tab" onclick="aTab('corrector',this)">✍️ Corrector</button>
    <button class="tab" onclick="aTab('prog',this)">📈 Progreso</button>
  </div>

  <div id="t-conv" class="sec on">
    <div class="card">
      <h2>💬 Conversá con tu Profe</h2>
      <div class="chips" id="topicChips">
        <div class="chip on" onclick="setTopic(this,'greetings')">👋 Saludos</div>
        <div class="chip" onclick="setTopic(this,'work')">💼 Trabajo</div>
        <div class="chip" onclick="setTopic(this,'travel')">✈️ Viajes</div>
        <div class="chip" onclick="setTopic(this,'family')">👨‍👩‍👧 Familia</div>
        <div class="chip" onclick="setTopic(this,'shopping')">🛒 Compras</div>
        <div class="chip" onclick="setTopic(this,'free')">🗣️ Libre</div>
      </div>
      <div id="chatBox"></div>
      <div class="row">
        <input id="chatIn" placeholder="Escribí en inglés..." onkeydown="if(event.key==='Enter')sendChat()"/>
        <button class="btn" onclick="sendChat()" id="btnSend">Enviar</button>
        <button class="btn grn" onclick="speakInput()" title="Pronunciar mi texto">🔊</button>
      </div>
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

  <div id="t-prog" class="sec">
    <div class="card">
      <h2>📈 Tu Progreso</h2>
      <p style="color:#6b7280;font-size:.82rem;margin-bottom:14px">Temas bajo 80% necesitan repaso.</p>
      <div id="progList"></div>
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
          <input id="kChatIn" placeholder="Escribí en inglés o español..." onkeydown="if(event.key==='Enter')sendKChat()"/>
          <button class="btn org" onclick="sendKChat()">Enviar</button>
        </div>
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

<div class="popup" id="popup">
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

let mode='adult',topic='greetings',kTopic='animals';
let chatHist=[],kChatHist=[];
let pronIdx=0,kWordIdx=0,kGIdx=0,lvl=0;
let stars=parseInt(localStorage.getItem('fa_stars')||'0');
let badges=JSON.parse(localStorage.getItem('fa_badges')||'[]');
let voiceCount=parseInt(localStorage.getItem('fa_vc')||'0');
let memoFlipped=[],memoMatched=0,memoCards=[];
let curLetter='A';
let progress=JSON.parse(localStorage.getItem('fa_prog')||JSON.stringify({
  greetings:0,work:0,travel:0,family:0,shopping:0,free:0,pronunciation:0,corrector:0
}));

function speak(text,rate,lang){
  rate=rate||0.85;lang=lang||'en-US';
  window.speechSynthesis.cancel();
  var u=new SpeechSynthesisUtterance(text);
  u.lang=lang;u.rate=rate;
  window.speechSynthesis.speak(u);
}

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

// ─── CHAT ADULTOS ───
function setTopic(el,t){
  document.querySelectorAll('#topicChips .chip').forEach(function(c){c.classList.remove('on');});
  el.classList.add('on');topic=t;chatHist=[];
  document.getElementById('chatBox').innerHTML='';startChat();
}
function startChat(){
  var greets={
    greetings:"Hello! I'm your English teacher at Academia Foschi! 😊 Today we practice greetings. Let's begin super easy: Can you say 'Hello, my name is...'? Try it!",
    work:"Welcome! Let's practice work vocabulary. Tell me: What do you do for work? Don't worry if it's not perfect — I'll help you!",
    travel:"Great! Travel English is super useful! Imagine you're at the airport. The agent asks: 'Where are you flying today?' What do you answer?",
    family:"Wonderful! Let's talk about family. Start simple: How many people are in your family? Say it in English!",
    shopping:"Let's practice shopping English! Imagine you're in a store. The clerk says: 'Can I help you?' How do you answer?",
    free:"Perfect! Let's have a free conversation. Tell me one thing about yourself in English — anything! I'll help you if you get stuck."
  };
  addMsg(greets[topic]||greets.free,'ai');
  chatHist.push({role:'assistant',content:greets[topic]||greets.free});
  speak((greets[topic]||greets.free).split('?')[0]);
}

function sendChat(){
  var inp=document.getElementById('chatIn');
  var txt=inp.value.trim();if(!txt)return;
  inp.value='';addMsg(txt,'usr');chatHist.push({role:'user',content:txt});
  var btn=document.getElementById('btnSend');
  btn.disabled=true;btn.innerHTML='<span class="spin"></span>Pensando...';
  addMsg('...','ai','loadingA');
  fetch('/academia/chat',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({history:chatHist.slice(-12),topic:topic})})
  .then(function(r){return r.json();})
  .then(function(data){
    var el=document.getElementById('loadingA');if(el)el.remove();
    if(data.reply){addMsg(data.reply,'ai');speak(data.reply.replace(/\[✅[^\]]+\]/g,'').replace(/\*\*/g,'').split('[')[0]);}
    if(data.correction)addMsg(data.correction,'corr');
    chatHist.push({role:'assistant',content:data.reply||''});
    if(data.score)updateProg(topic,data.score);
    btn.disabled=false;btn.textContent='Enviar';
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
  d.innerHTML=txt.replace(/\*\*(.*?)\*\*/g,'<strong>$1</strong>');
  box.appendChild(d);box.scrollTop=box.scrollHeight;
}
function speakInput(){var t=document.getElementById('chatIn').value.trim();if(t)speak(t);}

// ─── LECCIONES ───
var LESSONS=[
  {level:0,title:"🌱 Absoluto Cero — Primeras Palabras",content:'<div class="word-card"><div class="word-en" style="font-size:1.3rem">Bienvenido al inglés desde cero ✅</div><div class="word-es" style="margin-top:8px">Estas son las 8 palabras más importantes para comenzar</div></div><div style="display:grid;grid-template-columns:1fr 1fr;gap:8px">' +
    [['Hello','Hola'],['Goodbye','Adiós'],['Yes','Sí'],['No','No'],['Please','Por favor'],['Thank you','Gracias'],['Sorry','Perdón'],['Help','Ayuda']].map(function(x){return '<div style="background:#ede9fe;border-radius:10px;padding:10px"><div style="font-weight:800;font-size:1.1rem;color:#6c3fc5">'+x[0]+'</div><div style="color:#7c3aed;font-size:.88rem">'+x[1]+'</div></div>';}).join('') +
    '</div><button class="btn" style="margin-top:14px;width:100%" onclick="practiceWords([\'Hello\',\'Goodbye\',\'Yes\',\'No\',\'Please\',\'Thank you\',\'Sorry\',\'Help\'])">🔊 Escuchar todas</button>'},
  {level:1,title:"🔤 Básico — Presentarte",content:'<div class="word-card"><div class="word-en">My name is...</div><div class="word-es">Me llamo...</div><div class="word-ipa">/maɪ neɪm ɪz.../</div></div><div style="display:flex;flex-direction:column;gap:8px">' +
    [['My name is [nombre]','Me llamo [nombre]'],['I am [edad] years old','Tengo [edad] años'],['I am from Argentina','Soy de Argentina'],['I live in Buenos Aires','Vivo en Buenos Aires'],['Nice to meet you','Mucho gusto'],['I speak a little English','Hablo un poco de inglés']].map(function(x){return '<div style="background:#f0f4ff;border-radius:10px;padding:10px;display:flex;justify-content:space-between;align-items:center;gap:8px"><div><div style="font-weight:700;color:#4c1d95">'+x[0]+'</div><div style="color:#7c3aed;font-size:.82rem">'+x[1]+'</div></div><button class="btn" style="padding:5px 10px;font-size:.75rem" onclick="speak(\''+x[0]+'\')">🔊</button></div>';}).join('') + '</div>'},
  {level:2,title:"📘 Intermedio — Tiempos Verbales",content:'<div class="word-card"><div class="word-en">The Verb "To Be"</div><div class="word-es">El verbo Ser/Estar — el más importante</div></div><div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:14px">' +
    [['I am','Yo soy/estoy'],['You are','Vos sos/estás'],['He/She is','Él/Ella es/está'],['We are','Nosotros somos'],['They are','Ellos son/están']].map(function(x){return '<div style="background:#ede9fe;border-radius:10px;padding:10px"><div style="font-weight:800;color:#6c3fc5">'+x[0]+'</div><div style="color:#7c3aed;font-size:.82rem">'+x[1]+'</div></div>';}).join('') +
    '</div><div style="background:#f0fdf4;border-radius:10px;padding:12px;font-size:.88rem;line-height:1.8"><strong>I work</strong> → Trabajo (presente)<br><strong>I worked</strong> → Trabajé (pasado)<br><strong>I will work</strong> → Voy a trabajar (futuro)</div>'},
  {level:3,title:"🚀 Avanzado — Modales y Condicionales",content:'<div class="word-card"><div class="word-en">Modal Verbs</div><div class="word-es">Posibilidad, obligación, permiso</div></div><div style="display:flex;flex-direction:column;gap:8px;margin-bottom:14px">' +
    [['Can / Could','Puedo / Podría'],['Must / Have to','Debo / Tengo que'],['Should','Debería'],['Would','Haría / Gustaría'],['May / Might','Puedo / Podría — permiso']].map(function(x){return '<div style="background:#f0f4ff;border-radius:10px;padding:10px"><div style="font-weight:800;color:#4c1d95">'+x[0]+'</div><div style="color:#7c3aed;font-size:.82rem">'+x[1]+'</div></div>';}).join('') +
    '</div><div style="background:#fef9c3;border-radius:10px;padding:12px;font-size:.85rem;line-height:2"><strong>If I study, I will pass.</strong> → real<br><strong>If I studied, I would pass.</strong> → hipotético<br><strong>If I had studied, I would have passed.</strong> → irreal pasado</div>'}
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
  var topics={greetings:'👋 Saludos',work:'💼 Trabajo',travel:'✈️ Viajes',family:'👨‍👩‍👧 Familia',shopping:'🛒 Compras',free:'🗣️ Libre',pronunciation:'🎤 Pronunciación',corrector:'✍️ Corrector'};
  var list=document.getElementById('progList');list.innerHTML='';
  Object.keys(topics).forEach(function(k){
    var lbl=topics[k];
    var p=progress[k]||0,cls=p>=80?'pct-g':p>=50?'pct-m':'pct-l';
    var rep=p<80&&p>0?'<span class="rb">↩ Repaso</span>':'';
    var col=p>=80?'#10b981':p>=50?'#f59e0b':'#ef4444';
    list.innerHTML+='<div class="prog-item"><div class="lbl"><span style="font-size:.85rem;font-weight:600">'+lbl+rep+'</span><span class="'+cls+'">'+p+'%</span></div><div class="bar-wrap"><div class="bar" style="width:'+p+'%;background:'+col+'"></div></div></div>';
  });
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
    btn.classList.add('ok');
    addKidsStars(10);
    speak('Yes! Correct! '+cor+' means '+corEs+' in Spanish. Excellent!',0.85);
    showPopup('⭐','¡Correcto!',cor+' = '+corEs+' 🎉 +10 puntos');
    checkBadges();
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
        a.classList.add('match');b.classList.add('match');
        memoMatched+=2;addKidsStars(20);
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
function addKidsStars(n){stars+=n;localStorage.setItem('fa_stars',stars);updateStars();checkBadges();}
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

window.onload=function(){
  updateStars();startChat();nextPron();loadProg();loadLesson();
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

REGLAS ESTRICTAS:
1. Siempre respondés en inglés simple y claro.
2. Si el alumno comete un error gramatical, respondés naturalmente en inglés y DESPUÉS agregás en español entre corchetes: [✅ Corrección: en inglés decimos "..." no "..." — REGLA: ...]
3. Hacés UNA pregunta de seguimiento para continuar la práctica.
4. Sos MUY paciente y motivador. Celebrás el esfuerzo siempre.
5. Si escribe en español, respondés en inglés y le pedís amablemente que lo intente en inglés.
6. Adaptás la dificultad: si se equivoca mucho → bajás el nivel; si está bien → subís.
7. NUNCA avanzás hasta que el alumno demuestre comprensión del tema actual.
8. Siempre terminás con una frase de motivación en inglés.
9. Al final de tu respuesta escribí exactamente en una línea separada: SCORE:{"score":85}
   donde el número es 0-100 según el dominio demostrado por el alumno en este intercambio.

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
   donde score = 0-100 (100 = texto perfecto) y has_errors = true/false."""


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

        system = SYSTEM_ADULT.replace("{topic}", topic)
        messages = [{"role": m["role"], "content": m["content"]} for m in history[-12:]]

        try:
            full = call_claude(system, messages)

            score_val = 70
            correction = None
            reply_text = full

            score_match = re.search(r'SCORE:\{"score":(\d+)\}', full)
            if score_match:
                score_val = int(score_match.group(1))
                reply_text = full[:score_match.start()].strip()

            corr_match = re.search(r'\[✅[^\]]+\]', reply_text)
            if corr_match:
                correction = corr_match.group(0)

            return jsonify({
                "reply": reply_text,
                "correction": correction,
                "score": score_val
            })

        except Exception as e:
            return jsonify({"error": str(e), "reply": "Lo siento, hubo un error. Intentá de nuevo."}), 500

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

    @app.route("/academia/correct", methods=["POST"])
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
            score_match = re.search(r'SCORE:\{"score":(\d+),"has_errors":(true|false)\}', full)
            if score_match:
                score_val = int(score_match.group(1))
                has_errors = score_match.group(2) == "true"
                full = full[:score_match.start()].strip()

            return jsonify({"result": full, "score": score_val, "has_errors": has_errors})

        except Exception as e:
            return jsonify({"result": f"Error: {str(e)}", "score": 0, "has_errors": True}), 500