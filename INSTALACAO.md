# Guia de Instalação - Solução de Problemas

## Problema com psycopg2-binary no Windows/Python 3.13

Se você encontrar erros ao instalar `psycopg2-binary`, siga estas soluções:

### Solução 1: Instalar psycopg2-binary separadamente (Recomendado)

```bash
# Primeiro, instale as outras dependências
pip install fastapi uvicorn[standard] sqlalchemy python-dotenv pydantic jinja2

# Depois, tente instalar psycopg2-binary
pip install psycopg2-binary
```

### Solução 2: Usar psycopg (versão 3) - Mais moderno

Se a Solução 1 não funcionar, você pode usar `psycopg` (versão 3):

```bash
# Instale todas as dependências exceto psycopg2-binary
pip install fastapi uvicorn[standard] sqlalchemy python-dotenv pydantic jinja2

# Instale psycopg (versão 3)
pip install "psycopg[binary]>=3.1.0"
```

**IMPORTANTE:** Se usar psycopg versão 3, você precisará atualizar a URL de conexão no `database.py`:
- Troque `postgresql://` por `postgresql+psycopg://` na URL de conexão

### Solução 3: Usar Python 3.11 ou 3.12 (Mais compatível)

O Python 3.13 é muito recente e pode ter problemas de compatibilidade. Considere usar Python 3.11 ou 3.12:

```bash
# Criar ambiente virtual com Python 3.11 ou 3.12
py -3.11 -m venv venv
# ou
py -3.12 -m venv venv
```

### Solução 4: Instalar dependências uma por uma

```bash
pip install fastapi==0.104.1
pip install "uvicorn[standard]==0.24.0"
pip install sqlalchemy==2.0.23
pip install python-dotenv==1.0.0
pip install pydantic==2.5.0
pip install jinja2==3.1.2
pip install psycopg2-binary --no-cache-dir
```

### Verificar instalação

Após instalar, verifique se tudo está funcionando:

```bash
python -c "import fastapi; import sqlalchemy; import psycopg2; print('Tudo instalado corretamente!')"
```

