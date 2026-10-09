@echo off
rem Construit HorlogeMondiale.exe (a lancer sous Windows, dans le dossier du .py)
cd /d "%~dp0"
echo Installation de PyInstaller et tzdata...
py -m pip install --upgrade pyinstaller tzdata
if errorlevel 1 goto erreur
echo.
echo Construction de HorlogeMondiale.exe...
py -m PyInstaller --noconfirm --onefile --windowed --name HorlogeMondiale --icon horloge.ico --collect-data tzdata horloge_mondiale.py
if errorlevel 1 goto erreur
copy /y dist\HorlogeMondiale.exe . >nul
echo.
echo ==========================================
echo  OK : HorlogeMondiale.exe est pret
echo  (dans ce dossier, et aussi dans dist\)
echo ==========================================
pause
exit /b 0
:erreur
echo.
echo Une erreur est survenue, voir les messages ci-dessus.
pause
exit /b 1
