"""Tests for the safe_rename_video utility."""

import os
import pytest

from src.utils.rename import safe_rename_video, SUPPORTED_VIDEO_EXTENSIONS


def _make_file(directory, name: str) -> str:
    """Create an empty file and return its absolute path."""
    path = os.path.join(str(directory), name)
    open(path, "w").close()
    return path


def test_rename_preserves_mp4_extension(tmp_path):
    """Renaming without explicit extension preserves the original .mp4 extension."""
    original = _make_file(tmp_path, "video.mp4")
    result = safe_rename_video(original, "new_name")
    assert result == str(tmp_path / "new_name.mp4")
    assert os.path.exists(result)
    assert not os.path.exists(original)


def test_rename_preserves_mkv_extension(tmp_path):
    """Renaming without explicit extension preserves the original .mkv extension."""
    original = _make_file(tmp_path, "video.mkv")
    result = safe_rename_video(original, "new_name")
    assert result == str(tmp_path / "new_name.mkv")
    assert os.path.exists(result)


def test_rename_preserves_mov_extension(tmp_path):
    """Renaming without explicit extension preserves the original .mov extension."""
    original = _make_file(tmp_path, "video.mov")
    result = safe_rename_video(original, "new_name")
    assert result == str(tmp_path / "new_name.mov")
    assert os.path.exists(result)


def test_rename_with_explicit_extension(tmp_path):
    """When new_name already has a supported extension, it is used as-is."""
    original = _make_file(tmp_path, "video.mp4")
    result = safe_rename_video(original, "new_name.mkv")
    assert result == str(tmp_path / "new_name.mkv")
    assert os.path.exists(result)


def test_rename_nonexistent_file_raises(tmp_path):
    """Attempting to rename a file that does not exist raises an OSError."""
    missing = str(tmp_path / "ghost.mp4")
    with pytest.raises(OSError):
        safe_rename_video(missing, "anything")
