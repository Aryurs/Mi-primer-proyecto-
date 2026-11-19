import sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
F = "/tmp/claude-0/-home-user-Mi-primer-proyecto-/aa0595ff-3a86-5860-ae3d-848db924c5e6/scratchpad/fonts/"
src, out = sys.argv[1], sys.argv[2]
S = 2; W, H = 1280*S, 720*S
im = Image.open(src).convert("RGB")
w, h = im.size
ch = int(w*9/16)
top = int(h*0.258)                      # cielo arriba, figura en el tercio inferior
im = im.crop((0, top, w, top+ch)).resize((W, H), Image.LANCZOS)
# Gradación Amanecer: un poco más cálida, sombras levantadas hacia ciruela suave
im = ImageEnhance.Contrast(im).enhance(1.04)
r, g, b = im.split()
r = r.point(lambda v: min(255, int(v*1.03+4)))
b = b.point(lambda v: int(v*0.94+6))
im = Image.merge("RGB", (r, g, b))

def font(name, wght, size):
    f = ImageFont.truetype(F+name, size); f.set_variation_by_axes([wght]); return f
disp = font("CormorantGaramond%5Bwght%5D.ttf", 600, 112*S)
ital = font("CormorantGaramond-Italic%5Bwght%5D.ttf", 500, 112*S)
sans = font("Mulish%5Bwght%5D.ttf", 800, 26*S)
INK, SUAVE, ORO, LUZ = (42,30,46), (106,82,96), (154,106,18), (255,250,240)

# Hilo de Luz: diagonal desde la esquina superior derecha hasta la cabeza
head = (668*S, 326*S)
p0 = (W+10*S, -10*S)
glow = Image.new("RGBA", (W, H), (0,0,0,0)); gd = ImageDraw.Draw(glow)
gd.line([p0, head], fill=ORO+(150,), width=16*S)
gd.ellipse([head[0]-34*S, head[1]-34*S, head[0]+34*S, head[1]+34*S], fill=(233,185,73,170))
glow = glow.filter(ImageFilter.GaussianBlur(12*S))
im = im.convert("RGBA"); im.alpha_composite(glow)
d = ImageDraw.Draw(im)
d.line([p0, head], fill=ORO, width=6*S)
rr = 14*S
d.ellipse([head[0]-rr, head[1]-rr, head[0]+rr, head[1]+rr], fill=LUZ, outline=ORO, width=6*S)

# Etiqueta + titular
x = 64*S
d.text((x, 70*S), "ORACIÓN DE LA MAÑANA", font=sans, fill=SUAVE, spacing=0)
y = 108*S
parts = [("Tú eres mi ", disp, INK), ("escudo", ital, ORO)]
for t, f, c in parts:
    d.text((x, y), t, font=f, fill=c); x += d.textlength(t, font=f)
print("fin del titular en x =", x//S)
im.convert("RGB").resize((1280, 720), Image.LANCZOS).save(out, quality=94)
