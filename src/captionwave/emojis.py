"""
Asignación palabra -> emoji.

Importante: solo se usan emojis cuya **versión de Unicode** es lo bastante
antigua como para estar presente en iOS. Esto evita "tofus" (cuadritos) en
iPhone. El umbral se controla con `max_version` (por defecto 15.0, que cubre
ampliamente las versiones recientes de iOS).

Nota sobre la APARIENCIA "estilo Apple": este módulo entrega el CARÁCTER de
emoji correcto (un punto de código Unicode), no la imagen de Apple. La imagen
con la que se ve un emoji la pone el sistema/fuente donde se renderice:
  - En un iPhone/Mac se verá con el diseño de Apple automáticamente.
  - En Linux (p. ej. un servidor) se verá con Noto/Twemoji.
La librería NO incluye ni descarga el arte propietario de Apple. Si necesitas
el diseño exacto de Apple en el video, superpón tus propias imágenes usando los
tiempos del emoji que entrega `generate(...)` (campo `emojis`).
"""

from __future__ import annotations
import unicodedata
import functools

import emoji as _emoji_lib


# Palabras que NO deben disparar la búsqueda de emoji.
_STOP = {
    "de", "del", "la", "el", "los", "las", "con", "y", "o", "un", "una", "para",
    "por", "en", "a", "al", "que", "se", "su", "sus", "sin", "sobre", "tipo",
    "como", "este", "esta", "ese", "esa", "es", "son", "tiene", "tienen", "fue",
    "ser", "han", "hay", "muy", "mas", "menos", "todo", "toda", "todos", "mismo",
    "cada", "entre", "hasta", "cuando", "donde", "porque", "mucho", "mucha",
    "uno", "dos", "tres", "cuatro", "cinco", "seis", "siete", "ocho", "nueve",
    "diez", "cien", "mil", "veces", "vez", "casi", "tan", "tanto", "cerca",
}

# Diccionario curado: control fino para palabras clave frecuentes.
CURADOS = {
    "estrella": "⭐", "estrellas": "⭐", "estelar": "⭐",
    "galaxia": "🌌", "galaxias": "🌌", "universo": "🌌", "cosmos": "🌌",
    "tierra": "🌍", "mundo": "🌍", "planeta": "🪐", "planetas": "🪐",
    "agua": "💧", "liquido": "💧", "oceano": "🌊", "mar": "🌊", "ola": "🌊",
    "arbol": "🌳", "arboles": "🌳", "bosque": "🌳", "selva": "🌳", "planta": "🌱",
    "cometa": "☄️", "meteorito": "☄️", "asteroide": "☄️",
    "luz": "💡", "brillo": "💡", "ilumina": "💡",
    "energia": "⚡", "electricidad": "⚡", "rayo": "⚡", "rayos": "⚡",
    "explosion": "💥", "estalla": "💥", "impacto": "💥", "choque": "💥",
    "molecula": "⚛️", "atomo": "⚛️", "particula": "⚛️", "neutron": "⚛️",
    "proton": "⚛️", "electron": "⚛️",
    "quimica": "🧪", "reaccion": "🧪", "experimento": "🔬", "ciencia": "🔬",
    "cientifico": "🔬", "microscopio": "🔬",
    "celula": "🦠", "celulas": "🦠", "virus": "🦠", "bacteria": "🦠", "microbio": "🦠",
    "dinosaurio": "🦕", "dinosaurios": "🦕", "fosil": "🦴",
    "terremoto": "🌋", "sismo": "🌋", "volcan": "🌋",
    "numero": "🔢", "numeros": "🔢", "millones": "🔢", "miles": "🔢",
    "diamante": "💎", "cristal": "💎", "oro": "🪙",
    "velocidad": "⚡", "veloz": "⚡", "rapido": "⚡",
    "calor": "🔥", "caliente": "🔥", "fuego": "🔥",
    "temperatura": "🌡️", "frio": "❄️", "congelado": "❄️", "hielo": "🧊",
    "aire": "💨", "viento": "💨", "gas": "💨",
    "oxigeno": "🫁", "pulmon": "🫁", "pulmones": "🫁",
    "sonido": "🔊", "oido": "👂", "musica": "🎵",
    "computadora": "💻", "ordenador": "💻", "datos": "💻",
    "tiempo": "⏳", "reloj": "⏰", "año": "📅", "años": "📅", "siglo": "📅",
    "cerebro": "🧠", "corazon": "❤️", "sangre": "🩸", "hueso": "🦴",
    "sol": "☀️", "luna": "🌙", "noche": "🌙", "dia": "🌞",
    "dinero": "💰", "ojo": "👀", "ojos": "👀", "mente": "🧠",
}

