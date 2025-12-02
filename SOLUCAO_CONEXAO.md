# Guia de Solução de Problemas de Conexão com Banco de Dados

## Erro: "could not translate host name to address"

Este erro indica que o sistema não consegue resolver o nome do servidor do Supabase. Siga os passos abaixo:

### 1. Verificar o arquivo .env

Certifique-se de que existe um arquivo `.env` na raiz do projeto com a URL correta:

```env
DATABASE_URL=postgresql://postgres.xxxxx:SUA_SENHA@aws-0-sa-east-1.pooler.supabase.com:6543/postgres
```

**Importante:**
- Substitua `xxxxx` pelo ID do seu projeto Supabase
- Substitua `SUA_SENHA` pela senha real do banco
- Verifique se o host está correto (pode ser `aws-0`, `aws-1`, etc.)

### 2. Obter a URL correta do Supabase

1. Acesse https://supabase.com/dashboard
2. Selecione seu projeto
3. Vá em **Settings** → **Database**
4. Role até **Connection string** → **Connection pooling**
5. Copie a URL que começa com `postgresql://`
6. Cole no arquivo `.env`

### 3. Verificar se o projeto está ativo

Projetos gratuitos do Supabase podem pausar após inatividade:

1. Acesse o dashboard do Supabase
2. Verifique se o projeto está **pausado** (aparece um botão "Restore" ou "Resume")
3. Se estiver pausado, clique para restaurar
4. Aguarde alguns minutos para o projeto ficar totalmente ativo

### 4. Testar conexão com a internet

O erro pode ser causado por problemas de rede:

```bash
# Teste se consegue acessar o Supabase
ping aws-0-sa-east-1.pooler.supabase.com
```

Se não conseguir fazer ping, pode ser:
- Problema de conexão com internet
- Firewall bloqueando
- DNS não funcionando

### 5. Testar a conexão

Execute o script de teste:

```bash
python testar_conexao.py
```

Este script vai mostrar exatamente qual é o problema.

### 6. Verificar firewall/antivírus

Alguns firewalls ou antivírus podem bloquear conexões PostgreSQL:
- Adicione uma exceção para Python
- Verifique se a porta 6543 (pooler) ou 5432 (direto) está bloqueada

### 7. Usar conexão direta (sem pooler)

Se o pooler não funcionar, tente a conexão direta:

1. No Supabase, vá em **Settings** → **Database**
2. Use a **Connection string** → **Direct connection** (não pooling)
3. A porta será `5432` ao invés de `6543`

### 8. Verificar formato da URL

A URL deve estar no formato:

```
postgresql://postgres.PROJETO_ID:SENHA@aws-0-sa-east-1.pooler.supabase.com:6543/postgres
```

**Erros comuns:**
- ❌ `postgres://` (deve ser `postgresql://`)
- ❌ Espaços na URL
- ❌ Caracteres especiais na senha não codificados
- ❌ Hostname incorreto

### 9. Recriar o arquivo .env

Se nada funcionar, recrie o arquivo:

1. Delete o arquivo `.env` atual
2. Copie o `env.example.txt`:
   ```bash
   # Windows
   copy env.example.txt .env
   
   # Linux/Mac
   cp env.example.txt .env
   ```
3. Edite o `.env` e cole a URL correta do Supabase

### 10. Modo de visualização

Se não conseguir resolver agora, a aplicação funcionará em **modo de visualização**:
- Você pode ver todas as páginas
- Mas não poderá salvar dados
- Os valores aparecerão zerados

Para usar o banco de dados, é necessário resolver o problema de conexão.

## Ainda com problemas?

1. Verifique os logs do Supabase no dashboard
2. Tente criar um novo projeto Supabase
3. Verifique se sua conta Supabase está ativa
4. Entre em contato com o suporte do Supabase se o problema persistir

