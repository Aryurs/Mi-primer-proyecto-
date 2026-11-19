"""Monta el video «Protección para este nuevo día» con la identidad del canal.

Uso: python3 -I render.py <carpeta_fotos> <audio_voz.mp3> <carpeta_fuentes> <salida.mp4>
"""
import sys, os, json, math, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

FOTOS, VOZ, FUENTES, SALIDA = sys.argv[1:5]
TRABAJO = os.path.join(os.path.dirname(os.path.abspath(SALIDA)), "trabajo")
os.makedirs(TRABAJO, exist_ok=True)
W, H, FPS = 1920, 1080, 30
D = 3.0            # la voz entra a los 3 s, después de la firma de apertura
CAMPANA = 2.5      # la campana suena cuando se enciende el punto de luz
COLA = 12.0        # pantalla final después de la voz

# ---- Hora Amanecer (tokens del sistema de diseño) ----
FONDO, ELEV, ATM = (246, 231, 218), (239, 214, 196), (232, 162, 124)
TEXTO, SUAVE, HILO, DESTELLO = (42, 30, 46), (106, 82, 96), (154, 106, 18), (255, 250, 240)

def fuente(nombre, peso, px):
    f = ImageFont.truetype(os.path.join(FUENTES, nombre), px)
    f.set_variation_by_axes([peso]); return f
SERIF = "CormorantGaramond%5Bwght%5D.ttf"; SERIF_I = "CormorantGaramond-Italic%5Bwght%5D.ttf"; SANS = "Mulish%5Bwght%5D.ttf"

# ---- Pausas de la voz (silencedetect -38 dB, 0.45 s) ----
PAUSAS = [(6.374, 7.004), (7.653, 8.290), (9.097, 9.554), (13.482, 13.961), (16.109, 16.616),
          (21.614, 22.103), (29.549, 30.137), (40.600, 41.056), (52.847, 53.381), (59.939, 60.455),
          (79.892, 80.487), (88.822, 89.394), (98.503, 99.013), (102.575, 103.130), (105.439, 105.924),
          (106.282, 107.234)]
FIN_VOZ = 123.17

# ---- Subtítulos (| = salto de línea) y foto que entra con cada frase ----
FRASES = [
 ("Esta oración está dirigida a la protección|y cobertura divina durante este nuevo día.", "prado", False),
 ("Oremos.", None, True),
 ("Padre bueno, en este nuevo amanecer|nos presentamos delante de ti,", None, True),
 ("primeramente para agradecerte.", None, True),
 ("Gracias por el regalo de la vida,", "bebe", True),
 ("porque no hemos despertado por casualidad,", "reloj", True),
 ("sino porque en tu gran misericordia|has decidido sostenernos una vez más", "ventana", True),
 ("con el aliento de tu Espíritu.", None, True),
 ("En este día elevamos|una oración de protección,", "hueco", True),
 ("pidiendo que tú, Señor Jesús,|seas el escudo que nos proteja", None, True),
 ("y la coraza que nos blinde.", None, True),
 ("Que cada paso que demos|esté bajo tu cuidado y protección,", "colinas", True),
 ("y que, donde aceche el peligro,|llegue primero tu cobertura,", "rayo", True),
 ("antes de que nos acerquemos|a cualquier lugar.", None, True),
 ("Amado Padre, en este día|guarda nuestros corazones", "lago", True),
 ("de todo aquello que nos roba la paz.", None, True),
 ("Aleja las distracciones y las tentaciones.", "nubes", True),
 ("Que tus ángeles vayan delante de nosotros,|abriendo caminos;", None, True),
 ("y si hoy nos corresponde enfrentar|decisiones difíciles,", "sol", True),
 ("trae claridad a nuestros pensamientos|para que podamos elegir sabiamente", None, True),
 ("y reconocer aquello que nos conviene.", None, True),
 ("En este día te pido que bendigas mi hogar,|mi familia, nuestro trabajo", "familia", True),
 ("y cada una de las áreas|de nuestras vidas.", None, True),
 ("Entregamos este día en tus manos,", "mano", True),
 ("confiando en que, al terminarlo,|podamos decir", None, True),
 ("que fue tu mano bondadosa|la que nos sostuvo.", None, True),
 ("Gracias, Señor,|porque tú tienes el control.", "brazos", True),
 ("En el nombre poderoso de Jesús.", "cruz", True),
 ("Amén.", None, True),
 ("Si esta oración fue de bendición|para tu vida, dale «Me gusta»,", "cierre", True),
 ("escribe AMÉN en los comentarios", None, True),
 ("y compártela con alguien que necesite|escuchar estas palabras.", None, True),
 ("¡Tu interacción nos ayuda a llevar|el mensaje de Dios a más corazones!", None, True),
]
# Grupos anclados a tramos de voz conocidos: (primera frase, última frase, inicio, fin)
GRUPOS = [(0, 0, 0.0, 6.374), (1, 1, 7.004, 7.653), (2, 3, 8.290, 13.482), (4, 25, 13.961, 98.503),
          (26, 26, 99.013, 102.575), (27, 27, 103.130, 105.439), (28, 28, 105.924, 106.282), (29, 32, 107.234, FIN_VOZ)]

