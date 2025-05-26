@echo off
REM Admin launcher for IDS
cd /d "%~dp0.."
powershell -Command "Start-Process powershell -Verb RunAs -ArgumentList '-NoExit', '-Command', 'cd ''%CD%''; python -m tools.network.ids %*'"
