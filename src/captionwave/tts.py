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
import os

import edge_tts


def _run_sync(coro):
    """Ejecuta una corrutina de forma síncrona, también dentro de Jupyter/Colab.

    En un script normal basta con ``asyncio.run``. Pero en notebooks (Google
    Colab, Jupyter) ya hay un event loop corriendo y ``asyncio.run`` fallaría
    con "cannot be called from a running event loop"; en ese caso la corrutina
    se ejecuta en un hilo aparte con su propio loop.
    """
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)  # no hay loop activo: caso normal (script)

    import threading

    box = {}

    def _worker():
        try:
            box["value"] = asyncio.run(coro)
        except BaseException as exc:  # se re-lanza en el hilo principal
            box["error"] = exc

    t = threading.Thread(target=_worker)
    t.start()
    t.join()
    if "error" in box:
        raise box["error"]
    return box["value"]


def _try_duration(path: str):
    """Intenta leer la duración real del MP3 con mutagen, si está instalado."""
    try:
        from mutagen.mp3 import MP3  # opcional
        return float(MP3(path).info.length)
    except Exception:
        return None


def _make_communicate(text: str, voice: str, rate: str):
    """Crea un Communicate pidiendo eventos por palabra (WordBoundary).

    edge-tts >= 7 cambió el valor por defecto del parámetro ``boundary`` a
    "SentenceBoundary"; sin "WordBoundary" no llegan los tiempos por palabra y
    los subtítulos saldrían vacíos. En edge-tts < 7 ese parámetro no existe (y
    el valor por defecto ya era WordBoundary), así que se omite.
    """
    try:
        return edge_tts.Communicate(text, voice, rate=rate, boundary="WordBoundary")
    except TypeError:
        return edge_tts.Communicate(text, voice, rate=rate)


async def _stream_one(text: str, voice: str, rate: str, fh):
    """Escribe el audio de un segmento en el handle abierto `fh` y devuelve sus palabras."""
    com = _make_communicate(text, voice, rate)
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
    try:
        words = _run_sync(_run(list(parts), voice, out_path))
    except Exception as e:
        # No dejes un .mp3 vacío/parcial tras un fallo.
        try:
            if os.path.exists(out_path) and os.path.getsize(out_path) == 0:
                os.remove(out_path)
        except OSError:
            pass
        raise RuntimeError(
            "No se pudo generar la voz con edge-tts. Comprueba:\n"
            "  • que tengas conexión a internet (edge-tts usa el servicio de "
            "Microsoft Edge),\n"
            "  • que ninguna red/proxy/firewall bloquee speech.platform.bing.com,\n"
            f"  • que la voz exista (voz='{voice}'; lista: 'edge-tts --list-voices').\n"
            f"Detalle técnico: {type(e).__name__}: {e}"
        ) from e

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
