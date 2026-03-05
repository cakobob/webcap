"""Tests for the get_resource_path helper."""

import os
import pytest

from src.utils.resource_path import get_resource_path


def test_returns_absolute_path():
    """get_resource_path always returns an absolute path."""
    result = get_resource_path("some/relative/file.txt")
    assert os.path.isabs(result)


def test_joins_relative_path():
    """The returned path ends with the relative path that was supplied."""
    relative = os.path.join("assets", "logo.png")
    result = get_resource_path(relative)
    # Normalise both paths so the comparison works on all platforms
    assert result.endswith(relative) or result.endswith(os.path.normpath(relative))
