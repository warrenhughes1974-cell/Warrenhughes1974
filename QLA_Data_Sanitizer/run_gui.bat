@echo off
cd /d "%~dp0"
python sanitize_app.py
if errorlevel 1 pause
