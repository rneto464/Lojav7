# 🚀 Guia de Deploy na Vercel

Este guia vai te ajudar a fazer deploy da aplicação na Vercel.

## 📋 Pré-requisitos

1. **Conta na Vercel**: Crie uma conta em [vercel.com](https://vercel.com)
2. **Vercel CLI** (opcional, mas recomendado): 
   ```bash
   npm i -g vercel
   ```
   Ou use a interface web da Vercel

## 🔧 Configuração

### 1. Variáveis de Ambiente

A Vercel precisa das variáveis de ambiente configuradas. Você pode fazer isso de duas formas:

#### Opção A: Via Interface Web (Recomendado)
1. Acesse seu projeto na Vercel
2. Vá em **Settings** → **Environment Variables**
3. Adicione:
   - `DATABASE_URL`: Sua URL de conexão do PostgreSQL (Supabase)
   - Exemplo: `postgresql://user:password@host:port/database`

#### Opção B: Via CLI
```bash
vercel env add DATABASE_URL
# Cole sua URL de conexão quando solicitado
```

### 2. Estrutura de Arquivos

A aplicação já está configurada com:
- ✅ `vercel.json` - Configuração do servidor
- ✅ `api/index.py` - Handler para a Vercel
- ✅ `.vercelignore` - Arquivos ignorados no deploy

## 🚀 Deploy

### Método 1: Via GitHub (Recomendado)

1. **Faça push do código para o GitHub** (se ainda não fez):
   ```bash
   git push origin main
   ```

2. **Conecte o repositório na Vercel**:
   - Acesse [vercel.com/new](https://vercel.com/new)
   - Conecte seu repositório do GitHub
   - A Vercel detectará automaticamente a configuração

3. **Configure as variáveis de ambiente** (Settings → Environment Variables)

4. **Deploy automático**: A Vercel fará deploy automaticamente a cada push

### Método 2: Via CLI

1. **Instale a Vercel CLI**:
   ```bash
   npm i -g vercel
   ```

2. **Faça login**:
   ```bash
   vercel login
   ```

3. **Deploy**:
   ```bash
   vercel
   ```

4. **Para produção**:
   ```bash
   vercel --prod
   ```

## ⚙️ Configurações Importantes

### Variáveis de Ambiente Necessárias

Certifique-se de configurar estas variáveis na Vercel:

- `DATABASE_URL`: URL completa de conexão com o PostgreSQL
  - Formato: `postgresql://usuario:senha@host:porta/banco`
  - Para Supabase: Use a connection string do projeto

### Limites da Vercel (Plano Gratuito)

- **Tempo de execução**: 10 segundos por requisição (Hobby)
- **Tamanho do projeto**: 100MB
- **Bandwidth**: 100GB/mês

### Dicas para Performance

1. **Use Supabase Connection Pooler**: 
   - Use a URL com `pooler.supabase.com` para melhor performance
   - Formato: `postgresql://user:pass@aws-0-region.pooler.supabase.com:6543/db`

2. **Otimize o banco de dados**:
   - Use índices nas tabelas
   - Evite queries muito complexas

3. **Cache quando possível**:
   - A Vercel faz cache automático de arquivos estáticos

## 🔍 Verificação Pós-Deploy

Após o deploy, verifique:

1. **URL da aplicação**: A Vercel fornecerá uma URL como `seu-projeto.vercel.app`
2. **Logs**: Verifique os logs em caso de erro (Vercel Dashboard → Deployments → Logs)
3. **Variáveis de ambiente**: Confirme que estão configuradas corretamente

## 🐛 Solução de Problemas

### Erro: "Module not found"
- Verifique se todos os arquivos necessários estão no repositório
- Confirme que `requirements.txt` está atualizado

### Erro: "Database connection failed"
- Verifique a `DATABASE_URL` nas variáveis de ambiente
- Confirme que o banco permite conexões externas (Supabase: Settings → Database → Connection Pooling)

### Erro: "Function timeout"
- Otimize queries complexas
- Considere usar cache ou reduzir processamento

### Erro: "Templates not found"
- Verifique se a pasta `templates/` está no repositório
- Confirme o caminho no `main.py`

## 📝 Estrutura de Arquivos para Vercel

```
projeto/
├── api/
│   └── index.py          # Handler da Vercel
├── templates/            # Templates HTML
├── services/             # Serviços auxiliares
├── main.py               # Aplicação FastAPI
├── models.py             # Modelos SQLAlchemy
├── schemas.py            # Schemas Pydantic
├── database.py           # Configuração do banco
├── requirements.txt      # Dependências
├── vercel.json           # Configuração da Vercel
├── .vercelignore         # Arquivos ignorados
└── .env                  # Variáveis locais (não commitado)
```

## 🔄 Atualizações

Para atualizar a aplicação:

1. **Via GitHub**: Faça push das alterações (deploy automático)
2. **Via CLI**: Execute `vercel --prod` novamente

## 📚 Recursos Adicionais

- [Documentação Vercel Python](https://vercel.com/docs/concepts/functions/serverless-functions/runtimes/python)
- [FastAPI na Vercel](https://vercel.com/guides/deploying-fastapi-with-vercel)
- [Supabase Connection Pooling](https://supabase.com/docs/guides/database/connecting-to-postgres#connection-pooler)

---

**Pronto!** Sua aplicação está configurada para deploy na Vercel! 🎉

