"""
Handler da Vercel para a aplicação FastAPI
Este arquivo é o ponto de entrada para o servidor serverless da Vercel
"""
import sys
import os

# Adiciona o diretório raiz ao path para importar os módulos
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root_dir)

# Muda o diretório de trabalho para a raiz do projeto
# Isso garante que os templates e outros arquivos sejam encontrados
os.chdir(root_dir)

# Importa a aplicação FastAPI
from main import app

# Handler para a Vercel (ASGI)
handler = app

