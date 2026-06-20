"""
De texto a un Short en MP4: voz + subtítulos animados quemados, todo en uno.

Genera voz.mp3 + subs.ass con captionwave y los monta sobre un fondo de color
vertical (1080x1920) con FFmpeg -> salida.mp4. No necesita ningún archivo previo.

Requisitos:  pip install captionwave   +   FFmpeg (ffmpeg -version)   +   internet.
Ejecuta:     python examples/texto_a_mp4.py
"""

import subprocess

from captionwave import CaptionGenerator

TEXTO = "El Sol es una estrella que contiene el 99% de la masa del sistema solar."
SALIDA = "salida.mp4"

# 1) Voz + subtítulos sincronizados
gen = CaptionGenerator(voice="es-MX-DaliaNeural", rate="+18%", style="fire")
r = gen.generate(TEXTO, out_audio="voz.mp3", out_ass="subs.ass")
print("Duración:", round(r["duration"], 2), "s")

# 2) Duración real del audio (para acotar el fondo)
dur = subprocess.run(
    ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
     "-of", "csv=p=0", "voz.mp3"],
    capture_output=True, text=True, check=True,
).stdout.strip()

# 3) Fondo de color 1080x1920 + subtítulos quemados + voz
subprocess.run([
    "ffmpeg", "-y", "-loglevel", "error",
    "-f", "lavfi", "-i", f"color=c=0x0E1116:s=1080x1920:r=30:d={dur}",
    "-i", "voz.mp3",
    "-vf", "ass=subs.ass",
    "-c:v", "libx264", "-pix_fmt", "yuv420p",
    "-c:a", "aac", "-shortest",
    SALIDA,
], check=True)
print(f"Listo: {SALIDA}")
