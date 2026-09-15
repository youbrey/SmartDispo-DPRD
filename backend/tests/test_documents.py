from app.services.documents import canonical_hash


def test_canonical_hash_is_order_independent() -> None:
    assert canonical_hash({"b": 2, "a": 1}) == canonical_hash({"a": 1, "b": 2})


def test_canonical_hash_changes_with_content() -> None:
    assert canonical_hash({"a": 1}) != canonical_hash({"a": 2})