def alinear():
    tiempos = [None] * len(FRASES)
    for a, b, t0, t1 in GRUPOS:
        pausas = [p for p in PAUSAS if t0 < p[0] and p[1] < t1]
        habla = (t1 - t0) - sum(p[1] - p[0] for p in pausas)
        pesos = [len(FRASES[i][0].replace("|", " ")) + 6 for i in range(a, b + 1)]
        total = sum(pesos)
        def a_reloj(s):            # segundos de habla -> tiempo real saltando pausas
            t = t0
            for p0, p1 in pausas:
                if t + s <= p0: return t + s
                s -= (p0 - t); t = p1
            return t + s
        acum, cortes = 0, [t0]
        for w in pesos[:-1]:
            acum += w; c = a_reloj(habla * acum / total)
            cerca = min(pausas, key=lambda p: abs((p[0] + p[1]) / 2 - c), default=None)
            if cerca and abs((cerca[0] + cerca[1]) / 2 - c) < 1.3: c = cerca
            cortes.append(c)
        cortes.append(t1)
        for k, i in enumerate(range(a, b + 1)):
            ini = cortes[k][1] if isinstance(cortes[k], tuple) else cortes[k]
            fin = cortes[k + 1][0] if isinstance(cortes[k + 1], tuple) else cortes[k + 1]
            tiempos[i] = (ini + D, fin + D)
    return tiempos
TIEMPOS = alinear()

# ---- Fotos: archivo, centro vertical del recorte, (ancho relativo, centro x) ----
FOTO = {
 "prado":   ("8e21430a", 0.52, None), "bebe": ("6880d166", 0.45, None), "reloj": ("8d4c6fcd", 0.47, None),
 "ventana": ("4977fa5b", 0.43, None), "hueco": ("d578ce58", 0.35, None), "colinas": ("762f8903", 0.47, None),
 "rayo":    ("a06b1a21", 0.55, None), "lago": ("4c0c2be4", 0.52, None), "nubes": ("9719e6c3", 0.60, (0.64, 0.32)),
 "sol":     ("98e1cf53", 0.58, None), "cielo": ("207c3c03", 0.50, None), "familia": ("b183e2de", 0.60, None),
 "mano":    ("24f91141", 0.62, None), "brazos": ("8e7c0384", 0.50, None), "cruz": ("e1596043", 0.52, None),
}
BW, BH = 2112, 1188   # base 1.1x para el zoom lento

