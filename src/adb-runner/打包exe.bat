@echo off
cd /d "%~dp0"
echo ============================================
echo   ADB Tool - build exe
echo ============================================
echo [0/3] closing running ADB Tool if any...
powershell -NoProfile -Command "Get-Process | Where-Object { $_.Path -like '*adb-runner*' } | Stop-Process -Force" >nul 2>&1
echo [1/3] install PyInstaller (first time only)...
"%~dp0..\..\.venv\Scripts\python.exe" -m pip install pyinstaller
if not errorlevel 1 goto build
echo Install failed. Check network / Python env.
pause
exit /b 1

:build
echo [2/3] building (PySide6, takes a few minutes)...
"%~dp0..\..\.venv\Scripts\python.exe" -m PyInstaller --noconfirm --clean "%~dp0tool.spec"
if not errorlevel 1 goto copy
echo Build failed. See errors above.
pause
exit /b 1

:copy
echo [3/3] copy data next to exe (merge, never delete)...
if exist "%~dp0data" xcopy /E /I /Y "%~dp0data" "dist\data" >nul

echo.
echo Done! exe in dist\, data copied to dist\data.
echo Delete build\ folder to clean intermediates (keep tool.spec).
pause
