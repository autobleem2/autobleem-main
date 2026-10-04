"""ABleemStation: a self-contained WebGL viewer (three.js from jsDelivr, the case STLs inlined as base64) + quick renders.
The page works by double-click. Hash options: #view=front|back|right|top|iso, &explode=1, &pi=1, &shot=1 (no UI).
Renders: headless Chrome screenshots of the same page into ../files/renders/. Run after make_case.py and
make_stickers.py:  python make_viewer.py
The universal case (make_universal.py):  python make_viewer.py universal  - the same page with the board (&m=pi23|pi4|pi5),
the front panel (&front=usb|blank) and the roof (&roof=active) to pick, into ../files/universal/."""
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
]
stl = {f[:-4]: base64.b64encode(open(os.path.join(VIEW, f), "rb").read()).decode()
       for f in sorted(os.listdir(VIEW)) if f.endswith(".stl")}
import json as _j
prm = _j.load(open(os.path.join(VIEW, "params.json")))
deco = {}
for n in ("sticker-top", "sticker-front"):
    p = os.path.join(FILES, "stickers", n + ".png")
    if os.path.exists(p):
        deco[n] = base64.b64encode(open(p, "rb").read()).decode()

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
.hint{position:absolute;left:16px;bottom:12px;color:var(--dim);font-size:12px}
body.shot .ui,body.shot .hint{display:none}
</style>
<script type="importmap">{"imports":{"three":"https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js","three/addons/":"https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/"}}</script>
</head><body>
<div class="ui"><b>ABleemStation</b>
<button data-v="iso" class="on">3/4</button><button data-v="front">Front</button><button data-v="back">Back</button>
<button data-v="right">Right</button><button data-v="top">Top</button>
<span id="um" style="display:contents"></span><button id="ex">Explode</button><button id="pi">Show Pi</button><button id="xr">X-ray</button><button id="sb">LED: standby</button><span id="cw" style="display:flex;gap:6px;flex-wrap:wrap"></span></div>
<div class="hint" id="hint">Drag to orbit · wheel to zoom</div>
<script type="module">
import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { STLLoader } from "three/addons/loaders/STLLoader.js";
const DATA = __DATA__, DECO = __DECO__, P = __PARAMS__, CW = __COLORS__;
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
// the universal case: a panel set and a ghost per board, two front panels, the active roof
const U = P.models ? {} : null;
if (U) {
  // panels print standing with the shell's filament change: the same two colours, the same line; they stand on the
  // base, so they stay put when the shell is lifted off
  const ZP = P.BAND - .6;
  MAT.panel = new THREE.MeshStandardMaterial({ color: 0xc4c8cd, roughness: .55, clippingPlanes: [new THREE.Plane(new THREE.Vector3(0, 0, 1), -ZP)] });
  MAT.panelDark = new THREE.MeshStandardMaterial({ color: 0x2e3742, roughness: .6, clippingPlanes: [new THREE.Plane(new THREE.Vector3(0, 0, -1), ZP)] });
  MAT.metal = new THREE.MeshStandardMaterial({ color: 0xb8bec4, roughness: .35, metalness: .8 });
  for (const n of Object.keys(DATA)) if (/^(set-|front-|pi-|usb-|shell-active)/.test(n)) {
    const g = loader.parse(b64(DATA[n])); g.computeVertexNormals();
    if (n === "shell-active") { U.active = g; continue; }
    const ghost = /^(pi-|usb-)/.test(n);
    const m = new THREE.Mesh(g, n.startsWith("pi-") ? MAT.pi : ghost ? MAT.metal : MAT.panel); m.castShadow = m.receiveShadow = true;
    if (!ghost) { const lo = new THREE.Mesh(g, MAT.panelDark); lo.castShadow = lo.receiveShadow = true; m.add(lo); }
    m.visible = false; U[n] = m; scene.add(m);
  }
  U.passive = mesh.shell.geometry;
}
let model = q.m || "pi4", front = q.front || "blank", roof = q.roof === "active", piOn = false;
function setU() {
  if (!U) return;
  for (const k of Object.keys(U)) if (U[k].isMesh) U[k].visible = false;
  U[front === "usb" ? `set-${model}-front` : `set-${model}`].visible = true; U["front-" + front].visible = true;
  if (U["usb-sockets"]) U["usb-sockets"].visible = front === "usb";
  mesh.pi = U["pi-" + model]; mesh.pi.visible = piOn;
  const g = roof ? U.active : U.passive; mesh.shell.geometry = g; mesh.low.geometry = g;
  document.querySelectorAll("[data-m]").forEach(b => b.classList.toggle("on", b.dataset.m === model));
  document.getElementById("fu").classList.toggle("on", front === "usb"); document.getElementById("ar").classList.toggle("on", roof);
}
if (U) {
  document.getElementById("um").innerHTML = Object.entries(P.models).map(([k, v]) => `<button data-m="${k}">${v}</button>`).join("")
    + `<button id="fu">Front USB</button><button id="ar">Active roof</button>`;
  document.querySelectorAll("[data-m]").forEach(b => b.onclick = () => { model = b.dataset.m; setU(); });
  document.getElementById("fu").onclick = () => { front = front === "usb" ? "blank" : "usb"; setU(); };
  document.getElementById("ar").onclick = () => { roof = !roof; setU(); };
}
// the front LED behind its clear lens, lit
if (DATA.lens) { const g = loader.parse(b64(DATA.lens)); g.computeVertexNormals();
  MAT.lens = new THREE.MeshStandardMaterial({ color: 0x1a1a1a, emissive: 0x3cff6e, emissiveIntensity: 1.4, roughness: .3 });
  mesh.shell.add(new THREE.Mesh(g, MAT.lens)); }
