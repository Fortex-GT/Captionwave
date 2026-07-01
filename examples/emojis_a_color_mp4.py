"""
De texto a un Short en MP4 con emojis A COLOR superpuestos (sin solaparse).

Genera los subtítulos SIN emoji (emoji_in_ass=False), quema el texto sobre un
fondo y superpone cada emoji como PNG a color (Twemoji). Los emojis NO se
solapan: cada uno desaparece justo antes de que aparezca el de la siguiente
palabra.

Pon USAR_TODO_EL_DICCIONARIO = True para narrar TODAS las palabras del
diccionario (un video largo que muestra los ~218 emojis; tarda varios minutos).

Requisitos:  pip install captionwave  +  FFmpeg  +  conexión a internet.
Ejecuta:     python examples/emojis_a_color_mp4.py
"""

import json
import os
import subprocess
import urllib.request
from collections import Counter

from captionwave import CaptionGenerator, CURADOS

# --- Ajustes ---
USAR_TODO_EL_DICCIONARIO = False   # True = narra las 407 palabras del diccionario
SALIDA = "salida.mp4"
GAP = 0.05                         # hueco (s) para que un emoji se apague antes del siguiente
DUR_MIN = 0.6                      # tiempo mínimo en pantalla de cada emoji (s)
TAM_EMOJI = 140                    # tamaño del emoji superpuesto (px)
POS_Y = 470                        # posición vertical del emoji (px)

# CDNs de Twemoji (se prueban en orden; algunas bloquean IPs de datacenter).
CDNS = [
    "https://cdn.jsdelivr.net/gh/twitter/twemoji@14.0.2/assets/72x72/{}.png",
    "https://raw.githubusercontent.com/twitter/twemoji/v14.0.2/assets/72x72/{}.png",
    "https://cdnjs.cloudflare.com/ajax/libs/twemoji/14.0.2/72x72/{}.png",
]


def descargar_emoji(emoji, carpeta="emo"):
    """Descarga el PNG a color de un emoji; devuelve su ruta o None."""
    cp = "-".join(f"{ord(c):x}" for c in emoji if ord(c) != 0xFE0F)
    png = os.path.join(carpeta, f"{cp}.png")
    if os.path.exists(png):
        return png
    for url in CDNS:
        try:
            req = urllib.request.Request(url.format(cp), headers={"User-Agent": "Mozilla/5.0"})
            data = urllib.request.urlopen(req, timeout=15).read()
            if data[:4] == b"\x89PNG":
                open(png, "wb").write(data)
                return png
        except Exception:
            continue
    return None


def eventos_sin_solape(emojis_json, carpeta="emo"):
    """Lee emojis.json y devuelve [(png, inicio, fin)] SIN solapamientos:
    cada emoji termina (con un pequeño hueco) antes de que empiece el siguiente."""
    os.makedirs(carpeta, exist_ok=True)
    brutos = []
    for e in json.load(open(emojis_json, encoding="utf-8")):
        if not e.get("emoji"):
            continue
        png = descargar_emoji(e["emoji"], carpeta)
        if png:
            brutos.append((png, e["start"], e["start"] + max(e["dur"], DUR_MIN)))
    brutos.sort(key=lambda x: x[1])
    limpios = []
    for n, (png, t0, t1) in enumerate(brutos):
        if n + 1 < len(brutos):
            t1 = min(t1, brutos[n + 1][1] - GAP)   # cortar antes del siguiente
        if t1 > t0:                                # descartar intervalos vacíos/invertidos
            limpios.append((png, t0, t1))
    return limpios


def comando_overlay(base, eventos, salida):
    """Comando FFmpeg que superpone todos los emojis en UNA sola pasada.
    Reutiliza cada PNG con 'split' para no repetir entradas."""
    unicos, idx = [], {}
    for png, _, _ in eventos:
        if png not in idx:
            idx[png] = len(unicos) + 1             # 0 = base.mp4
            unicos.append(png)
    veces = Counter(png for png, _, _ in eventos)
    inputs, filtros, etiquetas = [], [], {}
    for png in unicos:
        inputs += ["-i", png]
        i, c = idx[png], veces[png]
        labs = [f"u{i}_{j}" for j in range(c)]
        etiquetas[png] = labs[:]
        filtros.append(f"[{i}:v]scale={TAM_EMOJI}:{TAM_EMOJI}" +
                       (f"[{labs[0]}]" if c == 1 else f",split={c}" + "".join(f"[{l}]" for l in labs)))
    prev = "0:v"
    for n, (png, t0, t1) in enumerate(eventos):
        lab = etiquetas[png].pop()
        filtros.append(f"[{prev}][{lab}]overlay=(W-w)/2:{POS_Y}:"
                       f"enable='between(t,{t0:.2f},{t1:.2f})'[v{n}]")
        prev = f"v{n}"
    return ["ffmpeg", "-y", "-loglevel", "error", "-i", base, *inputs,
            "-filter_complex", ";".join(filtros),
            "-map", f"[{prev}]", "-map", "0:a",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "copy", salida]


# 1) Texto: una frase corta, o todas las palabras del diccionario
if USAR_TODO_EL_DICCIONARIO:
    pal = list(CURADOS.keys())
    texto = ". ".join(" ".join(pal[i:i + 8]) for i in range(0, len(pal), 8)) + "."
    intro = None
else:
    texto = "El Sol contiene el 99% de la masa del sistema solar."
    intro = "¿Sabías que...?"

# 2) Voz + subtítulos SIN emoji quemado (el emoji va como PNG a color)
gen = CaptionGenerator(voice="es-MX-DaliaNeural", rate="+18%", style="hormozi",
                       emoji_in_ass=False)
r = gen.generate(texto, intro=intro,
                 out_audio="voz.mp3", out_ass="subs.ass", out_emojis="emojis.json")
print("Duración:", round(r["duration"], 1), "s")

# 3) Fondo degradado vertical (1080x1920) + texto quemado -> base.mp4
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi",
    "-i", "gradients=s=1080x1920:c0=0x0f3460:c1=0x16213e:x0=0:y0=0:x1=1080:y1=1920",
    "-frames:v", "1", "fondo.png"], check=True)
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-i", "fondo.png",
    "-i", "voz.mp3", "-vf", "scale=1080:1920,ass=subs.ass",
    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", "base.mp4"], check=True)

# 4) Emojis a color, sin solaparse, superpuestos en una sola pasada
eventos = eventos_sin_solape("emojis.json")
print("Emojis a superponer:", len(eventos))
if eventos:
    subprocess.run(comando_overlay("base.mp4", eventos, SALIDA), check=True)
else:
    os.replace("base.mp4", SALIDA)
print(f"Listo: {SALIDA}")
