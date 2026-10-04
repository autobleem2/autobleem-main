"""ABleemStation: a self-contained WebGL viewer (three.js from jsDelivr, the case STLs inlined as base64) + quick renders.
The page works by double-click. Hash options: #view=front|back|right|top|iso, &explode=1, &pi=1, &shot=1 (no UI).
Renders: headless Chrome screenshots of the same page into ../files/renders/. Run after make_case.py and
make_stickers.py:  python make_viewer.py
The universal case (make_universal.py):  python make_viewer.py universal  - the same page with the board (&m=pi23|pi4|pi5),
the front panel (&front=usb|blank) and the roof (&roof=active) to pick, into ../files/universal/.
Both pages: &led=rgb (the RGB pixel's shell), &cw=<colourway>, and "Download ZIP" - the 3MFs, Orca profiles, stickers
and wiring of the option on screen plus a BUILD.txt with its settings, all inlined, built in the browser (&zipcheck=1 is
the self-test this script runs)."""
import base64
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FILES = os.path.normpath(os.path.join(HERE, "..", "files"))
VARIANT = sys.argv[1] if len(sys.argv) > 1 else ""
OUT = os.path.join(FILES, VARIANT) if VARIANT else FILES
VIEW = os.path.join(OUT, "viewer")
def find_chrome():
    """headless Chrome: $CHROME, else chrome / google-chrome on PATH, else the default Windows install"""
    for c in (os.environ.get("CHROME"), shutil.which("chrome"), shutil.which("google-chrome"),
              os.path.join(os.environ.get("ProgramFiles", ""), "Google", "Chrome", "Application", "chrome.exe")):
        if c and os.path.exists(c):
            return c
    raise SystemExit("Chrome not found - set CHROME to its path")


CHROME = find_chrome()
PAGE = os.path.join(OUT, "ableemstation-%sviewer.html" % (VARIANT + "-" if VARIANT else ""))

# colourways: top (above the waist), band (below it - the filament change), base plate, button caps (ASA colours
# that exist off the shelf; the LED stays cyan)
COLORWAYS = [
    ("classic", "Classic Grey", "c4c8cd", "2e3742", "3a414a", "2e3742"),
    ("graphite", "Graphite Cyan", "3a434e", "1b2026", "1b2026", "36d9e0"),
    ("arctic", "Arctic White", "f1f1ec", "9aa3ad", "6d757e", "9aa3ad"),
    ("cream", "Cream & Maroon", "e8dfcb", "7d1f2b", "4a3a32", "7d1f2b"),
    ("beige", "Retro Beige", "d6cdb2", "6b5e4d", "4f463b", "8a3b2e"),
    ("midnight", "Midnight Neon", "1f2125", "1f2125", "121316", "ff46aa"),
    ("purple", "Atomic Purple", "7a5ca8", "3b2a57", "2a1e3e", "e6e0f0"),
    ("mint", "Mint", "a9d6c6", "2e3742", "2e3742", "f1f1ec"),
    # a nod to the grey 1994 consoles - colours only, with the special edition stickers (stickers/special/)
    ("grey94", "Grey 94 Special Edition", "cfcdc8", "9c9a96", "6e6d6a", "85848a", "special"),
]
stl = {f[:-4]: base64.b64encode(open(os.path.join(VIEW, f), "rb").read()).decode()
       for f in sorted(os.listdir(VIEW)) if f.endswith(".stl")}
import json as _j
prm = _j.load(open(os.path.join(VIEW, "params.json")))
deco = {}
for sub in ("", "special"):
    d = os.path.join(FILES, "stickers", sub)
    for f in sorted(os.listdir(d)) if os.path.isdir(d) else []:
        if f.startswith("sticker-") and f.endswith(".png") and (f[:-4] in ("sticker-top", "sticker-front") or "side" in prm or "bottom" in prm):
            deco[(sub + "/" if sub else "") + f[:-4]] = base64.b64encode(open(os.path.join(d, f), "rb").read()).decode()


# the print files the page's "Download ZIP" picks from, by their path in the zip (the page takes only what the option
# on screen needs): the 3MFs, the Orca profiles, the stickers of both sets, the wiring diagrams, the README
def b64file(path):
    return base64.b64encode(open(path, "rb").read()).decode()


pack = {"README.md": b64file(os.path.join(FILES, "..", "README.md"))}
parts3mf = ["base", "shell", "shell-rgb"] if not VARIANT else (
    ["uni-base", "uni-shell", "uni-shell-rgb", "uni-shell-active", "uni-shell-active-rgb"]
    + ["panel-" + f[len("ableemstation-panel-"):-4] for f in sorted(os.listdir(OUT)) if f.startswith("ableemstation-panel-") and f.endswith(".3mf")])
for n in parts3mf:
    pack["3mf/ableemstation-%s.3mf" % n] = b64file(os.path.join(OUT, "ableemstation-%s.3mf" % n))
for n in ("button", "lens"):                       # the same parts for both cases, in files/
    pack["3mf/ableemstation-%s.3mf" % n] = b64file(os.path.join(FILES, "ableemstation-%s.3mf" % n))
