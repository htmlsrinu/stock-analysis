# ==========================================================================
# CONSENSUS ENGINE REPORT SCHEDULER SETTING SCRIPT (WINDOWS native PowerShell)
# ==========================================================================

$cwd = Get-Location
$scriptPath = Join-Path $cwd "run_reports.py"
$pythonPath = (Get-Command python).Source

if (-not $pythonPath) {
    $pythonPath = "python.exe" # Fallback
}

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "    CONSENSUS ENGINE SCHEDULER INSTALLER          " -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "Registering automated quantitative reports inside Windows Task Scheduler..."
Write-Host "Script Location : $scriptPath"
Write-Host "Python Path     : $pythonPath"
Write-Host ""

# Define the 4 standard daily times (EST local time triggers)
$triggers = @()

# Trigger 1: Pre-Open at 8:30 AM EST
$triggers += New-ScheduledTaskTrigger -Daily -At "8:30AM"
Write-Host "[Registered Trigger 1] Pre-Open Setup scan at 08:30 AM" -ForegroundColor Yellow

# Trigger 2: Mid-Day Session at 12:00 PM EST
$triggers += New-ScheduledTaskTrigger -Daily -At "12:00PM"
Write-Host "[Registered Trigger 2] Mid-Day Trend scan at 12:00 PM" -ForegroundColor Yellow

# Trigger 3: Power Hour Session at 3:15 PM EST
$triggers += New-ScheduledTaskTrigger -Daily -At "3:15PM"
Write-Host "[Registered Trigger 3] Power Hour Setup scan at 03:15 PM" -ForegroundColor Yellow

# Trigger 4: Post-Market Daily Close at 4:30 PM EST
$triggers += New-ScheduledTaskTrigger -Daily -At "4:30PM"
Write-Host "[Registered Trigger 4] Post-Market Audit scan at 04:30 PM" -ForegroundColor Yellow

# Configure Actions: Run python interpreter with the execution manager script argument
$action = New-ScheduledTaskAction -Execute $pythonPath -Argument "`"$scriptPath`""

# Configure Settings: Allow task to run on battery, stop if it runs longer than 15 mins
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Minutes 15)

# Register the Scheduled Task
$taskName = "ConsensusEngineStockAnalyzer"
Write-Host ""
Write-Host "Creating Task Scheduler entry '$taskName'..." -ForegroundColor Green

# Check if old task exists, delete it first to prevent duplicates
$existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($existingTask) {
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
}

Register-ScheduledTask -TaskName $taskName -Trigger $triggers -Action $action -Settings $settings -Description "Runs Consensus Engine scrapers, paper trading performance backtest auditors, and dispatches Space, Quantum, and Short report emails 4 times daily."

Write-Host "==================================================" -ForegroundColor Green
Write-Host "SUCCESS! The Consensus Engine task scheduler is fully registered." -ForegroundColor Green
Write-Host "Your stock reports will now run and email automatically 4 times daily." -ForegroundColor Green
Write-Host "To run the scripts manually right now, execute: python run_reports.py" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Green
