import sys

app_name = 'remover'
exe_name = 'remover'

if sys.platform == 'win32':
    exe_name += '.exe'
    run_upx = False

elif sys.platform.startswith('linux'):
    run_strip = True
    run_upx = False

elif sys.platform.startswith('darwin'):
    run_upx = False

else:
    print("Unsupported operating system")
    sys.exit(-1)

a = Analysis(['remover/__main__.py'],
             pathex=[],
             hiddenimports=[],
             hookspath=None,
             runtime_hooks=None)

pyz = PYZ(a.pure)

exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name=exe_name,
          debug=False,
          strip=None,
          upx=True,
          #icon=os.path.join('icons', 'icon.ico'),
          icon=None,
          console=False)

coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=None,
               upx=run_upx,
               name=app_name)

if sys.platform.startswith('darwin'):
    app = BUNDLE(coll,
                 name='Remover.app',
                 appname=exe_name,
                 #icon=os.path.join('icons', 'icon.icns'),
                 icons=None,
                 info_plist={
                     'NSPrincipalClass': 'NSApplication',
                     'NSAppleScriptEnabled': False
                 })
