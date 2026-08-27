@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ============================================
echo   ADB 脚本工具 - 打包成 exe
echo ============================================
echo [1/3] 安装 PyInstaller（仅首次需要）...
"%~dp0..\..\.venv\Scripts\python.exe" -m pip install pyinstaller
if errorlevel 1 ( echo 安装失败 & pause & exit /b 1 )

echo [2/3] 正在打包（PySide6 较大，需几分钟）...
"%~dp0..\..\.venv\Scripts\python.exe" -m PyInstaller --noconfirm --clean --onefile --windowed --name "ADB脚本工具" --icon "%~dp0icon.ico" --add-data "%~dp0icon.ico;." "%~dp0main.py"
if errorlevel 1 ( echo 打包失败 & pause & exit /b 1 )

echo [3/3] 复制脚本数据到 exe 同目录...
if exist "dist\data" rmdir /s /q "dist\data"
if exist "%~dp0data" xcopy /E /I /Y "%~dp0data" "dist\data" >nul

echo.
echo 打包完成！
echo   程序: dist\ADB脚本工具.exe
echo   数据: dist\data\（已自动复制，脚本增删改都写在这里）
echo 双击 dist\ADB脚本工具.exe 即可运行。
echo 想清理打包中间文件，可删除本目录的 build 文件夹和 ADB脚本工具.spec。
pause
