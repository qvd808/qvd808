import pathlib
L = pathlib.Path('template.html').read_text().split('\n')   # 0-indexed

# Scene code verbatim: template lines 125..1533  -> idx 124..1532
body = '\n'.join(L[124:1533])

def sub(old, new, why):
    global body
    assert body.count(old) == 1, f"FAILED ({why}): {body.count(old)} matches"
    body = body.replace(old, new)
    print(f"  patched: {why}")

sub("if (this._raf || this.state.phase) return;",
    "if (this._raf || this.phase) return;", "state.phase -> phase")
sub("this.setState({ phase: 1 });", "this.setPhase(1);", "setState phase 1")
sub("this.setState({ phase: 0 });", "this.setPhase(0);", "setState phase 0")
sub("""    this.setState({
      eyes: spots.map((e) => ({ x: e.x, y: e.y, r: e.r })),
      figBox: m ? { x: m.fx - m.hf * 0.22, y: m.fy - m.hf * 1.04, w: m.hf * 0.52, h: m.hf * 1.1 } : null
    });""",
    """    this.syncEyes(
      spots.map((e) => ({ x: e.x, y: e.y, r: e.r })),
      m ? { x: m.fx - m.hf * 0.22, y: m.fy - m.hf * 1.04, w: m.hf * 0.52, h: m.hf * 1.1 } : null
    );""", "setState eyes/figBox -> syncEyes")
sub('    const off = document.createElement("canvas");',
    '    const off = this._off || (this._off = document.createElement("canvas"));',
    "reuse offscreen canvas")


sub("\n  paint(target) {\n", "\n  async paint(target) {\n", "paint -> async")

sub("""    const ctx = c.getContext("2d");
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    this.vctx = ctx;""",
    """    const ctx = c.getContext("2d");
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    /* background goes to its own layer, so the visible canvas is not touched
       until the final composite and chunked painting never shows a half-scene */
    const bg = this._bg || (this._bg = document.createElement("canvas"));
    bg.width = c.width; bg.height = c.height;
    const bgctx = bg.getContext("2d");
    bgctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    this.vctx = bgctx;""", "background -> own layer")

sub("""    this.background();
    this.sky();
    octx.save();
    octx.globalCompositeOperation = "destination-out";
    octx.fillStyle = "#000";
    octx.fillRect(-2, this.skyBottom, W + 4, H - this.skyBottom + 4);
    octx.restore();
    this.distantRidge();
    this.mesas();
    this.terraces();
    this.foreground();
    this.figMark = this.figSpot();
    if (!this._phase) this.figure(); else this.wreck();""",
    """    /* Same calls in the same order -> same RNG sequence -> same picture.
       Yielding between phases only decides when they run, never what they draw. */
    const tok = ++this._paintTok;
    this._sliceT = performance.now();
    const slice = async () => {
      if (performance.now() - this._sliceT < 8) return true;
      await new Promise((r) => requestAnimationFrame(r));
      this._sliceT = performance.now();
      return tok === this._paintTok;
    };

    this.background();
    if (!(await slice())) return;
    this.sky();
    octx.save();
    octx.globalCompositeOperation = "destination-out";
    octx.fillStyle = "#000";
    octx.fillRect(-2, this.skyBottom, W + 4, H - this.skyBottom + 4);
    octx.restore();
    if (!(await slice())) return;
    this.distantRidge();
    if (!(await slice())) return;
    this.mesas();
    if (!(await slice())) return;
    this.terraces();
    if (!(await slice())) return;
    this.foreground();
    if (!(await slice())) return;
    this.figMark = this.figSpot();
    if (!this._phase) this.figure(); else this.wreck();
    if (!(await slice())) return;""", "chunk paint across frames")

sub("""    ctx.save();
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    if (this.night) {""",
    """    this.vctx = ctx;
    ctx.save();
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.globalCompositeOperation = "source-over";
    ctx.globalAlpha = 1;
    ctx.drawImage(bg, 0, 0);
    if (this.night) {""", "composite background layer first")

sub("    this.grainPass(c);", "    await this.grainPassAsync(c);", "grain -> worker")

sub("    this._pianoSprite = this.bakePiano(pw);",
    "    this._pianoSprite = this.bakePiano(pw);\n    this.bakeDebris(impact, pw);",
    "bake debris up front")

