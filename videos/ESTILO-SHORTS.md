# Estilo fijo de los Shorts · Oraciones: Mi Conexión Divina

Elegido el 19 de noviembre de 2026, a partir de los Shorts anteriores del canal.

## Formato
- Vertical 1080×1920, 30 fps. Duración: la de la oración más 5 s de cierre (máximo 3 minutos).
- Voz completa de principio a fin. Música de fondo a volumen medio: unos 14 dB por debajo de la voz.
- Sin campana, sin líneas doradas, sin sello ni marca de agua.

## Portada (primer cuadro)
- Cada video lleva su portada vertical (1080×1920) como primer cuadro, durante 0,5 s.
- Sirve para elegirla como portada desde la app de YouTube en el teléfono: al editar la portada,
  arrastra el selector hasta el inicio del video. La voz y la música empiezan justo después.
- Estilo de la portada: foto con mucho cielo, «ORACIÓN DE…» pequeño en dorado y el tema grande
  (una palabra en dorado, el resto en blanco), en la parte de arriba y al centro.

## Inicio
- Título centrado sobre la primera foto mientras la voz dice la introducción:
  «ORACIÓN PARA» pequeño en dorado y debajo el tema en 3 o 4 líneas, con 1 o 2 palabras en dorado.
- Después, «O R E M O S» en dorado, con letras espaciadas.

## Subtítulos (dinámicos)
- Grupos de 1 a 3 palabras, en MAYÚSCULAS, letra Poppins ExtraBold, blanca, con sombra suave oscura.
- Una palabra clave por grupo en dorado (#FDB813): Dios, Señor, Jesús, Padre, Amén o la palabra con más peso.
- Las palabras aparecen **una por una, al ritmo de la voz**, con un pequeño efecto de entrada.
  El grupo se queda en pantalla hasta que empieza el siguiente. Ningún grupo cruza una pausa de la voz.
- Posición: un poco por debajo del centro de la pantalla.

## Imágenes
- Una foto por frase importante de la oración, entrando cuando la voz llega a esa frase, con fundido suave.
- Movimiento en todas: acercar, alejar o desplazar, alternando para que dos seguidas no se muevan igual.
- Polvo dorado flotante sobre todas las fotos.
- Agua en movimiento (ondulación y brillos) en las fotos de lagos, mar o ríos.
- Fotos verticales, sin textos, logos, banderas ni marcas visibles.

## Cierre
- Fondo oscurecido sobre la última foto, manos en oración en contorno dorado,
  «¿TE BENDIJO ESTA ORACIÓN?», botón rojo «SUSCRÍBETE» y botón blanco «DALE LIKE», que entran con un pequeño rebote.

## Cómo se hace
Cada video tiene su carpeta (`01-proteccion-manana`, `02-gracias-nuevo-dia`, …) con:
- `texto.txt`: la oración tal como la lee la voz.
- `palabras.json`: la sincronía de cada palabra con la voz (la crea `alinear.py`).
- `video.json`: las frases, la foto que entra con cada frase, el título y las fotos con agua.

Programas compartidos en `videos/`:
- `alinear.py`: sincroniza cada palabra con la voz usando sus pausas.
- `render_short.py`: arma el Short (YouTube) o el Reel (`--facebook`), con la portada al inicio (`--portada`).
- `miniatura_short.py`: crea la portada vertical.
