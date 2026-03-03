@echo off
echo Eski build dosyalari temizleniyor...
if exist "dist\" rmdir /S /Q "dist"
if exist "build\" rmdir /S /Q "build"

echo Yeni build aliniyor...
pyinstaller --noconfirm --clean AutomateX.spec

echo Build islemi tamamlandi! 'dist' klasorunde AutomateX.exe yi bulabilirsiniz.
pause
