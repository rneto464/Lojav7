# Script PowerShell para fazer upload no GitHub
# Execute este script após criar o repositório no GitHub

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Upload para GitHub - Gestão Estoque" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Verificar se o Git está instalado
try {
    $gitVersion = git --version
    Write-Host "✓ Git encontrado: $gitVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Git não encontrado! Instale o Git primeiro." -ForegroundColor Red
    Write-Host "  Download: https://git-scm.com/download/win" -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# Verificar se já é um repositório Git
if (Test-Path .git) {
    Write-Host "✓ Repositório Git já inicializado" -ForegroundColor Green
} else {
    Write-Host "Inicializando repositório Git..." -ForegroundColor Yellow
    git init
    Write-Host "✓ Repositório inicializado" -ForegroundColor Green
}

Write-Host ""

# Adicionar todos os arquivos
Write-Host "Adicionando arquivos ao Git..." -ForegroundColor Yellow
git add .
Write-Host "✓ Arquivos adicionados" -ForegroundColor Green

Write-Host ""

# Verificar se há alterações para commitar
$status = git status --porcelain
if ($status) {
    Write-Host "Fazendo commit inicial..." -ForegroundColor Yellow
    git commit -m "Initial commit: Sistema de Gestão de Estoque e Assistência Técnica
    
    - Sistema completo de gestão de estoque
    - Controle de produtos com variações de cores
    - Gerenciamento de peças físicas e serviços
    - Ordens de serviço com cálculo de lucros
    - Controle financeiro de compras e vendas
    - Interface web moderna com FastAPI"
    Write-Host "✓ Commit realizado" -ForegroundColor Green
} else {
    Write-Host "ℹ Nenhuma alteração para commitar" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Próximos Passos:" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Crie um repositório no GitHub:" -ForegroundColor Yellow
Write-Host "   https://github.com/new" -ForegroundColor White
Write-Host ""
Write-Host "2. Depois de criar, execute estes comandos:" -ForegroundColor Yellow
Write-Host ""
Write-Host "   git remote add origin https://github.com/SEU_USUARIO/NOME_DO_REPO.git" -ForegroundColor White
Write-Host "   git branch -M main" -ForegroundColor White
Write-Host "   git push -u origin main" -ForegroundColor White
Write-Host ""
Write-Host "   (Substitua SEU_USUARIO e NOME_DO_REPO pelos seus valores)" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Ou use o GitHub CLI (se instalado):" -ForegroundColor Yellow
Write-Host "   gh repo create --public --source=. --remote=origin --push" -ForegroundColor White
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Para mais detalhes, consulte: GUIA_GITHUB.md" -ForegroundColor Cyan
Write-Host ""

