"""
Script para verificar e diagnosticar problemas de conexão com o Supabase
Execute: python verificar_conexao.py
"""
import os
import sys
from dotenv import load_dotenv

print("=" * 60)
print("DIAGNOSTICO DE CONEXAO COM SUPABASE")
print("=" * 60)

# 1. Verificar se o arquivo .env existe
print("\n1. Verificando arquivo .env...")
if not os.path.exists('.env'):
    print("   ❌ Arquivo .env NAO encontrado!")
    print("\n   Solucao:")
    print("   1. Copie o arquivo env.example.txt para .env:")
    print("      Windows: copy env.example.txt .env")
    print("      Linux/Mac: cp env.example.txt .env")
    print("   2. Edite o arquivo .env e adicione sua DATABASE_URL do Supabase")
    sys.exit(1)
else:
    print("   ✅ Arquivo .env encontrado")

# 2. Carregar variáveis
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("\n   ❌ DATABASE_URL nao encontrada no arquivo .env!")
    print("\n   Solucao:")
    print("   Adicione a linha no arquivo .env:")
    print("   DATABASE_URL=postgresql://postgres.xxxxx:SENHA@aws-0-sa-east-1.pooler.supabase.com:6543/postgres")
    sys.exit(1)
else:
    print("   ✅ DATABASE_URL encontrada")

# 3. Verificar formato da URL
print("\n2. Verificando formato da URL...")
if "usuario:senha" in DATABASE_URL or "nome_do_banco" in DATABASE_URL:
    print("   ❌ URL parece ser um placeholder!")
    print("   A URL contem valores de exemplo que precisam ser substituidos.")
    sys.exit(1)

if not DATABASE_URL.startswith("postgresql://"):
    if DATABASE_URL.startswith("postgres://"):
        print("   ⚠️  URL usa 'postgres://', sera convertida para 'postgresql://'")
    else:
        print("   ❌ URL nao comeca com 'postgresql://' ou 'postgres://'")
        sys.exit(1)

# Extrair informações da URL
try:
    if "@" in DATABASE_URL:
        host_part = DATABASE_URL.split('@')[1].split('/')[0]
        if ":" in host_part:
            host, port = host_part.split(':')
        else:
            host = host_part
            port = "5432"
        print(f"   ✅ Host: {host}")
        print(f"   ✅ Porta: {port}")
    else:
        print("   ❌ Formato de URL invalido")
        sys.exit(1)
except Exception as e:
    print(f"   ❌ Erro ao analisar URL: {e}")
    sys.exit(1)

# 4. Verificar se consegue resolver o DNS
print("\n3. Testando resolucao de DNS...")
try:
    import socket
    socket.gethostbyname(host)
    print(f"   ✅ Hostname '{host}' resolvido com sucesso")
except socket.gaierror:
    print(f"   ❌ NAO foi possivel resolver o hostname '{host}'")
    print("\n   Possiveis causas:")
    print("   - Problema de conexao com a internet")
    print("   - Hostname incorreto")
    print("   - Problemas de DNS")
    print("\n   Solucao:")
    print("   1. Verifique sua conexao com a internet")
    print("   2. Acesse https://supabase.com/dashboard")
    print("   3. Vá em Settings -> Database -> Connection string")
    print("   4. Copie a URL correta e atualize o .env")
    sys.exit(1)

# 5. Verificar se psycopg2 está instalado
print("\n4. Verificando biblioteca psycopg2...")
try:
    import psycopg2
    print("   ✅ psycopg2 instalado")
except ImportError:
    print("   ❌ psycopg2 NAO esta instalado")
    print("\n   Solucao:")
    print("   Execute: pip install psycopg2-binary")
    sys.exit(1)

# 6. Tentar conectar
print("\n5. Tentando conectar ao banco de dados...")
try:
    # Ajusta URL se necessário
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    
    conn = psycopg2.connect(DATABASE_URL, connect_timeout=10)
    print("   ✅ CONEXAO ESTABELECIDA COM SUCESSO!")
    
    # Testa uma query
    cur = conn.cursor()
    cur.execute("SELECT version();")
    version = cur.fetchone()
    print(f"   ✅ Versao do PostgreSQL: {version[0][:50]}...")
    
    cur.close()
    conn.close()
    
    print("\n" + "=" * 60)
    print("SUCESSO: Tudo esta funcionando corretamente!")
    print("=" * 60)
    
except psycopg2.OperationalError as e:
    error_msg = str(e)
    print(f"   ❌ ERRO DE CONEXAO: {e}")
    
    if "could not translate host name" in error_msg.lower() or "name resolution" in error_msg.lower():
        print("\n   PROBLEMA: Nao foi possivel resolver o nome do servidor")
        print("\n   Solucoes:")
        print("   1. Verifique se o projeto Supabase esta ATIVO (nao pausado)")
        print("   2. Acesse https://supabase.com/dashboard e verifique o status")
        print("   3. Se estiver pausado, clique em 'Restore' ou 'Resume'")
        print("   4. Obtenha a URL correta em: Settings -> Database -> Connection string")
        print("   5. Verifique se o hostname esta correto (pode ser aws-0, aws-1, etc.)")
    elif "password authentication failed" in error_msg.lower():
        print("\n   PROBLEMA: Senha incorreta")
        print("\n   Solucao:")
        print("   1. Acesse https://supabase.com/dashboard")
        print("   2. Vá em Settings -> Database")
        print("   3. Copie a senha correta")
        print("   4. Atualize o arquivo .env com a senha correta")
    elif "connection refused" in error_msg.lower():
        print("\n   PROBLEMA: Conexao recusada")
        print("\n   Solucoes:")
        print("   1. Verifique se o projeto Supabase esta ativo")
        print("   2. Verifique se a porta esta correta (6543 para pooler, 5432 para direto)")
        print("   3. Verifique configuracoes de firewall/antivirus")
    else:
        print("\n   Consulte o arquivo SOLUCAO_CONEXAO.md para mais detalhes")
    
    sys.exit(1)
    
except Exception as e:
    print(f"   ❌ ERRO INESPERADO: {e}")
    print("\n   Consulte o arquivo SOLUCAO_CONEXAO.md para mais detalhes")
    sys.exit(1)

