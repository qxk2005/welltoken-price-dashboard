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
    'anyio',
    'certifi'
]

datas = [
    ('backend/app', 'backend/app'),
    *collect_data_files('certifi')
]

cache_dir = project_dir / 'data' / 'cache'
if not cache_dir.exists():
    cache_dir.mkdir(parents=True, exist_ok=True)
datas.append(('data/cache', 'data/cache'))

# 官方定价离线种子包与官方 HTML 快照证据链目录
seed_file = project_dir / 'data' / 'official_prices_seed.json'
if seed_file.exists():
    datas.append(('data/official_prices_seed.json', 'data'))

snapshots_dir = project_dir / 'data' / 'official_snapshots'
if not snapshots_dir.exists():
    snapshots_dir.mkdir(parents=True, exist_ok=True)
datas.append(('data/official_snapshots', 'data/official_snapshots'))

a = Analysis(
    ['backend/run_server.py'],
    pathex=[str(project_dir)],
    binaries=[],
    datas=datas,
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
