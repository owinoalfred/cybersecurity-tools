#!/usr/bin/env pwsh

Write-Host ""
Write-Host "===================================" -ForegroundColor Green
Write-Host "  CYBERSECURITY TOOLS DASHBOARD" -ForegroundColor Green  
Write-Host "===================================" -ForegroundColor Green
Write-Host ""

# Change to script directory
Set-Location $PSScriptRoot

# Check if Python is installed
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Found Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "Error: Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python and try again" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Install requirements
Write-Host "Installing/updating dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt --quiet

if ($LASTEXITCODE -ne 0) {
    Write-Host "Warning: Some dependencies may not have installed correctly" -ForegroundColor Yellow
}

# Start the dashboard
Write-Host ""
Write-Host "Starting dashboard on http://localhost:8501" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop the dashboard" -ForegroundColor Yellow
Write-Host ""

try {
    streamlit run dashboard.py --server.port=8501 --server.address=localhost
} catch {
    Write-Host "Error starting dashboard: $($_.Exception.Message)" -ForegroundColor Red
    Read-Host "Press Enter to exit"
}
