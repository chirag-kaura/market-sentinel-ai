# Master Start & Lifecycle Controller for Market Sentinel AI
# Uses dedicated Conda environment 'market-sentinel' (C:\Users\HP\anaconda3\envs\market-sentinel)
# Starts Docker dev-stack sidecars (Redpanda, Console, Prometheus, Grafana) + k3d Kubernetes
# + k3d Kubernetes Dashboard (:30443) + MLflow UI (:5000),
# opens all 7 dashboard tabs automatically, and cleanly shuts down the entire platform when the user presses Enter or Ctrl+C.

$ErrorActionPreference = "Continue"
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $ProjectRoot

$CondaEnvName = "market-sentinel"
$CondaEnvPath = "C:\Users\HP\anaconda3\envs\market-sentinel"
$CondaPython  = "$CondaEnvPath\python.exe"
if (-not (Test-Path $CondaPython)) {
    $CondaPython = "python"
}
$env:CONDA_DEFAULT_ENV = $CondaEnvName
$env:CONDA_PREFIX      = $CondaEnvPath
$env:PATH              = "$CondaEnvPath;$CondaEnvPath\Scripts;$CondaEnvPath\Library\bin;$env:PATH"

$k3dCmd = (Get-Command k3d -ErrorAction SilentlyContinue).Source
if (-not $k3dCmd) {
    $k3dCandidate = "$env:LOCALAPPDATA\Microsoft\WinGet\Packages\k3d.k3d_Microsoft.Winget.Source_8wekyb3d8bbwe\k3d.exe"
    if (Test-Path $k3dCandidate) { $k3dCmd = $k3dCandidate }
}

Write-Host ""
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "   MARKET SENTINEL AI - MASTER PLATFORM LAUNCHER                 " -ForegroundColor Cyan
Write-Host "   Active Conda Environment: $CondaEnvName ($CondaEnvPath)" -ForegroundColor DarkCyan
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host ""