for f in sorted(os.listdir(os.path.join(FILES, "orca"))):
    pack["orca/" + f] = b64file(os.path.join(FILES, "orca", f))
for n in ("wiring", "wiring-rgb"):
    pack["wiring/%s.png" % n] = b64file(os.path.join(FILES, n + ".png"))
for sub in ("", "special"):
    d = os.path.join(FILES, "stickers", sub)
    for root, _dirs, fs in os.walk(d):
        if sub == "" and os.path.relpath(root, d).startswith("special"):
            continue
        for f in fs:
            rel = os.path.relpath(os.path.join(root, f), os.path.join(FILES, "stickers")).replace("\\", "/")
            pack["stickers/" + rel] = b64file(os.path.join(root, f))

HTML = r"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>ABleemStation case</title>
<style>
:root{--bg:#161b21;--ink:#eef3f6;--dim:#93a3b3;--cyan:#36d9e0;--panel:#1f262e}
html,body{margin:0;height:100%;background:var(--bg);color:var(--ink);font:14px/1.4 system-ui,sans-serif;overflow:hidden}
canvas{display:block}
.ui{position:absolute;left:16px;top:14px;display:flex;flex-wrap:wrap;gap:8px;align-items:center;max-width:calc(100% - 32px)}
.ui b{font-size:18px;margin-right:8px;letter-spacing:.5px}
.ui button{background:var(--panel);color:var(--ink);border:1px solid #33404c;border-radius:4px;padding:6px 10px;cursor:pointer;font:inherit}
.ui button.on{border-color:var(--cyan);color:var(--cyan)}
.ui button.dl{background:var(--cyan);color:#0d1216;border-color:var(--cyan);font-weight:600}
.hint{position:absolute;left:16px;bottom:12px;color:var(--dim);font-size:12px}
body.shot .ui,body.shot .hint{display:none}
</style>
<script type="importmap">{"imports":{"three":"https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js","three/addons/":"https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/"}}</script>
</head><body>
<div class="ui"><b>ABleemStation</b>
<button data-v="iso" class="on">3/4</button><button data-v="front">Front</button><button data-v="back">Back</button>
<button data-v="right">Right</button><button data-v="top">Top</button><button data-v="left">Side</button><button data-v="under">Bottom</button>
<span id="um" style="display:contents"></span><button id="ex">Explode</button><button id="pi">Show Pi</button><button id="xr">X-ray</button><button id="rg" title="a WS2812B pixel instead of the 5 mm LED">RGB LED</button><button id="sb">LED: standby</button><span id="cw" style="display:flex;gap:6px;flex-wrap:wrap"></span>
<button id="zp" class="dl" title="the files to print this option: 3MF, Orca profiles, stickers, wiring, notes">Download ZIP</button></div>
<div class="hint" id="hint">Drag to orbit · wheel to zoom</div>
<script type="module">
import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { STLLoader } from "three/addons/loaders/STLLoader.js";
const DATA = __DATA__, DECO = __DECO__, P = __PARAMS__, CW = __COLORS__, PACK = __PACK__;
const q = Object.fromEntries(location.hash.slice(1).split("&").filter(Boolean).map(s => s.split("=")));
if (q.shot) document.body.classList.add("shot");
const r = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
r.setPixelRatio(Math.min(2, devicePixelRatio)); r.setSize(innerWidth, innerHeight);
r.toneMapping = THREE.ACESFilmicToneMapping; r.shadowMap.enabled = true; r.shadowMap.type = THREE.PCFSoftShadowMap;
document.body.appendChild(r.domElement);
const scene = new THREE.Scene(); scene.background = new THREE.Color(0x161b21);
const cam = new THREE.PerspectiveCamera(32, innerWidth / innerHeight, 1, 3000);
// z is up: set before the controls exist, or they orbit round the wrong axis and the model tumbles
THREE.Object3D.DEFAULT_UP.set(0, 0, 1); cam.up.set(0, 0, 1);
const ctl = new OrbitControls(cam, r.domElement);
Object.assign(ctl, { enableDamping: true, dampingFactor: .12, rotateSpeed: .7, zoomSpeed: .9, panSpeed: .8,
  screenSpacePanning: true, minDistance: 120, maxDistance: 900, maxPolarAngle: Math.PI * .62 });
scene.add(new THREE.HemisphereLight(0xdfefff, 0x20262e, 1.1));
const key = new THREE.DirectionalLight(0xffffff, 2.2); key.position.set(-160, -220, 260); key.castShadow = true;
key.shadow.mapSize.set(2048, 2048); Object.assign(key.shadow.camera, { left: -200, right: 200, top: 200, bottom: -200 }); scene.add(key);
const rim = new THREE.DirectionalLight(0x36d9e0, .9); rim.position.set(220, 200, 120); scene.add(rim);
const floor = new THREE.Mesh(new THREE.PlaneGeometry(2000, 2000), new THREE.ShadowMaterial({ opacity: .35 }));
floor.receiveShadow = true; floor.position.z = -.01; scene.add(floor);
const grid = new THREE.GridHelper(600, 30, 0x2a333d, 0x222a32); grid.rotation.x = Math.PI / 2; scene.add(grid);
const loader = new STLLoader(), mesh = {};
function b64(s) { const b = atob(s), a = new Uint8Array(b.length); for (let i = 0; i < b.length; i++) a[i] = b.charCodeAt(i); return a.buffer; }
const MAT = {
  shell: new THREE.MeshStandardMaterial({ color: 0xc4c8cd, roughness: .55, metalness: .02 }),
  base: new THREE.MeshStandardMaterial({ color: 0x3a414a, roughness: .7 }),
  caps: new THREE.MeshStandardMaterial({ color: 0x2e3742, roughness: .5 }),
  pi: new THREE.MeshStandardMaterial({ color: 0x2f8a4e, roughness: .6 }),
};
for (const n of ["shell", "base", "caps", "pi"]) { if (!DATA[n]) continue;
  const g = loader.parse(b64(DATA[n])); g.computeVertexNormals();
  const m = new THREE.Mesh(g, MAT[n]); m.castShadow = m.receiveShadow = true; mesh[n] = m; scene.add(m);
}
if (mesh.pi) mesh.pi.visible = false;
// two-tone shell: below the waist groove the dark filament (printed upside down = a filament change at that layer);
// drawn as two clipped copies so the colour line is sharp
{ r.localClippingEnabled = true;
  const ZB = P.BAND - .6;
  MAT.shell.clippingPlanes = [new THREE.Plane(new THREE.Vector3(0, 0, 1), -ZB)];
  const dark = new THREE.MeshStandardMaterial({ color: 0x2e3742, roughness: .6, clippingPlanes: [new THREE.Plane(new THREE.Vector3(0, 0, -1), ZB)] });
  const low = new THREE.Mesh(mesh.shell.geometry, dark); low.castShadow = low.receiveShadow = true; mesh.shell.add(low); MAT.dark = dark; mesh.low = low; }
// the shells to swap: the passive or the active-cooler roof, the 5 mm LED's tube or the RGB pixel's slot
const SH = { shell: mesh.shell.geometry };
for (const n of Object.keys(DATA)) if (/^shell-/.test(n)) { const g = loader.parse(b64(DATA[n])); g.computeVertexNormals(); SH[n] = g; }
// the universal case: a panel set and a ghost per board, two front panels, the active roof
const U = P.models ? {} : null;
if (U) {
  // panels print standing with the shell's filament change: the same two colours, the same line; they stand on the
  // base, so they stay put when the shell is lifted off
  const ZP = P.BAND - .6;
  MAT.panel = new THREE.MeshStandardMaterial({ color: 0xc4c8cd, roughness: .55, clippingPlanes: [new THREE.Plane(new THREE.Vector3(0, 0, 1), -ZP)] });
  MAT.panelDark = new THREE.MeshStandardMaterial({ color: 0x2e3742, roughness: .6, clippingPlanes: [new THREE.Plane(new THREE.Vector3(0, 0, -1), ZP)] });
  MAT.metal = new THREE.MeshStandardMaterial({ color: 0xb8bec4, roughness: .35, metalness: .8 });
  for (const n of Object.keys(DATA)) if (/^(set-|front-|pi-|usb-)/.test(n)) {
    const g = loader.parse(b64(DATA[n])); g.computeVertexNormals();
    const ghost = /^(pi-|usb-)/.test(n);
    const m = new THREE.Mesh(g, n.startsWith("pi-") ? MAT.pi : ghost ? MAT.metal : MAT.panel); m.castShadow = m.receiveShadow = true;
    if (!ghost) { const lo = new THREE.Mesh(g, MAT.panelDark); lo.castShadow = lo.receiveShadow = true; m.add(lo); }
    m.visible = false; U[n] = m; scene.add(m);
  }
}
let model = q.m || "pi4", front = q.front || "blank", roof = q.roof === "active", piOn = false, rgb = q.led === "rgb", standby = false, cwKey = CW[0][0];
function setShell() {
  const g = SH["shell" + (U && roof ? "-active" : "") + (rgb ? "-rgb" : "")] || SH.shell;
  mesh.shell.geometry = g; mesh.low.geometry = g;
  document.getElementById("rg").classList.toggle("on", rgb); setStandby(standby);
}
function setU() {
  if (!U) return;
  for (const k of Object.keys(U)) if (U[k].isMesh) U[k].visible = false;
  U[front === "usb" ? `set-${model}-front` : `set-${model}`].visible = true; U["front-" + front].visible = true;
  if (U["usb-sockets"]) U["usb-sockets"].visible = front === "usb";
  mesh.pi = U["pi-" + model]; mesh.pi.visible = piOn;
  setShell();
  document.querySelectorAll("[data-m]").forEach(b => b.classList.toggle("on", b.dataset.m === model));
  document.getElementById("fu").classList.toggle("on", front === "usb"); document.getElementById("ar").classList.toggle("on", roof);
}
if (U) {
  document.getElementById("um").innerHTML = Object.entries(P.models).map(([k, v]) => `<button data-m="${k}">${v}</button>`).join("")
    + `<button id="fu">Front USB</button><button id="ar">Active roof</button>`;
  document.querySelectorAll("[data-m]").forEach(b => b.onclick = () => { model = b.dataset.m; setU(); showBottom(); });
  document.getElementById("fu").onclick = () => { front = front === "usb" ? "blank" : "usb"; setU(); };
  document.getElementById("ar").onclick = () => { roof = !roof; setU(); };
}
// the front LED behind its clear lens, lit
if (DATA.lens) { const g = loader.parse(b64(DATA.lens)); g.computeVertexNormals();
  MAT.lens = new THREE.MeshStandardMaterial({ color: 0x1a1a1a, emissive: 0x3cff6e, emissiveIntensity: 1.4, roughness: .3 });
  mesh.shell.add(new THREE.Mesh(g, MAT.lens)); }
// the LED: green while running; in standby the 5 mm LED goes dark, the RGB pixel turns orange (like the PlayStation Classic)
function setStandby(on) { standby = on; if (MAT.lens) MAT.lens.emissive.set(on ? (rgb ? 0xff8a1e : 0x000000) : 0x3cff6e);
  document.getElementById("sb").classList.toggle("on", on); }
// stickers as decals on the recesses (when the sticker art exists)
const tl = new THREE.TextureLoader(), TEX = {}, DEC = {};
function tex(key) { if (!TEX[key]) { const t = tl.load("data:image/png;base64," + DECO[key]); t.colorSpace = THREE.SRGBColorSpace;
  t.anisotropy = 8; TEX[key] = t; } return TEX[key]; }
function decal(name, w, h, pos, bx, by, parent) {
  if (!DECO[name]) return null;
  const t = tex(name);
  const m = new THREE.Mesh(new THREE.PlaneGeometry(w, h), new THREE.MeshStandardMaterial({ map: t, transparent: true, roughness: .4 }));
  const X = new THREE.Vector3(...bx), Y = new THREE.Vector3(...by), Z = new THREE.Vector3().crossVectors(X, Y);
  m.quaternion.setFromRotationMatrix(new THREE.Matrix4().makeBasis(X, Y, Z)); m.position.set(...pos); (parent || mesh.shell).add(m); m.userData.key = name; DEC[name] = m; return m;
}
// read from the front of the console: text runs along -x, "up" on the roof is -y (away from the viewer)
decal("sticker-top", P.top.w, P.top.h, P.top.c, [-1, 0, 0], [0, -1, 0]);
decal("sticker-front", P.front.w, P.front.h, P.front.c, [-1, 0, 0], [0, 0, 1]);
// the vent side (x = 0): read standing beside it - text along -y; the underside: text along +x, "up" towards the back
if (P.side) decal("sticker-side", P.side.w, P.side.h, P.side.c, [0, -1, 0], [0, 0, 1]);
const BOT = {};
if (P.bottom) for (const [k, n] of Object.entries(P.bottoms)) {
  BOT[k] = decal(n, P.bottom.w, P.bottom.h, P.bottom.c, [1, 0, 0], [0, -1, 0], mesh.base); if (BOT[k]) BOT[k].visible = false; }
function showBottom() { for (const [k, m] of Object.entries(BOT)) if (m) m.visible = k === model; }
const C = new THREE.Vector3(P.W / 2, P.D / 2, P.H / 2.2);
const VIEWS = { iso: [-150, 260, 190], front: [70, 380, 60], back: [70, -300, 60], right: [380, 52, 70], top: [70, 60, 400],
  left: [-240, 52, 30], under: [70, -10, -300] };
// a light from below, only for the underside view (the room's lights all come from above)
const below = new THREE.DirectionalLight(0xffffff, 2.4); below.position.set(40, 120, -300); below.visible = false; scene.add(below);
function view(v) {
  const p = VIEWS[v] || VIEWS.iso; ctl.maxPolarAngle = v === "under" ? Math.PI : Math.PI * .62;
  floor.visible = grid.visible = v !== "under"; below.visible = v === "under";
  cam.position.set(p[0], p[1], p[2]); ctl.target.copy(C); ctl.update();
  document.querySelectorAll("[data-v]").forEach(b => b.classList.toggle("on", b.dataset.v === v));
}
let ex = false, xr = false;
function setEx(on) { ex = on; mesh.shell.position.z = on ? 55 : 0; const zc = P.BAND - .6 + (on ? 55 : 0);
  MAT.shell.clippingPlanes[0].constant = -zc; MAT.dark.clippingPlanes[0].constant = zc; mesh.caps.position.y = on ? 22 : 0; mesh.caps.position.z = on ? 55 : 0;
  document.getElementById("ex").classList.toggle("on", on); }
function setPi(on) { piOn = on; mesh.pi.visible = on; document.getElementById("pi").classList.toggle("on", on); }
function setXr(on) { xr = on; for (const m of [MAT.shell, MAT.dark, MAT.panel, MAT.panelDark].filter(Boolean)) { m.transparent = on; m.opacity = on ? .28 : 1; m.depthWrite = !on; m.needsUpdate = true; }
  document.getElementById("xr").classList.toggle("on", on); if (on) setPi(true); }
document.querySelectorAll("[data-v]").forEach(b => b.onclick = () => view(b.dataset.v));
document.getElementById("ex").onclick = () => setEx(!ex);
document.getElementById("pi").onclick = () => setPi(!mesh.pi.visible);
document.getElementById("xr").onclick = () => setXr(!xr);
document.getElementById("sb").onclick = () => setStandby(!standby);
document.getElementById("rg").onclick = () => { rgb = !rgb; setShell(); };
function colorway(key) {
  const c = CW.find(x => x[0] === key) || CW[0]; cwKey = c[0];
  MAT.shell.color.set("#" + c[2]); MAT.dark.color.set("#" + c[3]); if (MAT.panel) { MAT.panel.color.set("#" + c[2]); MAT.panelDark.color.set("#" + c[3]); } MAT.base.color.set("#" + c[4]); MAT.caps.color.set("#" + c[5]);
  const set = c[6] ? c[6] + "/" : "";                      // a colourway may bring its own sticker set
  for (const [n, m] of Object.entries(DEC)) { const k = DECO[set + n] ? set + n : n;
    if (m.userData.key !== k) { m.material.map = tex(k); m.material.needsUpdate = true; m.userData.key = k; } }
  document.querySelectorAll("#cw button").forEach(b => b.classList.toggle("on", b.dataset.k === c[0]));
}
document.getElementById("cw").innerHTML = CW.map(c => `<button data-k="${c[0]}" title="${c[1]}" style="display:flex;gap:6px;align-items:center">`
  + `<i style="width:12px;height:12px;border-radius:2px;background:#${c[2]};box-shadow:inset 0 -5px 0 #${c[3]}"></i>${c[1]}</button>`).join("");
document.querySelectorAll("#cw button").forEach(b => b.onclick = () => colorway(b.dataset.k));
colorway(q.cw || "classic");
document.getElementById("hint").textContent += ` · ${P.hint || "Raspberry Pi 3B/3B+"} · ${P.W} x ${P.D} x ${P.H} mm`;
setU(); setShell(); showBottom();
view(q.view || "iso"); if (q.explode) setEx(true); if (q.pi) setPi(true); if (q.xray) setXr(true); if (q.standby) setStandby(true);
// ---- Download ZIP: only the files that print the option on screen, and a note with its settings. The zip is built
// here (stored, no compression - the 3MFs and PNGs are compressed already), so the page needs no server
function pick() {
  const c = CW.find(x => x[0] === cwKey), set = c[6] ? `stickers/${c[6]}/` : "stickers/";
  const shell = (U ? "uni-shell" + (roof ? "-active" : "") : "shell") + (rgb ? "-rgb" : "");
  const f = ["README.md", `3mf/ableemstation-${shell}.3mf`, `3mf/ableemstation-${U ? "uni-base" : "base"}.3mf`,
    "3mf/ableemstation-button.3mf", "3mf/ableemstation-lens.3mf", `wiring/${rgb ? "wiring-rgb" : "wiring"}.png`];
  if (U) for (const ears of ["", "-ears"])                 // each panel plain and with its breakaway ears
    f.push(`3mf/ableemstation-panel-back-${model}${ears}.3mf`, `3mf/ableemstation-panel-right-${model}${front === "usb" ? "-front" : ""}${ears}.3mf`,
      `3mf/ableemstation-panel-front-${front}${ears}.3mf`);
  f.push(...Object.keys(PACK).filter(k => k.startsWith("orca/")));
  for (const n of ["sticker-top", "sticker-front"].concat(U ? ["sticker-side", P.bottoms[model]] : []))
    f.push(set + n + ".svg", set + n + ".png", `${set}cricut-144dpi/ableemstation-${n}.png`);
  f.push(set + "ableemstation-stickers-A4.pdf", set + "ableemstation-stickers-A4-preview.png");
  const miss = f.filter(k => !PACK[k]); if (miss.length) console.warn("not in the page:", miss);
  return f.filter(k => PACK[k]);
}
function zipName() { return `ableemstation-${U ? `${model}-${front === "usb" ? "usb" : "blank"}-${roof ? "active" : "passive"}` : "pi3"}-${rgb ? "rgb" : "led"}-${cwKey}.zip`; }
function note(names) {
  const c = CW.find(x => x[0] === cwKey), L = P.layer_change_mm, PC = P.panel_change_mm, M = U ? P.models[model] : "Raspberry Pi 3B / 3B+";
  const has = s => names.filter(n => n.startsWith("3mf/") && n.includes(s)).map(n => "  " + n.slice(4)).join("\n");
  const S = [
    [`ABleemStation${U ? " universal" : ""} - your build`, "",
     `Board:   ${M}`, ...(U ? [`Front:   ${front === "usb" ? "2 x USB-A (the front-usb panel, the sockets on the base)" : "blank panel"}`,
       `Roof:    ${roof ? "active - over the Raspberry Pi 5 Active Cooler" : "passive (hidden vents)"}`] : []),
     `Light:   ${rgb ? "RGB pixel (one WS2812B cut from a 5 V, 10 mm strip)" : "5 mm diffused LED"}`, `Colours: ${c[1]}`],
    ["PRINT (no supports; README.md has the details)",
     `- shell, roof down, profile "ABleemStation - ASA". Filament change at ${L["0.16"].toFixed(2)} mm (0.16 mm layers) / ${L["0.24"].toFixed(2)} mm (0.24 mm):`,
     "  the top colour first, the band colour after the change.", has("shell"),
     ...(U ? [`- panels, standing on their bottom edge, "ABleemStation - ASA", with a brim. Filament change at ${PC["0.16"].toFixed(2)} mm / ${PC["0.24"].toFixed(2)} mm:`,
       "  the band colour first, the top colour after the change. The -ears files are the same panels with breakaway ears",
       "  that hold them upright: bend them off cold, trim the bridges flush (README).", has("panel-")] : []),
     `- base, flat, standoffs up, "ABleemStation - ASA Base".`, has("base"),
     `- button x 2, standing on the flange, "ABleemStation - ASA".`, "- lens x 1, clear PETG, standing on the flange, 100 % infill, slow."],
    ["COLOURS (the nearest ASA you can get)",
     `  top #${c[2]}   band (below the colour line) #${c[3]}   base #${c[4]}   buttons #${c[5]}   lens: clear PETG`],
    ["ORCA: orca/ - the process profiles (import them, or copy the .json + .info pairs into Orca's user process folder).",
     `  "ABleemStation - ASA Prototype" is a fast print that still answers "does it fit".`],
    [`STICKERS: stickers/${c[6] ? " (the special edition set)" : ""} - print the A4 PDF at 100 % on vinyl, or use the cricut-144dpi PNGs.`,
     ...(U ? [`  The bottom plate is the ${M} one: write the serial number in with a permanent marker before you stick it on.`] : [])],
    [`WIRING: wiring/${rgb ? "wiring-rgb" : "wiring"}.png`,
     rgb ? "  RGB pixel: 5V (pin 2), GND (pin 6), DIN <- 330 ohm <- GPIO10 (pin 19); config.txt: dtparam=spi=on"
         : "  LED: GPIO14 (pin 8) -> 330 ohm -> LED -> GND (pin 6); config.txt: enable_uart=1",
     "  POWER: " + (U && model === "pi5" ? "to the board's J2 pads (GPIO3 cannot wake a Pi 5)" : "GPIO3 (pin 5) + GND (pin 9); config.txt: dtoverlay=gpio-shutdown"),
     "  RESET: GPIO23 (pin 16) + GND (pin 20); config.txt: dtoverlay=gpio-key,gpio=23,active_low=1,gpio_pull=up,keycode=164"],
    ["PARTS FOR THIS OPTION (the full list: README.md, Parts)",
     "  4 x M3 heat-set insert, 4 x M3 x 8 countersunk, 4 x M2.5 x 5, 2 x 6 x 6 mm tactile switch (5 mm), 4 rubber feet, jumper wires",
     rgb ? "  1 x WS2812B pixel + 330 ohm resistor" : "  1 x 5 mm diffused LED + 330 ohm resistor (100 ohm for blue / white / cyan)",
     ...(U && front === "usb" ? ["  2 x USB-A female socket, THT 180 degrees, + a 4-wire cable each"] : []),
     ...(U && roof ? [`  Raspberry Pi 5 Active Cooler${model === "pi5" ? "" : " (the active roof is made for it - a " + M + " does not need it)"}`] : [])],
    ["FILES IN THIS ZIP", ...names.map(n => "  " + n)]];
  return S.map(s => s.join("\n")).join("\n\n") + "\n";
}
const CRC = new Uint32Array(256).map((_, n) => { let c = n; for (let k = 0; k < 8; k++) c = c & 1 ? 0xEDB88320 ^ (c >>> 1) : c >>> 1; return c >>> 0; });
function crc32(a) { let c = 0xFFFFFFFF; for (let i = 0; i < a.length; i++) c = CRC[(c ^ a[i]) & 255] ^ (c >>> 8); return (c ^ 0xFFFFFFFF) >>> 0; }
function zip(files) {                                      // [[name, Uint8Array]] -> a zip Blob (stored entries, UTF-8 names)
  const enc = new TextEncoder(), out = [], cd = []; let off = 0;
  const d = new Date(), dt = ((d.getFullYear() - 1980) << 9) | ((d.getMonth() + 1) << 5) | d.getDate(),
    tm = (d.getHours() << 11) | (d.getMinutes() << 5) | (d.getSeconds() >> 1);
  const put = (v, fields) => fields.forEach(([o, x, s]) => s === 4 ? v.setUint32(o, x, true) : v.setUint16(o, x, true));
  for (const [name, data] of files) {
    const n = enc.encode(name), c = crc32(data), h = new DataView(new ArrayBuffer(30)), e = new DataView(new ArrayBuffer(46));
    put(h, [[0, 0x04034b50, 4], [4, 20, 2], [6, 0x0800, 2], [10, tm, 2], [12, dt, 2], [14, c, 4], [18, data.length, 4],
      [22, data.length, 4], [26, n.length, 2]]);
    put(e, [[0, 0x02014b50, 4], [4, 20, 2], [6, 20, 2], [8, 0x0800, 2], [12, tm, 2], [14, dt, 2], [16, c, 4], [20, data.length, 4],
      [24, data.length, 4], [28, n.length, 2], [42, off, 4]]);
    out.push(h, n, data); cd.push(e, n); off += 30 + n.length + data.length;
  }
  const size = cd.reduce((s, x) => s + x.byteLength, 0), end = new DataView(new ArrayBuffer(22));
  put(end, [[0, 0x06054b50, 4], [8, files.length, 2], [10, files.length, 2], [12, size, 4], [16, off, 4]]);
  return new Blob([...out, ...cd, end], { type: "application/zip" });
}
function buildZip() {
  const files = pick().map(k => [k.replace(/^stickers\/special\//, "stickers/"), new Uint8Array(b64(PACK[k]))]);
  files.unshift(["BUILD.txt", new TextEncoder().encode(note(files.map(x => x[0])))]);
  return zip(files);
}
document.getElementById("zp").onclick = () => {
  const a = document.createElement("a"); a.href = URL.createObjectURL(buildZip()); a.download = zipName();
  document.body.appendChild(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(a.href), 5000);
};
// self-test (#zipcheck=1): the zip goes into the page as base64, for make_viewer's check
if (q.zipcheck) buildZip().arrayBuffer().then(b => { const u = new Uint8Array(b); let s = "";
  for (let i = 0; i < u.length; i += 32768) s += String.fromCharCode(...u.subarray(i, i + 32768));
  const p = document.createElement("pre"); p.id = "zipcheck"; p.dataset.name = zipName(); p.textContent = btoa(s); document.body.appendChild(p); });
addEventListener("resize", () => { cam.aspect = innerWidth / innerHeight; cam.updateProjectionMatrix(); r.setSize(innerWidth, innerHeight); });
(function loop() { ctl.update(); r.render(scene, cam); requestAnimationFrame(loop); })();
</script></body></html>"""

import json  # noqa: E402
open(PAGE, "w", encoding="utf-8", newline="\n").write(HTML.replace("__DATA__", json.dumps(stl)).replace("__DECO__", json.dumps(deco)).replace("__PARAMS__", json.dumps(prm)).replace("__COLORS__", json.dumps(COLORWAYS)).replace("__PACK__", json.dumps(pack)))
print("viewer:", PAGE)

# the download check: the page builds the zip of one option, headless Chrome dumps it, and every file in it must be
# readable and the same bytes as its source
import io, re, zipfile  # noqa: E401,E402
for hashq in (("m=pi5&front=usb&roof=active&led=rgb&cw=grey94", "m=pi23&cw=classic") if VARIANT else ("led=rgb&cw=grey94", "cw=classic")):
    dom = subprocess.run([CHROME, "--headless=new", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--virtual-time-budget=15000",
                          "--dump-dom", "file:///" + PAGE.replace("\\", "/") + "#zipcheck=1&shot=1&" + hashq],
                         check=True, capture_output=True, text=True, encoding="utf-8").stdout
    m = re.search(r'<pre id="zipcheck" data-name="([^"]+)">([A-Za-z0-9+/=]+)</pre>', dom)
    assert m, "the page built no zip for #" + hashq
    z = zipfile.ZipFile(io.BytesIO(base64.b64decode(m.group(2))))
    assert z.testzip() is None, "a damaged file in the zip"
    names = z.namelist()
    for n in names:
        src = [k for k in pack if k == n or k == n.replace("stickers/", "stickers/special/", 1)]
        if n != "BUILD.txt":
            assert any(base64.b64decode(pack[k]) == z.read(n) for k in src), "zip entry differs from its source: " + n
    assert sum(n.startswith("3mf/") for n in names) >= (10 if VARIANT else 4) and "BUILD.txt" in names, names
    print("zip %s: %d files, %.1f MB" % (m.group(1), len(names), len(base64.b64decode(m.group(2))) / 1e6))

shots = os.path.join(OUT, "renders")
os.makedirs(shots, exist_ok=True)
SHOTS = (("1-iso", "view=iso"), ("2-front", "view=front"), ("3-back", "view=back"), ("4-right", "view=right"),
         ("5-exploded", "view=iso&explode=1&pi=1"), ("6-xray", "view=iso&xray=1"), ("7-front-standby", "view=front&standby=1&led=rgb"))
if VARIANT:
    SHOTS = (("1-iso", "view=iso"), ("2-back-pi23", "view=back&m=pi23"), ("3-back-pi4", "view=back&m=pi4"),
             ("4-back-pi5", "view=back&m=pi5"), ("5-right-pi23", "view=right&m=pi23"), ("6-right-pi4", "view=right&m=pi4"),
             ("7-front-usb", "view=front&front=usb"), ("8-exploded", "view=iso&explode=1&pi=1&m=pi5&roof=active&front=usb"),
             ("9-xray-active", "view=iso&xray=1&m=pi5&roof=active"), ("10-top-active", "view=top&roof=active"),
             ("11-side-stickers", "view=left"), ("12-bottom-sticker", "view=under&m=pi4"))
for name, hashq in SHOTS:
    png = os.path.join(shots, name + ".png")
    subprocess.run([CHROME, "--headless=new", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--hide-scrollbars",
                    "--window-size=1280,800", "--virtual-time-budget=8000", "--screenshot=" + png,
                    "file:///" + PAGE.replace("\\", "/") + "#" + hashq + "&shot=1"],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("render:", png)

if VARIANT:
    # the sticker placement sheet: where each sticker goes, with the stickers themselves
    from PIL import Image, ImageDraw, ImageFont  # noqa: E402
    try:
        fb = ImageFont.truetype(os.path.join(HERE, "fonts", "RedHatText-SemiBold.ttf"), 30)
        fs = ImageFont.truetype(os.path.join(HERE, "fonts", "RedHatText-Medium.ttf"), 22)
    except OSError:
        fb = fs = ImageFont.load_default()
    shots_ = [("1-iso", "1 roof + 2 front: in their recesses"), ("11-side-stickers", "3 side: on the dark band, the vent side"),
              ("12-bottom-sticker", "4 bottom: on the base, between the feet")]
    tiles = [(Image.open(os.path.join(shots, n + ".png")).convert("RGB").crop((190, 110, 1090, 710)), t) for n, t in shots_]
    stk = os.path.join(FILES, "stickers")
    names = [("sticker-top", "1 roof - 61 x 17 mm"), ("sticker-front", "2 front - 43 x 4.6 mm"), ("sticker-side", "3 side - 80 x 8 mm"),
             ("sticker-bottom", "4 bottom, Pi 2 / 3 - 54 x 34"), ("sticker-bottom-pi4", "4 bottom, Pi 4"), ("sticker-bottom-pi5", "4 bottom, Pi 5")]
    sheet = Image.new("RGB", (2760, 1400), (22, 27, 33))
    d = ImageDraw.Draw(sheet)
    d.text((40, 30), "ABleemStation universal - the stickers and where they go", font=fb, fill=(238, 243, 246))
    for i, (im, t) in enumerate(tiles):
        sheet.paste(im, (40 + i * 910, 90))
        d.text((40 + i * 910, 700), t, font=fs, fill=(54, 217, 224))
    x, y = 40, 780
    for n, t in names:
        im = Image.open(os.path.join(stk, n + ".png")).convert("RGBA")
        sc = 300 / im.height if "bottom" in n else (130 / im.height if im.height * 4 > im.width else 440 / im.width)
        im = im.resize((round(im.width * sc), round(im.height * sc)), Image.LANCZOS)
        if n == "sticker-bottom":                      # the three rating plates on a row of their own
            x, y = 40, 1010
        sheet.paste(im, (x, y), im)
        d.text((x, y + im.height + 12), t, font=fs, fill=(147, 163, 179))
        x += im.width + 60
    sheet.save(os.path.join(OUT, "sticker-placement.png"), optimize=True)
    print("placement:", os.path.join(OUT, "sticker-placement.png"))
    sys.exit(0)
# one 3/4 render per colourway + a sheet with all of them
from PIL import Image, ImageDraw, ImageFont  # noqa: E402
cdir = os.path.join(shots, "colors")
os.makedirs(cdir, exist_ok=True)
tiles = []
for key, label, *_rest in COLORWAYS:
    png = os.path.join(cdir, key + ".png")
    subprocess.run([CHROME, "--headless=new", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--hide-scrollbars",
                    "--window-size=1280,800", "--virtual-time-budget=8000", "--screenshot=" + png,
                    "file:///" + PAGE.replace("\\", "/") + "#view=iso&cw=" + key + "&shot=1"],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    tiles.append((label, Image.open(png).convert("RGB").crop((240, 130, 1040, 730)).resize((560, 420), Image.LANCZOS)))
font_dir = os.path.join(HERE, "fonts")
try:
    fnt = ImageFont.truetype(os.path.join(font_dir, "RedHatText-SemiBold.ttf"), 24)
except OSError:
    fnt = ImageFont.load_default()
cols = 4
sheet = Image.new("RGB", (cols * 560, ((len(tiles) + cols - 1) // cols) * 470), (22, 27, 33))
d = ImageDraw.Draw(sheet)
for i, (label, im) in enumerate(tiles):
    x, y = (i % cols) * 560, (i // cols) * 470
    sheet.paste(im, (x, y))
    d.text((x + 280, y + 432), label, font=fnt, fill=(238, 243, 246), anchor="mm")
sheet.save(os.path.join(shots, "colorways.png"), optimize=True)
print("colourways:", os.path.join(shots, "colorways.png"))
