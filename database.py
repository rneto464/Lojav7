import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

# 1. Carrega as variáveis do arquivo .env
load_dotenv()

# 2. Pega a URL de conexão. Se não achar, usa placeholder.
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

# Verifica se é uma URL placeholder ou inválida
is_placeholder = False
DATABASE_AVAILABLE = False

if not SQLALCHEMY_DATABASE_URL:
    print("=" * 60)
    print("AVISO: A variavel DATABASE_URL nao foi encontrada no arquivo .env")
    print("=" * 60)
    print("Para usar o banco de dados, crie um arquivo .env na raiz do projeto com:")
    print("   DATABASE_URL=postgresql://usuario:senha@host:porta/banco")
    print("\nExemplo para Supabase:")
    print("   DATABASE_URL=postgresql://postgres.xxxxx:SENHA@aws-0-sa-east-1.pooler.supabase.com:6543/postgres")
    print("\nA aplicacao iniciara sem banco de dados (modo de visualizacao).")
    print("=" * 60)
    is_placeholder = True
elif "usuario:senha" in SQLALCHEMY_DATABASE_URL or "nome_do_banco" in SQLALCHEMY_DATABASE_URL:
    print("=" * 60)
    print("AVISO: DATABASE_URL parece ser um placeholder invalido.")
    print("=" * 60)
    print("Configure a URL correta no arquivo .env.")
    print("A URL atual contem valores de exemplo que precisam ser substituidos.")
    print("\nExemplo valido para Supabase:")
    print("   DATABASE_URL=postgresql://postgres.xxxxx:SUA_SENHA@aws-0-sa-east-1.pooler.supabase.com:6543/postgres")
    print("\nA aplicacao iniciara sem banco de dados (modo de visualizacao).")
    print("=" * 60)
    is_placeholder = True

# Ajuste específico para Supabase/Postgres se a string começar com "postgres://"
# O SQLAlchemy prefere "postgresql://"
if SQLALCHEMY_DATABASE_URL and not is_placeholder and SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql://", 1)

# 3. Cria o motor de conexão apenas se não for placeholder
if is_placeholder:
    # Não cria engine se for placeholder - a aplicação funcionará sem banco
    engine = None
    DATABASE_AVAILABLE = False
else:
    # Tenta criar o motor de conexão
    try:
        engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True)
        DATABASE_AVAILABLE = True
        print("[OK] Engine do banco de dados criado com sucesso!")
    except Exception as e:
        error_msg = str(e)
        print("=" * 60)
        print(f"ERRO: Nao foi possivel criar o engine do banco: {e}")
        print("=" * 60)
        
        # Mensagens específicas para diferentes tipos de erro
        if "could not translate host name" in error_msg.lower() or "name resolution" in error_msg.lower():
            print("ERRO ESPECIFICO: Nao foi possivel resolver o nome do servidor")
            print("\nPossiveis causas:")
            print("1. Problema de conexao com a internet")
            print("2. Hostname incorreto na DATABASE_URL")
            print("3. Projeto Supabase pausado ou inativo")
            print("4. Problemas de DNS")
            print("\nSolucoes:")
            print("1. Verifique sua conexao com a internet")
            print("2. Acesse https://supabase.com/dashboard e verifique se o projeto esta ATIVO")
            print("3. Se o projeto estiver pausado, clique em 'Restore' ou 'Resume'")
            print("4. Obtenha a URL correta em: Settings -> Database -> Connection string")
            print("5. Verifique se o hostname esta correto (pode ser aws-0, aws-1, etc.)")
            print("6. Execute: python testar_conexao.py para diagnosticar o problema")
        elif "password authentication failed" in error_msg.lower():
            print("ERRO: Autenticacao falhou")
            print("\nA senha no arquivo .env pode estar incorreta.")
            print("Verifique a senha no painel do Supabase e atualize o .env")
        elif "connection" in error_msg.lower() and "refused" in error_msg.lower():
            print("ERRO: Conexao recusada")
            print("\nPossiveis causas:")
            print("1. Projeto Supabase pausado")
            print("2. Porta incorreta na URL")
            print("3. Firewall bloqueando a conexao")
            print("\nSolucoes:")
            print("1. Verifique se o projeto Supabase esta ativo")
            print("2. Use a porta correta (6543 para pooler, 5432 para direto)")
            print("3. Verifique configuracoes de firewall/antivirus")
        else:
            print("Verifique se a DATABASE_URL no arquivo .env esta correta.")
            print("Consulte o arquivo SOLUCAO_CONEXAO.md para mais detalhes.")
        
        print("\nA aplicacao iniciara sem banco de dados (modo de visualizacao).")
        print("O dashboard funcionara normalmente, mostrando valores zerados.")
        print("=" * 60)
        engine = None
        DATABASE_AVAILABLE = False

# Cria SessionLocal apenas se o engine estiver disponível
if engine:
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
else:
    SessionLocal = None

Base = declarative_base()

# Dependência para injetar o banco nas rotas
def get_db():
    if not DATABASE_AVAILABLE or SessionLocal is None:
        yield None
        return
    
    db = None
    try:
        db = SessionLocal()
        yield db
    except Exception as e:
        print(f"[ERRO] Erro ao criar sessao do banco: {e}")
        yield None
    finally:
        if db:
            try:
                db.close()
            except:
                pass