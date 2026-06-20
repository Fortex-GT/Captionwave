"""
De texto a un Short en MP4 con emojis A COLOR superpuestos.

Al quemar emojis en el .ass, libass los pinta monocromos o como cuadritos. Aquí
generamos los subtítulos SIN emoji (emoji_in_ass=False), quemamos solo el texto
sobre un fondo y luego superponemos cada emoji como PNG a color (Twemoji) en su
intervalo de tiempo. El emoji de cada palabra lo elige el diccionario de la
librería (ver `emoji_for_word`).

Requisitos:  pip install captionwave  +  FFmpeg  +  conexión a internet
             (voz edge-tts y descarga de los PNG de Twemoji).
Ejecuta:     python examples/emojis_a_color_mp4.py
"""

import json
import os
import subprocess
import urllib.request

from captionwave import CaptionGenerator

# 72x72 PNG a color de cada emoji (CDN público de Twemoji).
TWEMOJI = "https://cdnjs.cloudflare.com/ajax/libs/twemoji/14.0.2/72x72/{}.png"
SALIDA = "salida.mp4"

# 1) Voz + subtítulos SIN emoji quemado (lo pondremos como PNG a color)
gen = CaptionGenerator(voice="es-MX-DaliaNeural", rate="+18%", style="hormozi",
                       emoji_in_ass=False)
r = gen.generate(
    "El Sol contiene el 99% de la masa del sistema solar.",
    intro="¿Sabías que...?",
    out_audio="voz.mp3", out_ass="subs.ass", out_emojis="emojis.json",
)
print("Duración:", round(r["duration"], 2), "s")

# 2) Fondo degradado vertical (1080x1920) + texto quemado -> base.mp4
subprocess.run([
    "ffmpeg", "-y", "-loglevel", "error",
    "-f", "lavfi",
    "-i", "gradients=s=1080x1920:c0=0x0f3460:c1=0x16213e:x0=0:y0=0:x1=1080:y1=1920",
    "-frames:v", "1", "fondo.png",
], check=True)
subprocess.run([
    "ffmpeg", "-y", "-loglevel", "error",
    "-loop", "1", "-i", "fondo.png", "-i", "voz.mp3",
    "-vf", "scale=1080:1920,ass=subs.ass",
    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest",
    "base.mp4",
], check=True)

# 3) Descargar el PNG de cada emoji y superponerlo en su intervalo de tiempo
os.makedirs("emo", exist_ok=True)
inputs, filtros, prev, idx = [], [], "[0:v]", 1
for e in json.load(open("emojis.json", encoding="utf-8")):
    em = e.get("emoji")
    if not em:                                   # palabra sin emoji asignado
        continue
    # nombre del archivo en Twemoji: codepoints en hex, sin el selector FE0F
    cp = "-".join(f"{ord(c):x}" for c in em if ord(c) != 0xFE0F)
    png = f"emo/{cp}.png"
    if not os.path.exists(png):
        try:
            urllib.request.urlretrieve(TWEMOJI.format(cp), png)
        except Exception:
            continue                             # si no existe el PNG, se omite
    inputs += ["-i", png]
    ini, fin = e["start"], e["start"] + e["dur"]
    filtros.append(f"[{idx}:v]scale=140:140[s{idx}]")
    filtros.append(f"{prev}[s{idx}]overlay=(W-w)/2:520:enable='between(t,{ini},{fin})'[v{idx}]")
    prev = f"[v{idx}]"
    idx += 1

# 4) Componer el MP4 final (o usar base.mp4 si no hubo emojis)
if filtros:
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-i", "base.mp4", *inputs,
         "-filter_complex", ";".join(filtros),
         "-map", prev, "-map", "0:a",
         "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "copy", SALIDA],
        check=True,
    )
else:
    os.replace("base.mp4", SALIDA)
print(f"Listo: {SALIDA}")
