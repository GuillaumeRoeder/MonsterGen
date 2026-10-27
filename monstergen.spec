# -*- mode: python ; coding: utf-8 -*-
# Spécification PyInstaller de MonsterGen.
# Build onedir (démarrage rapide, PySide6 s'y porte mieux qu'onefile) :
#   pyinstaller monstergen.spec
# Résultat dans dist/MonsterGen/ (exécutable + dépendances).

import os

block_cipher = None

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        "PySide6.QtSvg",
        "PIL._tkinter_finder",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "tkinter",
        "pytest",
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="MonsterGen",
    debug=False,
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
    name="MonsterGen",
)
