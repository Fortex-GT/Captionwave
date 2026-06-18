import asyncio

import pytest

from captionwave.tts import _make_communicate, _run_sync


async def _double(x):
    await asyncio.sleep(0)
    return x * 2


def test_run_sync_without_running_loop():
    # Caso script normal: no hay loop activo.
    assert _run_sync(_double(21)) == 42


def test_run_sync_inside_running_loop():
    # Simula Colab/Jupyter: ya hay un event loop corriendo.
    async def main():
        return _run_sync(_double(21))

    assert asyncio.run(main()) == 42


def test_run_sync_propagates_exceptions():
    async def boom():
        raise ValueError("explota")

    with pytest.raises(ValueError):
        _run_sync(boom())


def test_communicate_requests_word_boundary():
    # edge-tts >= 7 usa "SentenceBoundary" por defecto; necesitamos WordBoundary
    # para obtener los tiempos por palabra (si no, los subtítulos salen vacíos).
    com = _make_communicate("hola mundo", "es-MX-DaliaNeural", "+0%")
    assert getattr(com.tts_config, "boundary", "WordBoundary") == "WordBoundary"
