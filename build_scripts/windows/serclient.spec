# -*- mode: python -*-
import os
import shutil

a = Analysis([os.path.join(HOMEPATH,'support\\_mountzlib.py'), os.path.join(HOMEPATH,'support\\useUnicode.py'), '..\\..\\WindowsService.py'],
			 pathex=['..\\..', 'C:\\src\\arubasvn\\build_scripts\\windows'])
			 
okp = os.path.dirname(os.path.realpath('..\\..\\WindowsService.py'))
print okp

removed = []
pure = []
for x in a.pure:
	dn = os.path.dirname(x[1])
	if dn.startswith(okp):
		print 'Removing:', x
		removed.append(x[1][:-1])
	else:
		pure.append(x)

pyz = PYZ(TOC(pure))
exe = EXE( pyz,
		  a.scripts,
		  a.binaries,
		  a.zipfiles,
		  a.datas,
		  name=os.path.join('dist', 'serclient.exe'),
		  debug=False,
		  strip=False,
		  upx=True,
		  console=True )

for p in removed:
	for d in ['output', 'output_update']:
		dest = os.path.realpath(p)
		dest = os.path.join(d, dest[len(okp)+1:])
		print 'Copy', p, 'in', dest
		try:
			os.makedirs(os.path.dirname(dest))
		except:
			pass
		shutil.copy(p, dest)
	