@echo off
title NETRAVYA - AI Crowd Monitoring System
echo ==================================================
echo   Starting NETRAVYA Production Server...
echo ==================================================
cd /d "%~dp0"

IF EXIST "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) ELSE (
    echo [!] Virtual environment not found in venv\, using global Python.
)

python run_server.py
pause
