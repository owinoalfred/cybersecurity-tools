@echo off
REM Admin launcher for Packet Sniffer
cd /d "%~dp0.."
powershell -Command "Start-Process powershell -Verb RunAs -ArgumentList '-NoExit', '-Command', 'cd ''%CD%''; python -m tools.network.packet_sniffer %*'"
