# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['matrix_desktop.py'],
    pathex=[],
    binaries=[],
    datas=[('webapp', 'webapp')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', '_tkinter'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='矩阵计算工具',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    # 解包目录放在用户目录而不是 %TEMP%（部分机器上 %TEMP% 建目录会被拦截，
    # 且 _MEI 落在 D 盘时 pythonnet 加载托管程序集会失败）。
    # 注意：bootloader 只会创建最后一级目录，所以这里必须选一个「父目录已存在」的路径，
    # 写成 ...\MatrixCalculator\runtime 会因为 MatrixCalculator 不存在而报
    # 「系统找不到指定的路径」。bootloader 会展开环境变量。
    runtime_tmpdir='%LOCALAPPDATA%\\MatrixCalculator',
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='webapp/app.ico',
)