sub("        this.withCtx(fx, 9100 + Math.floor(p * 4), () => this.debris(impact, pw, p));",
    "        this.drawDebris(fx, impact, p);", "debris -> baked sprite")

sub("    this._pianoSprite = null;", "    this._pianoSprite = null;\n    this._debris = null;",
    "free debris sprites on reset")

# ---- swap the drawn face for the Wonder of U reference image ----
_start = body.index('  buildFace() {')
_end   = body.index('    return out;\n  }', _start) + len('    return out;\n  }')
body = body[:_start] + """  /* Position the reference art so its eyes land exactly on the two glows.
     Both scene eyes share a Y (foreground() gives them the same ay), so a
     scale + translate is enough - no rotation needed. */
  buildFace() {
    const M = this.faceMetrics();
    const img = this._faceImg;
    if (!M || !img || !img.complete || !img.naturalWidth) return null;
    const E = FACE_EYES;
    const dw = (M.Rr.x - M.L.x) / (E.rx - E.lx);
    const dh = dw * (img.naturalHeight / img.naturalWidth);
    this._faceBox = {
      x: M.L.x - E.lx * dw,
      y: M.my - ((E.ly + E.ry) / 2) * dh,
      w: dw,
      h: dh
    };
    return img;
  }""" + body[_end:]
print("  patched: buildFace -> reference image")

_a = body.index('  faceArt() {')
_b = body.index('  revealFace(fx, p) {')
print(f"  patched: removed faceArt() ({body[_a:_b].count(chr(10))} dead lines)")
body = body[:_a] + body[_b:]

sub('    fx.globalCompositeOperation = "lighter";\n    fx.globalAlpha = Math.min(1, p * 1.4);',
    '    fx.globalAlpha = Math.min(1, p * 1.4);',
    "reveal blend lighter -> source-over")

sub("""    fx.drawImage(this._face, b.x, b.y, b.w, b.h);
    fx.restore();
  }""",
    """    fx.drawImage(this._face, b.x, b.y, b.w, b.h);
    fx.restore();
    /* the glows are its eyes now - let ours fade out as it resolves */
    this.fadeEyes(Math.max(0, 1 - Math.min(1, p * 1.7)));
  }""", "fade the glow eyes during reveal")

sub("    this._debris = null;", "    this._debris = null;\n    this.fadeEyes(1);",
    "restore eye opacity on reset")

