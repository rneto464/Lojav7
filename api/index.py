"""
Handler da Vercel para a aplicação FastAPI
Este arquivo é o ponto de entrada para o servidor serverless da Vercel
"""
import sys
import os

# Adiciona o diretório raiz ao path para importar os módulos
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

# Muda o diretório de trabalho para a raiz do projeto
# Isso garante que os templates e outros arquivos sejam encontrados
if os.getcwd() != root_dir:
    os.chdir(root_dir)

# Importa a aplicação FastAPI
from main import app

# Exporta o app para a Vercel
# A Vercel detecta automaticamente aplicações ASGI/FastAPI quando o app é exportado diretamente
__all__ = ['app']
