from wordcounter.app import count_words

def test_word_count():
    assert count_words('hello, world') == 2
    assert count_words('foo--bar--baz') == 3
    assert count_words("don't break the build") == 4
    assert count_words("hello, world! how are you this wonderful---and i don't say that lightly--day?") == 14
