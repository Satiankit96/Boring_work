<# 
.SYNOPSIS
    Stop all Auth Module services (Backend and Frontend)

.DESCRIPTION
    This script stops all running Python and Node.js processes
    that are part of the Auth Module application.

.EXAMPLE
    .\stop.ps1           # Stop all services
    .\stop.ps1 -Check    # Check what's running without stopping

.NOTES
    Author: Auth Module Team
#>

param(
    [switch]$Check
)

function Get-AuthProcesses {
    $processes = @{
        Python = @()
        Node = @()
    }
    
    Get-Process -Name "python" -ErrorAction SilentlyContinue | ForEach-Object {
        $processes.Python += @{
            Id = $_.Id
            Name = $_.ProcessName
            Path = $_.Path
        }
    }
    
    Get-Process -Name "node" -ErrorAction SilentlyContinue | ForEach-Object {
        $processes.Node += @{
            Id = $_.Id
            Name = $_.ProcessName
            Path = $_.Path
        }
    }
    
    return $processes
}

function Get-PortStatus {
    $ports = @(
        @{ Port = 8000; Name = "Backend API" }
        @{ Port = 5173; Name = "Frontend Dev Server" }
    )
    
    $inUse = @()
    
    foreach ($p in $ports) {
        $conn = Get-NetTCPConnection -LocalPort $p.Port -State Listen -ErrorAction SilentlyContinue
        if ($conn) {
            $inUse += @{
                Port = $p.Port
                Name = $p.Name
                ProcessId = $conn.OwningProcess
            }
        }
    }
    
    return $inUse
}

function Stop-AuthServices {
    $stopped = @{
        Python = 0
        Node = 0
    }
    
    # Stop Python processes
    Get-Process -Name "python" -ErrorAction SilentlyContinue | ForEach-Object {
        Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
        $stopped.Python++
    }
    
    # Stop Node processes
    Get-Process -Name "node" -ErrorAction SilentlyContinue | ForEach-Object {
        Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
        $stopped.Node++
    }
    
    return $stopped
}

# Main execution
Write-Host ""
Write-Host "=" * 50 -ForegroundColor Cyan
if ($Check) {
    Write-Host "  Service Status Check" -ForegroundColor Cyan
} else {
    Write-Host "  Stopping All Services" -ForegroundColor Cyan
}
Write-Host "=" * 50 -ForegroundColor Cyan

if ($Check) {
    # Check mode - just show status
    $processes = Get-AuthProcesses
    $ports = Get-PortStatus
    
    Write-Host "`nRunning Processes:" -ForegroundColor Yellow
    
    if ($processes.Python.Count -gt 0) {
        Write-Host "  Python: $($processes.Python.Count) process(es)" -ForegroundColor White
        foreach ($p in $processes.Python) {
            Write-Host "    - PID $($p.Id)" -ForegroundColor Gray
        }
    } else {
        Write-Host "  Python: None" -ForegroundColor Gray
    }
    
    if ($processes.Node.Count -gt 0) {
        Write-Host "  Node.js: $($processes.Node.Count) process(es)" -ForegroundColor White
        foreach ($p in $processes.Node) {
            Write-Host "    - PID $($p.Id)" -ForegroundColor Gray
        }
    } else {
        Write-Host "  Node.js: None" -ForegroundColor Gray
    }
    
    Write-Host "`nPorts in Use:" -ForegroundColor Yellow
    if ($ports.Count -gt 0) {
        foreach ($p in $ports) {
            Write-Host "  - Port $($p.Port) ($($p.Name)): In use (PID: $($p.ProcessId))" -ForegroundColor White
        }
    } else {
        Write-Host "  - No auth module ports in use" -ForegroundColor Gray
    }
    
} else {
    # Stop mode
    Write-Host "`nStopping processes..." -ForegroundColor Yellow
    
    $stopped = Stop-AuthServices
    
    Write-Host "  Python processes stopped: $($stopped.Python)" -ForegroundColor Green
    Write-Host "  Node.js processes stopped: $($stopped.Node)" -ForegroundColor Green
    
    # Wait for ports to be released
    Start-Sleep -Seconds 1
    
    # Verify ports are free
    $ports = Get-PortStatus
    if ($ports.Count -gt 0) {
        Write-Host "`nSome ports may still be in use:" -ForegroundColor Yellow
        foreach ($p in $ports) {
            Write-Host "  - Port $($p.Port) ($($p.Name))" -ForegroundColor Yellow
        }
    } else {
        Write-Host "`nAll services stopped successfully!" -ForegroundColor Green
    }
    
    Write-Host "`nTo restart, run: python run.py all" -ForegroundColor Cyan
}

Write-Host ""
