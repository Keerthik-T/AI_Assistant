Write-Host "Creating Python Virtual Environment..." -ForegroundColor Cyan
python -m venv .venv

Write-Host "Activating Virtual Environment..." -ForegroundColor Cyan
& .venv\Scripts\Activate.ps1

Write-Host "Upgrading pip..." -ForegroundColor Cyan
python -m pip install --upgrade pip

Write-Host "Installing dependencies from requirements.txt..." -ForegroundColor Cyan
pip install -r requirements.txt

Write-Host "Virtual environment setup complete!" -ForegroundColor Green
