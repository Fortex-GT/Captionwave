"""
Ejemplo básico: de texto a audio + subtítulos animados.

Requiere internet (edge-tts). Ejecuta:  python examples/basico.py
"""

from captionwave import CaptionGenerator

TEXTO = "El Sol es una estrella que contiene el 99 por ciento de la masa del sistema solar."

gen = CaptionGenerator(
    voice="es-MX-DaliaNeural",
    rate="+18%",
    style="hormozi",        # prueba también: karaoke, pop, neon, single, green, fire, clean
)

resultado = gen.generate(
    TEXTO,
    intro="¿Sabías que...?",      # gancho opcional
    out_audio="voz.mp3",
    out_ass="subs.ass",
    out_srt="subs.srt",
    out_emojis="emojis.json",
)

print("Duración:", round(resultado["duration"], 2), "s")
print("Líneas de subtítulo:")
for ln in resultado["lines"]:
    print(f"  [{ln['start']:.2f}-{ln['end']:.2f}] {ln['emoji']}  {ln['text']}")

print("\nListo. Ahora monta el video, por ejemplo:")
print('  ffmpeg -loop 1 -i fondo.jpg -i voz.mp3 '
      '-vf "scale=1080:1920,ass=subs.ass" '
      '-c:v libx264 -pix_fmt yuv420p -c:a aac -shortest salida.mp4')
