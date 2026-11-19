@echo off
title Market Sentinel AI - Master Platform Controller (Conda: market-sentinel)
REM Managed UIs launched automatically (7 tabs):
REM   1. Kubernetes App UI (NGINX) : http://localhost:30080
REM   2. FastAPI Docs (K8s)        : http://localhost:8000/docs
REM   3. Redpanda Console          : http://localhost:8080
REM   4. Grafana Live Dashboard    : http://localhost:3001/d/market-sentinel-live
REM   5. Prometheus UI             : http://localhost:9090
REM   6. MLflow Model Registry     : http://localhost:5000
REM   7. k3d Kubernetes Dashboard  : http://localhost:30443/#/workloads?namespace=market-sentinel
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\start_local_platform.ps1"
