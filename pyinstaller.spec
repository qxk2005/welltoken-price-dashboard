# -*- mode: python ; coding: utf-8 -*-
import sys
from pathlib import Path

block_cipher = None

# 项目根路径
project_dir = Path('.').resolve()

from PyInstaller.utils.hooks import collect_submodules, collect_data_files

all_hiddenimports = [
    *collect_submodules('backend.app'),
    *collect_submodules('fastapi'),
    *collect_submodules('starlette'),
    *collect_submodules('uvicorn'),
    *collect_submodules('sqlalchemy'),
    *collect_submodules('aiosqlite'),
    *collect_submodules('pydantic'),
    *collect_submodules('pydantic_settings'),
    *collect_submodules('httpx'),
    'socksio',
    'dotenv',
    'websockets',
    'anyio'
]

a = Analysis(
    ['backend/run_server.py'],
    pathex=[str(project_dir)],
    binaries=[],
    datas=[
        ('backend/app', 'backend/app'),
        ('data/cache', 'data/cache')
    ],
    hiddenimports=all_hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'PIL', 'scipy', 'pandas', 'IPython'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='backend-server',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
