@echo off
cd /d "%~dp0"
REM Launch with the project venv Python (system Python lacks PySide6)
start "" "%~dp0..\..\.venv\Scripts\pythonw.exe" "%~dp0main.py"
