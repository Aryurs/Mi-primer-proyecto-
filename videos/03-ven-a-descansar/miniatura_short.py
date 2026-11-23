"""Portada vertical del Short «Ven a descansar», con el estilo fijo de los Shorts del canal.

Uso: python3 -I miniatura_short.py <foto.jpg> <carpeta_fuentes> <salida.jpg>
"""
import sys, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

FOTO, FUENTES, SALIDA = sys.argv[1:4]
W, H = 1080, 1920
DORADO, BLANCO = (253, 184, 19), (255, 255, 255)

im = Image.open(FOTO).convert("RGB"); w, h = im.size
cw = h * 9 / 16; cx = 0.49 * w
x0 = min(max(0, cx - cw / 2), w - cw)
im = im.crop((int(x0), 0, int(x0 + cw), h)).resize((W, H), Image.LANCZOS)
im = ImageEnhance.Color(ImageEnhance.Contrast(im).enhance(1.08)).enhance(1.12)

# Sombra suave detrás del título para que se lea sobre el cielo claro
a = np.asarray(im).astype(np.float32)
yy, xx = np.mgrid[0:H, 0:W]
m = np.exp(-(((xx - W / 2) / 620) ** 2 + ((yy - 560) / 330) ** 2))[..., None]
a = a * (1 - 0.45 * m)
# Polvo dorado
rng = np.random.default_rng(3); A = np.zeros((H, W), np.float32)
for _ in range(70):
    r = rng.choice([3, 4, 5, 7, 9, 12]); x, y = rng.uniform(0, W), rng.uniform(0, H)
    n = int(r * 4) | 1; c = n // 2; gy, gx = np.mgrid[0:n, 0:n]; d = np.hypot(gx - c, gy - c)
    mota = np.clip(np.exp(-(d / (r * .9)) ** 2) + .6 * np.exp(-(d / (r * .35)) ** 2), 0, 1) * rng.uniform(.5, 1)
    xa, ya = int(x) - c, int(y) - c
    sx, sy = slice(max(0, xa), min(W, xa + n)), slice(max(0, ya), min(H, ya + n))
    A[sy, sx] += mota[sy.start - ya:sy.stop - ya, sx.start - xa:sx.stop - xa]
A = np.clip(A, 0, 1)[..., None]
a = a * (1 - A) + np.array([255, 214, 140], np.float32) * A
im = Image.fromarray(a.clip(0, 255).astype(np.uint8)).convert("RGBA")

def F(px): return ImageFont.truetype(os.path.join(FUENTES, "Poppins-ExtraBold.ttf"), px)
def texto(lineas, px, y_centro, interlinea=1.08):
    f = F(px); d0 = ImageDraw.Draw(Image.new("RGBA", (1, 1))); esp = d0.textlength(" ", font=f)
    txt = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(txt)
    lh = px * interlinea; y = y_centro - lh * len(lineas) / 2
    for l in lineas:
        an = sum(d0.textlength(w_, font=f) for w_, _ in l) + esp * (len(l) - 1); x = (W - an) / 2
        for w_, oro in l:
            d.text((x, y), w_, font=f, fill=(DORADO if oro else BLANCO) + (255,)); x += d0.textlength(w_, font=f) + esp
        y += lh
    al = txt.getchannel("A")
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    s = Image.new("RGBA", (W, H), (0, 0, 0, 0)); s.putalpha(al.filter(ImageFilter.GaussianBlur(10)).point(lambda v: int(v * .9)))
    b = Image.new("RGBA", (W, H), (20, 20, 30, 0)); b.putalpha(al.filter(ImageFilter.MaxFilter(7)).point(lambda v: int(v * .6)))
    out.alpha_composite(s, (0, 6)); out.alpha_composite(b); out.alpha_composite(txt)
    return out

im.alpha_composite(texto([[("ORACIÓN", True), ("PARA", True), ("EL", True), ("ALMA", True), ("CANSADA", True)]], 46, 330))
im.alpha_composite(texto([[("VEN", False), ("A", False)], [("DESCANSAR", True)]], 112, 560))
im.convert("RGB").save(SALIDA, quality=94)
print("listo", SALIDA)
