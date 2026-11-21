# Renueva nuestras fuerzas · Short de YouTube y Reel de Facebook

Solo formato vertical (1080×1920), con el estilo fijo de `videos/ESTILO-SHORTS.md`:
movimiento en todas las fotos, polvo dorado flotante, agua en movimiento en las fotos con agua
y la misma música de fondo del video anterior.

- **Short de YouTube:** cierre con el botón rojo «SUSCRÍBETE».
- **Reel de Facebook:** el mismo video, con el botón azul «SÍGUEME» en el cierre.
- **Portada:** `miniatura-short.jpg` como primer cuadro (0,5 s), hecha con `fotos/portada-ventana.jpg`.
  Esa foto no se usa dentro del video.

## Fotos y frase con la que entra cada una

| # | Foto | Entra con |
|---|---|---|
| 1 | manantial | «Amado Padre celestial, fuente inagotable de vida y fortaleza» |
| 2 | oracion | «hoy nos presentamos delante de tu presencia en el poderoso nombre de Jesús» |
| 3 | ciudad (cielo estrellado) | «Reconocemos que no hay circunstancia de nuestras vidas que pase inadvertida ante tus ojos» |
| 4 | cansancio | «Señor, hoy ponemos delante de ti el cansancio, el agotamiento profundo…» |
| 5 | despertar | «Tú eres consciente de que hemos tenido días en los que abrir los ojos…» |
| 6 | taza | «y hasta las actividades más sencillas nos cuestan realizarlas» |
| 7 | fisico | «porque nos sentimos en un estado crítico de debilidad» |
| 8 | lluvia | «y agotamiento físico, mental y emocional» |
| 9 | mental | «Buscamos cada día fuerzas para continuar» |
| 10 | niebla | «porque, aunque estamos vivos, nos sentimos en un estado de supervivencia» |

(Al principio iban tres fotos en «físico, mental y emocional», pero la voz lo dice en 2 segundos:
habrían cambiado demasiado rápido. Se repartieron en frases de 3 a 5 segundos.)
| 11 | tormenta | «Dios invencible y fuerte en batalla» |
| 12 | clamor | «a ti levantamos nuestro clamor» |
| 13 | tierra | «y pedimos una restauración radical en nuestras vidas» |
| 14 | aguila | «Renueva nuestras fuerzas» |
| 15 | brote | «y transforma aquellas áreas que necesitan de tu intervención divina» |
| 16 | tumba | «Declaramos que el poder que levantó a Cristo Jesús de entre los muertos…» |
| 17 | cascada | «para revertir todo aquello que nos está robando las fuerzas, la energía y el vigor» |
| 18 | sendero | «y que tu poder restaurador nos conduzca» |
| 19 | victoria | «hacia un nuevo tiempo de renovación, restitución y victoria» |
| 20 | calma | «Gracias, Señor, porque tú tienes el control» |
| 21 | vela | «En el nombre poderoso de Jesús. Amén.» |
| — | cierre | «Si esta oración fue de bendición…» (fondo oscurecido sobre la última foto y botón final) |

## Cómo se arma

```
python3 -I alinear.py pausas.txt 130.35 texto.txt palabras.json      # texto: render_short.py x x x x x --texto
python3 -I render_short.py fotos voz.mp3 musica.mp3 fuentes short-youtube.mp4 --portada miniatura-short.jpg
python3 -I render_short.py fotos voz.mp3 musica.mp3 fuentes reel-facebook.mp4 --portada miniatura-short.jpg --facebook
```

Pausas: `silencedetect=n=-38dB:d=0.25`. Fin de la voz: 130,35 s.

## Audio

- Voz: −20,7 LUFS. Música de fondo (meditación 432 Hz, piano y cuencos): −14,5 LUFS, se baja 22 dB
  para quedar unos 16 dB por debajo de la voz. Mezcla final normalizada a −14 LUFS.
- Los videos terminados (unos 137 MB cada uno) no se guardan en el repositorio.