def preparar(clave):
    ruta = os.path.join(TRABAJO, clave + ".jpg")
    if os.path.exists(ruta): return Image.open(ruta).convert("RGB")
    cod, cy, ancho = FOTO[clave]
    im = Image.open(os.path.join(FOTOS, cod + "-image.jpg")).convert("RGB")
    w, h = im.size
    cw = w * (ancho[0] if ancho else 1.0)
    cx = w * (ancho[1] if ancho else 0.5)
    ch = cw * 9 / 16
    x0 = min(max(0, cx - cw / 2), w - cw); y0 = min(max(0, cy * h - ch / 2), h - ch)
    im = im.crop((int(x0), int(y0), int(x0 + cw), int(y0 + ch))).resize((BW, BH), Image.LANCZOS)
    # Gradación de la Hora Amanecer: luz cálida, sombras ciruela suave
    im = ImageEnhance.Contrast(im).enhance(1.04)
    a = np.asarray(im).astype(np.float32)
    a[..., 0] = a[..., 0] * 1.04 + 5; a[..., 1] = a[..., 1] * 1.0 + 2; a[..., 2] = a[..., 2] * 0.92 + 8
    lum = a.mean(axis=2, keepdims=True) / 255.0
    sombra = np.array([42, 30, 46], np.float32)
    a = a * (0.88 + 0.12 * lum) + sombra * (0.12 * (1 - lum))
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    im.save(ruta, quality=95); return im

# ---- Línea de tiempo de planos ----
CRUCE = 1.0
planos = []   # (clave, inicio, fin)
inicios = [(0.0, "prado")]
for i, (txt, foto, _) in enumerate(FRASES):
    if foto and foto != "prado": inicios.append((TIEMPOS[i][0] - 0.35, foto))
for k, (t, clave) in enumerate(inicios):
    fin = inicios[k + 1][0] + CRUCE if k + 1 < len(inicios) else FIN_VOZ + D + COLA
    planos.append((clave, t, fin))
DURACION = FIN_VOZ + D + COLA
NFRAMES = int(DURACION * FPS)

# ---- Capas de texto ----
def placa(texto):
    f = fuente(SANS, 600, 44)
    lineas = texto.split("|")
    tmp = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    anchos = [tmp.textlength(l, font=f) for l in lineas]
    lh = 57; pw = int(max(anchos)) + 64; ph = lh * len(lineas) + 40
    im = Image.new("RGBA", (pw, ph), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, pw - 1, ph - 1], radius=12, fill=ELEV + (214,))
    for k, l in enumerate(lineas):
        d.text(((pw - anchos[k]) / 2, 20 + k * lh), l, font=f, fill=TEXTO)
    return im
PLACAS = [placa(t) if mostrar else None for t, _, mostrar in FRASES]

def titulo_apertura():
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.text((96, 96), "ORACIÓN DE LA MAÑANA", font=fuente(SANS, 800, 28), fill=SUAVE)
    s, si = fuente(SERIF, 600, 96), fuente(SERIF_I, 500, 96)
    d.text((96, 140), "Tu cobertura", font=s, fill=TEXTO)
    x = 96; d.text((x, 236), "para ", font=s, fill=TEXTO); x += d.textlength("para ", font=s)
    d.text((x, 236), "hoy", font=si, fill=HILO)
    return im
TITULO = titulo_apertura()

