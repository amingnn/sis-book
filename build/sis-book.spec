# -*- mode: python ; coding: utf-8 -*-
# PyInstaller 打包配置 - 暮橙体育记账本
# 使用方式: pyinstaller build/sis-book.spec

import os
from PyInstaller.utils.hooks import collect_all

# spec 文件上级目录即项目根目录
ROOT = os.path.abspath(os.path.join(SPECPATH, '..'))

# 收集 pythonnet 和 clr_loader 的所有文件（包括 Python.Runtime.dll）
pn_datas, pn_binaries, pn_hiddenimports = collect_all('pythonnet')
clr_datas, clr_binaries, clr_hiddenimports = collect_all('clr_loader')
wv_datas, wv_binaries, wv_hiddenimports = collect_all('webview')

a = Analysis(
    [os.path.join(ROOT, 'backend', 'main.py')],
    pathex=[os.path.join(ROOT, 'backend')],
    binaries=[] + pn_binaries + clr_binaries + wv_binaries,
    datas=[
        (os.path.join(ROOT, 'frontend', 'dist'), os.path.join('frontend', 'dist')),
    ] + pn_datas + clr_datas + wv_datas,
    hiddenimports=[
        'app.sales.router',
        'app.purchases.router',
        'app.orders.router',
        'app.sales.models',
        'app.purchases.models',
        'app.orders.models',
        'webview.platforms.winforms',
        'clr',
        'clr_loader',
    ] + pn_hiddenimports + clr_hiddenimports + wv_hiddenimports,
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
