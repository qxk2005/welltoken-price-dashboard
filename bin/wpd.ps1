param (
    [string]$Action = "--restart"
)

$FrontendPort = 5173
$BackendPort = 8765
$ProjectRoot = (Get-Item -Path "$PSScriptRoot\..").FullName

function Stop-PortProcess {
    param ([int]$Port, [string]$Name)
    $conns = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
    if ($conns) {
        $pids = $conns.OwningProcess | Select-Object -Unique
        $pidStr = $pids -join ', '
        Write-Host ("[STOPPING] Stopping {0} (Port {1}, PIDs: {2})..." -f $Name, $Port, $pidStr) -ForegroundColor Yellow
        foreach ($pidToKill in $pids) {
            Stop-Process -Id $pidToKill -Force -ErrorAction SilentlyContinue
        }
        Write-Host ("[SUCCESS] {0} stopped, port {1} freed" -f $Name, $Port) -ForegroundColor Green
    } else {
        Write-Host ("[INFO] {0} port {1} is free" -f $Name, $Port) -ForegroundColor Gray
    }
}

function Stop-All {
    Stop-PortProcess -Port $FrontendPort -Name "Frontend Vite"
    Stop-PortProcess -Port $BackendPort -Name "Backend FastAPI"
}

function Start-Backend {
    Write-Host ("[STARTING] Starting Backend FastAPI (Port {0})..." -f $BackendPort) -ForegroundColor Cyan
    $env:PYTHONPATH = $ProjectRoot
    $pyExec = Join-Path $ProjectRoot "venv\Scripts\python.exe"
    if (-not (Test-Path $pyExec)) {
        $pyExec = "python"
    }
    Start-Process -FilePath $pyExec -ArgumentList "backend/run_server.py --port $BackendPort" -WorkingDirectory $ProjectRoot -WindowStyle Hidden
    Write-Host ("[SUCCESS] Backend started! API: http://127.0.0.1:{0}" -f $BackendPort) -ForegroundColor Green
}

function Start-Frontend {
    Write-Host ("[STARTING] Starting Frontend Vite (Port {0})..." -f $FrontendPort) -ForegroundColor Cyan
    Start-Process -FilePath "npx.cmd" -ArgumentList "vite --host 0.0.0.0 --port $FrontendPort" -WorkingDirectory $ProjectRoot -WindowStyle Hidden
    Write-Host ("[SUCCESS] Frontend started! URL: http://localhost:{0}/" -f $FrontendPort) -ForegroundColor Green
}

function Show-Status {
    Write-Host "======================================================" -ForegroundColor Cyan
    Write-Host "      WellToken Price Dashboard CLI (wpd)             " -ForegroundColor Cyan
    Write-Host "======================================================" -ForegroundColor Cyan
    $bConn = Get-NetTCPConnection -LocalPort $BackendPort -ErrorAction SilentlyContinue
    $fConn = Get-NetTCPConnection -LocalPort $FrontendPort -ErrorAction SilentlyContinue

    if ($bConn) {
        $bPids = ($bConn.OwningProcess | Select-Object -Unique) -join ', '
        Write-Host ("  * Backend FastAPI: [RUNNING] (Port {0}, PID: {1})" -f $BackendPort, $bPids) -ForegroundColor Green
    } else {
        Write-Host ("  * Backend FastAPI: [STOPPED] (Port {0})" -f $BackendPort) -ForegroundColor Red
    }

    if ($fConn) {
        $fPids = ($fConn.OwningProcess | Select-Object -Unique) -join ', '
        Write-Host ("  * Frontend Vite:   [RUNNING] (Port {0}, PID: {1})" -f $FrontendPort, $fPids) -ForegroundColor Green
        Write-Host ("    -> URL: http://localhost:{0}/" -f $FrontendPort) -ForegroundColor Yellow
    } else {
        Write-Host ("  * Frontend Vite:   [STOPPED] (Port {0})" -f $FrontendPort) -ForegroundColor Red
    }
}

if ($Action -eq "--restart" -or $Action -eq "restart" -or $Action -eq "") {
    Write-Host "[RESTART] Restarting WPD services..." -ForegroundColor Cyan
    Stop-All
    Start-Sleep -Seconds 1
    Start-Backend
    Start-Sleep -Seconds 1
    Start-Frontend
    Write-Host "[SUCCESS] All WPD services restarted!" -ForegroundColor Green
}
elseif ($Action -eq "--stop" -or $Action -eq "stop") {
    Stop-All
    Write-Host "[SUCCESS] All WPD services stopped." -ForegroundColor Green
}
elseif ($Action -eq "--status" -or $Action -eq "status") {
    Show-Status
}
elseif ($Action -eq "--start" -or $Action -eq "start") {
    Start-Backend
    Start-Frontend
}
else {
    Write-Host ("Unknown argument: {0}" -f $Action)
    Write-Host "Usage:"
    Write-Host "  .\wpd --restart   # Restart frontend & backend"
    Write-Host "  .\wpd --stop      # Stop all services"
    Write-Host "  .\wpd --status    # Check status"
    Write-Host "  .\wpd --start     # Start services"
}
