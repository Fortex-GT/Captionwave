# Ejemplos de captionwave

Estos scripts usan la librería tal como se usaría tras instalarla con `pip`.

## 1. Instalar el paquete

```bash
pip install captionwave
```

Para desarrollo, desde la raíz del repositorio:

```bash
pip install -e ".[test]"   # incluye pytest
```

Extras opcionales: `".[duration]"` (mutagen, duración exacta del audio) y
`".[video]"` (moviepy).

## 2. Ejecutar los ejemplos

| Script | Internet | FFmpeg | Qué hace |
|--------|:---:|:---:|----------|
| [`offline_sin_internet.py`](offline_sin_internet.py) | ❌ | ❌ | `.ass`/`.srt` a partir de tiempos dados a mano. **Ideal para verificar la instalación.** |
| [`basico.py`](basico.py) | ✅ | ❌ | Voz (edge-tts) + subtítulos + emojis sincronizados. |
| [`texto_a_mp4.py`](texto_a_mp4.py) | ✅ | ✅ | Todo el flujo → `salida.mp4` sobre un fondo de color (sin archivos extra). |
| [`emojis_a_color_mp4.py`](emojis_a_color_mp4.py) | ✅ | ✅ | Como el anterior pero con **emojis a color** superpuestos (PNG de Twemoji). |
| [`montaje_ffmpeg.py`](montaje_ffmpeg.py) | ✅ | ✅ | Quema los subtítulos sobre **tu propia** imagen/vídeo de fondo. |

```bash
python examples/offline_sin_internet.py   # empieza por este (sin internet)
python examples/basico.py                  # voz + subtítulos
python examples/texto_a_mp4.py             # MP4 final (fondo de color)
python examples/emojis_a_color_mp4.py      # MP4 con emojis a color
python examples/montaje_ffmpeg.py          # usa tu propio fondo.jpg
```

> Los ejemplos que usan voz llaman a **edge-tts** (servicio de Microsoft Edge).
> Si una red/proxy lo bloquea, la librería lanza un error claro; en ese caso usa
> `offline_sin_internet.py`, que no necesita red.

### En Google Colab

Pon la instalación en su propia celda con `!` y, para bajar el resultado, usa el
módulo de Colab:

```python
!pip install -q captionwave
!apt-get -qq install -y ffmpeg fonts-noto-emoji > /dev/null
# ...código del ejemplo...
from google.colab import files; files.download("salida.mp4")
```
