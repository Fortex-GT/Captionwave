from captionwave import get_style
from captionwave.ass_writer import build_ass
from captionwave.srt_writer import build_srt

LINES = [
    {
        "words": [
            {"word": "una", "start": 0.0, "dur": 0.2},
            {"word": "estrella", "start": 0.2, "dur": 0.4},
        ],
        "start": 0.0,
        "end": 0.8,
        "text": "una estrella",
        "emoji": "⭐",
    },
]


def test_build_srt_format():
    out = build_srt(LINES, uppercase=True)
    assert out.startswith("1\n")
    assert "-->" in out
    assert "UNA ESTRELLA" in out  # uppercase aplicado


def test_build_srt_lowercase():
    out = build_srt(LINES, uppercase=False)
    assert "una estrella" in out


def test_build_ass_header_and_resolution():
    out = build_ass(LINES, get_style("hormozi"), resolution=(1080, 1920))
    assert "[Script Info]" in out
    assert "PlayResX: 1080" in out
    assert "PlayResY: 1920" in out
    assert "[Events]" in out
    assert "Dialogue:" in out


def test_build_ass_custom_resolution():
    out = build_ass(LINES, get_style("clean"), resolution=(720, 1280))
    assert "PlayResX: 720" in out
    assert "PlayResY: 1280" in out
