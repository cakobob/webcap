import os

SUPPORTED_VIDEO_EXTENSIONS = ('.mp4', '.mkv', '.mov')


def safe_rename_video(old_path: str, new_name: str) -> str:
    """Rename a video file, preserving the original extension if the new name
    does not include a recognised video extension.

    Args:
        old_path: Absolute path to the existing video file.
        new_name: Desired new filename (with or without extension).

    Returns:
        The absolute path of the renamed file.

    Raises:
        OSError: If the rename operation fails (e.g. file not found, permission
                 denied, target already exists).
    """
    _, original_ext = os.path.splitext(old_path)

    _, new_ext = os.path.splitext(new_name)
    if new_ext.lower() in SUPPORTED_VIDEO_EXTENSIONS:
        new_name_with_ext = new_name
    else:
        new_name_with_ext = new_name + original_ext

    new_path = os.path.join(os.path.dirname(old_path), new_name_with_ext)
    os.rename(old_path, new_path)
    return new_path
