@echo off
echo ============================================
echo   Mackolik Istatistik Toplayici - Build
echo ============================================
echo.

REM Install dependencies
echo Bagimliliklar yukleniyor...
pip install -r requirements.txt
pip install pyinstaller

echo.
echo EXE olusturuluyor...
python build_exe.py

echo.
echo Tamamlandi! dist\MackolikStats.exe dosyasini calistirabilirsiniz.
pause
