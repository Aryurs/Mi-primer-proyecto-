"""Sincroniza cada palabra del texto con la voz usando las pausas finas del audio.

Divide la voz en tramos de habla (entre pausas) y reparte las palabras entre esos tramos con
programación dinámica: cada tramo debe durar lo que tardan sus sílabas al ritmo de la voz, y las
pausas caen preferentemente después de una coma o un punto. Dentro de cada tramo, cada palabra
recibe un tiempo proporcional a sus sílabas.

Uso: python3 -I alinear.py <pausas.txt> <fin_voz> <texto.txt> <salida.json>
"""
import sys, re, json, unicodedata

pausas_txt, fin_voz, texto_txt, salida = sys.argv[1], float(sys.argv[2]), sys.argv[3], sys.argv[4]
v = [float(x) for x in open(pausas_txt).read().split()]
pausas = list(zip(v[0::2], v[1::2]))
tramos, t = [], 0.0
for a, b in pausas:
    if a - t > 0.05: tramos.append((t, a))
    t = b
if fin_voz - t > 0.05: tramos.append((t, fin_voz))

def silabas(p):
    p = unicodedata.normalize("NFD", p.lower()); p = "".join(c for c in p if unicodedata.category(c) != "Mn")
    p = re.sub(r"[^a-zñ]", "", p)
    if not p: return 0
    n = len(re.findall(r"[aeiou]+", p))
    n += len(re.findall(r"(?<=[aeo])[aeo]", p))          # hiatos fuertes: «ea», «oe»...
    return max(1, n)

palabras = open(texto_txt, encoding="utf-8").read().split()
sil = [silabas(w) for w in palabras]
pausa_ok = [1 if re.search(r"[,.;:!?»]$", w) else 0 for w in palabras]
CORTAS = set("a de del la el los las y que te con en mi tu su por para".split())
colgante = [1 if (w.lower() in CORTAS) else 0 for w in palabras]   # palabras que no suelen quedar antes de una pausa
habla = sum(b - a for a, b in tramos)
ritmo = sum(sil) / habla                     # sílabas por segundo

N, M = len(palabras), len(tramos)
pref = [0]
for s in sil: pref.append(pref[-1] + s)
INF = float("inf")
coste = [[INF] * (N + 1) for _ in range(M + 1)]
desde = [[-1] * (N + 1) for _ in range(M + 1)]
coste[0][0] = 0.0
for j in range(1, M + 1):
    a, b = tramos[j - 1]; dur = b - a
    for k in range(1, N + 1):
        mejor, arg = INF, -1
        for i in range(max(0, k - 40), k):
            if coste[j - 1][i] == INF: continue
            s = pref[k] - pref[i]
            esperado = s / ritmo
            c = (dur - esperado) ** 2 / max(0.4, esperado)
            if j < M and colgante[k - 1]: c += 0.8
            if j < M and not pausa_ok[k - 1]: c += 0.35 + 0.6 * (pausas[j - 1][1] - pausas[j - 1][0] if j - 1 < len(pausas) else 0)
            c += coste[j - 1][i]
            if c < mejor: mejor, arg = c, i
        coste[j][k], desde[j][k] = mejor, arg

cortes, k = [N], N
for j in range(M, 0, -1):
    k = desde[j][k]; cortes.append(k)
cortes.reverse()
resultado = []
for j in range(M):
    a, b = tramos[j]; i0, i1 = cortes[j], cortes[j + 1]
    tot = sum(sil[i0:i1]) or 1; acc = 0
    for i in range(i0, i1):
        t0 = a + (b - a) * acc / tot; acc += sil[i]; t1 = a + (b - a) * acc / tot
        resultado.append({"w": palabras[i], "t0": round(t0, 3), "t1": round(t1, 3), "tramo": j})
json.dump(resultado, open(salida, "w"), ensure_ascii=False, indent=0)
print(f"ritmo {ritmo:.2f} sílabas/s · {M} tramos · {N} palabras")
for j in range(M):
    ws = [r["w"] for r in resultado if r["tramo"] == j]
    print(f"{tramos[j][0]:6.2f}-{tramos[j][1]:6.2f}  {' '.join(ws)}")
