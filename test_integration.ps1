$ErrorActionPreference = "Stop"
$env:FRONTEND_BUILD_DIR = "f:\ATS resume ANalyzer\frontend\dist"
$env:DATABASE_URL = "sqlite+aiosqlite:///./test_integration.db"
$env:ENVIRONMENT = "development"
$env:RATE_LIMIT_ENABLED = "false"
$env:JWT_SECRET_KEY = "dev-secret-key-change-in-production-abc123xyz"

Remove-Item test_integration.db -ErrorAction SilentlyContinue

Write-Host "Starting uvicorn..." -ForegroundColor Cyan
$proc = Start-Process -FilePath "python" `
    -ArgumentList "-m","uvicorn","app.main:app","--host","127.0.0.1","--port","8765" `
    -RedirectStandardOutput "uvicorn.log" `
    -RedirectStandardError "uvicorn_err.log" `
    -PassThru

Start-Sleep -Seconds 8

Write-Host "=== STARTING TESTS ===" -ForegroundColor Yellow

function Test-Endpoint {
    param([string]$Name, [string]$Url, [string]$Method = "GET", [string]$Body = $null, [hashtable]$Headers = @{})
    try {
        if ($Body) {
            $Headers["Content-Type"] = "application/json"
            $resp = Invoke-WebRequest -Uri $Url -Method $Method -Body $Body -Headers $Headers -UseBasicParsing -ErrorAction Stop
        } else {
            $resp = Invoke-WebRequest -Uri $Url -Method $Method -UseBasicParsing -ErrorAction Stop
        }
        Write-Host "  $Name : $($resp.StatusCode) OK" -ForegroundColor Green
    } catch {
        $code = if ($_.Exception.Response) { $_.Exception.Response.StatusCode.value__ } else { "ERR" }
        Write-Host "  $Name : $code" -ForegroundColor Red
    }
}

Test-Endpoint "healthz" "http://127.0.0.1:8765/healthz"
Test-Endpoint "health" "http://127.0.0.1:8765/health"
Test-Endpoint "spa_fallback" "http://127.0.0.1:8765/some-nonexistent-route"
Test-Endpoint "spa_upload" "http://127.0.0.1:8765/upload"
Test-Endpoint "spa_results" "http://127.0.0.1:8765/results/123"
Test-Endpoint "spa_history" "http://127.0.0.1:8765/history"
Test-Endpoint "spa_login" "http://127.0.0.1:8765/login"
Test-Endpoint "spa_root" "http://127.0.0.1:8765/"
Test-Endpoint "api_auth_register" "http://127.0.0.1:8765/auth/register" -Method POST -Body '{"email":"test@example.com","username":"testuser","password":"SecurePass1"}'
Test-Endpoint "api_analysis_demo" "http://127.0.0.1:8765/analysis/demo" -Method POST -Body '{"resume_text":"Test resume with Python and SQL skills","job_description":"Looking for Python SQL developer"}'
Test-Endpoint "static_asset" "http://127.0.0.1:8765/assets/index-C0kjRs8y.js"

Write-Host "`n=== STOPPING BACKEND ===" -ForegroundColor Yellow
$proc | Stop-Process -Force
Start-Sleep -Seconds 2

Write-Host "`n=== UVICORN LOG ===" -ForegroundColor Yellow
Get-Content uvicorn.log
Write-Host "`n=== UVICORN ERR LOG ===" -ForegroundColor Yellow
Get-Content uvicorn_err.log -ErrorAction SilentlyContinue