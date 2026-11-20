"""Short o Reel vertical con el estilo fijo del canal (ver ESTILO-SHORTS.md).

Uso: python3 -I render_short.py <carpeta_fotos> <voz.mp3> <musica.mp3> <carpeta_fuentes> <salida.mp4>
         --config <carpeta_del_video>/video.json [--facebook] [--portada portada.jpg] [--bloques] [--muestras 1,2,3]

Cada video tiene su carpeta con video.json (frases, fotos, título) y palabras.json (sincronía de alinear.py).
"""
import sys, os, math, re, subprocess, unicodedata
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageChops

FOTOS, VOZ, MUSICA, FUENTES, SALIDA = sys.argv[1:6]
TRABAJO = os.path.join(os.path.dirname(os.path.abspath(SALIDA)), "trabajo-short")
os.makedirs(TRABAJO, exist_ok=True)
W, H, FPS = 1080, 1920, 30
import json
CONFIG_RUTA = sys.argv[sys.argv.index("--config") + 1]
CONFIG = json.load(open(CONFIG_RUTA, encoding="utf-8"))
CARPETA_VIDEO = os.path.dirname(os.path.abspath(CONFIG_RUTA))
FIN_VOZ = CONFIG["fin_voz"]
TARJETA = 5.0                       # «¿Te bendijo esta oración?» al final
DURACION = FIN_VOZ + TARJETA
DORADO, BLANCO = (253, 184, 19), (255, 255, 255)

def F(nombre, px): return ImageFont.truetype(os.path.join(FUENTES, nombre), px)

# ---------- Texto y tiempos de la voz ----------
FRASES = [(t, f) for t, f in CONFIG["frases"]]       # (texto, foto que entra con la frase)

def silabas(p):
    p = unicodedata.normalize("NFD", p.lower()); p = "".join(c for c in p if unicodedata.category(c) != "Mn")
    return max(1, len(re.findall(r"[aeiouy]+", p)))

PALABRAS = json.load(open(os.path.join(CARPETA_VIDEO, "palabras.json"), encoding="utf-8"))
def tiempos_frases():
    """Inicio y fin de cada frase según la sincronía palabra por palabra (alinear.py)."""
    out, k = [], 0
    for txt, _ in FRASES:
        n = len(txt.split()); ws = PALABRAS[k:k + n]; k += n
        out.append((ws[0]["t0"], ws[-1]["t1"]))
    return out
TF = tiempos_frases()

# Subtítulos de 1 a 3 palabras, con la palabra clave en dorado
VACIAS = set("a al ante con de del el en es esta este la las los lo me mi mis nos nuestro nuestra nuestros nuestras o para por que se si sin su sus te ti tu tus un una y ya hoy más mas cada todo aquello estas porque no hemos sino has ha han fue sea seas esté vayan podamos tú tienes primeramente".split())
CLAVE_FIJA = {"dios", "señor", "jesús", "padre", "amén", "espíritu", "escudo", "coraza", "cobertura", "paz", "protección", "ángeles", "gracias"}

def clave(palabras):
    limpio = [re.sub(r"[^\wáéíóúüñÁÉÍÓÚÜÑ]", "", w).lower() for w in palabras]
    for i, w in enumerate(limpio):
        if w in CLAVE_FIJA: return i
    cand = [(len(w), i) for i, w in enumerate(limpio) if w and w not in VACIAS]
    return max(cand)[1] if cand else None

def bloques():
    """Grupos de 1 a 3 palabras que nunca cruzan una pausa de la voz."""
    out, k = [], 0
    for i, (txt, _) in enumerate(FRASES):
        n = len(txt.split()); ws = PALABRAS[k:k + n]; k += n
        if i == 0: continue                      # la primera frase la cubre el título
        grupo = []
        for j, w in enumerate(ws):
            grupo.append(w)
            largo = sum(len(x["w"]) for x in grupo) + len(grupo) - 1
            sig = ws[j + 1] if j + 1 < len(ws) else None
            corte = (len(grupo) >= 3 or largo >= 15 or re.search(r"[,.;:!?»]$", w["w"])
                     or sig is None or sig["tramo"] != w["tramo"])
            if corte:
                out.append({"ws": [x["w"] for x in grupo], "tw": [x["t0"] for x in grupo], "t0": grupo[0]["t0"], "t1": grupo[-1]["t1"] + 0.15, "frase": i})
                grupo = []
    for b in out: b["clave"] = clave(b["ws"])
    return out