# Emojis de respaldo cuando no se encuentra nada relevante.
DEFAULTS = ["✨", "🤯", "💫", "👀", "🔥"]


def _norm(w: str) -> str:
    """minúsculas, sin acentos (conservando ñ), solo letras."""
    w = w.lower().replace("ñ", "\x00")
    w = "".join(c for c in unicodedata.normalize("NFKD", w) if not unicodedata.combining(c))
    w = w.replace("\x00", "ñ")
    return "".join(c for c in w if c.isalpha())


def _es_bandera(ch: str) -> bool:
    return any(0x1F1E6 <= ord(c) <= 0x1F1FF or c == "\U0001F3F4" for c in ch)


@functools.lru_cache(maxsize=8)
def _build_index(max_version: float):
    """Construye {palabra_norm: emoji} desde la librería emoji.

    Filtra por versión (compatibilidad iOS), descarta banderas y se queda con
    el nombre más específico para cada palabra.
    """
    idx: dict[str, tuple[str, int]] = {}
    try:
        _emoji_lib.config.load_language("es")
    except Exception:
        pass
    for ch, d in _emoji_lib.EMOJI_DATA.items():
        if d.get("status") != _emoji_lib.STATUS["fully_qualified"]:
            continue
        ver = d.get("E")
        if not isinstance(ver, (int, float)) or ver > max_version:
            continue
        if _es_bandera(ch):
            continue
        nombre = d.get("es") or d.get("en")
        if not nombre:
            continue
        tokens = nombre.strip(":").split("_")
        ntok = len(tokens)
        for t in tokens:
            k = _norm(t)
            if len(k) < 3 or k in _STOP:
                continue
            if k not in idx or ntok < idx[k][1]:
                idx[k] = (ch, ntok)
    return idx


class EmojiPicker:
    """Selecciona emojis para palabras y frases, limitado a iOS."""

    def __init__(self, max_version: float = 15.0):
        self.max_version = max_version
        self._idx = _build_index(max_version)

    def for_word(self, palabra: str):
        """Devuelve un emoji para una sola palabra, o None si no aplica."""
        k = _norm(palabra)
        if not k or k in _STOP:
            return None
        if k in CURADOS:
            return CURADOS[k]
        # plurales sencillos
        for suf in ("es", "s"):
            base = k[:-len(suf)]
            if k.endswith(suf) and len(base) >= 3 and base in CURADOS:
                return CURADOS[base]
        if k in self._idx:
            return self._idx[k][0]
        for suf in ("es", "s"):
            base = k[:-len(suf)]
            if k.endswith(suf) and len(base) >= 3 and base in self._idx:
                return self._idx[base][0]
        return None

    def for_phrase(self, frase: str, fallback_idx: int = 0):
        """Mejor emoji para una frase (busca en sus palabras, de larga a corta)."""
        for w in sorted(frase.split(), key=len, reverse=True):
            e = self.for_word(w)
            if e:
                return e
        return DEFAULTS[fallback_idx % len(DEFAULTS)]

    def is_ios_safe(self, ch: str) -> bool:
        """True si el emoji está dentro de la versión permitida (iOS)."""
        d = _emoji_lib.EMOJI_DATA.get(ch)
        if not d:
            return False
        ver = d.get("E")
        return isinstance(ver, (int, float)) and ver <= self.max_version
