from captionwave import EmojiPicker


def test_curated_words():
    p = EmojiPicker()
    assert p.for_word("estrella") == "⭐"
    assert p.for_word("sol") == "☀️"
    assert p.for_word("cerebro") == "🧠"


def test_plurals_resolve_to_singular():
    p = EmojiPicker()
    assert p.for_word("estrellas") == "⭐"


def test_stopwords_return_none():
    p = EmojiPicker()
    assert p.for_word("de") is None
    assert p.for_word("la") is None
    assert p.for_word("") is None


def test_for_phrase_falls_back_to_default():
    p = EmojiPicker()
    # Solo stopwords -> debe devolver un emoji por defecto (no None).
    assert p.for_phrase("de la el", 0)


def test_for_phrase_prefers_relevant_word():
    p = EmojiPicker()
    assert p.for_phrase("una estrella enorme") == "⭐"
