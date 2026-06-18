"""
Ejemplo OFFLINE: genera subtítulos animados (.ass/.srt) SIN internet y SIN TTS.

Normalmente los tiempos por palabra los calcula edge-tts. Aquí los aportamos a
mano para demostrar que la librería (instalada con `pip install`) funciona
aunque no haya red ni FFmpeg. Útil para probar la instalación o integrarla en
un pipeline donde ya tienes los tiempos.

Ejecuta (tras `pip install -e .` desde la raíz del repo):

    python examples/offline_sin_internet.py
"""

from captionwave import CaptionGenerator

# words = [{"word", "start", "dur"}, ...]  (tiempos en segundos)
PALABRAS = [
    {"word": "El",       "start": 0.00, "dur": 0.18},
    {"word": "Sol",      "start": 0.18, "dur": 0.34},
    {"word": "es",       "start": 0.52, "dur": 0.16},
    {"word": "una",      "start": 0.68, "dur": 0.18},
    {"word": "estrella", "start": 0.86, "dur": 0.52},
    {"word": "enorme",   "start": 1.38, "dur": 0.50},
]
DURACION = 2.0  # duración total del audio en segundos

gen = CaptionGenerator(
    style="hormozi",   # prueba también: karaoke, pop, neon, single, green, fire, clean
)

resultado = gen.build_from_words(
    PALABRAS,
    DURACION,
    out_ass="subs.ass",
    out_srt="subs.srt",
    out_emojis="emojis.json",
)

print("Subtítulos generados SIN internet ni TTS:")
for ln in resultado["lines"]:
    print(f"  [{ln['start']:.2f}-{ln['end']:.2f}] {ln['emoji']}  {ln['text']}")

print("\nArchivos: subs.ass, subs.srt, emojis.json")
print("Falta solo el audio (eso sí necesita edge-tts); ver examples/basico.py.")
