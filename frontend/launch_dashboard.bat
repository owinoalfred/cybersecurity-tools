@echo off
echo.
echo ===================================
echo   CYBERSECURITY TOOLS DASHBOARD
echo ===================================
echo.
echo Starting Streamlit Dashboard...
echo Dashboard URL will open automatically
echo Press Ctrl+C to stop the dashboard
echo.

cd /d "%~dp0"

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python and try again
    pause
    exit /b 1
)

:: Install requirements if needed
echo Installing/updating dependencies...
pip install -r requirements.txt --quiet

:: Start the dashboard
echo.
echo Starting dashboard on http://localhost:8501
echo.
streamlit run dashboard.py --server.port=8501 --server.address=localhost

pause
