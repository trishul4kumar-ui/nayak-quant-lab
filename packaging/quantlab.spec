# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec. Does not embed secrets. Data dir remains OS-specific at runtime."""

from PyInstaller.utils.hooks import collect_all

datas, binaries, hiddenimports = collect_all("PySide6")

a = Analysis(
    ["../src/quantlab/ui/main.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports + ["quantlab", "numpy", "pydantic", "structlog"],
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
    name="QUANT LAB",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="QUANT LAB",
)
