"""
Ejemplo de montaje completo con FFmpeg.

Genera audio + .ass y luego quema los subtítulos sobre una imagen de fondo,
produciendo el MP4 final. Necesita FFmpeg instalado y un archivo `fondo.jpg`
(o cambia la ruta). Ejecuta:  python examples/montaje_ffmpeg.py
"""

import subprocess
from captionwave import CaptionGenerator

FONDO = "fondo.jpg"     # tu imagen vertical de fondo (o usa un .mp4 con -loop quitado)
SALIDA = "salida.mp4"

gen = CaptionGenerator(voice="es-MX-DaliaNeural", rate="+18%", style="pop")

r = gen.generate(
    "El cerebro humano genera suficiente electricidad para encender una pequeña bombilla.",
    intro="Dato curioso:",
    out_audio="voz.mp3",
    out_ass="subs.ass",
)

# Quemar subtítulos sobre la imagen, con la voz como audio.
cmd = [
    "ffmpeg", "-y",
    "-loop", "1", "-i", FONDO,
    "-i", "voz.mp3",
    "-vf", "scale=1080:1920,ass=subs.ass",
    "-c:v", "libx264", "-pix_fmt", "yuv420p",
    "-c:a", "aac", "-shortest",
    SALIDA,
]
print("Ejecutando FFmpeg...")
subprocess.run(cmd, check=True)
print(f"Video creado: {SALIDA}  ({r['duration']:.1f}s)")
