"""
Escritura del archivo .ass (Advanced SubStation Alpha).

Genera subtítulos animados que libass/ffmpeg renderiza de forma nativa. La
sincronización viene de los tiempos por palabra del TTS.

Técnica de resaltado: para los estilos de "palabra activa" se emite UN evento
por palabra, dibujando la línea completa con solo la palabra en curso resaltada.
Así nunca hay dos palabras activas, la posición no se mueve y se evita una
limitación de libass al encadenar varias transiciones \\t con huecos.
"""

from __future__ import annotations
from .styles import Style, hex_to_ass


# ---- utilidades de tiempo ----
def _fmt_time(seconds: float) -> str:
    if seconds < 0:
        seconds = 0
    cs = int(round(seconds * 100))
    h, cs = divmod(cs, 360000)
    m, cs = divmod(cs, 6000)
    s, cs = divmod(cs, 100)
    return f"{h:d}:{m:02d}:{s:02d}.{cs:02d}"


def _alignment(position: str) -> int:
    return {"center": 5, "lower": 2, "upper": 8}.get(position, 5)


def _txt(word: str, upper: bool) -> str:
    return word.upper() if upper else word


def _word_windows(words, line_start, line_end):
    """Ventana [inicio, fin) de cada palabra, continua (sin huecos)."""
    n = len(words)
    wins = []
    for i, w in enumerate(words):
        s = w["start"]
        e = words[i + 1]["start"] if i + 1 < n else line_end
        if e <= s:
            e = s + 0.12
        wins.append((i, s, e))
    return wins


# ---- karaoke (usa \k nativo de libass) ----
def _line_karaoke(style: Style, words, line_start):
    al = _alignment(style.position)
    parts = ["{\\an%d}" % al]
    cursor = 0
    for w in words:
        s = max(0, int(round((w["start"] - line_start) * 100)))
        e = max(s + 1, int(round((w["start"] + w["dur"] - line_start) * 100)))
        gap = s - cursor
        if gap > 0:
            parts.append("{\\k%d} " % gap)
        parts.append("{\\kf%d}%s " % (max(1, e - s), _txt(w["word"], style.uppercase)))
        cursor = e
    return "".join(parts).rstrip()


# ---- línea completa con UNA palabra resaltada (estática + pop opcional) ----
def _render_active(words, active_idx, style, fad=(0, 0)):
    al = _alignment(style.position)
    base = hex_to_ass(style.base_color)
    act = hex_to_ass(style.active_color)
    anim = style.animation

    head = "{\\an%d" % al
    if fad != (0, 0):
        head += "\\fad(%d,%d)" % fad
    head += "}"
    parts = [head]

    for k, w in enumerate(words):
        word = _txt(w["word"], style.uppercase)
        activa = (k == active_idx)
        if anim == "active_sticker":
            if activa:
                on = hex_to_ass(style.sticker_text_color)
                stick = hex_to_ass(style.sticker_color)
                blk = "{\\1c%s\\3c%s\\bord%d\\fscx70\\fscy70\\t(0,9,\\fscx100\\fscy100)}" % (
                    on, stick, style.sticker_bord)
            else:
                outline = hex_to_ass(style.outline_color)
                blk = "{\\1c%s\\3c%s\\bord%d}" % (base, outline, style.outline_w)
        elif anim == "active_pop":
            if activa:
                p = style.pop_scale
                blk = "{\\1c%s\\fscx80\\fscy80\\t(0,9,\\fscx%d\\fscy%d)}" % (act, p, p)
            else:
                blk = "{\\1c%s\\fscx100\\fscy100}" % base
        else:  # active_color / fade
            blk = "{\\1c%s}" % (act if activa else base)
        parts.append(blk + word + " ")

    return "".join(parts).rstrip()


