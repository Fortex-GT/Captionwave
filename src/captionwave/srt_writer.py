"""
Escritura de .srt (respaldo de compatibilidad).

SRT no admite animaciones ni karaoke: son bloques de texto con tiempo. Sirve
para reproductores/plataformas que no aceptan .ass. La sincronización por línea
se mantiene.
"""

from __future__ import annotations


def _fmt(seconds: float) -> str:
    if seconds < 0:
        seconds = 0
    ms = int(round(seconds * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def build_srt(lines, uppercase: bool = True) -> str:
    out = []
    for i, ln in enumerate(lines, 1):
        text = ln["text"]
        if uppercase:
            text = text.upper()
        out.append(str(i))
        out.append(f"{_fmt(ln['start'])} --> {_fmt(ln['end'])}")
        out.append(text)
        out.append("")
    return "\n".join(out) + "\n"