GLUE = '''  constructor(props) {
    this.props = Object.assign(
      { mode: "night", seed: 4211, inkStrength: 1, glow: 1, skyDensity: 1, grain: 1 },
      props || {}
    );
    this.phase = 0;
    this.figBox = null;
    this.stage = document.querySelector('[data-stage="1"]');
    this.canvas = this.stage.querySelector('canvas[data-sketch="1"]');
    this.hit = this.stage.querySelector('[data-hit="1"]');
    this.sockets = [];
    this.aimEls = [];
    this._tx = 0.5; this._ty = 0.5;   /* cursor target */
    this._ex = 0.5; this._ey = 0.5;   /* eased gaze */
    this._aimRaf = 0;
    this._paintTok = 0;
    this._faceImg = new Image();
    this._faceImg.src = FACE_IMG;
    this._aimStep = (now) => {
      const dt = Math.min(0.05, (now - this._aimT) / 1000);
      this._aimT = now;
      const k = 1 - Math.exp(-dt / 0.09);   /* ~90ms time constant */
      this._ex += (this._tx - this._ex) * k;
      this._ey += (this._ty - this._ey) * k;
      this.applyAim();
      if (Math.abs(this._tx - this._ex) > 0.0004 ||
          Math.abs(this._ty - this._ey) > 0.0004) {
        this._aimRaf = requestAnimationFrame(this._aimStep);
      } else {
        this._ex = this._tx; this._ey = this._ty;
        this.applyAim();
        this._aimRaf = 0;
      }
    };
    this.hit.addEventListener("click", () =>
      this.phase ? this.resetCalamity() : this.startCalamity());
  }

  cv() { return this.canvas; }

  fadeEyes(v) {
    for (const s of this.sockets) s.style.opacity = v;
  }

  mount() {
    this._resize = () => {
      clearTimeout(this._t);
      this._t = setTimeout(() => this.paint(), 220);
    };
    /* one resize source, not two: ResizeObserver already covers window resize */
    if (window.ResizeObserver) {
      this._ro = new ResizeObserver(this._resize);
      this._ro.observe(this.stage);
    } else {
      window.addEventListener("resize", this._resize);
    }
    this._move = (ev) => {
      const p = ev.touches && ev.touches[0] ? ev.touches[0] : ev;
      this.aimEyes(p.clientX / window.innerWidth, p.clientY / window.innerHeight);
    };
    window.addEventListener("mousemove", this._move, { passive: true });
    window.addEventListener("touchmove", this._move, { passive: true });
    this.paint();
  }

  destroy() {
    if (this._ro) this._ro.disconnect();
    else window.removeEventListener("resize", this._resize);
    window.removeEventListener("mousemove", this._move);
    window.removeEventListener("touchmove", this._move);
    clearTimeout(this._t);
    if (this._aimRaf) cancelAnimationFrame(this._aimRaf);
  }

  setPhase(p) { this.phase = p; this.syncHit(); }

  /* rebuild the eye elements after a repaint */
  syncEyes(spots, figBox) {
    this.figBox = figBox;
    for (const s of this.sockets) s.remove();
    this.sockets = [];
    this.aimEls = [];
    for (const e of spots) {
      const d = e.r * 2;
      const sock = document.createElement("div");
      sock.setAttribute("data-eye-socket", "1");
      sock.style.cssText =
        "position:absolute;left:" + (e.x - e.r) + "px;top:" + (e.y - e.r) +
        "px;width:" + d + "px;height:" + d + "px;pointer-events:none";
      const glow = this.layer(d * 0.92, (d * 0.086).toFixed(2),
        "radial-gradient(circle, #cfe8ff 0%, #7db4f5 22%, #3a6fb8 45%, rgba(32,74,140,0.42) 62%, rgba(24,56,110,0) 80%)",
        "data-eye-glow");
      const iris = this.layer(d * 0.52, (d * 0.114).toFixed(2),
        "radial-gradient(circle, #ffffff 0%, #eaf6ff 30%, rgba(200,230,255,0.5) 55%, rgba(170,210,255,0) 75%)",
        "data-eye-iris");
      sock.appendChild(glow);
      sock.appendChild(iris);
      this.stage.appendChild(sock);
      this.sockets.push(sock);
      /* k = d * range / 100; halo sweeps 35, iris 65 */
      this.aimEls.push({ el: glow, k: d * 0.35 }, { el: iris, k: d * 0.65 });
    }
    this.syncHit();
    this.applyAim();
  }

  layer(size, blur, bg, attr) {
    const el = document.createElement("div");
    el.setAttribute(attr, "1");
    el.style.cssText =
      "position:absolute;left:50%;top:50%;width:" + size + "px;height:" + size +
      "px;border-radius:50%;background:" + bg + ";filter:blur(" + blur +
      "px);transform:translate(-50%,-50%);will-change:transform";
    return el;
  }

  syncHit() {
    const h = this.hit, b = this.figBox;
    if (this.phase) {
      h.style.cssText = "position:absolute;inset:0;cursor:pointer;background:transparent";
      h.title = "back";
    } else if (b) {
      h.style.cssText =
        "position:absolute;left:" + b.x + "px;top:" + b.y + "px;width:" + b.w +
        "px;height:" + b.h + "px;cursor:pointer;background:transparent";
      h.title = "look down";
    } else {
      h.style.cssText = "display:none";
    }
  }

  /* cursor parallax: the iris outruns the halo, as in the reference sketch.
     The gaze eases toward the cursor instead of snapping to it. Exponential
     smoothing is framerate-independent, and the loop stops itself once
     settled, so an idle page schedules no frames at all. */
  aimEyes(fx, fy) {
    this._tx = fx; this._ty = fy;
    if (this._aimRaf) return;
    this._aimT = performance.now();
    this._aimRaf = requestAnimationFrame(this._aimStep);
  }

  applyAim() {
    const dx = this._ex - 0.5, dy = this._ey - 0.5;
    for (const a of this.aimEls) {
      a.el.style.transform =
        "translate(-50%,-50%) translate(" + (a.k * dx) + "px," + (a.k * dy) + "px)";
    }
  }

  /* --- grain, offloaded to a worker so the main thread stays free --- */
  grainPassAsync(c) {
    const G = this.props.grain == null ? 1 : this.props.grain;
    if (G <= 0.001) return Promise.resolve();
    const ctx = this.vctx, cw = c.width, ch = c.height;
    if (!cw || !ch) return Promise.resolve();
    if (!this._gw && window.Worker && !this._gwFailed) {
      try {
        this._gw = new Worker(URL.createObjectURL(
          new Blob([GRAIN_WORKER], { type: "text/javascript" })));
      } catch (err) { this._gwFailed = true; }
    }
    if (!this._gw) { this.grainPass(c); return Promise.resolve(); }
    const img = ctx.getImageData(0, 0, cw, ch);
    const w = this._gw;
    return new Promise((resolve) => {
      const fallback = () => {
        w.onmessage = null; w.onerror = null;
        try { this.grainPass(c); } catch (err) {}
        resolve();
      };
      const timer = setTimeout(fallback, 4000);
      w.onmessage = (e) => {
        clearTimeout(timer);
        w.onmessage = null; w.onerror = null;
        ctx.putImageData(new ImageData(new Uint8ClampedArray(e.data.buf), cw, ch), 0, 0);
        resolve();
      };
      w.onerror = () => { clearTimeout(timer); this._gw = null; this._gwFailed = true; fallback(); };
      w.postMessage({ buf: img.data.buffer, cw: cw, ch: ch, G: G, night: this.night },
                    [img.data.buffer]);
    });
  }

  /* --- debris, baked once per seed step instead of re-inked every frame --- */
  bakeDebris(impact, pw) {
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const maxL = pw * 0.75 * 1.4;
    /* debris only flies upward (angles -3.0..-0.15 rad), so the box is wide
       and shallow rather than square, and the backing store is capped so a
       wide display cannot allocate tens of MB of sprite */
    const padX = pw * 0.5 + maxL + 12, padT = padX, padB = pw * 0.45;
    const w = Math.ceil(padX * 2), h = Math.ceil(padT + padB);
    const bs = Math.min(dpr, 1600 / Math.max(w, h));
    const sprites = [];
    for (let s = 0; s < 4; s++) {
      const cnv = document.createElement("canvas");
      cnv.width = Math.round(w * bs);
      cnv.height = Math.round(h * bs);
      const cx2 = cnv.getContext("2d");
      cx2.setTransform(bs, 0, 0, bs, 0, 0);
      cx2.translate(padX, padT);
      /* same RNG call order as the original debris(), so each seed step
         produces the same shapes; only length and alpha are normalised out */
      this.withCtx(cx2, 9100 + s, () => {
        for (let i = 0; i < 22; i++) {
          const a = this.r(-3.0, -0.15), L = pw * this.r(0.15, 0.75) * 1.4;
          const x = this.g() * pw * 0.2, y = pw * 0.12;
          this.stroke([[x, y], [x + Math.cos(a) * L, y + Math.sin(a) * L]],
            { alpha: 0.9, width: this.r(1, 2.4), wobble: 0.5, taper: 0.9, grain: 0.3 });
        }
      });
      sprites.push(cnv);
    }
    this._debris = { sprites: sprites, padX: padX, padT: padT, w: w, h: h };
  }

  drawDebris(fx, impact, p) {
    const D = this._debris;
    if (!D) return;
    const k = (0.4 + p) / 1.4;
    fx.save();
    fx.globalAlpha = Math.max(0, Math.min(1, 1 - p));
    fx.translate(impact.x, impact.y);
    fx.scale(k, k);
    fx.drawImage(D.sprites[Math.min(3, Math.floor(p * 4))],
                 -D.padX, -D.padT, D.w, D.h);
    fx.restore();
  }
'''

