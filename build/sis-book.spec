# -*- mode: python ; coding: utf-8 -*-
# PyInstaller 打包配置 - 暮橙体育记账本
# 使用方式: pyinstaller build/sis-book.spec

import os

# spec 文件上级目录即项目根目录
ROOT = os.path.abspath(os.path.join(SPECPATH, '..'))

a = Analysis(
    [os.path.join(ROOT, 'backend', 'main.py')],
    pathex=[os.path.join(ROOT, 'backend')],
    binaries=[],
    datas=[
        (os.path.join(ROOT, 'frontend', 'dist'), os.path.join('frontend', 'dist')),
    ],
    hiddenimports=[
        'app.sales.router',
        'app.purchases.router',
        'app.orders.router',
        'app.sales.models',
        'app.purchases.models',
        'app.orders.models',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='暮橙记账本',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='暮橙记账本',
)
