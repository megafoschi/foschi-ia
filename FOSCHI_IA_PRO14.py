#!/usr/bin/env python3
# coding: utf-8
"""
=======================================================
 FOSCHI IA — NUEVAS RUTAS DE IMÁGENES
 Pegá este bloque ANTES de la línea:
   # ---------------- RESPUESTA IA ----------------
 (justo después del cierre de imagen_a_word)
=======================================================

FUNCIONES NUEVAS:
  1. /generar_imagen  → genera imagen con DALL-E 3
  2. /editar_imagen   → edita imagen existente con IA
                        (recorte + máscara opcional, DALL-E 2 inpainting)
  3. /variaciones_imagen → genera variaciones de una imagen

FRONTEND:
  Al final del archivo encontrás el bloque HTML/JS listo
  para pegar dentro de tu HTML_TEMPLATE.
=======================================================
"""

# ─────────────────────────────────────────────────────
# 1. GENERAR IMAGEN CON IA  (DALL-E 3)
# ─────────────────────────────────────────────────────
@app.route("/generar_imagen", methods=["POST"])
def generar_imagen():
    """
    Body JSON esperado:
      {
        "prompt":  "un gato astronauta en la luna",
        "size":    "1024x1024",          # opcional (default 1024x1024)
        "quality": "standard",           # opcional: "standard" | "hd"
        "style":   "vivid"               # opcional: "vivid" | "natural"
      }
    Devuelve JSON:
      { "ok": true, "url": "...", "nombre": "gen_xxx.png" }
    """
    data = request.get_json(silent=True) or {}
    prompt = data.get("prompt", "").strip()

    if not prompt:
        return jsonify({"ok": False, "error": "El prompt está vacío."}), 400

    size    = data.get("size",    "1024x1024")
    quality = data.get("quality", "standard")
    style   = data.get("style",   "vivid")

    # Tamaños válidos para DALL-E 3
    SIZES_VALIDOS = {"1024x1024", "1792x1024", "1024x1792"}
    if size not in SIZES_VALIDOS:
        size = "1024x1024"

    try:
        respuesta = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size=size,
            quality=quality,
            style=style,
            n=1,
            response_format="url"
        )

        url_imagen = respuesta.data[0].url

        # Descargar y guardar localmente para poder servir/editar después
        r = requests.get(url_imagen, timeout=30)
        nombre = f"gen_{uuid.uuid4().hex}.png"
        ruta_local = os.path.join(IMAGES_DIR, nombre)
        with open(ruta_local, "wb") as f:
            f.write(r.content)

        return jsonify({
            "ok": True,
            "url": f"/imagen_generada/{nombre}",
            "nombre": nombre
        })

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


# ─────────────────────────────────────────────────────
# 2. SERVIR IMÁGENES GENERADAS
# ─────────────────────────────────────────────────────
@app.route("/imagen_generada/<nombre>")
def servir_imagen_generada(nombre):
    """Sirve imágenes guardadas en IMAGES_DIR."""
    ruta = os.path.join(IMAGES_DIR, nombre)
    if not os.path.exists(ruta):
        return "Imagen no encontrada", 404
    return send_file(ruta, mimetype="image/png")


