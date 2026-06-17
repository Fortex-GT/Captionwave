"""
Generación de voz (TTS) con tiempos por palabra.

Usa edge-tts. La clave de la sincronización es que el motor devuelve eventos
`WordBoundary` con el offset y duración EXACTOS de cada palabra dentro del audio
que se está generando. Por eso los subtítulos quedan pegados al audio: ambos
salen de la misma fuente.

Requiere conexión a internet (endpoint de Microsoft Edge TTS).
"""

from __future__ import annotations
import asyncio

import edge_tts


def _try_duration(path: str):
    """Intenta leer la duración real del MP3 con mutagen, si está instalado."""
    try:
        from mutagen.mp3 import MP3  # opcional
        return float(MP3(path).info.length)
    except Exception:
        return None


async def _stream_one(text: str, voice: str, rate: str, fh):
    """Escribe el audio de un segmento en el handle abierto `fh` y devuelve sus palabras."""
    com = edge_tts.Communicate(text, voice, rate=rate)
    words = []
    async for chunk in com.stream():
        if chunk["type"] == "audio":
            fh.write(chunk["data"])
        elif chunk["type"] == "WordBoundary":
            words.append({
                "word": chunk["text"],
                "start": chunk["offset"] / 1e7,
                "dur": max(chunk["duration"] / 1e7, 0.02),
            })
    return words


async def _run(parts, voice, out_path):
    """parts = [(text, rate), ...]  -> audio concatenado + palabras con offset acumulado."""
    todas = []
    cursor = 0.0
    with open(out_path, "wb") as fh:
        for (text, rate) in parts:
            ws = await _stream_one(text, voice, rate, fh)
            for w in ws:
                todas.append({"word": w["word"], "start": w["start"] + cursor, "dur": w["dur"]})
            # avanzar el cursor por la duración de este segmento
            if ws:
                cursor = todas[-1]["start"] + todas[-1]["dur"]
            else:
                cursor = cursor  # segmento sin palabras (raro)
    return todas


def synthesize(text: str, voice: str = "es-MX-DaliaNeural",
               rate: str = "+0%", out_path: str = "audio.mp3"):
    """Genera audio de un texto y devuelve (words, duration).

    words: lista de dicts {word, start, dur} en segundos.
    duration: duración total estimada del audio (s).
    """
    return synthesize_segments([(text, rate)], voice=voice, out_path=out_path)


def synthesize_segments(parts, voice: str = "es-MX-DaliaNeural",
                        out_path: str = "audio.mp3"):
    """Igual que synthesize, pero une varios segmentos (p. ej. intro + cuerpo).

    parts: lista de tuplas (texto, rate). Ej: [("¿Sabías que...?", "+25%"),
           ("el sol es una estrella", "+18%")]
    """
    words = asyncio.run(_run(list(parts), voice, out_path))

    if not words:
        dur = _try_duration(out_path) or 0.0
        return words, dur

    last_end = words[-1]["start"] + words[-1]["dur"]
    real = _try_duration(out_path)

    if real and last_end > 0.3:
        # Reescalar suavemente para alinear el último subtítulo con el fin real
        factor = real / last_end
        if 0.85 <= factor <= 1.15:
            for w in words:
                w["start"] *= factor
                w["dur"] = max(w["dur"] * factor, 0.02)
        dur = real
    else:
        dur = last_end + 0.4  # colchón final

    return words, dur
