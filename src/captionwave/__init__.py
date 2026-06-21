"""
captionwave — genera audio + subtítulos animados sincronizados a partir de texto.

Salidas: .ass (animado), .srt (respaldo), audio (.mp3) y emojis con tiempos.
Tú montas el video con FFmpeg/MoviePy usando esos archivos.
"""

from .core import CaptionGenerator, chunk_words
from .styles import Style, PRESETS, get_style, list_styles, hex_to_ass
from .emojis import EmojiPicker, emoji_for_word, CURADOS

__version__ = "0.3.0"
__all__ = [
    "CaptionGenerator",
    "chunk_words",
    "Style",
    "PRESETS",
    "get_style",
    "list_styles",
    "hex_to_ass",
    "EmojiPicker",
    "emoji_for_word",
    "CURADOS",
]