HTML = '''<!DOCTYPE html>
<html lang="en">
<head>
<!--
  ==========================================================================
  CREDIT / ATTRIBUTION  -  hidden easter egg

  The character revealed by the easter egg is WONDER OF U, from
  "JoJo's Bizarre Adventure" (Part 8: JoJolion).

  JoJo's Bizarre Adventure and all of its characters are
  copyright (c) Hirohiko Araki / Shueisha.

  Reference image source:
    https://jojo.fandom.com/wiki/Wonder_of_U

  Used here as a non-commercial personal easter egg on a personal profile
  page. All rights in the character and its depiction remain with the
  original creator and rights holders. No affiliation with, sponsorship by,
  or endorsement from the rights holders is implied.

  Full respect and credit to Hirohiko Araki as the creator.
  ==========================================================================
-->
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Eyes</title>
<style>
  html, body { margin: 0; padding: 0; height: 100%; background: #0b0c0e; overflow: hidden; }
  a { color: rgb(226, 235, 244); } a:hover { color: rgb(160, 176, 192); }
  #wrap { position: relative; width: 100%; height: 100dvh; min-height: 100%; background: #0b0c0e; overflow: hidden; }
  [data-stage] { position: absolute; inset: 0; will-change: transform; }
  [data-stage] canvas { position: absolute; inset: 0; width: 100%; height: 100%; display: block; }
  canvas[data-sketch] { touch-action: none; }
  canvas[data-fx] { pointer-events: none; }
</style>
</head>
<body>

<div id="wrap">
  <div data-stage="1">
    <canvas data-sketch="1"></canvas>
    <canvas data-fx="1"></canvas>
    <div data-hit="1" style="display:none"></div>
  </div>
</div>

<script>
%FACE%/* grain is a pure per-pixel pass, so it runs off-thread; identical math */
const GRAIN_WORKER = `
self.onmessage = function (e) {
  var d = new Uint8ClampedArray(e.data.buf);
  var cw = e.data.cw, ch = e.data.ch, G = e.data.G, night = e.data.night;
  var s = 1234567;
  var rnd = function () { s = (s * 1664525 + 1013904223) >>> 0; return s / 4294967296; };
  var T0 = new Float32Array(65536), i;
  for (i = 0; i < T0.length; i++) T0[i] = rnd();
  var T = new Float32Array(65536), x, y;
  for (y = 0; y < 256; y++) for (x = 0; x < 256; x++) {
    i = y * 256 + x;
    T[i] = (T0[i] * 2 + T0[y * 256 + ((x + 1) & 255)] + T0[(((y + 1) & 255) * 256) + x]) / 4;
  }
  var PR = night ? 11 : 240, PG = night ? 12 : 237, PB = night ? 14 : 228;
  var vx = new Float32Array(cw);
  for (x = 0; x < cw; x++) { var t = x / cw - 0.5; vx[x] = t * t; }
  for (y = 0; y < ch; y++) {
    var ty = y / ch - 0.5, vyv = ty * ty, row = (y & 255) << 8;
    for (x = 0; x < cw; x++) {
      i = (y * cw + x) << 2;
      var n = T[row | (x & 255)];
      var light = Math.max(0, n - 0.56) * 1.7 * G, dark = Math.max(0, 0.42 - n) * 0.2 * G;
      var vig = 1 - (vx[x] + vyv) * (night ? 0.36 : 0.19);
      if (night) vig *= 1 - Math.max(0, (y / ch - 0.74) / 0.26) * 0.3;
      var r = d[i], g = d[i + 1], b = d[i + 2];
      r += (PR - r) * light; g += (PG - g) * light; b += (PB - b) * light;
      r = r * (1 - dark) * vig; g = g * (1 - dark) * vig; b = b * (1 - dark) * vig;
      if (night) { var f = (n - 0.5) * 8 * G; r += f; g += f; b += f * 1.12; }
      d[i] = r; d[i + 1] = g; d[i + 2] = b;
    }
  }
  self.postMessage({ buf: d.buffer }, [d.buffer]);
};
`;

class Scene {
%GLUE%
%BODY%
}

new Scene().mount();
</script>

</body>
</html>
'''

import json as _j, pathlib as _pl
_fa = _j.loads(_pl.Path('face_asset.json').read_text())
_face = ('const FACE_IMG = "data:image/webp;base64,%s";\n'
         'const FACE_EYES = { lx: %.5f, ly: %.5f, rx: %.5f, ry: %.5f };\n\n'
         % (_fa['b64'], _fa['eyes']['lx'], _fa['eyes']['ly'],
            _fa['eyes']['rx'], _fa['eyes']['ry']))
print(f"  asset: {len(_fa['b64'])} b64 chars, eyes dy={abs(_fa['eyes']['ry']-_fa['eyes']['ly'])*_fa['h']:.3f}px")
out = HTML.replace('%FACE%', _face).replace('%GLUE%', GLUE).replace('%BODY%', body)
pathlib.Path('new_index.html').write_text(out)
print(f"\nwrote new_index.html: {len(out):,} bytes")
