# -*- mode: python ; coding: utf-8 -*-

block_cipher = None


a = Analysis(['c:\\Users\\Internet\\Downloads\\Compressed\\CSI\\CSI\\Nueva carpeta\\ClienteMonitoreoLocal\\main.py'],
             pathex=['C:\\Users\\Internet\\Downloads\\Compressed\\CSI\\CSI\\Nueva carpeta\\ClienteMonitoreoLocal'],
             binaries=[],
             datas=[('c:\\Users\\Internet\\Downloads\\Compressed\\CSI\\CSI\\Nueva carpeta\\ClienteMonitoreoLocal\\core', 'core'), ('c:\\Users\\Internet\\Downloads\\Compressed\\CSI\\CSI\\Nueva carpeta\\ClienteMonitoreoLocal\\services', 'services'), ('c:\\Users\\Internet\\Downloads\\Compressed\\CSI\\CSI\\Nueva carpeta\\ClienteMonitoreoLocal\\sistema', 'sistema'), ('c:\\Users\\Internet\\Downloads\\Compressed\\CSI\\CSI\\Nueva carpeta\\ClienteMonitoreoLocal\\utils', 'utils')],
             hiddenimports=['requests', 'win32net', 'win32netcon', 'pywintypes', 'wmi'],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='ClienteMonitoreo',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=True )
