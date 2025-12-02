# 🚀 Guia para Fazer Upload no GitHub

Este guia vai te ajudar a fazer upload da aplicação para o GitHub.

## 📋 Pré-requisitos

1. **Conta no GitHub**: Crie uma conta em [github.com](https://github.com) se ainda não tiver
2. **Git instalado**: Verifique se o Git está instalado:
   ```bash
   git --version
   ```
   Se não estiver, baixe em: [git-scm.com](https://git-scm.com/)

## 🔧 Passo a Passo

### 1. Inicializar o Repositório Git

Abra o PowerShell ou Terminal no diretório do projeto e execute:

```powershell
# Inicializar o repositório Git
git init

# Adicionar todos os arquivos (exceto os ignorados pelo .gitignore)
git add .

# Fazer o primeiro commit
git commit -m "Initial commit: Sistema de Gestão de Estoque e Assistência Técnica"
```

### 2. Criar Repositório no GitHub

1. Acesse [github.com](https://github.com) e faça login
2. Clique no botão **"+"** no canto superior direito
3. Selecione **"New repository"**
4. Preencha:
   - **Repository name**: `sistema-gestao-estoque` (ou o nome que preferir)
   - **Description**: "Sistema completo de gestão de estoque e assistência técnica"
   - **Visibility**: Escolha **Public** ou **Private**
   - **NÃO marque** "Initialize this repository with a README" (já temos um)
5. Clique em **"Create repository"**

### 3. Conectar o Repositório Local ao GitHub

Após criar o repositório, o GitHub vai mostrar comandos. Use estes:

```powershell
# Adicionar o repositório remoto (substitua SEU_USUARIO pelo seu usuário do GitHub)
git remote add origin https://github.com/SEU_USUARIO/sistema-gestao-estoque.git

# Renomear a branch principal para 'main' (se necessário)
git branch -M main

# Fazer o primeiro push
git push -u origin main
```

### 4. Autenticação

Na primeira vez, o GitHub pode pedir autenticação:

- **Opção 1 - Token de Acesso Pessoal** (Recomendado):
  1. Vá em: GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
  2. Clique em "Generate new token"
  3. Dê um nome e selecione o escopo `repo`
  4. Copie o token gerado
  5. Use o token como senha quando o Git pedir

- **Opção 2 - GitHub CLI**:
  ```powershell
  # Instalar GitHub CLI
  winget install GitHub.cli
  
  # Autenticar
  gh auth login
  ```

### 5. Verificar o Upload

1. Acesse seu repositório no GitHub
2. Você deve ver todos os arquivos do projeto
3. O README.md será exibido automaticamente na página principal

## 🔄 Atualizações Futuras

Sempre que fizer alterações, use estes comandos:

```powershell
# Ver o status das alterações
git status

# Adicionar arquivos alterados
git add .

# Fazer commit com mensagem descritiva
git commit -m "Descrição das alterações feitas"

# Enviar para o GitHub
git push
```

## 📝 Boas Práticas

### Mensagens de Commit

Use mensagens claras e descritivas:

```powershell
git commit -m "Adiciona funcionalidade de cálculo de lucros"
git commit -m "Corrige bug na atualização de estoque"
git commit -m "Atualiza documentação do README"
```

### Branches (Opcional)

Para trabalhar em funcionalidades separadas:

```powershell
# Criar nova branch
git checkout -b feature/nova-funcionalidade

# Trabalhar normalmente...
git add .
git commit -m "Implementa nova funcionalidade"

# Voltar para main
git checkout main

# Mesclar a branch
git merge feature/nova-funcionalidade

# Deletar a branch (opcional)
git branch -d feature/nova-funcionalidade
```

## ⚠️ Arquivos que NÃO serão enviados

O arquivo `.gitignore` garante que estes arquivos **NÃO** sejam enviados:

- `.env` (variáveis de ambiente com senhas)
- `config.json` (configurações locais)
- `__pycache__/` (arquivos Python compilados)
- `venv/` (ambiente virtual)
- Arquivos temporários e de backup

## 🔐 Segurança

**IMPORTANTE**: Nunca faça commit de:

- Arquivos `.env` com senhas reais
- Tokens de API
- Chaves de acesso ao banco de dados
- Credenciais de produção

Se você acidentalmente commitou algo sensível:

1. Remova do histórico (cuidado!):
   ```powershell
   git filter-branch --force --index-filter "git rm --cached --ignore-unmatch .env" --prune-empty --tag-name-filter cat -- --all
   ```

2. Ou use o GitHub Secret Scanning para detectar vazamentos

## 📚 Recursos Adicionais

- [Documentação do Git](https://git-scm.com/doc)
- [GitHub Guides](https://guides.github.com/)
- [Git Cheat Sheet](https://education.github.com/git-cheat-sheet-education.pdf)

## 🆘 Problemas Comuns

### Erro: "remote origin already exists"
```powershell
git remote remove origin
git remote add origin https://github.com/SEU_USUARIO/sistema-gestao-estoque.git
```

### Erro: "failed to push some refs"
```powershell
git pull origin main --rebase
git push origin main
```

### Esqueceu de adicionar arquivo ao .gitignore
```powershell
# Remover arquivo do cache do Git (mas manter localmente)
git rm --cached arquivo_sensivel.txt
git commit -m "Remove arquivo sensível do repositório"
git push
```

---

**Pronto!** Sua aplicação está no GitHub! 🎉