def sello(r, color, punto=True, alfa=255):
    S = 4; n = int(r * 2 + 40) * S
    im = Image.new("RGBA", (n, n), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    c = n / 2; R = r * S; wl = max(2, int(r * 0.07)) * S
    d.ellipse([c - R, c - R, c + R, c + R], outline=color + (alfa,), width=wl)
    pr = R * 0.24; py = c + R * 0.32
    d.line([(c, c - R), (c, py - pr)], fill=color + (alfa,), width=int(wl * 1.4))
    if punto:
        d.ellipse([c - pr, py - pr, c + pr, py + pr], fill=DESTELLO + (alfa,), outline=color + (alfa,), width=int(wl * 1.2))
    return im.resize((n // S, n // S), Image.LANCZOS)
MARCA = sello(30, (255, 250, 240), alfa=178)

def hilo(capa, p0, p1, prog, punto_alfa):
    """Dibuja el Hilo de Luz de p0 a p1 hasta 'prog' (0..1) con su halo, y el punto."""
    x = p0[0] + (p1[0] - p0[0]) * prog; y = p0[1] + (p1[1] - p0[1]) * prog
    halo = Image.new("RGBA", (W, H), (0, 0, 0, 0)); g = ImageDraw.Draw(halo)
    if prog > 0: g.line([p0, (x, y)], fill=(233, 185, 73, 150), width=18)
    if punto_alfa > 0:
        rr = 42 * punto_alfa; g.ellipse([p1[0] - rr, p1[1] - rr, p1[0] + rr, p1[1] + rr], fill=(233, 185, 73, int(190 * punto_alfa)))
    halo = halo.filter(ImageFilter.GaussianBlur(14))
    capa.alpha_composite(halo); d = ImageDraw.Draw(capa)
    if prog > 0: d.line([p0, (x, y)], fill=HILO, width=4)
    if punto_alfa > 0:
        r = 10; a = int(255 * punto_alfa)
        d.ellipse([p1[0] - r, p1[1] - r, p1[0] + r, p1[1] + r], fill=DESTELLO + (a,), outline=HILO + (a,), width=4)

def cierre_fondo():
    a = np.zeros((H, W, 3), np.float32); a[:] = FONDO
    yy, xx = np.mgrid[0:H, 0:W]
    m = np.exp(-(((xx - W / 2) / 900) ** 2 + ((yy - 330) / 520) ** 2))[..., None]
    a = a * (1 - 0.45 * m) + np.array(ATM, np.float32) * 0.45 * m
    return Image.fromarray(a.astype(np.uint8))
CIERRE = cierre_fondo()
SELLO_GRANDE = sello(64, HILO)

def texto_centrado(partes, px, y):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    fs = [(t, fuente(SERIF_I if it else SERIF, 500 if it else 600, px), HILO if it else TEXTO) for t, it in partes]
    ancho = sum(d.textlength(t, font=f) for t, f, _ in fs); x = (W - ancho) / 2
    for t, f, c in fs: d.text((x, y), t, font=f, fill=c); x += d.textlength(t, font=f)
    return im
CTA = texto_centrado([("Escribe ", False), ("Amén", True), (" en los comentarios", False)], 76, 440)
BENDICION = texto_centrado([("Que la paz de Dios ", False), ("te acompañe", True)], 76, 440)

# ---- Render ----
CACHE = {}
def base(clave):
    if clave not in CACHE:
        CACHE.clear() if len(CACHE) > 3 else None
        CACHE[clave] = CIERRE if clave == "cierre" else preparar(clave)
    return CACHE[clave]

def cuadro_plano(idx, t):
    clave, t0, t1 = planos[idx]
    if clave == "cierre": return CIERRE.copy()
    im = base(clave); p = min(1, max(0, (t - t0) / max(0.1, t1 - t0)))
    p = 0.5 - 0.5 * math.cos(math.pi * p)
    z = 1.0 + 0.035 * (p if idx % 2 == 0 else 1 - p)
    bw, bh = BW / (1.1 * z) * 1.0, BH / (1.1 * z)
    deriva = (p - 0.5) * 0.012 * BW * (1 if idx % 3 else -1)
    cx, cy = BW / 2 + deriva, BH / 2
    if clave == "prado":      # el zoom se ancla en el sol para que el punto de luz no se mueva
        e = (BW / 1.1) / W; ax = (BW - BW / 1.1) / 2 + SOL_APERTURA[0] * e; ay = (BH - BH / 1.1) / 2 + SOL_APERTURA[1] * e
        k = bw / W; x0, y0 = ax - SOL_APERTURA[0] * k, ay - SOL_APERTURA[1] * k
        return im.resize((W, H), Image.BICUBIC, box=(x0, y0, x0 + bw, y0 + bh))
    return im.resize((W, H), Image.BICUBIC, box=(cx - bw / 2, cy - bh / 2, cx + bw / 2, cy + bh / 2))

def suave(t, a, b):
    if b <= a: return 1.0 if t >= b else 0.0
    x = min(1, max(0, (t - a) / (b - a))); return x * x * (3 - 2 * x)

T_CIERRE = [p for p in planos if p[0] == "cierre"][0][1]
SOL_APERTURA = (976, 458)

def cuadro(n):
    t = n / FPS
    activos = [i for i, (c, a, b) in enumerate(planos) if a <= t < b]
    i = activos[-1]
    im = cuadro_plano(i, t).convert("RGBA")
    if len(activos) > 1:
        j = activos[0]; k = suave(t, planos[i][1], planos[j][2])
        im = Image.blend(cuadro_plano(j, t).convert("RGBA"), im, k)
    capa = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    # Firma de apertura: el hilo baja hasta el sol y se enciende con la campana
    if t < planos[1][1] + CRUCE:
        prog = suave(t, 0.5, CAMPANA); pa = suave(t, CAMPANA - 0.1, CAMPANA + 0.4)
        fuera = 1 - suave(t, planos[1][1], planos[1][1] + CRUCE)
        h = Image.new("RGBA", (W, H), (0, 0, 0, 0)); hilo(h, (SOL_APERTURA[0], -10), SOL_APERTURA, prog, pa)
        if fuera < 1: h.putalpha(h.getchannel("A").point(lambda v: int(v * fuera)))
        capa.alpha_composite(h)
        a = suave(t, CAMPANA, CAMPANA + 0.6) * (1 - suave(t, TIEMPOS[1][0] - 0.6, TIEMPOS[1][0]))
        if a > 0:
            tt = TITULO.copy(); tt.putalpha(tt.getchannel("A").point(lambda v: int(v * a))); capa.alpha_composite(tt)
    # Cierre: el hilo baja y termina en el sello
    if t >= T_CIERRE:
        a = suave(t, T_CIERRE, T_CIERRE + CRUCE)
        h = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        hilo(h, (W // 2, -10), (W // 2, 230), suave(t, T_CIERRE + 0.4, T_CIERRE + 2.4), 0)
        sa = suave(t, T_CIERRE + 2.2, T_CIERRE + 2.8)
        if sa > 0:
            s = SELLO_GRANDE.copy(); s.putalpha(s.getchannel("A").point(lambda v: int(v * sa)))
            h.alpha_composite(s, (W // 2 - s.width // 2, 300 - s.height // 2))
        fin = FIN_VOZ + D
        for capa_txt, a0, a1 in ((CTA, T_CIERRE + 2.6, fin - 0.3), (BENDICION, fin + 0.2, DURACION + 5)):
            k = suave(t, a0, a0 + 0.6) * (1 - suave(t, a1, a1 + 0.5))
            if k > 0:
                c = capa_txt.copy(); c.putalpha(c.getchannel("A").point(lambda v: int(v * k))); h.alpha_composite(c)
        if a < 1: h.putalpha(h.getchannel("A").point(lambda v: int(v * a)))
        capa.alpha_composite(h)
    # Marca de agua: el sello en la esquina superior derecha
    ma = suave(t, TIEMPOS[1][0], TIEMPOS[1][0] + 1) * (1 - suave(t, T_CIERRE - 0.5, T_CIERRE + 0.5))
    if ma > 0:
        m = MARCA.copy(); m.putalpha(m.getchannel("A").point(lambda v: int(v * ma)))
        capa.alpha_composite(m, (W - 72 - m.width + 20, 52))
    # Subtítulos sobre su placa, en el tercio inferior
    for k, (a0, a1) in enumerate(TIEMPOS):
        if PLACAS[k] is None or not (a0 <= t < a1): continue
        al = suave(t, a0, a0 + 0.15) * (1 - suave(t, a1 - 0.15, a1))
        p = PLACAS[k].copy(); p.putalpha(p.getchannel("A").point(lambda v: int(v * al)))
        capa.alpha_composite(p, ((W - p.width) // 2, H - 96 - p.height))
    im.alpha_composite(capa)
    return im.convert("RGB")

# ---- Audio: campana sintetizada + voz, normalizado para YouTube ----
def campana(ruta):
    sr = 44100; dur = 7.0; t = np.arange(int(sr * dur)) / sr
    f0 = 220.0; parc = [(1, 1.0, 6.0), (2.71, 0.45, 3.6), (5.15, 0.22, 2.2), (8.4, 0.08, 1.3)]
    s = np.zeros_like(t)
    for r, amp, dec in parc:
        f = f0 * r
        s += amp * np.exp(-t / dec) * (np.sin(2 * np.pi * f * t) + 0.6 * np.sin(2 * np.pi * (f + 0.45) * t))
    s *= np.minimum(1, t / 0.006); s /= np.abs(s).max(); s *= 0.32
    with wave.open(ruta, "w") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes((s * 32767).astype(np.int16).tobytes())

if __name__ == "__main__":
    json.dump({"frases": [(FRASES[i][0], round(a, 2), round(b, 2)) for i, (a, b) in enumerate(TIEMPOS)],
               "planos": [(c, round(a, 2), round(b, 2)) for c, a, b in planos]},
              open(os.path.join(TRABAJO, "linea-de-tiempo.json"), "w"), ensure_ascii=False, indent=1)
    if "--muestras" in sys.argv:
        for seg in [float(x) for x in sys.argv[sys.argv.index("--muestras") + 1].split(",")]:
            cuadro(int(seg * FPS)).save(os.path.join(TRABAJO, f"muestra-{seg:06.1f}.jpg"), quality=88)
        sys.exit(0)
    wav = os.path.join(TRABAJO, "campana.wav"); campana(wav)
    audio = os.path.join(TRABAJO, "audio.m4a")
    # Voz medida en -21.5 LUFS y música en -14.5 LUFS: la música baja 21 dB para quedar ~14 dB bajo la voz
    MUSICA = sys.argv[5] if len(sys.argv) > 5 and not sys.argv[5].startswith("--") else None
    entradas = ["-i", VOZ, "-i", wav] + (["-i", MUSICA] if MUSICA else [])
    mus = (f"[2:a]atrim=0:{DURACION},asetpts=PTS-STARTPTS,volume=-21dB,afade=t=in:d=3,"
           f"afade=t=out:st={DURACION-5}:d=5,aformat=channel_layouts=mono[m];") if MUSICA else ""
    n_in = 3 if MUSICA else 2
    subprocess.run(["ffmpeg", "-y", "-v", "error"] + entradas + ["-filter_complex",
        f"[0:a]adelay={int(D*1000)},apad=whole_dur={DURACION}[v];[1:a]adelay={int(CAMPANA*1000)},volume=0.9[c];" + mus +
        f"[v][c]{'[m]' if MUSICA else ''}amix=inputs={n_in}:duration=first:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[a]",
        "-map", "[a]", "-c:a", "aac", "-b:a", "192k", audio], check=True)
    enc = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
        "-r", str(FPS), "-i", "-", "-i", audio, "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "medium",
        "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "copy", "-shortest", "-movflags", "+faststart", SALIDA],
        stdin=subprocess.PIPE)
    for n in range(NFRAMES):
        enc.stdin.write(cuadro(n).tobytes())
        if n % (FPS * 10) == 0: print(f"{n / FPS:5.0f} s / {DURACION:.0f} s", flush=True)
    enc.stdin.close(); enc.wait()
    print("listo", SALIDA)
