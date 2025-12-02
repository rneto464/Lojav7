# Sistema de Gestão de Estoque e Assistência Técnica

Sistema web completo para gerenciamento de estoque de produtos, controle de variações de cores, movimentações, fornecedores, peças de reparo, serviços e ordens de serviço com controle financeiro.

## 📋 Pré-requisitos

- Python 3.8 ou superior
- PostgreSQL (ou Supabase)
- pip (gerenciador de pacotes Python)

## 🚀 Instalação

1. **Clone ou navegue até o diretório do projeto:**
   ```bash
   cd lojaV7
   ```

2. **Crie um ambiente virtual (recomendado):**
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # Linux/Mac
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure o banco de dados:**
   - Copie o arquivo `.env.example` para `.env`:
     ```bash
     copy .env.example .env
     ```
   - Edite o arquivo `.env` e adicione sua URL de conexão do PostgreSQL:
     ```
     DATABASE_URL=postgresql://usuario:senha@host:porta/nome_do_banco
     ```

## ▶️ Como Iniciar

### Opção 1: Usando Python -m (Recomendado)

```bash
python -m uvicorn main:app --reload
```

### Opção 2: Usando os scripts fornecidos

**Windows (PowerShell):**
```powershell
.\iniciar.ps1
```

**Windows (CMD):**
```cmd
iniciar.bat
```

### Opção 3: Com host e porta personalizados

```bash
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### ⚠️ Nota Importante

Se o comando `uvicorn` não for reconhecido, use sempre `python -m uvicorn` ao invés de apenas `uvicorn`. Isso acontece quando o uvicorn não está no PATH do sistema.

3. **Acesse a aplicação:**
   - Abra seu navegador e acesse: `http://localhost:8000`
   - A documentação interativa da API estará disponível em: `http://localhost:8000/docs`

## 🚀 Deploy na Vercel

A aplicação está configurada para deploy na Vercel. Consulte o arquivo `DEPLOY_VERCEL.md` para instruções detalhadas.

**Deploy rápido:**
1. Conecte seu repositório GitHub na Vercel
2. Configure a variável de ambiente `DATABASE_URL`
3. Deploy automático a cada push!

## 📁 Estrutura do Projeto

```
lojaV7/
├── main.py              # Arquivo principal da aplicação FastAPI
├── database.py          # Configuração do banco de dados
├── models.py            # Modelos SQLAlchemy
├── schemas.py           # Schemas Pydantic para validação
├── requirements.txt     # Dependências do projeto
├── .env                 # Variáveis de ambiente (criar a partir do .env.example)
├── services/
│   └── categorizer.py   # Serviços auxiliares
├── services/
│   └── categorizer.py   # Serviços auxiliares
└── templates/
    ├── dashboard.html      # Página principal
    ├── products.html       # Página de produtos
    ├── movements.html      # Página de movimentações
    ├── suppliers.html      # Página de fornecedores
    ├── reparos.html        # Página de peças e serviços
    ├── ordens_servico.html # Página de ordens de serviço
    ├── financas.html       # Página de finanças
    └── configuracoes.html  # Página de configurações
```

## 🗄️ Banco de Dados

O sistema utiliza PostgreSQL (recomendado: Supabase). Execute os scripts SQL na ordem:

1. **Para recriar todas as tabelas:**
   ```sql
   -- Execute: criar_todas_tabelas.sql
   ```

2. **Para apagar todas as tabelas (cuidado!):**
   ```sql
   -- Execute: apagar_todas_tabelas.sql
   ```

## 📊 Estrutura de Dados

- **Produtos**: Produtos com variações de cores (SKU completo)
- **Peças Físicas**: Peças de reparo com estoque e custo
- **Serviços**: Serviços de mão de obra (sem estoque)
- **Ordens de Serviço**: Combinação de peças + serviços
- **Compras**: Controle de compras de peças com frete
- **Finanças**: Cálculo automático de lucros e margens
```

## 🔧 Funcionalidades

- **Dashboard**: Visão geral do estoque com métricas e alertas
- **Produtos**: Cadastro e gerenciamento de produtos e variações de cores
- **Movimentações**: Controle de entradas, saídas e ajustes de estoque
- **Fornecedores**: Cadastro de fornecedores
- **Catálogo de Peças**: Gerenciamento de peças físicas (Telas, Baterias, etc.)
- **Tabela de Serviços**: Gerenciamento de serviços de mão de obra
- **Ordens de Serviço**: Criação e acompanhamento de ordens de serviço
- **Finanças**: Controle de compras, custos e cálculo de lucros por serviço

## ⚠️ Nota Importante

O arquivo principal está nomeado como `main.py`. Use o comando de inicialização:

```bash
python -m uvicorn main:app --reload
```

## 🐛 Solução de Problemas

- **Erro de conexão com banco**: Verifique se a `DATABASE_URL` no arquivo `.env` está correta
- **Módulo não encontrado**: Certifique-se de que o ambiente virtual está ativado e as dependências foram instaladas
- **Porta já em uso**: Use uma porta diferente com `--port 8001`

