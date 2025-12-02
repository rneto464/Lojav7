# Script PowerShell para iniciar o servidor
Write-Host "Iniciando servidor FastAPI..." -ForegroundColor Green
python -m uvicorn main:app --reload

