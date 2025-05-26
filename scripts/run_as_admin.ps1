# PowerShell Script to Run Cybersecurity Tools with Admin Privileges
# run_as_admin.ps1

param(
    [Parameter(Mandatory=$true)]
    [string]$Tool,
    
    [Parameter(ValueFromRemainingArguments=$true)]
    [string[]]$Arguments
)

# Check if running as administrator
function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

# Get the cybersecurity tools directory
$toolsDir = Split-Path $MyInvocation.MyCommand.Path -Parent | Split-Path -Parent

Write-Host "🔧 Cybersecurity Tools Admin Launcher" -ForegroundColor Cyan
Write-Host "=" * 50 -ForegroundColor Cyan

if (-NOT (Test-Administrator)) {
    Write-Host "❌ Not running as Administrator!" -ForegroundColor Red
    Write-Host "🚀 Restarting with elevated privileges..." -ForegroundColor Yellow
    
    # Construct the command to run
    $pythonCmd = "python -m tools.$Tool"
    if ($Arguments) {
        $pythonCmd += " " + ($Arguments -join " ")
    }
    
    # Create the full command
    $fullCmd = "cd '$toolsDir'; $pythonCmd; Read-Host 'Press Enter to exit'"
    
    # Start elevated process
    Start-Process powershell -Verb RunAs -ArgumentList "-NoExit", "-Command", $fullCmd
    exit
}

Write-Host "✅ Running with Administrator privileges" -ForegroundColor Green
Write-Host "📁 Tools Directory: $toolsDir" -ForegroundColor Gray

# Change to tools directory
Set-Location $toolsDir

# Map tool names to modules
$toolMap = @{
    "hash-cracker" = "password.hash_cracker"
    "password-checker" = "password.password_checker"
    "port-scanner" = "network.port_scanner"
    "web-scanner" = "web.web_scanner"
    "ids" = "network.ids"
    "packet-sniffer" = "network.packet_sniffer"
}

if ($toolMap.ContainsKey($Tool)) {
    $module = $toolMap[$Tool]
    Write-Host "🎯 Launching: $Tool" -ForegroundColor Green
    Write-Host "📦 Module: $module" -ForegroundColor Gray
    
    if ($Arguments) {
        Write-Host "⚙️  Arguments: $($Arguments -join ' ')" -ForegroundColor Gray
        & python -m $module @Arguments
    } else {
        & python -m $module
    }
} else {
    Write-Host "❌ Unknown tool: $Tool" -ForegroundColor Red
    Write-Host "Available tools:" -ForegroundColor Yellow
    $toolMap.Keys | ForEach-Object { Write-Host "  • $_" -ForegroundColor White }
}

Write-Host "`n🔚 Tool execution completed" -ForegroundColor Cyan
Read-Host "Press Enter to exit"
