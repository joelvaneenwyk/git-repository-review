"""Test the core module."""

from git_repository_review.validate import main


def test_validate_empty():
    """Test the demo function returns the expected value."""
    assert main(None) == 0
