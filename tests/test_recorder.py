"""Tests for Recorder init and static utility methods.

These tests do NOT require physical camera or microphone hardware.
"""

import os
import pytest

from src.core.recorder import Recorder


def test_recorder_init():
    """A fresh Recorder instance is in a non-recording state with no open resources."""
    r = Recorder()
    assert r.is_recording is False
    assert r.cap is None
    assert r.out is None


def test_temp_files_unique():
    """Two separate Recorder instances must have distinct temp file paths."""
    r1 = Recorder()
    r2 = Recorder()
    assert r1.temp_video != r2.temp_video
    assert r1.temp_audio != r2.temp_audio


def test_temp_files_in_temp_dir():
    """Temp file paths must live inside the system temp directory."""
    import tempfile
    r = Recorder()
    temp_dir = tempfile.gettempdir()
    assert r.temp_video.startswith(temp_dir)
    assert r.temp_audio.startswith(temp_dir)


def test_start_recording_without_camera():
    """start_recording() without an open camera returns None and does not crash."""
    r = Recorder()
    # cap is None — the method should return early without raising
    result = r.start_recording("output.mp4")
    assert result is None
    assert r.is_recording is False


def test_static_methods_exist():
    """get_available_cameras and get_available_microphones are callable as static methods."""
    assert callable(Recorder.get_available_cameras)
    assert callable(Recorder.get_available_microphones)
    # Calling them as class methods (no instance needed) must not raise
    cameras = Recorder.get_available_cameras()
    mics = Recorder.get_available_microphones()
    assert isinstance(cameras, list)
    assert isinstance(mics, list)
