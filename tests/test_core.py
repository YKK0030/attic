from apps.api.attic_api.core import chunks


def test_chunks_overlap_and_empty():
    assert chunks("") == []
    assert chunks("one two three", size=2, overlap=1) == ["one two", "two three", "three"]