def _line_events(ln, style):
    """Devuelve lista de (start, end, text) para una línea según su animación."""
    words = ln["words"]
    ls, le = ln["start"], ln["end"]
    anim = style.animation

    if anim == "karaoke":
        return [(ls, le, _line_karaoke(style, words, ls))]

    wins = _word_windows(words, ls, le)
    n = len(wins)
    evs = []
    for (i, s, e) in wins:
        fad = (0, 0)
        if anim == "fade":
            fad = (120 if i == 0 else 0, 120 if i == n - 1 else 0)
        evs.append((s, e, _render_active(words, i, style, fad=fad)))
    return evs


# ---- single_word: una palabra a la vez, grande y centrada ----
def _single_word_events(style: Style, words, total):
    act = hex_to_ass(style.active_color)
    rows = []
    n = len(words)
    for i, w in enumerate(words):
        s = w["start"]
        e = words[i + 1]["start"] if i + 1 < n else total
        if e <= s + 0.05:
            e = s + 0.2
        txt = ("{\\an5\\1c%s\\fscx70\\fscy70\\t(0,140,\\fscx100\\fscy100)\\fad(50,50)}%s"
               % (act, _txt(w["word"], style.uppercase)))
        rows.append((s, e, txt))
    return rows


# ---- cabecera y estilos ----
def _header(style: Style, W: int, H: int) -> str:
    primary = (hex_to_ass(style.active_color)
               if style.animation == "karaoke" else hex_to_ass(style.base_color))
    secondary = hex_to_ass(style.base_color)
    outline = hex_to_ass(style.outline_color)
    back = hex_to_ass("#000000")
    bold = -1 if style.bold else 0
    align = _alignment(style.position)
    margin_v = 0 if style.position == "center" else style.margin_v
    mh = style.margin_h

    return (
        "[Script Info]\n"
        "ScriptType: v4.00+\n"
        "WrapStyle: 0\n"
        "ScaledBorderAndShadow: yes\n"
        f"PlayResX: {W}\n"
        f"PlayResY: {H}\n"
        "YCbCr Matrix: TV.709\n"
        "\n"
        "[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, "
        "OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, "
        "ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
        "Alignment, MarginL, MarginR, MarginV, Encoding\n"
        f"Style: Main,{style.font},{style.font_size},{primary},{secondary},"
        f"{outline},{back},{bold},0,0,0,100,100,0,0,1,{style.outline_w},"
        f"{style.shadow},{align},{mh},{mh},{margin_v},1\n"
        f"Style: Emoji,{style.font},96,&H00FFFFFF,&H00FFFFFF,&H00000000,"
        f"&H00000000,0,0,0,0,100,100,0,0,1,0,0,5,0,0,0,1\n"
        "\n"
        "[Events]\n"
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    )


def _dialogue(start, end, text, style_name="Main", layer=0):
    return f"Dialogue: {layer},{_fmt_time(start)},{_fmt_time(end)},{style_name},,0,0,0,,{text}\n"


def build_ass(lines, style: Style, resolution=(1080, 1920),
              emojis=None, emoji_in_ass=True) -> str:
    """Construye el contenido completo del .ass.

    lines: lista de dicts {words:[{word,start,dur}], start, end, emoji?}
    """
    W, H = resolution
    chunks = [_header(style, W, H)]

    if style.animation == "single_word":
        flat = [w for ln in lines for w in ln["words"]]
        total = lines[-1]["end"] if lines else 0.0
        for (s, e, t) in _single_word_events(style, flat, total):
            chunks.append(_dialogue(s, e, t))
    else:
        for ln in lines:
            for (s, e, t) in _line_events(ln, style):
                chunks.append(_dialogue(s, e, t))

    # Emoji por línea (capa superior). Ojo: libass no garantiza emoji a color
    # (ver nota en emojis.py); usa emojis.json para superponer tu propio arte.
    if emoji_in_ass:
        cx, cy = W // 2, int(H * 0.34)
        for ln in lines:
            em = ln.get("emoji")
            if not em:
                continue
            txt = "{\\an5\\pos(%d,%d)\\fad(120,120)}%s" % (cx, cy, em)
            chunks.append(_dialogue(ln["start"], ln["end"], txt, style_name="Emoji", layer=2))

    return "".join(chunks)
