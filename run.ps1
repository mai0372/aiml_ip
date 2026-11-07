<#
.SYNOPSIS
    ClauseLens Windows PowerShell Task Runner
.DESCRIPTION
    Runs tests, evaluation, linter, builds, or launches development servers.
.EXAMPLE
    .\run.ps1 test
    .\run.ps1 eval
    .\run.ps1 dev
#>

param(
    [Parameter(Position=0)]
    [ValidateSet("test", "eval", "lint", "build", "dev", "dev-backend", "dev-frontend", "install", "help")]
    [string]$Task = "help"
)

$ErrorActionPreference = "Stop"

switch ($Task) {
    "test" {
        Write-Host "`n[ClauseLens] Running 16 Pytest tests..." -ForegroundColor Cyan
        python -m pytest backend/tests -v
    }
    "eval" {
        Write-Host "`n[ClauseLens] Running benchmark evaluation harness..." -ForegroundColor Cyan
        python -m backend.eval.run_eval
    }
    "lint" {
        Write-Host "`n[ClauseLens] Running Ruff linter..." -ForegroundColor Cyan
        python -m ruff check backend/
    }
    "build" {
        Write-Host "`n[ClauseLens] Building React/TypeScript frontend..." -ForegroundColor Cyan
        Set-Location frontend
        npm run build
        Set-Location ..
    }
    "dev-backend" {
        Write-Host "`n[ClauseLens] Starting FastAPI backend on http://localhost:8000..." -ForegroundColor Cyan
        python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
    }
    "dev-frontend" {
        Write-Host "`n[ClauseLens] Starting Vite frontend on http://localhost:5173..." -ForegroundColor Cyan
        Set-Location frontend
        npm run dev
        Set-Location ..
    }
    "dev" {
        Write-Host "`n[ClauseLens] Starting backend and frontend concurrently..." -ForegroundColor Cyan
        $backendProcess = Start-Process python -ArgumentList "-m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload" -PassThru
        try {
            Set-Location frontend
            npm run dev
        }
        finally {
            Set-Location ..
            Stop-Process -Id $backendProcess.Id -Force -ErrorAction SilentlyContinue
        }
    }
    "install" {
        Write-Host "`n[ClauseLens] Installing Python and Node dependencies..." -ForegroundColor Cyan
        python -m pip install -r backend/requirements.txt
        Set-Location frontend
        npm install
        Set-Location ..
    }
    default {
        Write-Host "ClauseLens PowerShell Runner Usage:" -ForegroundColor Yellow
        Write-Host "  .\run.ps1 test         - Run all 16 backend unit & integration tests"
        Write-Host "  .\run.ps1 eval         - Run benchmark evaluation harness"
        Write-Host "  .\run.ps1 lint         - Run ruff linter check"
        Write-Host "  .\run.ps1 build        - Compile production frontend build"
        Write-Host "  .\run.ps1 dev          - Start both backend & frontend dev servers"
        Write-Host "  .\run.ps1 dev-backend  - Start FastAPI server on port 8000"
        Write-Host "  .\run.ps1 dev-frontend - Start Vite server on port 5173"
    }
}
