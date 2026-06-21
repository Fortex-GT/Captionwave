import pytest

from captionwave import CaptionGenerator, chunk_words, list_styles

WORDS = [
    {"word": "El", "start": 0.00, "dur": 0.18},
    {"word": "Sol", "start": 0.18, "dur": 0.34},
    {"word": "es", "start": 0.52, "dur": 0.16},
    {"word": "una", "start": 0.68, "dur": 0.18},
    {"word": "estrella", "start": 0.86, "dur": 0.52},
    {"word": "enorme", "start": 1.38, "dur": 0.50},
]
DUR = 2.0


def test_chunk_words_is_continuous():
    lines = chunk_words(WORDS, max_words=3, max_chars=18, total=DUR)
    assert lines
    # El fin de cada línea coincide con el inicio de la siguiente.
    for a, b in zip(lines, lines[1:]):
        assert a["end"] == pytest.approx(b["start"])
    # La última línea se extiende hasta la duración total.
    assert lines[-1]["end"] >= DUR


def test_chunk_words_respects_max_chars():
    largas = "computadora ordenador laptop rinoceronte electricidad sol".split()
    ws = [{"word": w, "start": i * 0.5, "dur": 0.4} for i, w in enumerate(largas)]
    lines = chunk_words(ws, max_words=3, max_chars=18, total=10)
    # Ninguna línea supera max_chars (salvo que sea una sola palabra muy larga).
    for ln in lines:
        assert len(ln["words"]) == 1 or len(ln["text"]) <= 18


def test_build_from_words_writes_files(tmp_path):
    gen = CaptionGenerator(style="hormozi")
    ass = tmp_path / "s.ass"
    srt = tmp_path / "s.srt"
    emo = tmp_path / "e.json"
    r = gen.build_from_words(
        WORDS, DUR, out_ass=str(ass), out_srt=str(srt), out_emojis=str(emo)
    )
    assert ass.exists() and srt.exists() and emo.exists()
    assert r["audio"] is None
    assert r["duration"] == DUR
    assert r["lines"]
    assert "[Script Info]" in ass.read_text(encoding="utf-8")


def test_build_from_words_empty_raises():
    with pytest.raises(ValueError):
        CaptionGenerator().build_from_words([], DUR)


def test_all_presets_build(tmp_path):
    for style in list_styles():
        out = tmp_path / f"{style}.ass"
        CaptionGenerator(style=style).build_from_words(
            WORDS, DUR, out_ass=str(out), out_srt=None
        )
        assert out.exists() and out.stat().st_size > 0


def test_emoji_disabled(tmp_path):
    gen = CaptionGenerator(style="hormozi", emoji=False)
    r = gen.build_from_words(WORDS, DUR, out_ass=str(tmp_path / "s.ass"))
    assert r["emojis"] == []
    assert all(ln["emoji"] is None for ln in r["lines"])