# ─────────────────────────────────────────────────────
# 3. EDITAR IMAGEN CON IA  (DALL-E 2 inpainting)
# ─────────────────────────────────────────────────────
@app.route("/editar_imagen", methods=["POST"])
def editar_imagen():
    """
    Form-data esperado:
      imagen  : archivo PNG original (obligatorio)
      mascara : archivo PNG con zonas transparentes a editar (opcional)
      prompt  : texto describiendo el cambio (obligatorio)
      size    : "256x256" | "512x512" | "1024x1024"  (opcional)

    Si no se envía máscara, se usa la mitad derecha de la imagen como
    zona de edición automáticamente.

    Devuelve JSON:
      { "ok": true, "url": "/imagen_generada/edit_xxx.png" }
    """
    prompt = request.form.get("prompt", "").strip()
    if not prompt:
        return jsonify({"ok": False, "error": "El prompt está vacío."}), 400

    if "imagen" not in request.files:
        return jsonify({"ok": False, "error": "No se recibió imagen."}), 400

    size = request.form.get("size", "1024x1024")
    SIZES_VALIDOS = {"256x256", "512x512", "1024x1024"}
    if size not in SIZES_VALIDOS:
        size = "1024x1024"
    lado = int(size.split("x")[0])

    # ── Procesar imagen original ──
    archivo_img = request.files["imagen"]
    nombre_orig = f"orig_{uuid.uuid4().hex}.png"
    ruta_orig   = os.path.join(IMAGES_DIR, nombre_orig)
    archivo_img.save(ruta_orig)

    try:
        # Convertir a RGBA y redimensionar
        img = Image.open(ruta_orig).convert("RGBA").resize((lado, lado))
        img.save(ruta_orig)

        # ── Procesar máscara ──
        if "mascara" in request.files and request.files["mascara"].filename:
            archivo_mask = request.files["mascara"]
            nombre_mask  = f"mask_{uuid.uuid4().hex}.png"
            ruta_mask    = os.path.join(IMAGES_DIR, nombre_mask)
            archivo_mask.save(ruta_mask)
            mask = Image.open(ruta_mask).convert("RGBA").resize((lado, lado))
            mask.save(ruta_mask)
        else:
            # Máscara automática: mitad derecha transparente
            nombre_mask = f"mask_{uuid.uuid4().hex}.png"
            ruta_mask   = os.path.join(IMAGES_DIR, nombre_mask)
            mask = Image.new("RGBA", (lado, lado), (0, 0, 0, 255))  # negro opaco
            # Zona a editar = mitad derecha, alfa = 0
            for x in range(lado // 2, lado):
                for y in range(lado):
                    mask.putpixel((x, y), (0, 0, 0, 0))
            mask.save(ruta_mask)

        # ── Llamar a DALL-E 2 edit ──
        with open(ruta_orig, "rb") as f_img, open(ruta_mask, "rb") as f_mask:
            respuesta = client.images.edit(
                model="dall-e-2",
                image=f_img,
                mask=f_mask,
                prompt=prompt,
                n=1,
                size=size,
                response_format="url"
            )

        url_editada = respuesta.data[0].url

        # Guardar resultado
        r = requests.get(url_editada, timeout=30)
        nombre_out = f"edit_{uuid.uuid4().hex}.png"
        ruta_out   = os.path.join(IMAGES_DIR, nombre_out)
        with open(ruta_out, "wb") as f:
            f.write(r.content)

        return jsonify({
            "ok": True,
            "url": f"/imagen_generada/{nombre_out}",
            "nombre": nombre_out
        })

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

    finally:
        # Limpiar temporales de entrada
        for ruta in [ruta_orig, ruta_mask]:
            try:
                if os.path.exists(ruta):
                    os.remove(ruta)
            except Exception:
                pass


# ─────────────────────────────────────────────────────
# 4. VARIACIONES DE IMAGEN  (DALL-E 2)
# ─────────────────────────────────────────────────────
@app.route("/variaciones_imagen", methods=["POST"])
def variaciones_imagen():
    """
    Form-data esperado:
      imagen : archivo PNG (obligatorio)
      n      : cantidad de variaciones 1-4 (opcional, default 2)
      size   : "256x256" | "512x512" | "1024x1024"

    Devuelve JSON:
      { "ok": true, "variaciones": ["/imagen_generada/var_xxx.png", ...] }
    """
    if "imagen" not in request.files:
        return jsonify({"ok": False, "error": "No se recibió imagen."}), 400

    n_var = min(max(int(request.form.get("n", 2)), 1), 4)
    size  = request.form.get("size", "1024x1024")
    SIZES_VALIDOS = {"256x256", "512x512", "1024x1024"}
    if size not in SIZES_VALIDOS:
        size = "1024x1024"
    lado = int(size.split("x")[0])

    archivo_img = request.files["imagen"]
    nombre_orig = f"var_orig_{uuid.uuid4().hex}.png"
    ruta_orig   = os.path.join(IMAGES_DIR, nombre_orig)
    archivo_img.save(ruta_orig)

    try:
        # Convertir a RGBA y redimensionar
        img = Image.open(ruta_orig).convert("RGBA").resize((lado, lado))
        img.save(ruta_orig)

        with open(ruta_orig, "rb") as f_img:
            respuesta = client.images.create_variation(
                model="dall-e-2",
                image=f_img,
                n=n_var,
                size=size,
                response_format="url"
            )

        urls_out = []
        for item in respuesta.data:
            r = requests.get(item.url, timeout=30)
            nombre_out = f"var_{uuid.uuid4().hex}.png"
            ruta_out   = os.path.join(IMAGES_DIR, nombre_out)
            with open(ruta_out, "wb") as f:
                f.write(r.content)
            urls_out.append(f"/imagen_generada/{nombre_out}")

        return jsonify({"ok": True, "variaciones": urls_out})

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

    finally:
        try:
            if os.path.exists(ruta_orig):
                os.remove(ruta_orig)
        except Exception:
            pass


# =======================================================
# BLOQUE HTML/JS  —  pegalo dentro de HTML_TEMPLATE
# donde quieras mostrar el panel de imágenes
# =======================================================
"""
<!-- ════════ PANEL DE IMÁGENES ════════ -->
<div id="panelImagenes" style="display:none; padding:16px; background:#00111a; border:1px solid #00eaff44; border-radius:12px; margin:10px;">

  <!-- TABS -->
  <div style="display:flex; gap:8px; margin-bottom:14px;">
    <button onclick="tabImg('generar')"  id="tab_generar"  class="tabImg active">🎨 Generar</button>
    <button onclick="tabImg('editar')"   id="tab_editar"   class="tabImg">✏️ Editar</button>
    <button onclick="tabImg('variar')"   id="tab_variar"   class="tabImg">🔀 Variaciones</button>
  </div>

  <!-- ── TAB GENERAR ── -->
  <div id="sec_generar">
    <textarea id="promptGen" rows="3" placeholder="Describí la imagen que querés generar..."
      style="width:100%;background:#001a2a;color:#00eaff;border:1px solid #006688;border-radius:8px;padding:8px;font-size:14px;resize:vertical;"></textarea>
    <div style="display:flex;gap:8px;margin-top:8px;flex-wrap:wrap;">
      <select id="sizeGen" style="background:#001a2a;color:#00eaff;border:1px solid #006688;padding:6px;border-radius:6px;">
        <option value="1024x1024">1024×1024 (cuadrada)</option>
        <option value="1792x1024">1792×1024 (landscape)</option>
        <option value="1024x1792">1024×1792 (portrait)</option>
      </select>
      <select id="qualityGen" style="background:#001a2a;color:#00eaff;border:1px solid #006688;padding:6px;border-radius:6px;">
        <option value="standard">Standard</option>
        <option value="hd">HD</option>
      </select>
      <select id="styleGen" style="background:#001a2a;color:#00eaff;border:1px solid #006688;padding:6px;border-radius:6px;">
        <option value="vivid">Vivid</option>
        <option value="natural">Natural</option>
      </select>
      <button onclick="generarImagen()" style="padding:6px 16px;">✨ Generar</button>
    </div>
    <div id="resultGen" style="margin-top:12px;"></div>
  </div>

  <!-- ── TAB EDITAR ── -->
  <div id="sec_editar" style="display:none;">
    <label>Imagen original (PNG):</label>
    <input type="file" id="imgEdit" accept="image/png,image/jpeg" style="display:block;margin:6px 0;">
    <label>Máscara (opcional, PNG con zonas transparentes):</label>
    <input type="file" id="maskEdit" accept="image/png" style="display:block;margin:6px 0;">
    <textarea id="promptEdit" rows="2" placeholder="Describí qué querés cambiar en la zona marcada..."
      style="width:100%;background:#001a2a;color:#00eaff;border:1px solid #006688;border-radius:8px;padding:8px;font-size:14px;resize:vertical;margin-top:6px;"></textarea>
    <div style="display:flex;gap:8px;margin-top:8px;">
      <select id="sizeEdit" style="background:#001a2a;color:#00eaff;border:1px solid #006688;padding:6px;border-radius:6px;">
        <option value="1024x1024">1024×1024</option>
        <option value="512x512">512×512</option>
        <option value="256x256">256×256</option>
      </select>
      <button onclick="editarImagen()" style="padding:6px 16px;">✏️ Editar</button>
    </div>
    <div id="resultEdit" style="margin-top:12px;"></div>
  </div>

  <!-- ── TAB VARIACIONES ── -->
  <div id="sec_variar" style="display:none;">
    <label>Imagen PNG de referencia:</label>
    <input type="file" id="imgVar" accept="image/png,image/jpeg" style="display:block;margin:6px 0;">
    <div style="display:flex;gap:8px;margin-top:8px;align-items:center;">
      <label>Variaciones:</label>
      <select id="nVar" style="background:#001a2a;color:#00eaff;border:1px solid #006688;padding:6px;border-radius:6px;">
        <option value="1">1</option>
        <option value="2" selected>2</option>
        <option value="3">3</option>
        <option value="4">4</option>
      </select>
      <select id="sizeVar" style="background:#001a2a;color:#00eaff;border:1px solid #006688;padding:6px;border-radius:6px;">
        <option value="1024x1024">1024×1024</option>
        <option value="512x512">512×512</option>
        <option value="256x256">256×256</option>
      </select>
      <button onclick="generarVariaciones()" style="padding:6px 16px;">🔀 Variar</button>
    </div>
    <div id="resultVar" style="margin-top:12px;"></div>
  </div>

</div>

<!-- BOTÓN para abrir/cerrar el panel (agregalo donde tenés los otros botones) -->
<!-- <button onclick="togglePanelImagenes()">🖼️ Imágenes IA</button> -->

<style>
.tabImg {
  padding:6px 14px;
  border-radius:6px;
  background:#001f2e;
  color:#00eaff;
  border:1px solid #006688;
  cursor:pointer;
  font-size:13px;
}
.tabImg.active {
  background:#003547;
  box-shadow:0 0 10px #00eaff;
}
.img-result {
  border:1px solid #00eaff44;
  border-radius:8px;
  max-width:100%;
  margin-top:8px;
  box-shadow:0 0 12px #00eaff33;
}
.img-descarga {
  display:inline-block;
  margin-top:6px;
  color:#00eaff;
  font-size:13px;
  text-decoration:underline;
  cursor:pointer;
}
.spinner-img {
  display:inline-block;
  width:20px; height:20px;
  border:3px solid #00eaff44;
  border-top-color:#00eaff;
  border-radius:50%;
  animation:spin 0.8s linear infinite;
  vertical-align:middle;
  margin-right:8px;
}
@keyframes spin { to { transform:rotate(360deg); } }
</style>

<script>
// ── Toggle panel ──
function togglePanelImagenes() {
  const p = document.getElementById("panelImagenes");
  p.style.display = p.style.display === "none" ? "block" : "none";
}

// ── Tabs ──
function tabImg(tab) {
  ["generar","editar","variar"].forEach(t => {
    document.getElementById("sec_" + t).style.display = t === tab ? "block" : "none";
    document.getElementById("tab_" + t).classList.toggle("active", t === tab);
  });
}

// ── Helper: mostrar spinner ──
function setLoading(id, msg) {
  document.getElementById(id).innerHTML =
    `<span class="spinner-img"></span>${msg}`;
}

// ── Helper: mostrar imagen resultado ──
function mostrarImagen(containerId, url, nombre) {
  document.getElementById(containerId).innerHTML = `
    <img src="${url}" class="img-result" alt="imagen generada"><br>
    <a href="${url}" download="${nombre}" class="img-descarga">⬇️ Descargar imagen</a>
  `;
}

// ── 1. GENERAR ──
async function generarImagen() {
  const prompt  = document.getElementById("promptGen").value.trim();
  const size    = document.getElementById("sizeGen").value;
  const quality = document.getElementById("qualityGen").value;
  const style   = document.getElementById("styleGen").value;

  if (!prompt) { alert("Escribí un prompt primero."); return; }

  setLoading("resultGen", "Generando imagen con DALL-E 3…");

  try {
    const res  = await fetch("/generar_imagen", {
      method: "POST",
      headers: {"Content-Type":"application/json"},
      body: JSON.stringify({ prompt, size, quality, style })
    });
    const data = await res.json();
    if (data.ok) {
      mostrarImagen("resultGen", data.url, data.nombre);
    } else {
      document.getElementById("resultGen").innerHTML =
        `<span style="color:#ff4444;">❌ ${data.error}</span>`;
    }
  } catch(e) {
    document.getElementById("resultGen").innerHTML =
      `<span style="color:#ff4444;">❌ Error de red: ${e}</span>`;
  }
}

// ── 2. EDITAR ──
async function editarImagen() {
  const imgFile  = document.getElementById("imgEdit").files[0];
  const maskFile = document.getElementById("maskEdit").files[0];
  const prompt   = document.getElementById("promptEdit").value.trim();
  const size     = document.getElementById("sizeEdit").value;

  if (!imgFile)  { alert("Seleccioná una imagen primero."); return; }
  if (!prompt)   { alert("Escribí qué querés cambiar."); return; }

  setLoading("resultEdit", "Editando imagen con IA…");

  const fd = new FormData();
  fd.append("imagen",  imgFile);
  if (maskFile) fd.append("mascara", maskFile);
  fd.append("prompt", prompt);
  fd.append("size",   size);

  try {
    const res  = await fetch("/editar_imagen", { method:"POST", body:fd });
    const data = await res.json();
    if (data.ok) {
      mostrarImagen("resultEdit", data.url, data.nombre);
    } else {
      document.getElementById("resultEdit").innerHTML =
        `<span style="color:#ff4444;">❌ ${data.error}</span>`;
    }
  } catch(e) {
    document.getElementById("resultEdit").innerHTML =
      `<span style="color:#ff4444;">❌ Error de red: ${e}</span>`;
  }
}

// ── 3. VARIACIONES ──
async function generarVariaciones() {
  const imgFile = document.getElementById("imgVar").files[0];
  const n       = document.getElementById("nVar").value;
  const size    = document.getElementById("sizeVar").value;

  if (!imgFile) { alert("Seleccioná una imagen PNG primero."); return; }

  setLoading("resultVar", `Generando ${n} variación(es)…`);

  const fd = new FormData();
  fd.append("imagen", imgFile);
  fd.append("n",    n);
  fd.append("size", size);

  try {
    const res  = await fetch("/variaciones_imagen", { method:"POST", body:fd });
    const data = await res.json();
    if (data.ok) {
      let html = "";
      data.variaciones.forEach((url, i) => {
        const nombre = url.split("/").pop();
        html += `<img src="${url}" class="img-result" alt="variacion ${i+1}">
                 <a href="${url}" download="${nombre}" class="img-descarga">⬇️ Descargar variación ${i+1}</a><br>`;
      });
      document.getElementById("resultVar").innerHTML = html;
    } else {
      document.getElementById("resultVar").innerHTML =
        `<span style="color:#ff4444;">❌ ${data.error}</span>`;
    }
  } catch(e) {
    document.getElementById("resultVar").innerHTML =
      `<span style="color:#ff4444;">❌ Error de red: ${e}</span>`;
  }
}
</script>
"""
