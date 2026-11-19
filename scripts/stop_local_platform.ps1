# Stop Script for Market Sentinel AI
# Cleanly stops k3d Kubernetes, Docker dev-stack sidecars (Redpanda, Console, Prometheus, Grafana),
# local background tasks (MLflow, Vite, local Uvicorn, k3d UI port-forward :30443), AND shuts down Docker Desktop + vmmemWSL
# so 100% of container & WSL2 RAM is returned to Windows immediately.

$ErrorActionPreference = "Continue"
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $ProjectRoot

Write-Host ""
Write-Host "=================================================================" -ForegroundColor Yellow
Write-Host "   MARKET SENTINEL AI - FULL SHUTDOWN & RAM RECOVERY             " -ForegroundColor Yellow
Write-Host "=================================================================" -ForegroundColor Yellow

# 1. Stop k3d Kubernetes cluster (pauses nodes without deleting cluster/images)
$k3dCmd = (Get-Command k3d -ErrorAction SilentlyContinue).Source
if (-not $k3dCmd) {
    $k3dCandidate = "$env:LOCALAPPDATA\Microsoft\WinGet\Packages\k3d.k3d_Microsoft.Winget.Source_8wekyb3d8bbwe\k3d.exe"
    if (Test-Path $k3dCandidate) { $k3dCmd = $k3dCandidate }
}
docker info >$null 2>&1
if ($LASTEXITCODE -eq 0) {
    if ($k3dCmd) {
        Write-Host "[1/4] Pausing k3d Kubernetes cluster 'sentinel'..." -ForegroundColor Cyan
        & $k3dCmd cluster stop sentinel 2>$null
    }
    Write-Host "[2/4] Stopping Docker sidecar containers (Redpanda, Console, Prometheus, Grafana)..." -ForegroundColor Cyan
    docker compose --profile dev-stack stop 2>$null
} else {
    Write-Host "[1/4] Docker Engine already stopped; skipping container stop." -ForegroundColor DarkGray
}

# 3. Stop local background listeners on ports 5000 (MLflow), 5173 (Vite), non-Docker 8000 (Uvicorn), and 30443 (k3d UI port-forward)
Write-Host "[3/4] Stopping local background processes (MLflow :5000, Vite :5173, local Uvicorn :8000, k3d UI :30443)..." -ForegroundColor Cyan
foreach ($port in @(5000, 5173, 8000, 30443)) {
    $conns = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    foreach ($c in $conns) {
        $proc = Get-Process -Id $c.OwningProcess -ErrorAction SilentlyContinue
        if ($proc -and $proc.ProcessName -notmatch "docker|com\.docker|vpnkit|wsl") {
            Write-Host "  -> Stopping $($proc.ProcessName) (PID $($proc.Id)) on port $port" -ForegroundColor DarkYellow
            Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
        }
    }
}
Get-Process -Name "kubectl" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue

# 4. Quit Docker Desktop background engines & shut down WSL2 VM (vmmemWSL) to reclaim ~2.5 GB RAM
Write-Host "[4/4] Shutting down Docker Desktop & WSL2 (vmmemWSL) to return all RAM to Windows..." -ForegroundColor Cyan
foreach ($procName in @("Docker Desktop", "com.docker.backend", "com.docker.build", "com.docker.dev-envs", "vpnkit")) {
    Get-Process -Name $procName -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
}
wsl --shutdown 2>$null

$os = Get-CimInstance Win32_OperatingSystem
$totalGB = [math]::Round($os.TotalVisibleMemorySize / 1MB, 2)
$freeGB = [math]::Round($os.FreePhysicalMemory / 1MB, 2)
$usedGB = [math]::Round($totalGB - $freeGB, 2)

Write-Host ""
Write-Host "=== All Market Sentinel AI Services & WSL2 Stopped Cleanly ===" -ForegroundColor Green
Write-Host "  (Native Windows PostgreSQL 16 database preserved intact on port 5432)" -ForegroundColor Gray
Write-Host "  Laptop RAM Now: $usedGB GB used / $totalGB GB total ($freeGB GB FREE)" -ForegroundColor Green
Write-Host ""