BLOQUES = bloques()
for k in range(len(BLOQUES) - 1):           # cada bloque dura hasta que entra el siguiente (sin huecos cortos)
    if BLOQUES[k + 1]["t0"] - BLOQUES[k]["t1"] < 0.5: BLOQUES[k]["t1"] = BLOQUES[k + 1]["t0"]

# ---------- Fotos ----------
# archivo, centro x del recorte, alto relativo, centro y
# clave: [archivo, centro x del recorte, alto relativo, centro y]
FOTO = CONFIG["fotos"]
BW, BH = 1350, 2400
AGUA = CONFIG.get("agua", {})          # clave: altura del horizonte (0 a 1) en fotos con agua

def preparar(clave_):
    ruta = os.path.join(TRABAJO, clave_ + ".jpg")
    if os.path.exists(ruta): return Image.open(ruta).convert("RGB")
    cod, cx, alto, cy = FOTO[clave_]
    im = Image.open(os.path.join(FOTOS, cod)).convert("RGB"); w, h = im.size
    ch = h * alto; cw = ch * 9 / 16
    if cw > w: cw = w; ch = cw * 16 / 9
    x0 = min(max(0, cx * w - cw / 2), w - cw); y0 = min(max(0, cy * h - ch / 2), h - ch)
    im = im.crop((int(x0), int(y0), int(x0 + cw), int(y0 + ch))).resize((BW, BH), Image.LANCZOS)
    im = ImageEnhance.Color(ImageEnhance.Contrast(im).enhance(1.06)).enhance(1.10)
    im.save(ruta, quality=95); return im

CRUCE = 0.8
inicios = [(0.0, "prado")] + [(TF[i][0] - 0.3, f) for i, (_, f) in enumerate(FRASES) if f and f != "prado"]
PLANOS = [(c, t, inicios[k + 1][0] + CRUCE if k + 1 < len(inicios) else DURACION) for k, (t, c) in enumerate(inicios)]
MOV = [("acercar", 0, 0), ("alejar", 1, 0), ("desplazar", 0, 1), ("acercar", -1, 1), ("alejar", 0, -1),
       ("desplazar", 0, -1), ("acercar", 1, -1), ("alejar", -1, 1)]
CACHE = {}
def base(c):
    if c not in CACHE:
        if len(CACHE) > 3: CACHE.clear()
        CACHE[c] = preparar(c)
    return CACHE[c]

def plano(idx, t):
    c, t0, t1 = PLANOS[idx]; im = base(c)
    p = min(1, max(0, (t - t0) / max(.1, t1 - t0))); p = .5 - .5 * math.cos(math.pi * p)
    tipo, dx, dy = MOV[idx % len(MOV)]
    z = 1 + .10 * p if tipo == "acercar" else 1.10 - .10 * p if tipo == "alejar" else 1.08
    bw, bh = BW / (1.25 * z), BH / (1.25 * z); lx, ly = (BW - bw) / 2, (BH - bh) / 2
    if tipo == "desplazar": cx, cy = BW / 2, BH / 2 + ly * .85 * (p - .5) * 2 * (dy or 1)
    else: cx, cy = BW / 2 + lx * .5 * (p - .5) * 2 * dx, BH / 2 + ly * .5 * (p - .5) * 2 * dy
    out = im.resize((W, H), Image.BICUBIC, box=(cx - bw / 2, cy - bh / 2, cx + bw / 2, cy + bh / 2))
    if c in AGUA: out = agua(out, t, (AGUA[c] * BH - (cy - bh / 2)) / bh * H)
    return out

