@echo off
cd /d "%~dp0..\starter_app"
where py >nul 2>nul
if %ERRORLEVEL% EQU 0 (
  py server.py
) else (
  python server.py
)
