@echo off
chcp 65001 >nul
cd /d "%~dp0"
REM 用项目虚拟环境里的 Python 启动（系统 Python 没有 PySide6，双击 .py 会失败）
start "" "%~dp0..\..\.venv\Scripts\pythonw.exe" "%~dp0main.py"
