"""
Estilos de subtítulos.

Cada estilo combina:
  - una `animation` (cómo se mueve/resalta la palabra activa)
  - colores, fuente, tamaño, posición

Los colores se escriben en HEX normal ("#RRGGBB") y se convierten al
formato de ASS internamente. Puedes usar un preset tal cual o copiarlo y
cambiarle cualquier campo.

Animaciones disponibles:
  - "karaoke"        -> barrido tipo karaoke (color tenue -> color activo)
  - "active_color"   -> solo la palabra que se está diciendo cambia de color
  - "active_pop"     -> la palabra activa crece (rebote) y cambia de color
  - "active_sticker" -> la palabra activa recibe un "sticker" de fondo (estilo Hormozi)
  - "single_word"    -> una palabra a la vez, grande y centrada
  - "fade"           -> la frase aparece con fade + palabra activa en color
"""

from __future__ import annotations
from dataclasses import dataclass, replace
from typing import Optional


def hex_to_ass(color: str, alpha: int = 0) -> str:
    """Convierte '#RRGGBB' al formato de color de ASS '&HAABBGGRR'.

    alpha: 0 = opaco, 255 = totalmente transparente.
    """
    c = color.lstrip("#")
    if len(c) == 3:
        c = "".join(ch * 2 for ch in c)
    r = int(c[0:2], 16)
    g = int(c[2:4], 16)
    b = int(c[4:6], 16)
    return f"&H{alpha:02X}{b:02X}{g:02X}{r:02X}"


@dataclass
class Style:
    name: str = "custom"
    animation: str = "active_color"   # ver lista arriba

    # Tipografía
    font: str = "DejaVu Sans"         # nombre de la fuente (debe existir en el sistema que renderiza)
    font_file: Optional[str] = None   # ruta opcional al .ttf (útil para fijar la fuente al render)
    font_size: int = 84
    bold: bool = True

    # Colores
    base_color: str = "#FFFFFF"       # color normal del texto
    active_color: str = "#FFD23F"     # color de la palabra activa
    outline_color: str = "#000000"    # contorno
    outline_w: int = 5
    shadow: int = 0

    # Solo para animation="active_sticker"
    sticker_color: str = "#FFD23F"        # color del "sticker" de fondo
    sticker_text_color: str = "#000000"   # color del texto cuando está sobre el sticker
    sticker_bord: int = 18                # grosor del sticker

    # Solo para animation="active_pop" / "single_word"
    pop_scale: int = 130              # % de escala al hacer "pop"

    # Texto
    uppercase: bool = True
    max_words: int = 3                # máximo de palabras por línea
    max_chars: int = 18              # corte adicional por longitud

    # Posición: "center" (medio de la pantalla), "lower" (abajo), "upper" (arriba)
    position: str = "center"
    margin_v: int = 260               # margen vertical cuando position != center

    def copy(self, **cambios) -> "Style":
        """Devuelve una copia del estilo con los campos indicados modificados."""
        return replace(self, **cambios)


# --------------------------------------------------------------------------
#   PRESETS  (inspirados en las opciones de revid.ai)
# --------------------------------------------------------------------------
PRESETS = {
    # Clásico de Shorts/Reels: palabra activa con "sticker" amarillo.
    "hormozi": Style(
        name="hormozi", animation="active_sticker",
        base_color="#FFFFFF", active_color="#FFD23F",
        sticker_color="#FFD23F", sticker_text_color="#101010",
        font_size=88, outline_w=6, uppercase=True, max_words=3,
    ),
    # Barrido karaoke: el texto se "llena" de color al ritmo de la voz.
    "karaoke": Style(
        name="karaoke", animation="karaoke",
        base_color="#FFFFFF", active_color="#FFD23F",
        font_size=82, outline_w=5, uppercase=True, max_words=4,
    ),
    # La palabra activa crece con un rebote.
    "pop": Style(
        name="pop", animation="active_pop",
        base_color="#FFFFFF", active_color="#FFD23F",
        pop_scale=134, font_size=84, outline_w=5, uppercase=True, max_words=3,
    ),
    # Una sola palabra a la vez, grande y centrada.
    "single": Style(
        name="single", animation="single_word",
        base_color="#FFFFFF", active_color="#FFD23F",
        pop_scale=118, font_size=120, outline_w=7, uppercase=True,
    ),
    # Neón: contorno de color y palabra activa cian.
    "neon": Style(
        name="neon", animation="active_color",
        base_color="#FFFFFF", active_color="#27E1FF",
        outline_color="#0066FF", outline_w=5, font_size=82, uppercase=True, max_words=3,
    ),
    # Sticker verde.
    "green": Style(
        name="green", animation="active_sticker",
        base_color="#FFFFFF", active_color="#27E36B",
        sticker_color="#27E36B", sticker_text_color="#08240F",
        font_size=86, outline_w=6, uppercase=True, max_words=3,
    ),
    # "Fuego": palabra activa naranja con pop.
    "fire": Style(
        name="fire", animation="active_pop",
        base_color="#FFFFFF", active_color="#FF5630",
        pop_scale=132, font_size=84, outline_w=5, uppercase=True, max_words=3,
    ),
    # Limpio: parecido a unos subtítulos blancos con contorno (estilo simple).
    "clean": Style(
        name="clean", animation="active_color",
        base_color="#FFFFFF", active_color="#FFE9A8",
        outline_color="#000000", outline_w=5, font_size=78,
        uppercase=True, max_words=3, position="lower",
    ),
}


def get_style(estilo) -> Style:
    """Acepta un nombre de preset (str) o un objeto Style y devuelve un Style."""
    if isinstance(estilo, Style):
        return estilo
    if isinstance(estilo, str):
        key = estilo.lower()
        if key not in PRESETS:
            disponibles = ", ".join(sorted(PRESETS))
            raise ValueError(f"Estilo '{estilo}' no existe. Disponibles: {disponibles}")
        return PRESETS[key].copy()
    raise TypeError("estilo debe ser un nombre (str) o un objeto Style")


def list_styles() -> list[str]:
    """Lista los nombres de los presets disponibles."""
    return sorted(PRESETS)
