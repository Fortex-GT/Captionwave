"""
De texto a un Short en MP4 con emojis A COLOR superpuestos.

Al quemar emojis en el .ass, libass los pinta monocromos o como cuadritos. Aquí
generamos los subtítulos SIN emoji (emoji_in_ass=False), quemamos solo el texto
sobre un fondo y luego superponemos cada emoji como PNG a color (Twemoji) en su
intervalo de tiempo. Los emojis NO se solapan: cada uno desaparece justo cuando
aparece el de la siguiente palabra.

Requisitos:  pip install captionwave  +  FFmpeg  +  conexión a internet
             (voz edge-tts y descarga de los PNG de Twemoji).
Ejecuta:     python examples/emojis_a_color_mp4.py
"""

import json
import os
import subprocess
import urllib.request

from captionwave import CaptionGenerator

# PNG a color de cada emoji. Se prueban varias CDNs (algunas bloquean IPs de
# datacenter) con User-Agent de navegador, para evitar respuestas 403.
CDNS = [
    "https://cdn.jsdelivr.net/gh/twitter/twemoji@14.0.2/assets/72x72/{}.png",
    "https://raw.githubusercontent.com/twitter/twemoji/v14.0.2/assets/72x72/{}.png",
    "https://cdnjs.cloudflare.com/ajax/libs/twemoji/14.0.2/72x72/{}.png",
]
SALIDA = "salida.mp4"


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


# 1) Voz + subtítulos SIN emoji quemado (el emoji va aparte, como PNG a color)
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
    "ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi",
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

# 3) Emojis (en orden temporal) con su PNG a color
os.makedirs("emo", exist_ok=True)
eventos = []
for e in json.load(open("emojis.json", encoding="utf-8")):
    if not e.get("emoji"):
        continue
    png = descargar_emoji(e["emoji"])
    if png:
        eventos.append({"png": png, "start": e["start"], "dur": e["dur"]})

# Sin solapamientos: cada emoji se ve hasta que empieza el siguiente.
for i, ev in enumerate(eventos):
    ev["end"] = eventos[i + 1]["start"] if i + 1 < len(eventos) else ev["start"] + ev["dur"]

# 4) Superponer cada emoji en su intervalo, en una sola pasada de FFmpeg
inputs, filtros, prev = [], [], "[0:v]"
for i, ev in enumerate(eventos, start=1):
    inputs += ["-i", ev["png"]]
    filtros.append(f"[{i}:v]scale=140:140[s{i}]")
    filtros.append(
        f"{prev}[s{i}]overlay=(W-w)/2:470:"
        f"enable='between(t,{ev['start']:.2f},{ev['end']:.2f})'[v{i}]"
    )
    prev = f"[v{i}]"

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
