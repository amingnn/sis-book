# -*- mode: python ; coding: utf-8 -*-
# type: ignore
# PyInstaller 打包配置 - 暮橙体育记账本
# 使用方式: pyinstaller build/sis-book.spec

import os
import sys
from PyInstaller.utils.hooks import collect_all

# spec 文件上级目录即项目根目录
ROOT = os.path.abspath(os.path.join(SPECPATH, '..')) 
APP_NAME = '暮橙记账本'  # APP 名

extra_datas = []
extra_binaries = []
extra_hiddenimports = []

# Windows 专用：收集 pythonnet/clr_loader（PyWebView WinForms 后端依赖）
if sys.platform == 'win32':
    pn_datas, pn_binaries, pn_hiddenimports = collect_all('pythonnet')
    clr_datas, clr_binaries, clr_hiddenimports = collect_all('clr_loader')
    extra_datas += pn_datas + clr_datas
    extra_binaries += pn_binaries + clr_binaries
    extra_hiddenimports += pn_hiddenimports + clr_hiddenimports + [
        'webview.platforms.winforms',
        'clr',
        'clr_loader',
    ]

wv_datas, wv_binaries, wv_hiddenimports = collect_all('webview')
extra_datas += wv_datas
extra_binaries += wv_binaries
extra_hiddenimports += wv_hiddenimports

a = Analysis(
    [os.path.join(ROOT, 'backend', 'main.py')],
    pathex=[os.path.join(ROOT, 'backend')],
    binaries=extra_binaries,
    datas=[
        (os.path.join(ROOT, 'frontend', 'dist'), os.path.join('frontend', 'dist')),
    ] + extra_datas,
    hiddenimports=[
        'app.sales.router',
        'app.purchases.router',
        'app.orders.router',
        'app.sales.models',
        'app.purchases.models',
        'app.orders.models',
    ] + extra_hiddenimports,
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
    name=APP_NAME,
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
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name=APP_NAME,
)
    
if sys.platform == 'darwin':
    app = BUNDLE(
        coll, # 将上面收集好的散装零件作为输入
        name='暮橙记账本.app', # 最终生成的 App 包名
        # 建议在项目根目录创建 assets 文件夹放图标
        # icon=os.path.join(ROOT, 'assets', 'icon.icns'), 
        icon=None, 
        bundle_identifier='com.sisbook', # 唯一的 ID
        info_plist={
            'CFBundleDisplayName': APP_NAME,
            'CFBundleName': APP_NAME,
            'CFBundleShortVersionString': '1.0.0',
            'NSHighResolutionCapable': True, # 开启 Retina 支持，否则网页会糊
            'LSMinimumSystemVersion': '10.13',
            # 解决 pywebview 可能需要的权限提示
            'NSAppTransportSecurity': {'NSAllowsArbitraryLoads': True},
        },
    )