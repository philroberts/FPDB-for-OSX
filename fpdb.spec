# -*- mode: python -*-
import os, glob

# Hand history parsers are imported programmatically so we have to
# manually specify them for pyinstaller.
parsers = glob.glob('pyfpdb/*ToFpdb.py') + glob.glob('pyfpdb/*Summary.py')
parsers = [os.path.splitext(os.path.basename(p))[0] for p in parsers]

# Likewise hud classes.
hudclasses = ['Aux_Base', 'Aux_Hud', 'Aux_Classic_Hud', 'Mucked', 'Popup', 'Stats']

import platform
os_family = platform.system()
ignore=['sqlite3.test'] # sqlite test suite brings in tkinter, don't want that

a = Analysis(['pyfpdb/fpdb.pyw'],
             excludes=['gobject'] + ignore,
             pathex=['../pypoker-eval'],
             # MergeStructures should be auto-added as it is imported
             # by merge parser, but isn't due to a bug in pyinstaller
             # that is fixed in pyinstaller git afaik.
             hiddenimports=parsers + ['MergeStructures', '_pokereval_2_7'],
             hookspath=None,
             runtime_hooks=None)
ahud = Analysis(['pyfpdb/HUD_main.pyw'],
             excludes=ignore,
             hiddenimports=parsers + ['MergeStructures'] + hudclasses,
             hookspath=None,
             runtime_hooks=None)

if os_family == "Windows":
    MERGE( (a, 'fpdb', 'fpdb'), (ahud, 'HUD_main', 'HUD_main') )

pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='fpdb.exe' if os_family == "Windows" else 'fpdb',
          debug=False,
          strip=False,
          upx=True,
          console=False,
          icon="gfx/fpdb_large_icon.ico" if os_family == "Windows" else None)
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               Tree('gfx', prefix='gfx'),
               Tree('pyfpdb/locale', prefix='pyfpdb/locale', excludes=['*.po', '*.pot', '*.sh']),
               [('pyfpdb/logging.conf','pyfpdb/logging.conf','DATA')],
               [('pyfpdb/HUD_config.xml.example','pyfpdb/HUD_config.xml.example','DATA')],
               strip=None,
               upx=True,
               name='fpdb')

pyzhud = PYZ(ahud.pure)
exehud = EXE(pyzhud,
          ahud.scripts,
          exclude_binaries=True,
          name='HUD_main.exe' if os_family == "Windows" else 'HUD_main',
          debug=False,
          strip=None,
          upx=True,
          console=False )
collhud = COLLECT(exehud,
               ahud.binaries,
               ahud.zipfiles,
               ahud.datas,
               strip=None,
               upx=True,
               name='HUD_main')

if os_family == "Darwin":
    app = BUNDLE(coll, collhud,
                 name='fpdb.app',
                 icon='gfx/fpdb-mac-icon.icns')

