rmdir /Q /S clone
rmdir /Q /S dist
rmdir /Q /S output
rmdir /Q /S output_update

mkdir output
mkdir output\internals
mkdir output\plugins

mkdir output_update
mkdir output_update\internals
mkdir output_update\plugins

rem call git clone ..\.. clone
call c:\pyinstaller-1.5.1\pyinstaller.py -n serclient -F serclient.spec

xcopy /Y dist\serclient.exe output
xcopy /Y /S ..\..\internals output\internals
xcopy /Y /S ..\..\plugins output\plugins
xcopy /Y /S ..\..\internals output_update\internals
xcopy /Y /S ..\..\plugins output_update\plugins

"c:\Program Files\Inno Setup 5\ISCC.exe" setup_full.iss 
"c:\Program Files\Inno Setup 5\ISCC.exe" setup_update.iss 
