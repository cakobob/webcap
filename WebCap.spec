# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('src', 'src'), ('assets', 'assets')],
    hiddenimports=['PyQt6.QtMultimedia', 'PyQt6.QtMultimediaWidgets'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='WebCap',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='WebCap',
)
app = BUNDLE(
    coll,
    name='WebCap.app',
    icon='assets/logos/webcap_dark.png',
    bundle_identifier='com.webcap.recorder',
    info_plist={
        'NSCameraUsageDescription': 'WebCap needs access to your camera to record video.',
        'NSMicrophoneUsageDescription': 'WebCap needs access to your microphone to record audio.',
        'NSHighResolutionCapable': 'True'
    },
)