def agua(im, t, horizonte):
    a = np.asarray(im); y0 = int(max(0, min(H - 2, horizonte + 8)))
    ys = np.arange(y0, H); prof = (ys - y0) / max(1, H - y0)
    amp = 1.2 + 8.0 * prof
    sh = amp * np.sin(ys * .07 - t * 2.1) + .5 * amp * np.sin(ys * .023 + t * 1.2)
    xs = (np.arange(W)[None, :] + sh[:, None]).round().astype(np.int32).clip(0, W - 1)
    ag = a[ys[:, None], xs].astype(np.float32)
    br = 1 + (.035 + .05 * prof)[:, None] * np.sin(ys[:, None] * .18 - t * 3 + np.arange(W)[None, :] * .005)
    b = a.copy(); b[y0:] = (ag * br[..., None]).clip(0, 255).astype(np.uint8)
    return Image.fromarray(b)

# ---------- Polvo dorado ----------
rng = np.random.default_rng(7); N = 85
PV = {"x": rng.uniform(0, W, N), "y": rng.uniform(0, H, N), "v": rng.uniform(12, 36, N), "am": rng.uniform(8, 30, N),
      "f": rng.uniform(.08, .25, N), "fa": rng.uniform(0, 6.28, N), "a": rng.uniform(.5, 1, N),
      "r": rng.choice([2.5, 3.5, 4.5, 6, 8, 11], N, p=[.24, .24, .2, .16, .1, .06])}
def _mota(r):
    n = int(r * 4) | 1; c = n // 2; yy, xx = np.mgrid[0:n, 0:n]; d = np.hypot(xx - c, yy - c)
    return np.clip(np.exp(-(d / (r * .9)) ** 2) + .6 * np.exp(-(d / (r * .35)) ** 2), 0, 1)
MOTAS = {r: _mota(r) for r in set(PV["r"].tolist())}
def polvo(im, t):
    A = np.zeros((H, W), np.float32)
    for i in range(N):
        y = (PV["y"][i] - PV["v"][i] * t) % (H + 40) - 20
        x = (PV["x"][i] + PV["am"][i] * math.sin(t * PV["f"][i] * 6.28 + PV["fa"][i])) % W
        tit = .55 + .45 * math.sin(t * (.7 + PV["f"][i] * 4) + PV["fa"][i] * 3)
        m = MOTAS[PV["r"][i]]; n = m.shape[0]; x0, y0 = int(x) - n // 2, int(y) - n // 2
        xa, ya, xb, yb = max(0, x0), max(0, y0), min(W, x0 + n), min(H, y0 + n)
        if xb > xa and yb > ya: A[ya:yb, xa:xb] += m[ya - y0:yb - y0, xa - x0:xb - x0] * PV["a"][i] * tit
    A = np.clip(A, 0, 1)[..., None]; a = np.asarray(im).astype(np.float32)
    return Image.fromarray((a * (1 - A) + np.array([255, 214, 140], np.float32) * A).astype(np.uint8))

# ---------- Texto con el estilo del canal ----------
def capa_texto(lineas, px, y_centro, interlinea=1.12):
    """lineas: lista de listas de (palabra, dorado). Blanco con sombra suave, palabra clave en dorado."""
    f = F("Poppins-ExtraBold.ttf", px)
    d0 = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    esp = d0.textlength(" ", font=f)
    anchos = [sum(d0.textlength(w, font=f) for w, _ in l) + esp * (len(l) - 1) for l in lineas]
    lh = px * interlinea; alto = lh * len(lineas)
    txt = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(txt)
    y = y_centro - alto / 2
    for l, an in zip(lineas, anchos):
        x = (W - an) / 2
        for w, oro in l:
            d.text((x, y), w, font=f, fill=(DORADO if oro else BLANCO) + (255,)); x += d.textlength(w, font=f) + esp
        y += lh
    alfa = txt.getchannel("A")
    sombra = Image.new("RGBA", (W, H), (0, 0, 0, 0)); sombra.putalpha(alfa.filter(ImageFilter.GaussianBlur(7)).point(lambda v: int(v * .85)))
    borde = Image.new("RGBA", (W, H), (20, 20, 30, 0)); borde.putalpha(alfa.filter(ImageFilter.MaxFilter(5)).point(lambda v: int(v * .55)))
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    out.alpha_composite(sombra, (0, 5)); out.alpha_composite(borde); out.alpha_composite(txt)
    return out