// the LED: green while running, orange in standby (the RGB version shows both, like the PlayStation Classic)
function setStandby(on) { if (MAT.lens) MAT.lens.emissive.set(on ? 0xff8a1e : 0x3cff6e);
  document.getElementById("sb").classList.toggle("on", on); }
// stickers as decals on the recesses (when the sticker art exists)
const tl = new THREE.TextureLoader();
function decal(name, w, h, pos, bx, by) {
  if (!DECO[name]) return;
  const t = tl.load("data:image/png;base64," + DECO[name]); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 8;
  const m = new THREE.Mesh(new THREE.PlaneGeometry(w, h), new THREE.MeshStandardMaterial({ map: t, transparent: true, roughness: .4 }));
  const X = new THREE.Vector3(...bx), Y = new THREE.Vector3(...by), Z = new THREE.Vector3().crossVectors(X, Y);
  m.quaternion.setFromRotationMatrix(new THREE.Matrix4().makeBasis(X, Y, Z)); m.position.set(...pos); mesh.shell.add(m);
}
// read from the front of the console: text runs along -x, "up" on the roof is -y (away from the viewer)
decal("sticker-top", P.top.w, P.top.h, P.top.c, [-1, 0, 0], [0, -1, 0]);
decal("sticker-front", P.front.w, P.front.h, P.front.c, [-1, 0, 0], [0, 0, 1]);
const C = new THREE.Vector3(P.W / 2, P.D / 2, P.H / 2.2);
const VIEWS = { iso: [-150, 260, 190], front: [70, 380, 60], back: [70, -300, 60], right: [380, 52, 70], top: [70, 60, 400] };
function view(v) {
  const p = VIEWS[v] || VIEWS.iso; cam.position.set(p[0], p[1], p[2]); ctl.target.copy(C); ctl.update();
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
document.getElementById("sb").onclick = () => setStandby(!document.getElementById("sb").classList.contains("on"));
function colorway(key) {
  const c = CW.find(x => x[0] === key) || CW[0];
  MAT.shell.color.set("#" + c[2]); MAT.dark.color.set("#" + c[3]); if (MAT.panel) { MAT.panel.color.set("#" + c[2]); MAT.panelDark.color.set("#" + c[3]); } MAT.base.color.set("#" + c[4]); MAT.caps.color.set("#" + c[5]);
  document.querySelectorAll("#cw button").forEach(b => b.classList.toggle("on", b.dataset.k === c[0]));
}
document.getElementById("cw").innerHTML = CW.map(c => `<button data-k="${c[0]}" title="${c[1]}" style="display:flex;gap:6px;align-items:center">`
  + `<i style="width:12px;height:12px;border-radius:2px;background:#${c[2]};box-shadow:inset 0 -5px 0 #${c[3]}"></i>${c[1]}</button>`).join("");
document.querySelectorAll("#cw button").forEach(b => b.onclick = () => colorway(b.dataset.k));
colorway(q.cw || "classic");
document.getElementById("hint").textContent += ` · ${P.hint || "Raspberry Pi 3B/3B+"} · ${P.W} x ${P.D} x ${P.H} mm`;
setU();
view(q.view || "iso"); if (q.explode) setEx(true); if (q.pi) setPi(true); if (q.xray) setXr(true); if (q.standby) setStandby(true);
addEventListener("resize", () => { cam.aspect = innerWidth / innerHeight; cam.updateProjectionMatrix(); r.setSize(innerWidth, innerHeight); });
(function loop() { ctl.update(); r.render(scene, cam); requestAnimationFrame(loop); })();
</script></body></html>"""

import json  # noqa: E402
open(PAGE, "w", encoding="utf-8", newline="\n").write(HTML.replace("__DATA__", json.dumps(stl)).replace("__DECO__", json.dumps(deco)).replace("__PARAMS__", json.dumps(prm)).replace("__COLORS__", json.dumps(COLORWAYS)))
print("viewer:", PAGE)

shots = os.path.join(OUT, "renders")
os.makedirs(shots, exist_ok=True)
SHOTS = (("1-iso", "view=iso"), ("2-front", "view=front"), ("3-back", "view=back"), ("4-right", "view=right"),
         ("5-exploded", "view=iso&explode=1&pi=1"), ("6-xray", "view=iso&xray=1"), ("7-front-standby", "view=front&standby=1"))
if VARIANT:
    SHOTS = (("1-iso", "view=iso"), ("2-back-pi23", "view=back&m=pi23"), ("3-back-pi4", "view=back&m=pi4"),
             ("4-back-pi5", "view=back&m=pi5"), ("5-right-pi23", "view=right&m=pi23"), ("6-right-pi4", "view=right&m=pi4"),
             ("7-front-usb", "view=front&front=usb"), ("8-exploded", "view=iso&explode=1&pi=1&m=pi5&roof=active&front=usb"),
             ("9-xray-active", "view=iso&xray=1&m=pi5&roof=active"), ("10-top-active", "view=top&roof=active"))
for name, hashq in SHOTS:
    png = os.path.join(shots, name + ".png")
    subprocess.run([CHROME, "--headless=new", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--hide-scrollbars",
                    "--window-size=1280,800", "--virtual-time-budget=8000", "--screenshot=" + png,
                    "file:///" + PAGE.replace("\\", "/") + "#" + hashq + "&shot=1"],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("render:", png)

if VARIANT:
    sys.exit(0)
# one 3/4 render per colourway + a sheet with all of them
from PIL import Image, ImageDraw, ImageFont  # noqa: E402
cdir = os.path.join(shots, "colors")
os.makedirs(cdir, exist_ok=True)
tiles = []
for key, label, *_ in COLORWAYS:
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
