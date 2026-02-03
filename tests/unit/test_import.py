# ABOUTME: Smoke test verifying the newsroom package is importable.
# ABOUTME: Validates that the package structure is intact.
"""Smoke test for package importability."""


def test_newsroom_is_importable():
    """The newsroom package can be imported without error."""
    import newsroom

    assert newsroom is not None