def capa_bloque(b):
    ws = [w.upper() for w in b["ws"]]
    linea = [(w, k == b["clave"]) for k, w in enumerate(ws)]
    px = 74
    f = F("Poppins-ExtraBold.ttf", px); d0 = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    while d0.textlength(" ".join(ws), font=f) > 960 and px > 50: px -= 4; f = F("Poppins-ExtraBold.ttf", px)
    return capa_texto([linea], px, H * .55)

FACEBOOK = "--facebook" in sys.argv
PROGRESIVO = "--bloques" not in sys.argv     # estilo fijo: palabra por palabra (usa --bloques para el estilo anterior)

def sprites_bloque(b):
    """Una imagen pequeña por palabra, ya colocada donde va en la línea completa."""
    ws = [w.upper() for w in b["ws"]]; px = 74
    f = F("Poppins-ExtraBold.ttf", px); d0 = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    while d0.textlength(" ".join(ws), font=f) > 960 and px > 50: px -= 4; f = F("Poppins-ExtraBold.ttf", px)
    esp = d0.textlength(" ", font=f); total = sum(d0.textlength(w, font=f) for w in ws) + esp * (len(ws) - 1)
    x = (W - total) / 2; y = H * .55 - px * 1.12 / 2; out = []
    for k, w in enumerate(ws):
        tw = d0.textlength(w, font=f); m = 24
        txt = Image.new("RGBA", (int(tw) + 2 * m, int(px * 1.5) + 2 * m), (0, 0, 0, 0))
        ImageDraw.Draw(txt).text((m, m), w, font=f, fill=(DORADO if k == b["clave"] else BLANCO) + (255,))
        a = txt.getchannel("A")
        sp = Image.new("RGBA", txt.size, (0, 0, 0, 0))
        sombra = Image.new("RGBA", txt.size, (0, 0, 0, 0)); sombra.putalpha(a.filter(ImageFilter.GaussianBlur(7)).point(lambda v: int(v * .85)))
        borde = Image.new("RGBA", txt.size, (20, 20, 30, 0)); borde.putalpha(a.filter(ImageFilter.MaxFilter(5)).point(lambda v: int(v * .55)))
        sp.alpha_composite(sombra, (0, 5)); sp.alpha_composite(borde); sp.alpha_composite(txt)
        out.append((sp, int(x - m), int(y - m), b["tw"][k])); x += tw + esp
    return out

TITULO = Image.new("RGBA", (W, H), (0, 0, 0, 0))
# Título: «ORACIÓN …» pequeño en dorado y el tema en líneas; *palabra* va en dorado
def _linea(txt): return [(w.strip("*"), w.startswith("*")) for w in txt.split()]
TITULO.alpha_composite(capa_texto([_linea(CONFIG["titulo"]["arriba"])], 40, H * .37))
TITULO.alpha_composite(capa_texto([_linea(l) for l in CONFIG["titulo"]["lineas"]], 84, H * .50))
OREMOS = capa_texto([[("O R E M O S", True)]], 80, H * .5)

def emoji(ch, px):
    f = ImageFont.truetype("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf", 109)
    im = Image.new("RGBA", (160, 160), (0, 0, 0, 0)); ImageDraw.Draw(im).text((10, 10), ch, font=f, embedded_color=True)
    im = im.crop(im.getbbox()); r = px / max(im.size)
    return im.resize((int(im.width * r), int(im.height * r)), Image.LANCZOS)

