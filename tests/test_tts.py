import asyncio

import pytest

from captionwave.tts import _run_sync


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
