"""Miniatura de YouTube (1280x720) de «Renueva nuestras fuerzas». Hora Sanación, composición Ventana.

Uso: python3 -I miniatura.py <foto.jpg> <carpeta_fuentes> <salida.jpg>
"""
import sys, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

FOTO, FUENTES, SALIDA = sys.argv[1:4]
S = 2; W, H = 1280 * S, 720 * S

# Recorte horizontal de la foto vertical: pared con los rayos arriba, alféizar y madera oscura abajo
im = Image.open(FOTO).convert("RGB"); w, h = im.size
top = int(h * 0.50)
im = im.crop((0, top, w, top + int(w * 9 / 16))).resize((W, H), Image.LANCZOS)

# Gradación Sanación: sombras hacia el verde profundo del fondo, luces hacia el oro de vela
FONDO, ORO_LUZ = np.array([23, 39, 31], np.float32), np.array([255, 226, 178], np.float32)
a = np.asarray(im).astype(np.float32) / 255
L = (0.30 * a[..., 0] + 0.59 * a[..., 1] + 0.11 * a[..., 2])[..., None]
L2 = L ** 1.45                                     # baja los medios: la luz queda solo en los rayos
a = a * (L2 / np.maximum(L, 1e-4))
calido = ORO_LUZ / 255 * L2 * 1.18                 # el blanco azulado de la pared pasa a luz de vela
a = a * 0.2 + calido * 0.8
sombra = (1 - L2) ** 2.2
a = a * (1 - 0.55 * sombra) + FONDO / 255 * 0.55 * sombra
# Velo abajo a la izquierda, donde va el titular
yy, xx = np.mgrid[0:H, 0:W] / np.array([H, W])[:, None, None]
velo = np.clip((yy - 0.38) / 0.40, 0, 1) * np.clip(1.15 - xx * 1.1, 0, 1)
a = a * (1 - 0.6 * velo[..., None]) + FONDO / 255 * 0.6 * velo[..., None]
im = Image.fromarray((a.clip(0, 1) * 255).astype(np.uint8)).convert("RGBA")

def fuente(nombre, peso, px):
    f = ImageFont.truetype(os.path.join(FUENTES, nombre), px); f.set_variation_by_axes([peso]); return f
disp = fuente("CormorantGaramond%5Bwght%5D.ttf", 600, 112 * S)
ital = fuente("CormorantGaramond-Italic%5Bwght%5D.ttf", 500, 112 * S)
sans = fuente("Mulish%5Bwght%5D.ttf", 800, 24 * S)
TEXTO, SUAVE, HILO, DESTELLO = (242, 241, 230), (184, 205, 190), (233, 185, 73), (255, 244, 214)

# Hilo de Luz: entra por arriba siguiendo un rayo de la ventana y se posa en el zócalo
p1 = (int(1280 * 0.565) * S, int(720 * 0.585) * S)
p0 = (p1[0] - int(p1[1] / 1.42), -10 * S)
halo = Image.new("RGBA", (W, H), (0, 0, 0, 0)); gd = ImageDraw.Draw(halo)
gd.line([p0, p1], fill=HILO + (150,), width=16 * S)
gd.ellipse([p1[0] - 34 * S, p1[1] - 34 * S, p1[0] + 34 * S, p1[1] + 34 * S], fill=HILO + (170,))
im.alpha_composite(halo.filter(ImageFilter.GaussianBlur(12 * S)))
d = ImageDraw.Draw(im)
d.line([p0, p1], fill=HILO, width=6 * S)
r = 14 * S
d.ellipse([p1[0] - r, p1[1] - r, p1[0] + r, p1[1] + r], fill=DESTELLO, outline=HILO, width=6 * S)

# Etiqueta + titular abajo a la izquierda (la esquina derecha queda libre para la duración)
x0, y = 64 * S, 418 * S
d.text((x0, y), "ORACIÓN POR EL CANSANCIO", font=sans, fill=SUAVE)
y += 30 * S
d.text((x0, y), "Renueva mis", font=disp, fill=TEXTO)
d.text((x0, y + 96 * S), "fuerzas", font=ital, fill=HILO)
im.convert("RGB").resize((1280, 720), Image.LANCZOS).save(SALIDA, quality=94)
print("listo", SALIDA)