def tarjeta_final():
    capa = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    manos = emoji("🙏", 170).getchannel("A")
    contorno = ImageChops.subtract(manos.filter(ImageFilter.MaxFilter(7)), manos.filter(ImageFilter.MinFilter(5)))
    icono = Image.new("RGBA", manos.size, DORADO + (0,)); icono.putalpha(contorno)
    capa.alpha_composite(icono, ((W - icono.width) // 2, 650))
    capa.alpha_composite(capa_texto([[("¿TE", False), ("BENDIJO", False), ("ESTA", False), ("ORACIÓN?", False)]], 50, 1000))
    botones = []
    b1 = Image.new("RGBA", (580, 128), (0, 0, 0, 0)); d = ImageDraw.Draw(b1)
    # YouTube: «SUSCRÍBETE» en rojo · Facebook (--facebook): «SÍGUEME» en azul
    etiqueta, color = ("SÍGUEME", (24, 119, 242)) if FACEBOOK else ("SUSCRÍBETE", (232, 52, 28))
    d.rounded_rectangle([0, 0, 579, 127], radius=26, fill=color, outline=BLANCO, width=5)
    f = F("Poppins-ExtraBold.ttf", 62); tw = d.textlength(etiqueta, font=f)
    d.text(((580 - tw) / 2, 20), etiqueta, font=f, fill=BLANCO); botones.append((b1, 1085))
    b2 = Image.new("RGBA", (430, 104), (0, 0, 0, 0)); d = ImageDraw.Draw(b2)
    d.rounded_rectangle([0, 0, 429, 103], radius=24, fill=BLANCO, outline=DORADO, width=5)
    pulgar = emoji("👍", 56).getchannel("A"); negro = Image.new("RGBA", pulgar.size, (20, 20, 20, 0)); negro.putalpha(pulgar)
    f = F("Poppins-ExtraBold.ttf", 48); tw = d.textlength("DALE LIKE", font=f); x0 = (430 - (pulgar.width + 14 + tw)) / 2
    b2.alpha_composite(negro, (int(x0), (104 - pulgar.height) // 2)); d.text((x0 + pulgar.width + 14, 18), "DALE LIKE", font=f, fill=(20, 20, 20))
    botones.append((b2, 1250))
    return capa, botones
TARJ, BOTONES = tarjeta_final()

def suave(t, a, b):
    if b <= a: return 1.0 if t >= b else 0.0
    x = min(1, max(0, (t - a) / (b - a))); return x * x * (3 - 2 * x)
def con_alfa(im, a):
    if a >= 1: return im
    c = im.copy(); c.putalpha(c.getchannel("A").point(lambda v: int(v * a))); return c

CAPAS = {}
def cuadro(n):
    t = n / FPS
    act = [i for i, (c, a, b) in enumerate(PLANOS) if a <= t < b]
    i = act[-1]; im = plano(i, t)
    if len(act) > 1:
        j = act[0]; im = Image.blend(plano(j, t), im, suave(t, PLANOS[i][1], PLANOS[j][2]))
    im = polvo(im, t).convert("RGBA")
    # Título y «Oremos»
    a = suave(t, .2, .8) * (1 - suave(t, TF[1][0] - .5, TF[1][0]))
    if a > 0: im.alpha_composite(con_alfa(TITULO, a))
    a = suave(t, TF[1][0], TF[1][0] + .3) * (1 - suave(t, TF[2][0] - .4, TF[2][0]))
    if a > 0: im.alpha_composite(con_alfa(OREMOS, a))
    # Subtítulos
    for k, b in enumerate(BLOQUES):
        if b["frase"] == 1 or not (b["t0"] <= t < b["t1"]): continue
        if PROGRESIVO:          # palabra por palabra, al ritmo de la voz
            if k not in CAPAS:
                if len(CAPAS) > 6: CAPAS.clear()
                CAPAS[k] = sprites_bloque(b)
            for sp, x, y, tw in CAPAS[k]:
                e = suave(t, tw, tw + .14)
                if e <= 0: continue
                if e < 1:
                    s_ = .75 + .25 * e; r = sp.resize((max(1, int(sp.width * s_)), max(1, int(sp.height * s_))), Image.BILINEAR)
                    im.alpha_composite(con_alfa(r, e), (x + (sp.width - r.width) // 2, y + (sp.height - r.height) // 2))
                else:
                    im.alpha_composite(sp, (x, y))
            continue
        if k not in CAPAS:
            if len(CAPAS) > 6: CAPAS.clear()
            CAPAS[k] = capa_bloque(b)
        e = suave(t, b["t0"], b["t0"] + .12)
        capa = CAPAS[k]
        if e < 1:
            s = .88 + .12 * e; cw, ch = int(W * s), int(H * s)
            cc = capa.resize((cw, ch), Image.BILINEAR); capa = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            capa.alpha_composite(cc, ((W - cw) // 2, int(H * .55 - H * .55 * s)))
            capa = con_alfa(capa, e)
        im.alpha_composite(capa)
    # Tarjeta final
    if t >= FIN_VOZ:
        osc = suave(t, FIN_VOZ, FIN_VOZ + .5)
        im.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, int(115 * osc))))
        im.alpha_composite(con_alfa(TARJ, osc))
        for k, (bt, y) in enumerate(BOTONES):
            t0 = FIN_VOZ + .4 + k * .6; e = suave(t, t0, t0 + .25)
            if e <= 0: continue
            s = .6 + .4 * e + .08 * math.sin(min(1, (t - t0) / .45) * math.pi)
            r = bt.resize((int(bt.width * s), int(bt.height * s)), Image.BICUBIC)
            im.alpha_composite(con_alfa(r, e), ((W - r.width) // 2, int(y + (bt.height - r.height) / 2)))
    return im.convert("RGB")

if __name__ == "__main__":
    if "--muestras" in sys.argv:
        for s in [float(x) for x in sys.argv[sys.argv.index("--muestras") + 1].split(",")]:
            cuadro(int(s * FPS)).save(os.path.join(TRABAJO, f"m-{s:06.1f}.jpg"), quality=88)
        for b in BLOQUES[:12]: print(round(b["t0"], 2), round(b["t1"], 2), " ".join(b["ws"]), "| clave:", b["clave"])
        sys.exit(0)
    # Portada al inicio (--portada imagen.jpg [--portada-seg 0.5]): unos cuadros fijos antes del video,
    # para poder elegirla como portada desde la app de YouTube del teléfono. Voz y música empiezan después.
    PORTADA = sys.argv[sys.argv.index("--portada") + 1] if "--portada" in sys.argv else None
    PRE = float(sys.argv[sys.argv.index("--portada-seg") + 1]) if "--portada-seg" in sys.argv else (0.5 if PORTADA else 0.0)
    audio = os.path.join(TRABAJO, "audio.m4a")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", VOZ, "-i", MUSICA, "-filter_complex",
        f"[0:a]apad=whole_dur={DURACION}[v];[1:a]atrim=0:{DURACION},asetpts=PTS-STARTPTS,volume=-21dB,afade=t=in:d=2,"
        f"afade=t=out:st={DURACION-3}:d=3,aformat=channel_layouts=mono[m];"
        f"[v][m]amix=inputs=2:duration=first:normalize=0,adelay={int(PRE*1000)}:all=1,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[a]",
        "-map", "[a]", "-c:a", "aac", "-b:a", "192k", audio], check=True)
    enc = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
        "-r", str(FPS), "-i", "-", "-i", audio, "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "medium",
        "-crf", "19", "-pix_fmt", "yuv420p", "-c:a", "copy", "-shortest", "-movflags", "+faststart", SALIDA], stdin=subprocess.PIPE)
    if PORTADA:
        portada = Image.open(PORTADA).convert("RGB").resize((W, H), Image.LANCZOS).tobytes()
        for _ in range(int(round(PRE * FPS))): enc.stdin.write(portada)
    for n in range(int(DURACION * FPS)):
        enc.stdin.write(cuadro(n).tobytes())
        if n % (FPS * 10) == 0: print(f"{n / FPS:5.0f} s / {DURACION:.0f} s", flush=True)
    enc.stdin.close(); enc.wait(); print("listo", SALIDA)
