import pytest

from captionwave import PRESETS, Style, get_style, hex_to_ass, list_styles


def test_list_styles_matches_presets():
    styles = list_styles()
    assert "hormozi" in styles
    assert set(styles) == set(PRESETS)


def test_get_style_by_name():
    st = get_style("hormozi")
    assert isinstance(st, Style)
    assert st.name == "hormozi"


def test_get_style_accepts_style_object():
    st = get_style("pop")
    assert isinstance(get_style(st), Style)


def test_get_style_invalid_name():
    with pytest.raises(ValueError):
        get_style("no-existe")


def test_style_copy_is_independent():
    base = get_style("hormozi")
    custom = base.copy(font_size=120, max_words=2)
    assert custom.font_size == 120
    assert custom.max_words == 2
    assert base.font_size != 120  # el original no se modifica


def test_hex_to_ass_conversion():
    # '#RRGGBB' -> '&HAABBGGRR' (alpha 00 = opaco)
    assert hex_to_ass("#FFD23F") == "&H003FD2FF"
    assert hex_to_ass("#000000") == "&H00000000"
    assert hex_to_ass("#FFFFFF") == "&H00FFFFFF"
