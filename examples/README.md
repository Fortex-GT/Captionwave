# Ejemplos de captionwave

Estos scripts usan la librería tal como se usaría tras instalarla con `pip`.

## 1. Instalar el paquete

Desde la raíz del repositorio (recomendado en modo editable para desarrollo):

```bash
pip install -e .
```

O una instalación normal desde el código fuente:

```bash
pip install .
```

Cuando el paquete esté publicado en PyPI, bastará con:

```bash
pip install captionwave
```

Extras opcionales:

```bash
pip install -e ".[duration]"   # mutagen: duración exacta del audio (recomendado)
pip install -e ".[video]"      # moviepy: para montar el video desde Python
```

## 2. Ejecutar los ejemplos

| Script | Necesita internet | Necesita FFmpeg | Qué hace |
|--------|:---:|:---:|----------|
| [`offline_sin_internet.py`](offline_sin_internet.py) | ❌ | ❌ | Genera `.ass`/`.srt` a partir de tiempos por palabra dados a mano. **Ideal para verificar la instalación.** |
| [`basico.py`](basico.py) | ✅ | ❌ | Voz (edge-tts) + subtítulos + emojis sincronizados. |
| [`montaje_ffmpeg.py`](montaje_ffmpeg.py) | ✅ | ✅ | Lo anterior y además quema los subtítulos sobre una imagen → `salida.mp4`. |

```bash
python examples/offline_sin_internet.py   # empieza por este
python examples/basico.py                  # requiere conexión a internet
python examples/montaje_ffmpeg.py          # requiere internet + FFmpeg + fondo.jpg
```

> `basico.py` y `montaje_ffmpeg.py` usan **edge-tts**, que se conecta al servicio
> de Microsoft Edge (`speech.platform.bing.com`). Si una red/proxy/firewall lo
> bloquea, la librería lanza un error claro explicando la causa. En ese caso usa
> `offline_sin_internet.py`, que no necesita red.