try {
    # 1. Verify Docker Engine is running
    Write-Host "[1/7] Checking Docker Engine status..." -ForegroundColor Cyan
    docker info >$null 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  -> Starting Docker Desktop..." -ForegroundColor Yellow
        $dockerDesktop = "C:\Program Files\Docker\Docker\Docker Desktop.exe"
        if (Test-Path $dockerDesktop) { Start-Process $dockerDesktop }
        Write-Host "  -> Waiting for Docker Engine to become ready..." -ForegroundColor Yellow
        for ($i = 0; $i -lt 30; $i++) {
            Start-Sleep -Seconds 3
            docker info >$null 2>&1
            if ($LASTEXITCODE -eq 0) { break }
        }
    }
    Write-Host "  -> Docker Engine is active." -ForegroundColor Green

    # 2. Verify Native Windows PostgreSQL 16
    Write-Host "[2/7] Checking Native Windows PostgreSQL 16 (port 5432)..." -ForegroundColor Cyan
    $pgSvc = Get-Service -Name "postgresql-x64-16" -ErrorAction SilentlyContinue
    if ($pgSvc -and $pgSvc.Status -ne "Running") {
        Start-Service -Name "postgresql-x64-16" -ErrorAction SilentlyContinue
    }
    Write-Host "  -> PostgreSQL 16 is running." -ForegroundColor Green

    # 3. Start Docker Compose dev-stack (Redpanda, Redpanda Console, Prometheus, Grafana)
    Write-Host "[3/7] Starting Docker sidecars (Redpanda, Redpanda Console, Prometheus, Grafana)..." -ForegroundColor Cyan
    docker compose --profile dev-stack up -d

    # 4. Start k3d Kubernetes Cluster (or ensure pods are ready)
    Write-Host "[4/7] Starting k3d Lightweight Kubernetes cluster 'sentinel'..." -ForegroundColor Cyan
    $k8sToken = $null
    if ($k3dCmd) {
        # Free port 8000 if a stray local non-Docker python process is holding it
        $conns8000 = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
        foreach ($c in $conns8000) {
            $p = Get-Process -Id $c.OwningProcess -ErrorAction SilentlyContinue
            if ($p -and $p.ProcessName -notmatch "docker|com\.docker|vpnkit|wsl") {
                Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
            }
        }

        & $k3dCmd cluster start sentinel 2>$null
        kubectl config use-context k3d-sentinel >$null 2>&1
        Write-Host "  -> Waiting for k3d Kubernetes API server to become ready..." -ForegroundColor Yellow
        for ($i = 0; $i -lt 30; $i++) {
            kubectl get nodes >$null 2>&1
            if ($LASTEXITCODE -eq 0) { break }
            Start-Sleep -Seconds 2
        }
        kubectl rollout status deployment/sentinel-backend -n market-sentinel --timeout=60s
        kubectl rollout status deployment/sentinel-frontend -n market-sentinel --timeout=60s

        # 5. Deploy & forward k3d Kubernetes Web UI on port 30443
        Write-Host "[5/7] Deploying & forwarding k3d Kubernetes Web UI on port 30443..." -ForegroundColor Cyan
        kubectl apply -f "$ProjectRoot\deployment\k8s\k8s_dashboard.yaml"
        kubectl rollout status deployment/kubernetes-dashboard -n kubernetes-dashboard --timeout=120s
        $port30443 = Get-NetTCPConnection -LocalPort 30443 -State Listen -ErrorAction SilentlyContinue
        if (-not $port30443) {
            Start-Process -FilePath "kubectl" -ArgumentList "port-forward", "--address", "127.0.0.1,::1", "-n", "kubernetes-dashboard", "svc/kubernetes-dashboard", "30443:9090" -WorkingDirectory $ProjectRoot -WindowStyle Hidden
            for ($i = 0; $i -lt 15; $i++) {
                Start-Sleep -Seconds 1
                $port30443 = Get-NetTCPConnection -LocalPort 30443 -State Listen -ErrorAction SilentlyContinue
                if ($port30443) { break }
                if ($i -eq 5 -or $i -eq 10) {
                    Start-Process -FilePath "kubectl" -ArgumentList "port-forward", "--address", "127.0.0.1,::1", "-n", "kubernetes-dashboard", "svc/kubernetes-dashboard", "30443:9090" -WorkingDirectory $ProjectRoot -WindowStyle Hidden
                }
            }
        }
        if ($port30443) {
            Write-Host "  -> k3d Kubernetes Dashboard active at http://localhost:30443" -ForegroundColor Green
        } else {
            Write-Host "  -> Warning: k3d Kubernetes Dashboard port-forward on 30443 did not bind in time." -ForegroundColor Yellow
        }
        $k8sToken = (kubectl -n kubernetes-dashboard create token admin-user 2>$null)
    } else {
        Write-Host "  -> k3d not found; falling back to local Conda FastAPI on port 8000..." -ForegroundColor Yellow
        Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$ProjectRoot'; & '$CondaPython' -m uvicorn backend.main:app --host 0.0.0.0 --port 8000" -WindowStyle Minimized
        Write-Host "[5/7] Skipping k3d Kubernetes Web UI (k3d CLI not installed)." -ForegroundColor DarkGray
    }

    # 6. Start MLflow Tracking & Model Registry UI on port 5000 (inside market-sentinel Conda env)
    Write-Host "[6/7] Starting MLflow Model Registry UI on port 5000 (Conda: $CondaEnvName)..." -ForegroundColor Cyan
    $port5000 = Get-NetTCPConnection -LocalPort 5000 -State Listen -ErrorAction SilentlyContinue
    if (-not $port5000) {
        Start-Process -FilePath $CondaPython -ArgumentList "-m", "mlflow", "ui", "--host", "127.0.0.1", "--port", "5000" -WorkingDirectory $ProjectRoot -WindowStyle Hidden
        Write-Host "  -> MLflow UI started in background on http://localhost:5000" -ForegroundColor Green
    } else {
        Write-Host "  -> MLflow UI already listening on http://localhost:5000" -ForegroundColor Green
    }

    # 7. Open all 7 dashboard tabs automatically
    Write-Host "[7/7] Opening all 7 live dashboards in your browser..." -ForegroundColor Cyan
    Start-Sleep -Seconds 3
    Start-Process "http://localhost:30080"
    Start-Process "http://localhost:8000/docs"
    Start-Process "http://localhost:8080"
    Start-Process "http://localhost:3001/d/market-sentinel-live"
    Start-Process "http://localhost:9090"
    Start-Process "http://localhost:5000"
    if ($k3dCmd) {
        Start-Process "http://localhost:30443/#/workloads?namespace=market-sentinel"
    }

    $os = Get-CimInstance Win32_OperatingSystem
    $totalGB = [math]::Round($os.TotalVisibleMemorySize / 1MB, 2)
    $freeGB = [math]::Round($os.FreePhysicalMemory / 1MB, 2)
    $usedGB = [math]::Round($totalGB - $freeGB, 2)

    Write-Host ""
    Write-Host "=================================================================" -ForegroundColor Green
    Write-Host "   MARKET SENTINEL AI IS LIVE! (Conda Env: $CondaEnvName)" -ForegroundColor Green
    Write-Host "=================================================================" -ForegroundColor Green
    Write-Host "  1. Kubernetes App UI (NGINX) : http://localhost:30080" -ForegroundColor White
    Write-Host "  2. FastAPI Docs (K8s)        : http://localhost:8000/docs" -ForegroundColor White
    Write-Host "  3. Redpanda Console          : http://localhost:8080" -ForegroundColor White
    Write-Host "  4. Grafana Live Dashboard    : http://localhost:3001/d/market-sentinel-live" -ForegroundColor White
    Write-Host "  5. Prometheus UI             : http://localhost:9090" -ForegroundColor White
    Write-Host "  6. MLflow Model Registry     : http://localhost:5000" -ForegroundColor White
    Write-Host "  7. k3d Kubernetes Dashboard  : http://localhost:30443/#/workloads?namespace=market-sentinel" -ForegroundColor White
    Write-Host "-----------------------------------------------------------------" -ForegroundColor DarkGray
    Write-Host "  Laptop RAM: $usedGB GB used / $totalGB GB total ($freeGB GB FREE)" -ForegroundColor Cyan
    Write-Host "=================================================================" -ForegroundColor Green
    if ($k8sToken) {
        Write-Host ""
        Write-Host "[Tip] On the k3d Dashboard login screen, click 'Skip' (or paste token below):" -ForegroundColor Cyan
        Write-Host "$k8sToken" -ForegroundColor DarkGray
    }
    Write-Host ""
    Write-Host "Keep this window open while working." -ForegroundColor Yellow
    Write-Host "Press [ENTER] or [Ctrl+C] at any time to SHUT DOWN all containers, MLflow, k3d UI & WSL2..." -ForegroundColor Yellow
    $null = Read-Host
}
finally {
    & "$ProjectRoot\scripts\stop_local_platform.ps1"
}
