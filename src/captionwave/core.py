"""
API principal de captionwave.

Ejemplo mínimo:

    from captionwave import CaptionGenerator

    gen = CaptionGenerator(voice="es-MX-DaliaNeural", rate="+18%", style="hormozi")
    r = gen.generate(
        "El Sol es una estrella que contiene el 99% de la masa del sistema solar.",
        out_audio="voz.mp3",
        out_ass="subs.ass",
        out_srt="subs.srt",
    )
    print(r["duration"], "segundos")

Devuelve un dict con: audio, ass, srt, duration, words, lines, emojis.
Los archivos quedan listos para que tú montes el video (FFmpeg, MoviePy, etc.).
"""

from __future__ import annotations
import json
from typing import Optional, Union

from .styles import Style, get_style, list_styles  # re-export
from .emojis import EmojiPicker
from . import tts as _tts
from . import ass_writer as _ass
from . import srt_writer as _srt


def chunk_words(words, max_words=3, max_chars=18, total=None):
    """Agrupa palabras en líneas. Devuelve lista de dicts con start/end/words/text."""
    lines = []
    cur = []
    for w in words:
        cur.append(w)
        txt = " ".join(x["word"] for x in cur)
        if len(cur) >= max_words or len(txt) >= max_chars:
            lines.append(cur)
            cur = []
    if cur:
        lines.append(cur)

    salida = []
    for grupo in lines:
        salida.append({
            "words": grupo,
            "start": grupo[0]["start"],
            "end": grupo[-1]["start"] + grupo[-1]["dur"],
            "text": " ".join(x["word"] for x in grupo),
        })
    # El fin de cada línea = inicio de la siguiente (subtítulos continuos)
    for i in range(len(salida) - 1):
        salida[i]["end"] = salida[i + 1]["start"]
    if salida:
        fin = total if total else (salida[-1]["end"] + 0.4)
        salida[-1]["end"] = max(salida[-1]["end"], fin)
    return salida


class CaptionGenerator:
    def __init__(
        self,
        voice: str = "es-MX-DaliaNeural",
        rate: str = "+0%",
        style: Union[str, Style] = "hormozi",
        emoji: bool = True,
        emoji_max_version: float = 15.0,
        emoji_in_ass: bool = True,
        resolution=(1080, 1920),
    ):
        self.voice = voice
        self.rate = rate
        self.style = get_style(style)
        self.use_emoji = emoji
        self.emoji_in_ass = emoji_in_ass
        self.resolution = resolution
        self._picker = EmojiPicker(emoji_max_version) if emoji else None

    # -- API principal --
    def generate(
        self,
        text: str,
        out_audio: str = "audio.mp3",
        out_ass: Optional[str] = "subs.ass",
        out_srt: Optional[str] = None,
        out_emojis: Optional[str] = None,
        intro: Optional[str] = None,
        intro_rate: Optional[str] = None,
    ) -> dict:
        """Genera audio + subtítulos sincronizados a partir de `text`.

        intro: texto opcional que se dice ANTES (p. ej. un gancho), con su propio
               ritmo `intro_rate`. Sus tiempos se integran automáticamente.
        """
        # 1) Voz + tiempos por palabra
        if intro:
            parts = [(intro.strip(), intro_rate or self.rate), (text.strip(), self.rate)]
            words, dur = _tts.synthesize_segments(parts, voice=self.voice, out_path=out_audio)
        else:
            words, dur = _tts.synthesize(text, voice=self.voice, rate=self.rate, out_path=out_audio)

        if not words:
            raise RuntimeError("El TTS no devolvió palabras. ¿Conexión a internet / voz válida?")

        # 2) Construir subtítulos a partir de los tiempos por palabra del TTS
        resultado = self.build_from_words(
            words, dur, out_ass=out_ass, out_srt=out_srt, out_emojis=out_emojis,
        )
        resultado["audio"] = out_audio
        return resultado

    # -- API sin TTS (offline) --
    def build_from_words(
        self,
        words,
        duration: float,
        out_ass: Optional[str] = "subs.ass",
        out_srt: Optional[str] = None,
        out_emojis: Optional[str] = None,
    ) -> dict:
        """Construye los subtítulos a partir de tiempos por palabra ya calculados.

        No usa TTS ni internet: tú aportas
        ``words = [{"word", "start", "dur"}, ...]`` (en segundos) y la duración
        total. Útil para pruebas, pipelines offline o cuando ya tienes los
        tiempos de otra fuente.

        Devuelve el mismo dict que ``generate`` (con ``audio=None``).
        """
        if not words:
            raise ValueError("`words` está vacío: no hay nada que subtitular.")

        # 1) Agrupar en líneas
        lines = chunk_words(words, self.style.max_words, self.style.max_chars, total=duration)

        # 2) Emojis: por línea (para el .ass) y por palabra (para overlay propio)
        emojis_palabra = []
        if self.use_emoji and self._picker:
            for i, ln in enumerate(lines):
                ln["emoji"] = self._picker.for_phrase(ln["text"], i)
            for w in words:
                emojis_palabra.append({
                    "word": w["word"],
                    "emoji": self._picker.for_word(w["word"]),
                    "start": round(w["start"], 3),
                    "dur": round(w["dur"], 3),
                })

        # 3) Escribir .ass
        if out_ass:
            ass_text = _ass.build_ass(
                lines, self.style, resolution=self.resolution,
                emoji_in_ass=(self.emoji_in_ass and self.use_emoji),
            )
            with open(out_ass, "w", encoding="utf-8") as f:
                f.write(ass_text)

        # 4) Escribir .srt (opcional)
        if out_srt:
            with open(out_srt, "w", encoding="utf-8") as f:
                f.write(_srt.build_srt(lines, uppercase=self.style.uppercase))

        # 5) Escribir emojis.json (opcional, para superponer arte propio)
        if out_emojis and self.use_emoji:
            with open(out_emojis, "w", encoding="utf-8") as f:
                json.dump(emojis_palabra, f, ensure_ascii=False, indent=2)

        return {
            "audio": None,
            "ass": out_ass,
            "srt": out_srt,
            "duration": duration,
            "words": words,
            "lines": [
                {"text": ln["text"], "start": ln["start"], "end": ln["end"],
                 "emoji": ln.get("emoji")}
                for ln in lines
            ],
            "emojis": emojis_palabra,
        }
