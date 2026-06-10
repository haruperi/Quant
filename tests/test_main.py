"""Tests for the application entry module."""

from app.main import add_numbers


def test_add_numbers_returns_sum() -> None:
    """It returns the sum of two integers."""
    assert add_numbers(2, 3) == 5
