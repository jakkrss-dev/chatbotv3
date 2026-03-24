Write-Host "Starting RAG Chatbot v2 Services..." -ForegroundColor Cyan

Write-Host "Starting PostgreSQL via Docker..." -ForegroundColor Cyan
Set-Location infra
docker compose up -d
Set-Location ..
Write-Host "Waiting for DB to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Check if deps are installed
if (!(Test-Path "backend\venv")) {
    Write-Host "Setting up Python Virtual Environment..."
    python -m venv backend\venv
}

Write-Host "Installing Backend Dependencies..."
.\backend\venv\Scripts\python.exe -m pip install -r backend\requirements.txt

Write-Host "Installing Frontend Dependencies..."
Set-Location frontend
npm install
Set-Location ..

Write-Host "Starting Backend on Port 8001..." -ForegroundColor Green
Start-Process -FilePath ".\backend\venv\Scripts\python.exe" -ArgumentList "-m backend.main" -WindowStyle Normal

Write-Host "Starting Frontend on Port 5174..." -ForegroundColor Green
Set-Location frontend
Start-Process -FilePath "npm.cmd" -ArgumentList "run dev" -WindowStyle Normal
Set-Location ..

Write-Host "All services started! Check the new windows. UI is at http://localhost:5174/" -ForegroundColor Yellow
