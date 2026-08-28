@echo off
cd /d "%~dp0"
echo ============================================
echo   ADB Tool - build FAST version (folder)
echo   onedir: instant start, no 2-3s delay
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
echo [2/3] building onedir (fast start)...
rem 备份现有 data：onedir 构建会清空整个 dist\ADB脚本工具，先保护用户数据
if exist "dist\ADB脚本工具\data" (
    if exist "%~dp0data_backup" rmdir /s /q "%~dp0data_backup"
    xcopy /E /I /Y "dist\ADB脚本工具\data" "%~dp0data_backup" >nul
)
"%~dp0..\..\.venv\Scripts\python.exe" -m PyInstaller --noconfirm --clean "%~dp0tool_onedir.spec"
if not errorlevel 1 goto copy
echo Build failed. See errors above.
pause
exit /b 1

:copy
echo [3/3] restore data into the app folder (merge, never delete)...
for /d %%D in ("dist\*") do if exist "%%D\ADB*.exe" (
    if exist "%~dp0data_backup" (
        xcopy /E /I /Y "%~dp0data_backup" "%%D\data" >nul
    ) else if exist "%~dp0data" (
        xcopy /E /I /Y "%~dp0data" "%%D\data" >nul
    )
)

echo.
echo Done! Fast version folder: dist\ (onedir, instant start)
echo   Start by double-clicking the exe inside that folder.
echo Delete build\ folder to clean intermediates (keep tool_onedir.spec).
pause
