from fastapi import FastAPI, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, select
from sqlalchemy.orm import joinedload
from schemas import ProdutoCreate, CorCreate, SupplierCreate, ProdutoUpdate, CorUpdate
from schemas import MovementCreate, ConfigUpdate, RepairPartCreate, RepairPartUpdate
from schemas import ServiceCreate, ServiceUpdate
from schemas import ServiceOrderCreate, ServiceOrderUpdate, ServiceOrderPartCreate, ServiceOrderServiceCreate
from schemas import PurchaseCreate, PurchaseUpdate, PurchaseItemCreate
from sqlalchemy import desc
import json
import os
from pydantic import BaseModel
from typing import Optional

# Importações dos arquivos que criamos acima
from database import engine, get_db, DATABASE_AVAILABLE
import models

# Cria as tabelas no banco automaticamente se não existirem
# Tenta criar as tabelas, mas não falha se não houver conexão
if DATABASE_AVAILABLE and engine:
    try:
        models.Base.metadata.create_all(bind=engine)
        print("[OK] Tabelas criadas/verificadas com sucesso")
    except Exception as e:
        error_msg = str(e)
        print("=" * 60)
        print("[AVISO] Nao foi possivel criar as tabelas no banco de dados")
        print("=" * 60)
        
        # Mensagens específicas para diferentes tipos de erro
        if "Tenant or user not found" in error_msg or "tenant or user not found" in error_msg.lower():
            print("ERRO ESPECIFICO: Projeto Supabase nao encontrado")
            print("\nPossiveis causas:")
            print("1. O projeto Supabase esta PAUSADO (projetos gratuitos pausam apos inatividade)")
            print("2. O projeto foi DELETADO ou MOVIDO")
            print("3. O ID do projeto na URL esta INCORRETO")
            print("\nSolucoes:")
            print("1. Acesse https://supabase.com/dashboard")
            print("2. Verifique se o projeto esta ATIVO (nao pausado)")
            print("3. Se estiver pausado, clique em 'Restore' ou 'Resume'")
            print("4. Obtenha a URL correta em: Settings -> Database -> Connection string")
            print("5. Atualize o arquivo .env com a nova URL")
        elif "password authentication failed" in error_msg.lower():
            print("ERRO: Autenticacao falhou")
            print("\nA senha no arquivo .env pode estar incorreta.")
            print("Verifique a senha no painel do Supabase e atualize o .env")
        elif "connection" in error_msg.lower() and "failed" in error_msg.lower():
            print("ERRO: Falha na conexao com o banco de dados")
            print("\nVerifique:")
            print("1. Sua conexao com a internet")
            print("2. Se o projeto Supabase esta ativo")
            print("3. Se a URL no .env esta correta")
        else:
            print(f"Detalhes do erro: {error_msg[:200]}")
        
        print("\nA aplicacao iniciara sem banco de dados (modo visualizacao).")
        print("O dashboard funcionara normalmente, mostrando valores zerados.")
        print("=" * 60)
        # Marca como não disponível para evitar tentativas futuras
        DATABASE_AVAILABLE = False
else:
    print("[AVISO] Banco de dados nao configurado. Aplicacao funcionara sem banco (modo visualizacao).")

app = FastAPI(title="Sistema de Gestão de Estoque")

templates = Jinja2Templates(directory="templates")

# Arquivo de configurações
CONFIG_FILE = "config.json"

# Funções para gerenciar configurações
def get_config():
    """Lê as configurações do arquivo JSON"""
    default_config = {
        "mensagem_fornecedor": "Olá! Preciso dos seguintes itens:\n\n{itens}\n\nAguardo seu retorno. Obrigado!",
        "mensagens_fornecedores": {}  # {fornecedor_id: mensagem}
    }
    
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # Garante que tem todos os campos necessários
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                # Garante que mensagens_fornecedores é um dict
                if not isinstance(config.get("mensagens_fornecedores"), dict):
                    config["mensagens_fornecedores"] = {}
                return config
        except Exception as e:
            print(f"[ERRO] Erro ao ler configurações: {e}")
            return default_config
    else:
        # Cria arquivo com configurações padrão
        save_config(default_config)
        return default_config

def get_mensagem_fornecedor(fornecedor_id=None):
    """Retorna a mensagem personalizada para um fornecedor específico ou a padrão"""
    config = get_config()
    if fornecedor_id and fornecedor_id in config.get("mensagens_fornecedores", {}):
        return config["mensagens_fornecedores"][str(fornecedor_id)]
    return config.get("mensagem_fornecedor", "Olá! Preciso dos seguintes itens:\n\n{itens}\n\nAguardo retorno. Obrigado!")

def save_config(config):
    """Salva as configurações no arquivo JSON"""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"[ERRO] Erro ao salvar configurações: {e}")
        return False

# Valores padrão quando não há banco de dados
def get_default_dashboard_data():
    return {
        "dados": {
            "total_skus": 0,
            "valor_estoque": "R$ 0,00",
            "alertas_criticos": 0,
            "lucro_potencial": "R$ 0,00",
            "margem_media": "0",
            "percentual_estoque": "0,0",
            "qtd_criticos": 0,
            "qtd_baixos": 0,
            "qtd_zerados": 0,
            "qtd_reposicao_urgente": 0,
            "qtd_produtos_parados": 0,
            "percentual_aumento_top5": 0
        },
        "produtos_criticos": [],
        "todos_produtos": [],
        "fornecedores": []
    }

def can_use_database(db):
    """Verifica se podemos usar o banco de dados"""
    if db is None:
        return False
    try:
        # Verifica se tem o atributo bind e se é válido
        if hasattr(db, 'bind') and db.bind is not None:
            # Verifica se é SQLite em memória (que não tem dados)
            if hasattr(db.bind, 'url') and 'sqlite:///:memory:' in str(db.bind.url):
                return False
        # Tenta uma query simples para verificar se o banco está funcionando
        from sqlalchemy import text
        result = db.execute(text("SELECT 1"))
        result.fetchone()
        return True
    except Exception:
        # Se houver qualquer erro, não podemos usar o banco
        return False

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    """
    Rota principal FUNCIONAL.
    Conecta ao PostgreSQL, calcula métricas reais e popula a tabela de alertas.
    """
    # Verifica se podemos usar o banco de dados
    if not can_use_database(db):
        return templates.TemplateResponse(
            request,
            "dashboard.html", 
            get_default_dashboard_data()
        )
    
    try:
        # ---------------------------------------------------------
        # 1. CÁLCULOS DOS CARTÕES (Métricas Gerais)
        # ---------------------------------------------------------

        # Total de SKUs (conta quantas linhas tem na tabela de variações)
        try:
            total_skus = db.query(models.ColorVariation).count()
        except Exception:
            total_skus = 0

        # Valor em Estoque (Soma: preço * quantidade de cada item)
        try:
            valor_total_query = db.query(
                func.sum(models.ColorVariation.variation_price * models.ColorVariation.available_stock)
            ).scalar()
            valor_estoque = float(valor_total_query) if valor_total_query else 0
        except Exception:
            valor_estoque = 0

        # Lucro Potencial - Calcula: (preço_venda - custo) * quantidade_estoque
        try:
            lucro_total_query = db.query(
                func.sum((models.ColorVariation.variation_price - models.ColorVariation.cost_price) * models.ColorVariation.available_stock)
            ).scalar()
            lucro_potencial = float(lucro_total_query) if lucro_total_query else 0
        except Exception:
            lucro_potencial = 0
        
        # Margem média percentual - Calcula a média das margens: ((preço - custo) / preço) * 100
        try:
            variacoes_com_preco = db.query(models.ColorVariation).filter(
                models.ColorVariation.variation_price > 0
            ).all()
            
            if variacoes_com_preco:
                margens = []
                for var in variacoes_com_preco:
                    preco = float(var.variation_price) if var.variation_price else 0
                    custo = float(var.cost_price) if var.cost_price else 0
                    if preco > 0:
                        margem = ((preco - custo) / preco) * 100
                        margens.append(margem)
                
                margem_media = sum(margens) / len(margens) if margens else 0
            else:
                margem_media = 0
        except Exception:
            margem_media = 0
        
        # Percentual em estoque (calcula quantos % dos SKUs têm estoque > 0)
        percentual_estoque = 0
        if total_skus > 0:
            try:
                skus_com_estoque = db.query(models.ColorVariation).filter(
                    models.ColorVariation.available_stock > 0
                ).count()
                percentual_estoque = (skus_com_estoque / total_skus) * 100
            except Exception:
                percentual_estoque = 0

        # Contagem de Críticos (Itens onde o estoque é menor ou igual ao mínimo configurado)
        try:
            qtd_criticos = db.query(models.ColorVariation).filter(
                models.ColorVariation.available_stock <= models.ColorVariation.min_stock_alert
            ).count()
        except Exception:
            qtd_criticos = 0

        # Contagem de Baixos (quase no mínimo - quando estoque = mínimo + 1)
        qtd_baixos = 0
        try:
            variacoes = db.query(models.ColorVariation).all()
            for var in variacoes:
                if var and var.min_stock_alert is not None and var.available_stock is not None:
                    if var.min_stock_alert > 0:
                        # Classifica como "Baixo" quando estoque = mínimo + 1
                        if var.available_stock == var.min_stock_alert + 1:
                            qtd_baixos += 1
        except Exception:
            qtd_baixos = 0
        
        # Contagem de Zerados
        try:
            qtd_zerados = db.query(models.ColorVariation).filter(
                models.ColorVariation.available_stock == 0
            ).count()
        except Exception:
            qtd_zerados = 0

        # Contagem de produtos que precisam de reposição urgente (críticos)
        qtd_reposicao_urgente = qtd_criticos
        
        # Produtos parados (sem movimentação há mais de 60 dias) - por enquanto 0
        qtd_produtos_parados = 0
        
        # Top 5 produtos - por enquanto 0% de aumento
        percentual_aumento_top5 = 0
    except Exception as e:
        # Se houver qualquer erro, usa valores padrão zero
        total_skus = 0
        valor_estoque = 0
        lucro_potencial = 0
        margem_media = 0
        percentual_estoque = 0
        qtd_criticos = 0
        qtd_baixos = 0
        qtd_zerados = 0
        qtd_reposicao_urgente = 0
        qtd_produtos_parados = 0
        percentual_aumento_top5 = 0
        print(f"[ERRO] Erro ao calcular métricas: {e}")

    # Formata valores monetários (garante que seja float)
    try:
        valor_estoque_float = float(valor_estoque) if valor_estoque else 0
    except (TypeError, ValueError):
        valor_estoque_float = 0
    
    try:
        lucro_potencial_float = float(lucro_potencial) if lucro_potencial else 0
    except (TypeError, ValueError):
        lucro_potencial_float = 0
    
    if valor_estoque_float == 0:
        valor_formatado = "R$ 0,00"
    elif valor_estoque_float >= 1000:
        valor_formatado = f"R$ {valor_estoque_float/1000:.1f}k".replace('.', ',')
    else:
        valor_formatado = f"R$ {valor_estoque_float:,.2f}".replace('.', ',')
    
    if lucro_potencial_float == 0:
        lucro_formatado = "R$ 0,00"
    elif lucro_potencial_float >= 1000:
        lucro_formatado = f"R$ {lucro_potencial_float/1000:.1f}k".replace('.', ',')
    else:
        lucro_formatado = f"R$ {lucro_potencial_float:,.2f}".replace('.', ',')

    # Monta o dicionário para os cartões do topo
    dados_cards = {
        "total_skus": total_skus,
        "valor_estoque": valor_formatado,
        "alertas_criticos": qtd_criticos,
        "lucro_potencial": lucro_formatado,
        "margem_media": f"{margem_media:.0f}" if margem_media > 0 else "0",
        "percentual_estoque": f"{percentual_estoque:.1f}" if percentual_estoque > 0 else "0,0",
        "qtd_criticos": qtd_criticos,
        "qtd_baixos": qtd_baixos,
        "qtd_zerados": qtd_zerados,
        "qtd_reposicao_urgente": qtd_reposicao_urgente,
        "qtd_produtos_parados": qtd_produtos_parados,
        "percentual_aumento_top5": percentual_aumento_top5
    }

    # ---------------------------------------------------------
    # 2. LISTA DA TABELA (Produtos Críticos)
    # ---------------------------------------------------------
    
    lista_criticos = []
    try:
        if db is None:
            raise Exception("Sessão de banco não disponível")
        
        # Busca no banco os produtos que estão com estoque crítico (<= mínimo) ou baixo (= mínimo + 1)
        # Faz um JOIN com a tabela Product para pegar o nome do produto (ex: "Capa Silicone")
        # Filtra apenas variações com estoque e mínimo definidos
        produtos_criticos_db = db.query(models.ColorVariation)\
            .join(models.Product)\
            .filter(
                models.ColorVariation.available_stock.isnot(None),
                models.ColorVariation.min_stock_alert.isnot(None),
                or_(
                    models.ColorVariation.available_stock <= models.ColorVariation.min_stock_alert,
                    models.ColorVariation.available_stock == models.ColorVariation.min_stock_alert + 1
                )
            ).all()

        # Transforma os dados do banco no formato que o HTML espera
        for item in produtos_criticos_db:
            if item and item.product:
                # Define o status visual
                estoque_atual = item.available_stock if item.available_stock is not None else 0
                minimo = item.min_stock_alert if item.min_stock_alert is not None else 0
                
                # Se estoque = mínimo + 1, classifica como "Baixo"
                if estoque_atual == minimo + 1:
                    status_texto = "Baixo"
                else:
                    status_texto = "Crítico"

                lista_criticos.append({
                    "sku": item.full_sku or "N/A",
                    "produto": item.product.name if item.product.name else "N/A",
                    "cor": item.color_name or "N/A",
                    "estoque": estoque_atual,
                    "minimo": minimo,
                    "status": status_texto
                })
    except Exception as e:
        print(f"[ERRO] Erro ao buscar produtos críticos: {e}")
        lista_criticos = []

    # ---------------------------------------------------------
    # 2.1. LISTA DE TODOS OS PRODUTOS (Para aparecer no dashboard)
    # ---------------------------------------------------------
    
    lista_todos_produtos = []
    try:
        if db is not None:
            # Busca todos os produtos com suas variações
            produtos_db = db.query(models.Product).options(
                joinedload(models.Product.variations)
            ).all()
            
            # Transforma os dados para o template
            for produto in produtos_db:
                if produto:
                    # Conta variações e calcula estoque total
                    total_variacoes = len(produto.variations) if produto.variations else 0
                    estoque_total = sum(
                        var.available_stock if var.available_stock is not None else 0 
                        for var in produto.variations
                    )
                    
                    # Pega o preço da primeira variação (ou 0)
                    preco_base = 0
                    if produto.variations and len(produto.variations) > 0:
                        preco_base = float(produto.variations[0].variation_price) if produto.variations[0].variation_price is not None else 0
                    
                    lista_todos_produtos.append({
                        "id": produto.id,
                        "nome": produto.name or "N/A",
                        "fabricante": produto.manufacturer or "Genérico",
                        "categoria": produto.category or "Capas",
                        "total_variacoes": total_variacoes,
                        "estoque_total": estoque_total,
                        "preco_base": preco_base
                    })
    except Exception as e:
        print(f"[ERRO] Erro ao buscar todos os produtos: {e}")
        lista_todos_produtos = []

    # ---------------------------------------------------------
    # 2.2. BUSCAR FORNECEDORES (Para o dropdown de solicitação)
    # ---------------------------------------------------------
    
    fornecedores = []
    try:
        if db is not None:
            fornecedores = db.query(models.Supplier).all()
    except Exception as e:
        print(f"[ERRO] Erro ao buscar fornecedores: {e}")
        fornecedores = []

    # ---------------------------------------------------------
    # 3. RENDERIZAÇÃO
    # ---------------------------------------------------------
    try:
        return templates.TemplateResponse(
            request,
            "dashboard.html", 
            {
                "dados": dados_cards,
                "produtos_criticos": lista_criticos,
                "todos_produtos": lista_todos_produtos,
                "fornecedores": fornecedores
            }
        )
    except Exception as e:
        print(f"[ERRO] Erro ao renderizar template: {e}")
        # Retorna uma resposta de erro simples
        from fastapi.responses import HTMLResponse
        return HTMLResponse(
            content=f"<h1>Erro no Dashboard</h1><p>Erro: {str(e)}</p>",
            status_code=500
        )

@app.get("/produtos", response_class=HTMLResponse)
async def produtos_page(request: Request, db: Session = Depends(get_db)):
    """
    Lista todos os produtos agrupados com suas variações.
    """
    # Verifica se podemos usar o banco de dados
    if not can_use_database(db):
        return templates.TemplateResponse(
            request,
            "products.html", 
            {
                "products": []
            }
        )
    
    try:
        # Busca produtos e já carrega as variações (cores) para evitar lentidão
        products = db.query(models.Product).options(
            joinedload(models.Product.variations)
        ).all()
    except Exception as e:
        print(f"[ERRO] Erro ao buscar produtos: {e}")
        products = []

    return templates.TemplateResponse(
        request,
        "products.html", 
        {
            "products": products
        }
    )

@app.get("/fornecedores", response_class=HTMLResponse)
async def fornecedores_page(request: Request, db: Session = Depends(get_db)):
    # Verifica se podemos usar o banco de dados
    if not can_use_database(db):
        return templates.TemplateResponse(
            request,
            "suppliers.html", 
            {"suppliers": [], "products": []}
        )
    
    try:
        suppliers = db.query(models.Supplier).options(
            joinedload(models.Supplier.products)
        ).all()
        products = db.query(models.Product).all()
    except Exception as e:
        print(f"[ERRO] Erro ao buscar fornecedores: {e}")
        suppliers = []
        products = []
    
    return templates.TemplateResponse(
        request,
        "suppliers.html", 
        {"suppliers": suppliers, "products": products}
    )

# --- API: LISTAR TODOS OS PRODUTOS (para seleção em movimentações) ---
@app.get("/api/produtos")
async def listar_produtos(db: Session = Depends(get_db)):
    """Retorna todos os produtos com suas variações de cor"""
    if not can_use_database(db):
        return JSONResponse(
            status_code=503,
            content={"message": "Banco de dados não disponível"}
        )
    
    try:
        products = db.query(models.Product).options(
            joinedload(models.Product.variations)
        ).all()
        
        produtos_data = []
        for produto in products:
            variacoes = []
            for var in produto.variations:
                variacoes.append({
                    "id": var.id,
                    "color_name": var.color_name,
                    "full_sku": var.full_sku,
                    "available_stock": var.available_stock if var.available_stock is not None else 0
                })
            
            produtos_data.append({
                "id": produto.id,
                "name": produto.name,
                "variations": variacoes
            })
        
        return {"products": produtos_data}
    except Exception as e:
        print(f"[ERRO] Erro ao listar produtos: {e}")
        return JSONResponse(
            status_code=500,
            content={"message": f"Erro ao listar produtos: {str(e)}"}
        )

# --- API: CRIAR PRODUTO ---
@app.post("/api/produtos")
async def criar_produto(produto: ProdutoCreate, db: Session = Depends(get_db)):
    if not can_use_database(db):
        return JSONResponse(
            status_code=503, 
            content={"message": "Banco de dados não disponível"}
        )
    
    try:
        # 1. Criar o produto
        novo_produto = models.Product(
            name=produto.name,
            manufacturer=produto.manufacturer or "Genérico",
            compatibility=produto.compatibility or "Universal",
            category=produto.category or "Capas"
        )
        
        db.add(novo_produto)
        db.flush()  # Para obter o ID do produto antes do commit
        
        # 2. Criar as variações de cor
        variacoes_criadas = []
        for cor in produto.colors:
            # Gerar SKU automaticamente se não fornecido
            if not cor.full_sku:
                # Formato: CAT-PROD-COR (ex: CAP-SIL-IP14-BLK)
                categoria_abrev = produto.category[:3].upper() if produto.category else "CAP"
                produto_abrev = produto.name[:3].upper() if len(produto.name) >= 3 else produto.name.upper()
                cor_abrev = cor.color_name[:3].upper() if len(cor.color_name) >= 3 else cor.color_name.upper()
                sku_gerado = f"{categoria_abrev}-{produto_abrev}-{cor_abrev}".replace(" ", "-")
                
                # Verificar se o SKU já existe e adicionar sufixo se necessário
                contador = 1
                sku_final = sku_gerado
                while db.query(models.ColorVariation).filter(models.ColorVariation.full_sku == sku_final).first():
                    sku_final = f"{sku_gerado}-{contador}"
                    contador += 1
            else:
                sku_final = cor.full_sku
            
            # Obter preço (prioriza variation_price, depois price)
            preco_final = cor.variation_price if cor.variation_price is not None else (cor.price or 0.0)
            # Obter custo (prioriza cost_price, depois cost)
            custo_final = cor.cost_price if cor.cost_price is not None else (cor.cost or 0.0)
            # Obter estoque (prioriza available_stock, depois stock)
            estoque_final = cor.available_stock if cor.available_stock is not None else (cor.stock or 0)
            
            nova_variacao = models.ColorVariation(
                product_id=novo_produto.id,
                color_name=cor.color_name,
                full_sku=sku_final,
                variation_price=preco_final,
                cost_price=custo_final,
                available_stock=estoque_final,
                min_stock_alert=cor.min_stock_alert
            )
            
            db.add(nova_variacao)
            db.flush()  # Para obter o ID antes do commit
            variacoes_criadas.append({
                "id": nova_variacao.id,
                "sku": sku_final,
                "color_name": cor.color_name
            })
        
        db.commit()
        db.refresh(novo_produto)
        
        return {
            "status": "sucesso", 
            "id": novo_produto.id,
            "variacoes": variacoes_criadas
        }
    except Exception as e:
        print(f"[ERRO] Erro ao criar produto: {e}")
        try:
            if db is not None:
                db.rollback()
        except:
            pass
        return JSONResponse(
            status_code=500, 
            content={"message": f"Erro ao criar produto: {str(e)}"}
        )

# --- API: CRIAR FORNECEDOR ---
@app.post("/api/fornecedores")
async def criar_fornecedor(supplier: SupplierCreate, db: Session = Depends(get_db)):
    if not can_use_database(db):
        return JSONResponse(
            status_code=503, 
            content={"message": "Banco de dados não disponível"}
        )
    
    try:
        novo_fornecedor = models.Supplier(
            name=supplier.name,
            email=supplier.email,
            phone=supplier.phone,
            contact_person=supplier.contact_person,
            observations=supplier.observations
        )
        
        db.add(novo_fornecedor)
        db.flush()  # Para obter o ID antes do commit
        
        # Adiciona os produtos que o fornecedor vende
        if supplier.product_ids:
            produtos = db.query(models.Product).filter(models.Product.id.in_(supplier.product_ids)).all()
            novo_fornecedor.products = produtos
        
        db.commit()
        db.refresh(novo_fornecedor)
        
        return {"status": "sucesso", "id": novo_fornecedor.id}
    except Exception as e:
        print(f"[ERRO] Erro ao criar fornecedor: {e}")
        try:
            if db is not None:
                db.rollback()
        except:
            pass
        return JSONResponse(
            status_code=500, 
            content={"message": f"Erro ao criar fornecedor: {str(e)}"}
        )

# --- API: OBTER PRODUTO ---
@app.get("/api/produtos/{produto_id}")
async def obter_produto(produto_id: int, db: Session = Depends(get_db)):
    """Retorna um produto específico com suas variações"""
    if not can_use_database(db):
        return JSONResponse(
            status_code=503, 
            content={"message": "Banco de dados não disponível"}
        )
    
    try:
        produto = db.query(models.Product).options(
            joinedload(models.Product.variations)
        ).filter(models.Product.id == produto_id).first()
        
        if not produto:
            return JSONResponse(
                status_code=404, 
                content={"message": "Produto não encontrado"}
            )
        
        # Formata os dados para retornar
        variacoes = []
        for var in produto.variations:
            variacoes.append({
                "id": var.id,
                "color_name": var.color_name,
                "full_sku": var.full_sku,
                "variation_price": float(var.variation_price) if var.variation_price else 0.0,
                "cost_price": float(var.cost_price) if var.cost_price else 0.0,
                "available_stock": var.available_stock if var.available_stock else 0,
                "min_stock_alert": var.min_stock_alert if var.min_stock_alert else 10
            })
        
        return {
            "id": produto.id,
            "name": produto.name,
            "manufacturer": produto.manufacturer,
            "compatibility": produto.compatibility,
            "category": produto.category,
            "variations": variacoes
        }
    except Exception as e:
        print(f"[ERRO] Erro ao buscar produto: {e}")
        return JSONResponse(
            status_code=500, 
            content={"message": f"Erro ao buscar produto: {str(e)}"}
        )

# --- API: ATUALIZAR PRODUTO ---
@app.put("/api/produtos/{produto_id}")
async def atualizar_produto(produto_id: int, produto: ProdutoUpdate, db: Session = Depends(get_db)):
    """Atualiza um produto existente e suas variações"""
    if not can_use_database(db):
        return JSONResponse(
            status_code=503, 
            content={"message": "Banco de dados não disponível"}
        )
    
    try:
        # Busca o produto
        produto_existente = db.query(models.Product).options(
            joinedload(models.Product.variations)
        ).filter(models.Product.id == produto_id).first()
        
        if not produto_existente:
            return JSONResponse(
                status_code=404, 
                content={"message": "Produto não encontrado"}
            )
        
        # Atualiza os dados do produto
        produto_existente.name = produto.name
        produto_existente.manufacturer = produto.manufacturer or "Genérico"
        produto_existente.compatibility = produto.compatibility or "Universal"
        produto_existente.category = produto.category or "Capas"
        
        # Mapeia variações existentes por ID
        variacoes_existentes = {var.id: var for var in produto_existente.variations}
        ids_recebidos = {cor.id for cor in produto.colors if cor.id is not None}
        
        # Remove variações que não foram enviadas
        for var_id, variacao in variacoes_existentes.items():
            if var_id not in ids_recebidos:
                db.delete(variacao)
        
        # Atualiza ou cria variações
        variacoes_atualizadas = []
        for cor in produto.colors:
            if cor.id and cor.id in variacoes_existentes:
                # Atualiza variação existente
                variacao = variacoes_existentes[cor.id]
                variacao.color_name = cor.color_name
                if cor.full_sku:
                    variacao.full_sku = cor.full_sku
                variacao.variation_price = cor.variation_price if cor.variation_price is not None else (cor.price or 0.0)
                variacao.cost_price = cor.cost_price if cor.cost_price is not None else (cor.cost or 0.0)
                variacao.available_stock = cor.available_stock if cor.available_stock is not None else (cor.stock or 0)
                variacao.min_stock_alert = cor.min_stock_alert
            else:
                # Cria nova variação
                # Gerar SKU automaticamente se não fornecido
                if not cor.full_sku:
                    categoria_abrev = produto.category[:3].upper() if produto.category else "CAP"
                    produto_abrev = produto.name[:3].upper() if len(produto.name) >= 3 else produto.name.upper()
                    cor_abrev = cor.color_name[:3].upper() if len(cor.color_name) >= 3 else cor.color_name.upper()
                    sku_gerado = f"{categoria_abrev}-{produto_abrev}-{cor_abrev}".replace(" ", "-")
                    
                    contador = 1
                    sku_final = sku_gerado
                    while db.query(models.ColorVariation).filter(models.ColorVariation.full_sku == sku_final).first():
                        sku_final = f"{sku_gerado}-{contador}"
                        contador += 1
                else:
                    sku_final = cor.full_sku
                
                nova_variacao = models.ColorVariation(
                    product_id=produto_id,
                    color_name=cor.color_name,
                    full_sku=sku_final,
                    variation_price=cor.variation_price if cor.variation_price is not None else (cor.price or 0.0),
                    cost_price=cor.cost_price if cor.cost_price is not None else (cor.cost or 0.0),
                    available_stock=cor.available_stock if cor.available_stock is not None else (cor.stock or 0),
                    min_stock_alert=cor.min_stock_alert
                )
                db.add(nova_variacao)
                variacoes_atualizadas.append({
                    "id": nova_variacao.id,
                    "sku": sku_final,
                    "color_name": cor.color_name
                })
        
        db.commit()
        db.refresh(produto_existente)
        
        return {
            "status": "sucesso", 
            "id": produto_existente.id,
            "message": "Produto atualizado com sucesso"
        }
    except Exception as e:
        print(f"[ERRO] Erro ao atualizar produto: {e}")
        try:
            if db is not None:
                db.rollback()
        except:
            pass
        return JSONResponse(
            status_code=500, 
            content={"message": f"Erro ao atualizar produto: {str(e)}"}
        )

# --- API: EXCLUIR PRODUTO ---
@app.delete("/api/produtos/{produto_id}")
async def excluir_produto(produto_id: int, db: Session = Depends(get_db)):
    if not can_use_database(db):
        return JSONResponse(
            status_code=503, 
            content={"message": "Banco de dados não disponível"}
        )
    
    try:
        # Busca o produto com suas variações carregadas
        produto = db.query(models.Product).options(
            joinedload(models.Product.variations)
        ).filter(models.Product.id == produto_id).first()
        
        if not produto:
            return JSONResponse(
                status_code=404, 
                content={"message": "Produto não encontrado"}
            )
        
        # Exclui manualmente as variações de cor primeiro
        # Isso evita problemas com o SQLAlchemy tentando atualizar product_id para None
        if produto.variations:
            for variacao in list(produto.variations):
                db.delete(variacao)
        
        # Agora exclui o produto
        db.delete(produto)
        db.commit()
        
        return {"status": "sucesso", "message": "Produto excluído com sucesso"}
    except Exception as e:
        print(f"[ERRO] Erro ao excluir produto: {e}")
        try:
            if db is not None:
                db.rollback()
        except:
            pass
        return JSONResponse(
            status_code=500, 
            content={"message": f"Erro ao excluir produto: {str(e)}"}
        )

# --- API: OBTER FORNECEDOR ---
@app.get("/api/fornecedores/{fornecedor_id}")
async def obter_fornecedor(fornecedor_id: int, db: Session = Depends(get_db)):
    """Retorna um fornecedor específico com seus produtos"""
    if not can_use_database(db):
        return JSONResponse(
            status_code=503, 
            content={"message": "Banco de dados não disponível"}
        )
    
    try:
        fornecedor = db.query(models.Supplier).options(
            joinedload(models.Supplier.products)
        ).filter(models.Supplier.id == fornecedor_id).first()
        
        if not fornecedor:
            return JSONResponse(
                status_code=404, 
                content={"message": "Fornecedor não encontrado"}
            )
        
        # Formata os dados para retornar
        produtos = []
        for produto in fornecedor.products:
            produtos.append({
                "id": produto.id,
                "name": produto.name
            })
        
        return {
            "id": fornecedor.id,
            "name": fornecedor.name,
            "email": fornecedor.email or "",
            "phone": fornecedor.phone or "",
            "contact_person": fornecedor.contact_person or "",
            "observations": fornecedor.observations or "",
            "product_ids": [p["id"] for p in produtos]
        }
    except Exception as e:
        print(f"[ERRO] Erro ao buscar fornecedor: {e}")
        return JSONResponse(
            status_code=500, 
            content={"message": f"Erro ao buscar fornecedor: {str(e)}"}
        )

# --- API: ATUALIZAR FORNECEDOR ---
@app.put("/api/fornecedores/{fornecedor_id}")
async def atualizar_fornecedor(fornecedor_id: int, supplier: SupplierCreate, db: Session = Depends(get_db)):
    """Atualiza um fornecedor existente"""
    if not can_use_database(db):
        return JSONResponse(
            status_code=503, 
            content={"message": "Banco de dados não disponível"}
        )
    
    try:
        # Busca o fornecedor
        fornecedor = db.query(models.Supplier).options(
            joinedload(models.Supplier.products)
        ).filter(models.Supplier.id == fornecedor_id).first()
        
        if not fornecedor:
            return JSONResponse(
                status_code=404, 
                content={"message": "Fornecedor não encontrado"}
            )
        
        # Atualiza os dados do fornecedor
        fornecedor.name = supplier.name
        fornecedor.email = supplier.email
        fornecedor.phone = supplier.phone
        fornecedor.contact_person = supplier.contact_person
        fornecedor.observations = supplier.observations
        
        # Atualiza os produtos que o fornecedor vende
        if supplier.product_ids:
            produtos = db.query(models.Product).filter(models.Product.id.in_(supplier.product_ids)).all()
            fornecedor.products = produtos
        else:
            fornecedor.products = []
        
        db.commit()
        db.refresh(fornecedor)
        
        return {"status": "sucesso", "message": "Fornecedor atualizado com sucesso"}
    except Exception as e:
        print(f"[ERRO] Erro ao atualizar fornecedor: {e}")
        try:
            if db is not None:
                db.rollback()
        except:
            pass
        return JSONResponse(
            status_code=500, 
            content={"message": f"Erro ao atualizar fornecedor: {str(e)}"}
        )

# --- API: EXCLUIR FORNECEDOR ---
@app.delete("/api/fornecedores/{fornecedor_id}")
async def excluir_fornecedor(fornecedor_id: int, db: Session = Depends(get_db)):
    if not can_use_database(db):
        return JSONResponse(
            status_code=503, 
            content={"message": "Banco de dados não disponível"}
        )
    
    try:
        # Busca o fornecedor
        fornecedor = db.query(models.Supplier).filter(models.Supplier.id == fornecedor_id).first()
        
        if not fornecedor:
            return JSONResponse(
                status_code=404, 
                content={"message": "Fornecedor não encontrado"}
            )
        
        # Exclui o fornecedor
        db.delete(fornecedor)
        db.commit()
        
        return {"status": "sucesso", "message": "Fornecedor excluído com sucesso"}
    except Exception as e:
        print(f"[ERRO] Erro ao excluir fornecedor: {e}")
        try:
            if db is not None:
                db.rollback()
        except:
            pass
        return JSONResponse(
            status_code=500, 
            content={"message": f"Erro ao excluir fornecedor: {str(e)}"}
        )

@app.get("/movimentacoes", response_class=HTMLResponse)
async def movimentacoes_page(request: Request, db: Session = Depends(get_db)):
    # Verifica se podemos usar o banco de dados
    if not can_use_database(db):
        return templates.TemplateResponse(
            request,
            "movements.html", 
            {"movements": []}
        )
    
    try:
        # Busca todas as movimentações, da mais recente para a mais antiga
        # Carrega junto os dados da Variação e do Produto (join) para mostrar o nome na tela
        movements = db.query(models.StockMovement)\
            .join(models.ColorVariation)\
            .join(models.Product)\
            .order_by(desc(models.StockMovement.created_at))\
            .all()
    except Exception as e:
        print(f"[ERRO] Erro ao buscar movimentações: {e}")
        movements = []
        
    return templates.TemplateResponse(
        request,
        "movements.html", 
        {"movements": movements}
    )

# --- API: CRIAR MOVIMENTAÇÃO (O "Coração" do Estoque) ---
@app.post("/api/movimentacoes")
async def criar_movimentacao(mov: MovementCreate, db: Session = Depends(get_db)):
    if not can_use_database(db):
        return JSONResponse(
            status_code=503, 
            content={"message": "Banco de dados não disponível"}
        )
    
    try:
        # Valida quantidade
        if mov.quantity <= 0:
            return JSONResponse(
                status_code=400,
                content={"message": "Quantidade deve ser maior que zero"}
            )
        
        # Valida tipo de movimentação
        if mov.movement_type not in ['entrada', 'saida', 'ajuste']:
            return JSONResponse(
                status_code=400,
                content={"message": "Tipo de movimentação inválido. Use: 'entrada', 'saida' ou 'ajuste'"}
            )
        
        # 1. Encontrar a variação pelo SKU
        variacao = db.query(models.ColorVariation).filter(models.ColorVariation.full_sku == mov.sku).first()
        
        if not variacao:
            return JSONResponse(status_code=404, content={"message": "SKU não encontrado"})

        # 2. Calcular novo estoque
        estoque_anterior = variacao.available_stock if variacao.available_stock is not None else 0
        novo_estoque = estoque_anterior

        if mov.movement_type == 'entrada':
            novo_estoque += mov.quantity
        elif mov.movement_type == 'saida':
            if estoque_anterior < mov.quantity:
                 return JSONResponse(status_code=400, content={"message": "Estoque insuficiente"})
            novo_estoque -= mov.quantity
        elif mov.movement_type == 'ajuste':
            # No ajuste, assumimos que a quantidade informada é a DIFERENÇA (para cima ou baixo)
            # Se quiser definir o valor FINAL, a lógica seria diferente. 
            # Vamos seguir a lógica da imagem: Ajuste de -2 (Perda/Quebra)
            # Tratamos 'ajuste' como SAÍDA (quebra/perda) - subtrai a quantidade
            if estoque_anterior < mov.quantity:
                return JSONResponse(status_code=400, content={"message": "Estoque insuficiente para ajuste"})
            novo_estoque -= mov.quantity

        # 3. Atualizar a tabela de Variações (Saldo Atual)
        variacao.available_stock = novo_estoque
        
        # 4. Gravar o Histórico
        historico = models.StockMovement(
            variation_id=variacao.id,
            movement_type=mov.movement_type,
            quantity=mov.quantity,
            previous_stock=estoque_anterior,
            new_stock=novo_estoque,
            reason=mov.reason
        )
        
        db.add(historico)
        db.commit()
        
        return {"status": "sucesso", "novo_estoque": novo_estoque}
    except Exception as e:
        print(f"[ERRO] Erro ao criar movimentação: {e}")
        try:
            if db is not None:
                db.rollback()
        except:
            pass
        return JSONResponse(
            status_code=500, 
            content={"message": f"Erro ao criar movimentação: {str(e)}"}
        )

# --- PÁGINA DE CONFIGURAÇÕES ---
@app.get("/configuracoes", response_class=HTMLResponse)
async def configuracoes_page(request: Request, db: Session = Depends(get_db)):
    """Página de configurações do sistema"""
    config = get_config()
    
    # Busca todos os fornecedores
    suppliers = []
    if can_use_database(db):
        try:
            suppliers = db.query(models.Supplier).all()
        except Exception as e:
            print(f"[ERRO] Erro ao buscar fornecedores: {e}")
            suppliers = []
    
    return templates.TemplateResponse(
        request,
        "configuracoes.html",
        {
            "config": config,
            "suppliers": suppliers
        }
    )

# --- API: OBTER CONFIGURAÇÕES ---
@app.get("/api/configuracoes")
async def obter_configuracoes():
    """Retorna as configurações atuais"""
    config = get_config()
    return config

# --- API: ATUALIZAR CONFIGURAÇÕES ---
@app.post("/api/configuracoes")
async def atualizar_configuracoes(config_update: ConfigUpdate):
    """Atualiza as configurações do sistema"""
    try:
        config = get_config()
        config["mensagem_fornecedor"] = config_update.mensagem_fornecedor
        
        if config_update.mensagens_fornecedores:
            config["mensagens_fornecedores"] = config_update.mensagens_fornecedores
        
        if save_config(config):
            return {"status": "sucesso", "message": "Configurações atualizadas com sucesso"}
        else:
            return JSONResponse(
                status_code=500,
                content={"message": "Erro ao salvar configurações"}
            )
    except Exception as e:
        print(f"[ERRO] Erro ao atualizar configurações: {e}")
        return JSONResponse(
            status_code=500,
            content={"message": f"Erro ao atualizar configurações: {str(e)}"}
        )

# =========================================
# ÁREA DE PEÇAS
# =========================================

# --- PÁGINA DE PEÇAS E SERVIÇOS ---
@app.get("/reparos", response_class=HTMLResponse)
async def reparos_page(request: Request, db: Session = Depends(get_db)):
    """Página de gerenciamento de peças físicas e serviços"""
    if not can_use_database(db):
        return templates.TemplateResponse(
            request,
            "reparos.html",
            {
                "pecas": [],
                "servicos": [],
                "pecas_disponiveis": []
            }
        )
    
    try:
        # Busca todas as peças físicas (sem subcategoria, todas são peças)
        pecas = db.query(models.RepairPart).order_by(desc(models.RepairPart.created_at)).all()
        
        # Busca todos os serviços (mão de obra)
        servicos = db.query(models.Service).order_by(desc(models.Service.created_at)).all()
        
        # Busca peças disponíveis para formulários
        pecas_disponiveis = db.query(models.RepairPart).filter(
            models.RepairPart.status == "available"
        ).all()
    except Exception as e:
        print(f"[ERRO] Erro ao buscar peças e serviços: {e}")
        pecas = []
        servicos = []
        pecas_disponiveis = []
    
    return templates.TemplateResponse(
        request=request,
        name="reparos.html",
        context={
            "pecas": pecas,
            "servicos": servicos,
            "pecas_disponiveis": pecas_disponiveis
        }
    )

# --- API: LISTAR PEÇAS FÍSICAS ---
@app.get("/api/reparos")
async def listar_pecas(db: Session = Depends(get_db)):
    """Lista todas as peças físicas (catálogo de peças)"""
    if not can_use_database(db):
        return JSONResponse(
            status_code=503,
            content={"message": "Banco de dados não disponível"}
        )
    
    try:
        pecas = db.query(models.RepairPart).all()
        return [
            {
                "id": p.id,
                "device_model": p.device_model,
                "part_name": p.part_name if hasattr(p, 'part_name') else (p.replaced_part if hasattr(p, 'replaced_part') else ""),
                "price": float(p.price) if p.price else 0.0,
                "cost_price": float(p.cost_price) if p.cost_price else 0.0,
                "available_stock": p.available_stock or 0,
                "min_stock_alert": p.min_stock_alert or 5,
                "status": p.status
            }
            for p in pecas
        ]
    except Exception as e:
        print(f"[ERRO] Erro ao listar peças: {e}")
        return JSONResponse(
            status_code=500,
            content={"message": f"Erro ao listar peças: {str(e)}"}
        )

# --- API: LISTAR SERVIÇOS (MÃO DE OBRA) ---
@app.get("/api/servicos")
async def listar_servicos(status: Optional[str] = None, db: Session = Depends(get_db)):
    """Lista todos os serviços (mão de obra)"""
    if not can_use_database(db):
        return JSONResponse(
            status_code=503,
            content={"message": "Banco de dados não disponível"}
        )
    
    try:
        query = db.query(models.Service)
        if status:
            query = query.filter(models.Service.status == status)
        
        servicos = query.all()
        return [
            {
                "id": s.id,
                "name": s.name,
                "description": s.description,
                "price": float(s.price) if s.price else 0.0,
                "estimated_time": s.estimated_time,
                "status": s.status
            }
            for s in servicos
        ]
    except Exception as e:
        print(f"[ERRO] Erro ao listar serviços: {e}")
        return JSONResponse(
            status_code=500,
            content={"message": f"Erro ao listar serviços: {str(e)}"}
        )

# --- API: CRIAR PEÇA DE REPARO ---
@app.post("/api/reparos")
async def criar_reparo(peca: RepairPartCreate, db: Session = Depends(get_db)):
    """Cria uma nova peça de reparo"""
    if not can_use_database(db):
        return JSONResponse(
            status_code=503,
            content={"message": "Banco de dados não disponível"}
        )
    
    try:
        # Usa data personalizada se fornecida, senão usa data atual
        data_cadastro = peca.created_at if peca.created_at else datetime.datetime.utcnow()
        
        nova_peca = models.RepairPart(
            device_model=peca.device_model,
            part_name=peca.part_name,
            price=peca.price,
            cost_price=peca.cost_price or 0,
            available_stock=peca.available_stock or 0,
            min_stock_alert=peca.min_stock_alert or 5,
            created_at=data_cadastro
        )
        
        db.add(nova_peca)
        db.commit()
        db.refresh(nova_peca)
        
        return {
            "status": "sucesso",
            "message": "Peça de reparo cadastrada com sucesso",
            "id": nova_peca.id
        }
    except Exception as e:
        try:
            if db is not None:
                db.rollback()
        except:
            pass
        print(f"[ERRO] Erro ao criar peça de reparo: {e}")
        return JSONResponse(
            status_code=500,
            content={"message": f"Erro ao criar peça: {str(e)}"}
        )

# --- API: ATUALIZAR PEÇA DE REPARO ---
@app.put("/api/reparos/{peca_id}")
async def atualizar_reparo(peca_id: int, peca: RepairPartUpdate, db: Session = Depends(get_db)):
    """Atualiza uma peça de reparo existente"""
    if not can_use_database(db):
        return JSONResponse(
            status_code=503,
            content={"message": "Banco de dados não disponível"}
        )
    
    try:
        peca_db = db.query(models.RepairPart).filter(models.RepairPart.id == peca_id).first()
        if not peca_db:
            return JSONResponse(
                status_code=404,
                content={"message": "Peça não encontrada"}
            )
        
        if peca.device_model is not None:
            peca_db.device_model = peca.device_model
        if peca.part_name is not None:
            peca_db.part_name = peca.part_name
        if peca.price is not None:
            peca_db.price = peca.price
        if peca.cost_price is not None:
            peca_db.cost_price = peca.cost_price
        if peca.available_stock is not None:
            peca_db.available_stock = peca.available_stock
        if peca.min_stock_alert is not None:
            peca_db.min_stock_alert = peca.min_stock_alert
        if peca.status is not None:
            peca_db.status = peca.status
        
        db.commit()
        
        return {"status": "sucesso", "message": "Peça atualizada com sucesso"}
    except Exception as e:
        try:
            if db is not None:
                db.rollback()
        except:
            pass
        print(f"[ERRO] Erro ao atualizar peça de reparo: {e}")
        return JSONResponse(
            status_code=500,
            content={"message": f"Erro ao atualizar peça: {str(e)}"}
        )

# --- API: EXCLUIR PEÇA DE REPARO ---
@app.delete("/api/reparos/{peca_id}")
async def excluir_reparo(peca_id: int, db: Session = Depends(get_db)):
    """Exclui uma peça de reparo"""
    if not can_use_database(db):
        return JSONResponse(
            status_code=503,
            content={"message": "Banco de dados não disponível"}
        )
    
    try:
        peca = db.query(models.RepairPart).filter(models.RepairPart.id == peca_id).first()
        if not peca:
            return JSONResponse(
                status_code=404,
                content={"message": "Peça não encontrada"}
            )
        
        db.delete(peca)
        db.commit()
        
        return {"status": "sucesso", "message": "Peça excluída com sucesso"}
    except Exception as e:
        try:
            if db is not None:
                db.rollback()
        except:
            pass
        print(f"[ERRO] Erro ao excluir peça de reparo: {e}")
        return JSONResponse(
            status_code=500,
            content={"message": f"Erro ao excluir peça: {str(e)}"}
        )

# =========================================
# ROTAS PARA SERVIÇOS (MÃO DE OBRA)
# =========================================

# --- API: CRIAR SERVIÇO ---
@app.post("/api/servicos")
async def criar_servico(servico: ServiceCreate, db: Session = Depends(get_db)):
    """Cria um novo serviço (mão de obra)"""
    if not can_use_database(db):
        return JSONResponse(
            status_code=503,
            content={"message": "Banco de dados não disponível"}
        )
    
    try:
        # Usa data personalizada se fornecida, senão usa data atual
        data_cadastro = servico.created_at if servico.created_at else datetime.datetime.utcnow()
        
        novo_servico = models.Service(
            name=servico.name,
            description=servico.description,
            price=servico.price,
            estimated_time=servico.estimated_time,
            status=servico.status or "active",
            created_at=data_cadastro
        )
        
        db.add(novo_servico)
        db.commit()
        db.refresh(novo_servico)
        
        return {
            "status": "sucesso",
            "message": "Serviço cadastrado com sucesso",
            "id": novo_servico.id
        }
    except Exception as e:
        try:
            if db is not None:
                db.rollback()
        except:
            pass
        print(f"[ERRO] Erro ao criar serviço: {e}")
        return JSONResponse(
            status_code=500,
            content={"message": f"Erro ao criar serviço: {str(e)}"}
        )

# --- API: ATUALIZAR SERVIÇO ---
@app.put("/api/servicos/{servico_id}")
async def atualizar_servico(servico_id: int, servico: ServiceUpdate, db: Session = Depends(get_db)):
    """Atualiza um serviço existente"""
    if not can_use_database(db):
        return JSONResponse(
            status_code=503,
            content={"message": "Banco de dados não disponível"}
        )
    
    try:
        servico_db = db.query(models.Service).filter(models.Service.id == servico_id).first()
        if not servico_db:
            return JSONResponse(
                status_code=404,
                content={"message": "Serviço não encontrado"}
            )
        
        if servico.name is not None:
            servico_db.name = servico.name
        if servico.description is not None:
            servico_db.description = servico.description
        if servico.price is not None:
            servico_db.price = servico.price
        if servico.estimated_time is not None:
            servico_db.estimated_time = servico.estimated_time
        if servico.status is not None:
            servico_db.status = servico.status
        
        db.commit()
        
        return {"status": "sucesso", "message": "Serviço atualizado com sucesso"}
    except Exception as e:
        try:
            if db is not None:
                db.rollback()
        except:
            pass
        print(f"[ERRO] Erro ao atualizar serviço: {e}")
        return JSONResponse(
            status_code=500,
            content={"message": f"Erro ao atualizar serviço: {str(e)}"}
        )

# --- API: EXCLUIR SERVIÇO ---
@app.delete("/api/servicos/{servico_id}")
async def excluir_servico(servico_id: int, db: Session = Depends(get_db)):
    """Exclui um serviço"""
    if not can_use_database(db):
        return JSONResponse(
            status_code=503,
            content={"message": "Banco de dados não disponível"}
        )
    
    try:
        servico = db.query(models.Service).filter(models.Service.id == servico_id).first()
        if not servico:
            return JSONResponse(
                status_code=404,
                content={"message": "Serviço não encontrado"}
            )
        
        db.delete(servico)
        db.commit()
        
        return {"status": "sucesso", "message": "Serviço excluído com sucesso"}
    except Exception as e:
        try:
            if db is not None:
                db.rollback()
        except:
            pass
        print(f"[ERRO] Erro ao excluir serviço: {e}")
        return JSONResponse(
            status_code=500,
            content={"message": f"Erro ao excluir serviço: {str(e)}"}
        )

# --- API: OBTER MENSAGEM DE FORNECEDOR ---
@app.get("/api/configuracoes/fornecedor/{fornecedor_id}")
async def obter_mensagem_fornecedor(fornecedor_id: int):
    """Retorna a mensagem personalizada para um fornecedor específico"""
    mensagem = get_mensagem_fornecedor(fornecedor_id)
    return {"mensagem": mensagem}

# =========================================
# ORDENS DE SERVIÇO
# =========================================

def gerar_numero_ordem(db: Session) -> str:
    """Gera um número único de ordem de serviço no formato OS-YYYY-NNN"""
    from datetime import datetime
    ano_atual = datetime.now().year
    
    # Busca a última ordem do ano atual
    ultima_ordem = db.query(models.ServiceOrder).filter(
        models.ServiceOrder.order_number.like(f"OS-{ano_atual}-%")
    ).order_by(desc(models.ServiceOrder.id)).first()
    
    if ultima_ordem and ultima_ordem.order_number:
        # Extrai o número sequencial
        try:
            numero = int(ultima_ordem.order_number.split('-')[-1])
            proximo_numero = numero + 1
        except:
            proximo_numero = 1
    else:
        proximo_numero = 1
    
    return f"OS-{ano_atual}-{proximo_numero:03d}"

@app.get("/ordens-servico", response_class=HTMLResponse)
async def ordens_servico_page(request: Request, db: Session = Depends(get_db)):
    """Página de gerenciamento de ordens de serviço"""
    if not can_use_database(db):
        return templates.TemplateResponse(
            request,
            "ordens_servico.html",
            {
                "ordens": [],
                "pecas": []
            }
        )
    
    try:
        # Busca todas as ordens de serviço
        ordens = db.query(models.ServiceOrder).order_by(desc(models.ServiceOrder.created_at)).all()
        
        # Busca todas as peças de reparo para o formulário
        pecas = db.query(models.RepairPart).filter(
            models.RepairPart.status == "available"
        ).all()
    except Exception as e:
        print(f"[ERRO] Erro ao buscar ordens de serviço: {e}")
        ordens = []
        pecas = []
    
    return templates.TemplateResponse(
        request,
        "ordens_servico.html",
        {
            "ordens": ordens,
            "pecas": pecas
        }
    )

# --- API: LISTAR ORDENS DE SERVIÇO ---
@app.get("/api/ordens-servico")
async def listar_ordens_servico(status: Optional[str] = None, db: Session = Depends(get_db)):
    """Lista todas as ordens de serviço, opcionalmente filtradas por status"""
    if not can_use_database(db):
        return JSONResponse(
            status_code=503,
            content={"message": "Banco de dados não disponível"}
        )
    
    try:
        query = db.query(models.ServiceOrder).options(
            joinedload(models.ServiceOrder.parts),
            joinedload(models.ServiceOrder.services)
        )
        if status:
            query = query.filter(models.ServiceOrder.status == status)
        
        ordens = query.order_by(desc(models.ServiceOrder.created_at)).all()
        
        resultado = []
        for ordem in ordens:
            # Busca quantidades das peças da tabela de associação
            from sqlalchemy import select
            quantidades_pecas = {}
            for part in ordem.parts:
                stmt = select(models.service_order_parts.c.quantity).where(
                    models.service_order_parts.c.service_order_id == ordem.id,
                    models.service_order_parts.c.repair_part_id == part.id
                )
                result = db.execute(stmt).first()
                quantidades_pecas[part.id] = result[0] if result else 1
            
            # Busca quantidades dos serviços da tabela de associação
            quantidades_servicos = {}
            for servico in ordem.services:
                stmt = select(models.service_order_services.c.quantity).where(
                    models.service_order_services.c.service_order_id == ordem.id,
                    models.service_order_services.c.service_id == servico.id
                )
                result = db.execute(stmt).first()
                quantidades_servicos[servico.id] = result[0] if result else 1
            
            # Calcula o valor total das peças
            valor_pecas = sum(
                float(part.price) * quantidades_pecas.get(part.id, 1)
                for part in ordem.parts
            )
            # Calcula o valor total dos serviços
            valor_servicos = sum(
                float(servico.price) * quantidades_servicos.get(servico.id, 1)
                for servico in ordem.services
            )
            total = valor_pecas + valor_servicos
            
            resultado.append({
                "id": ordem.id,
                "order_number": ordem.order_number,
                "client_name": ordem.client_name,
                "client_phone": ordem.client_phone,
                "client_email": ordem.client_email,
                "device_model": ordem.device_model,
                "service_description": ordem.service_description,
                "status": ordem.status,
                "total_value": float(ordem.total_value) if ordem.total_value else total,
                "notes": ordem.notes,
                "created_at": ordem.created_at.isoformat() if ordem.created_at else None,
                "completed_at": ordem.completed_at.isoformat() if ordem.completed_at else None,
                "parts": [
                    {
                        "id": part.id,
                        "device_model": part.device_model,
                        "part_name": part.part_name if hasattr(part, 'part_name') else (part.replaced_part if hasattr(part, 'replaced_part') else "N/A"),
                        "price": float(part.price) if part.price else 0.0,
                        "quantity": quantidades_pecas.get(part.id, 1)
                    }
                    for part in ordem.parts
                ],
                "services": [
                    {
                        "id": servico.id,
                        "name": servico.name,
                        "description": servico.description,
                        "price": float(servico.price) if servico.price else 0.0,
                        "quantity": quantidades_servicos.get(servico.id, 1)
                    }
                    for servico in ordem.services
                ]
            })
        
        return resultado
    except Exception as e:
        print(f"[ERRO] Erro ao listar ordens de serviço: {e}")
        return JSONResponse(
            status_code=500,
            content={"message": f"Erro ao listar ordens: {str(e)}"}
        )

# --- API: OBTER ORDEM DE SERVIÇO ESPECÍFICA ---
@app.get("/api/ordens-servico/{ordem_id}")
async def obter_ordem_servico(ordem_id: int, db: Session = Depends(get_db)):
    """Obtém uma ordem de serviço específica"""
    if not can_use_database(db):
        return JSONResponse(
            status_code=503,
            content={"message": "Banco de dados não disponível"}
        )
    
    try:
        ordem = db.query(models.ServiceOrder).options(
            joinedload(models.ServiceOrder.parts),
            joinedload(models.ServiceOrder.services)
        ).filter(
            models.ServiceOrder.id == ordem_id
        ).first()
        
        if not ordem:
            return JSONResponse(
                status_code=404,
                content={"message": "Ordem de serviço não encontrada"}
            )
        
        # Busca quantidades das peças da tabela de associação
        from sqlalchemy import select
        quantidades_pecas = {}
        for part in ordem.parts:
            stmt = select(models.service_order_parts.c.quantity).where(
                models.service_order_parts.c.service_order_id == ordem.id,
                models.service_order_parts.c.repair_part_id == part.id
            )
            result = db.execute(stmt).first()
            quantidades_pecas[part.id] = result[0] if result else 1
        
        # Busca quantidades dos serviços da tabela de associação
        quantidades_servicos = {}
        for servico in ordem.services:
            stmt = select(models.service_order_services.c.quantity).where(
                models.service_order_services.c.service_order_id == ordem.id,
                models.service_order_services.c.service_id == servico.id
            )
            result = db.execute(stmt).first()
            quantidades_servicos[servico.id] = result[0] if result else 1
        
        valor_pecas = sum(
            float(part.price) * quantidades_pecas.get(part.id, 1)
            for part in ordem.parts
        )
        valor_servicos = sum(
            float(servico.price) * quantidades_servicos.get(servico.id, 1)
            for servico in ordem.services
        )
        total = valor_pecas + valor_servicos
        
        return {
            "id": ordem.id,
            "order_number": ordem.order_number,
            "client_name": ordem.client_name,
            "client_phone": ordem.client_phone,
            "client_email": ordem.client_email,
            "device_model": ordem.device_model,
            "service_description": ordem.service_description,
            "status": ordem.status,
            "total_value": float(ordem.total_value) if ordem.total_value else total,
            "notes": ordem.notes,
            "created_at": ordem.created_at.isoformat() if ordem.created_at else None,
            "completed_at": ordem.completed_at.isoformat() if ordem.completed_at else None,
            "parts": [
                {
                    "id": part.id,
                    "device_model": part.device_model,
                    "part_name": part.part_name if hasattr(part, 'part_name') else (part.replaced_part if hasattr(part, 'replaced_part') else "N/A"),
                    "price": float(part.price) if part.price else 0.0,
                    "quantity": quantidades_pecas.get(part.id, 1)
                }
                for part in ordem.parts
            ],
            "services": [
                {
                    "id": servico.id,
                    "name": servico.name,
                    "description": servico.description,
                    "price": float(servico.price) if servico.price else 0.0,
                    "quantity": quantidades_servicos.get(servico.id, 1)
                }
                for servico in ordem.services
            ]
        }
    except Exception as e:
        print(f"[ERRO] Erro ao obter ordem de serviço: {e}")
        return JSONResponse(
            status_code=500,
            content={"message": f"Erro ao obter ordem: {str(e)}"}
        )

# --- API: CRIAR ORDEM DE SERVIÇO ---
@app.post("/api/ordens-servico")
async def criar_ordem_servico(ordem: ServiceOrderCreate, db: Session = Depends(get_db)):
    """Cria uma nova ordem de serviço"""
    if not can_use_database(db):
        return JSONResponse(
            status_code=503,
            content={"message": "Banco de dados não disponível"}
        )
    
    try:
        # Valida peças se fornecidas
        if ordem.parts:
            for part_data in ordem.parts:
                if part_data.quantity <= 0:
                    return JSONResponse(
                        status_code=400,
                        content={"message": f"Quantidade deve ser maior que zero para a peça {part_data.repair_part_id}"}
                    )
                # Verifica se a peça existe e está disponível
                peca = db.query(models.RepairPart).filter(models.RepairPart.id == part_data.repair_part_id).first()
                if not peca:
                    return JSONResponse(
                        status_code=404,
                        content={"message": f"Peça com ID {part_data.repair_part_id} não encontrada"}
                    )
                if peca.status != "available":
                    part_name = peca.part_name if hasattr(peca, 'part_name') else (peca.replaced_part if hasattr(peca, 'replaced_part') else "N/A")
                    return JSONResponse(
                        status_code=400,
                        content={"message": f"Peça {peca.device_model} - {part_name} não está disponível"}
                    )
                # Verifica estoque
                estoque_disponivel = peca.available_stock or 0
                if estoque_disponivel < part_data.quantity:
                    part_name = peca.part_name if hasattr(peca, 'part_name') else (peca.replaced_part if hasattr(peca, 'replaced_part') else "N/A")
                    return JSONResponse(
                        status_code=400,
                        content={"message": f"Estoque insuficiente para a peça {peca.device_model} - {part_name}. Disponível: {estoque_disponivel}, Solicitado: {part_data.quantity}"}
                    )
        
        # Valida serviços se fornecidos
        if ordem.services:
            for service_data in ordem.services:
                if service_data.quantity <= 0:
                    return JSONResponse(
                        status_code=400,
                        content={"message": f"Quantidade deve ser maior que zero para o serviço {service_data.service_id}"}
                    )
                # Verifica se o serviço existe e está ativo
                servico = db.query(models.Service).filter(models.Service.id == service_data.service_id).first()
                if not servico:
                    return JSONResponse(
                        status_code=404,
                        content={"message": f"Serviço com ID {service_data.service_id} não encontrado"}
                    )
                if servico.status != "active":
                    return JSONResponse(
                        status_code=400,
                        content={"message": f"Serviço {servico.name} não está ativo"}
                    )
        
        # Gera número da ordem
        numero_ordem = gerar_numero_ordem(db)
        
        # Calcula valor total das peças
        valor_pecas = 0.0
        for part_data in ordem.parts:
            peca = db.query(models.RepairPart).filter(models.RepairPart.id == part_data.repair_part_id).first()
            if peca:
                valor_pecas += float(peca.price) * part_data.quantity
        
        # Calcula valor total dos serviços
        valor_servicos = 0.0
        for service_data in ordem.services:
            servico = db.query(models.Service).filter(models.Service.id == service_data.service_id).first()
            if servico:
                valor_servicos += float(servico.price) * service_data.quantity
        
        total = valor_pecas + valor_servicos
        
        # Usa data personalizada se fornecida, senão usa data atual
        import datetime
        data_criacao = ordem.created_at if ordem.created_at else datetime.datetime.utcnow()
        
        # Cria a ordem
        nova_ordem = models.ServiceOrder(
            order_number=numero_ordem,
            client_name=ordem.client_name,
            client_phone=ordem.client_phone,
            client_email=ordem.client_email,
            device_model=ordem.device_model,
            service_description=ordem.service_description,
            status="em_andamento",
            total_value=total,
            notes=ordem.notes,
            created_at=data_criacao,
            completed_at=ordem.completed_at if ordem.completed_at else None
        )
        
        db.add(nova_ordem)
        db.flush()  # Para obter o ID da ordem
        
        # Adiciona as peças
        for part_data in ordem.parts:
            peca = db.query(models.RepairPart).filter(models.RepairPart.id == part_data.repair_part_id).first()
            if peca:
                # Adiciona relacionamento usando a tabela de associação
                stmt = models.service_order_parts.insert().values(
                    service_order_id=nova_ordem.id,
                    repair_part_id=peca.id,
                    quantity=part_data.quantity
                )
                db.execute(stmt)
                
                # Atualiza estoque (reduz a quantidade)
                peca.available_stock = (peca.available_stock or 0) - part_data.quantity
                if peca.available_stock < 0:
                    peca.available_stock = 0
        
        # Adiciona os serviços
        for service_data in ordem.services:
            servico = db.query(models.Service).filter(models.Service.id == service_data.service_id).first()
            if servico:
                # Adiciona relacionamento usando a tabela de associação
                stmt = models.service_order_services.insert().values(
                    service_order_id=nova_ordem.id,
                    service_id=servico.id,
                    quantity=service_data.quantity
                )
                db.execute(stmt)
        
        db.commit()
        db.refresh(nova_ordem)
        
        return {
            "status": "sucesso",
            "message": "Ordem de serviço criada com sucesso",
            "id": nova_ordem.id,
            "order_number": nova_ordem.order_number
        }
    except Exception as e:
        try:
            if db is not None:
                db.rollback()
        except:
            pass
        print(f"[ERRO] Erro ao criar ordem de serviço: {e}")
        return JSONResponse(
            status_code=500,
            content={"message": f"Erro ao criar ordem: {str(e)}"}
        )

# --- API: ATUALIZAR ORDEM DE SERVIÇO ---
@app.put("/api/ordens-servico/{ordem_id}")
async def atualizar_ordem_servico(ordem_id: int, ordem: ServiceOrderUpdate, db: Session = Depends(get_db)):
    """Atualiza uma ordem de serviço existente"""
    if not can_use_database(db):
        return JSONResponse(
            status_code=503,
            content={"message": "Banco de dados não disponível"}
        )
    
    try:
        ordem_db = db.query(models.ServiceOrder).filter(models.ServiceOrder.id == ordem_id).first()
        if not ordem_db:
            return JSONResponse(
                status_code=404,
                content={"message": "Ordem de serviço não encontrada"}
            )
        
        # Atualiza campos básicos
        if ordem.client_name is not None:
            ordem_db.client_name = ordem.client_name
        if ordem.client_phone is not None:
            ordem_db.client_phone = ordem.client_phone
        if ordem.client_email is not None:
            ordem_db.client_email = ordem.client_email
        if ordem.device_model is not None:
            ordem_db.device_model = ordem.device_model
        if ordem.service_description is not None:
            ordem_db.service_description = ordem.service_description
        if ordem.status is not None:
            ordem_db.status = ordem.status
            if ordem.status == "concluido" and not ordem_db.completed_at:
                from datetime import datetime
                ordem_db.completed_at = datetime.utcnow()
        if ordem.notes is not None:
            ordem_db.notes = ordem.notes
        
        # Atualiza peças se fornecidas
        valor_pecas = 0.0
        if ordem.parts is not None:
            # Valida peças antes de atualizar
            for part_data in ordem.parts:
                if part_data.quantity <= 0:
                    return JSONResponse(
                        status_code=400,
                        content={"message": f"Quantidade deve ser maior que zero para a peça {part_data.repair_part_id}"}
                    )
                # Verifica se a peça existe
                peca = db.query(models.RepairPart).filter(models.RepairPart.id == part_data.repair_part_id).first()
                if not peca:
                    return JSONResponse(
                        status_code=404,
                        content={"message": f"Peça com ID {part_data.repair_part_id} não encontrada"}
                    )
            
            # Remove relacionamentos antigos de peças
            db.execute(
                models.service_order_parts.delete().where(
                    models.service_order_parts.c.service_order_id == ordem_id
                )
            )
            
            # Adiciona novos relacionamentos de peças
            for part_data in ordem.parts:
                peca = db.query(models.RepairPart).filter(models.RepairPart.id == part_data.repair_part_id).first()
                if peca:
                    stmt = models.service_order_parts.insert().values(
                        service_order_id=ordem_id,
                        repair_part_id=peca.id,
                        quantity=part_data.quantity
                    )
                    db.execute(stmt)
                    valor_pecas += float(peca.price) * part_data.quantity
        
        # Atualiza serviços se fornecidos
        valor_servicos = 0.0
        if ordem.services is not None:
            # Valida serviços antes de atualizar
            for service_data in ordem.services:
                if service_data.quantity <= 0:
                    return JSONResponse(
                        status_code=400,
                        content={"message": f"Quantidade deve ser maior que zero para o serviço {service_data.service_id}"}
                    )
                # Verifica se o serviço existe
                servico = db.query(models.Service).filter(models.Service.id == service_data.service_id).first()
                if not servico:
                    return JSONResponse(
                        status_code=404,
                        content={"message": f"Serviço com ID {service_data.service_id} não encontrado"}
                    )
            
            # Remove relacionamentos antigos de serviços
            db.execute(
                models.service_order_services.delete().where(
                    models.service_order_services.c.service_order_id == ordem_id
                )
            )
            
            # Adiciona novos relacionamentos de serviços
            for service_data in ordem.services:
                servico = db.query(models.Service).filter(models.Service.id == service_data.service_id).first()
                if servico:
                    stmt = models.service_order_services.insert().values(
                        service_order_id=ordem_id,
                        service_id=servico.id,
                        quantity=service_data.quantity
                    )
                    db.execute(stmt)
                    valor_servicos += float(servico.price) * service_data.quantity
        
        # Atualiza valor total (só se peças ou serviços foram atualizados)
        if ordem.parts is not None or ordem.services is not None:
            # Se apenas um foi atualizado, busca o outro do banco
            if ordem.parts is None:
                # Busca peças existentes
                for part in ordem_db.parts:
                    stmt = select(models.service_order_parts.c.quantity).where(
                        models.service_order_parts.c.service_order_id == ordem_id,
                        models.service_order_parts.c.repair_part_id == part.id
                    )
                    result = db.execute(stmt).first()
                    qty = result[0] if result else 1
                    valor_pecas += float(part.price) * qty
            
            if ordem.services is None:
                # Busca serviços existentes
                for servico in ordem_db.services:
                    stmt = select(models.service_order_services.c.quantity).where(
                        models.service_order_services.c.service_order_id == ordem_id,
                        models.service_order_services.c.service_id == servico.id
                    )
                    result = db.execute(stmt).first()
                    qty = result[0] if result else 1
                    valor_servicos += float(servico.price) * qty
            
            ordem_db.total_value = valor_pecas + valor_servicos
        
        db.commit()
        
        return {"status": "sucesso", "message": "Ordem de serviço atualizada com sucesso"}
    except Exception as e:
        try:
            if db is not None:
                db.rollback()
        except:
            pass
        print(f"[ERRO] Erro ao atualizar ordem de serviço: {e}")
        return JSONResponse(
            status_code=500,
            content={"message": f"Erro ao atualizar ordem: {str(e)}"}
        )

# --- API: EXCLUIR ORDEM DE SERVIÇO ---
@app.delete("/api/ordens-servico/{ordem_id}")
async def excluir_ordem_servico(ordem_id: int, db: Session = Depends(get_db)):
    """Exclui uma ordem de serviço"""
    if not can_use_database(db):
        return JSONResponse(
            status_code=503,
            content={"message": "Banco de dados não disponível"}
        )
    
    try:
        ordem = db.query(models.ServiceOrder).filter(models.ServiceOrder.id == ordem_id).first()
        if not ordem:
            return JSONResponse(
                status_code=404,
                content={"message": "Ordem de serviço não encontrada"}
            )
        
        db.delete(ordem)
        db.commit()
        
        return {"status": "sucesso", "message": "Ordem de serviço excluída com sucesso"}
    except Exception as e:
        try:
            if db is not None:
                db.rollback()
        except:
            pass
        print(f"[ERRO] Erro ao excluir ordem de serviço: {e}")
        return JSONResponse(
            status_code=500,
            content={"message": f"Erro ao excluir ordem: {str(e)}"}
        )

# =========================================
# ROTAS PARA FINANÇAS - COMPRAS DE PEÇAS
# =========================================

def gerar_numero_compra(db: Session) -> str:
    """Gera um número único de compra no formato COMP-YYYY-NNN"""
    from datetime import datetime
    ano_atual = datetime.now().year
    
    # Busca a última compra do ano atual
    ultima_compra = db.query(models.Purchase).filter(
        models.Purchase.purchase_number.like(f"COMP-{ano_atual}-%")
    ).order_by(desc(models.Purchase.id)).first()
    
    if ultima_compra and ultima_compra.purchase_number:
        # Extrai o número sequencial
        try:
            numero = int(ultima_compra.purchase_number.split('-')[-1])
            proximo_numero = numero + 1
        except:
            proximo_numero = 1
    else:
        proximo_numero = 1
    
    return f"COMP-{ano_atual}-{proximo_numero:03d}"

@app.get("/financas", response_class=HTMLResponse)
async def financas_page(request: Request, db: Session = Depends(get_db)):
    """Página de finanças - compras e lucros"""
    if not can_use_database(db):
        return templates.TemplateResponse(
            request,
            "financas.html",
            {"purchases": [], "service_orders": [], "error": "Banco de dados não disponível"}
        )
    
    try:
        # Busca todas as compras
        purchases = db.query(models.Purchase).order_by(desc(models.Purchase.created_at)).all()
        
        # Busca apenas ordens de serviço concluídas para calcular lucros
        service_orders = db.query(models.ServiceOrder).options(
            joinedload(models.ServiceOrder.parts),
            joinedload(models.ServiceOrder.services)
        ).filter(models.ServiceOrder.status == "concluido").order_by(desc(models.ServiceOrder.created_at)).all()
        
        # Prepara dados das compras
        purchases_data = []
        for purchase in purchases:
            items_data = []
            for item in purchase.items:
                items_data.append({
                    "id": item.id,
                    "repair_part": {
                        "id": item.repair_part.id if item.repair_part else None,
                        "device_model": item.repair_part.device_model if item.repair_part else "N/A",
                        "part_name": item.repair_part.part_name if item.repair_part and hasattr(item.repair_part, 'part_name') else (item.repair_part.replaced_part if item.repair_part and hasattr(item.repair_part, 'replaced_part') else "N/A")
                    },
                    "quantity": item.quantity,
                    "unit_cost": float(item.unit_cost) if item.unit_cost else 0.0,
                    "total_cost": float(item.total_cost) if item.total_cost else 0.0
                })
            
            purchases_data.append({
                "id": purchase.id,
                "purchase_number": purchase.purchase_number,
                "supplier_name": purchase.supplier_name,
                "shipping_cost": float(purchase.shipping_cost) if purchase.shipping_cost else 0.0,
                "total_value": float(purchase.total_value) if purchase.total_value else 0.0,
                "notes": purchase.notes,
                "created_at": purchase.created_at.isoformat() if purchase.created_at else None,
                "items": items_data
            })
        
        # Calcula totais de compras para cálculo de frete proporcional
        total_frete_compras = sum(float(p.shipping_cost or 0) for p in purchases)
        total_custo_pecas_compras = 0.0
        for purchase in purchases:
            for item in purchase.items:
                total_custo_pecas_compras += float(item.total_cost or 0)
        
        # Prepara dados das ordens de serviço com cálculo de lucro
        orders_data = []
        for order in service_orders:
            # Busca quantidades das peças
            quantidades = {}
            for part in order.parts:
                stmt = select(models.service_order_parts.c.quantity).where(
                    models.service_order_parts.c.service_order_id == order.id,
                    models.service_order_parts.c.repair_part_id == part.id
                )
                result = db.execute(stmt).first()
                quantidades[part.id] = result[0] if result else 1
            
            # Calcula custo total das peças (usando cost_price)
            # Se cost_price não estiver definido, usa uma estimativa baseada no preço (assumindo 50% de margem)
            custo_pecas = 0.0
            pecas_sem_custo = []
            for part in order.parts:
                quantidade = quantidades.get(part.id, 1)
                if part.cost_price and part.cost_price > 0:
                    custo_pecas += float(part.cost_price) * quantidade
                else:
                    # Se não tem cost_price, estima como 50% do preço (margem padrão)
                    custo_estimado = float(part.price or 0) * 0.5
                    custo_pecas += custo_estimado * quantidade
                    part_name = part.part_name if hasattr(part, 'part_name') else (part.replaced_part if hasattr(part, 'replaced_part') else "N/A")
                    pecas_sem_custo.append({
                        "id": part.id,
                        "nome": f"{part.device_model} - {part_name}",
                        "preco": float(part.price or 0)
                    })
            
            # Calcula frete proporcional baseado no custo das peças
            # Distribui o frete proporcionalmente ao custo das peças usadas
            if total_custo_pecas_compras > 0 and custo_pecas > 0:
                frete_proporcional = (custo_pecas / total_custo_pecas_compras) * total_frete_compras
            else:
                frete_proporcional = 0.0
            
            # Busca quantidades dos serviços
            quantidades_servicos = {}
            for servico in order.services:
                stmt = select(models.service_order_services.c.quantity).where(
                    models.service_order_services.c.service_order_id == order.id,
                    models.service_order_services.c.service_id == servico.id
                )
                result = db.execute(stmt).first()
                quantidades_servicos[servico.id] = result[0] if result else 1
            
            # Calcula custo dos serviços (serviços não têm custo de compra, apenas preço de venda)
            # O custo de serviços seria o tempo/homem, mas como não temos isso, consideramos 0
            # Ou seja, o lucro dos serviços é 100% (ou você pode ajustar isso depois)
            custo_servicos = 0.0  # Serviços não têm custo de compra, apenas mão de obra (que não rastreamos)
            
            # Calcula lucro
            receita = float(order.total_value) if order.total_value else 0.0
            custo_total = custo_pecas + frete_proporcional + custo_servicos
            lucro = receita - custo_total
            margem_lucro = (lucro / receita * 100) if receita > 0 else 0
            
            orders_data.append({
                "id": order.id,
                "order_number": order.order_number,
                "client_name": order.client_name,
                "device_model": order.device_model,
                "service_description": order.service_description,
                "status": order.status,
                "total_value": receita,
                "custo_pecas": custo_pecas,
                "custo_servicos": custo_servicos,
                "frete_proporcional": frete_proporcional,
                "custo_total": custo_total,
                "lucro": lucro,
                "margem_lucro": margem_lucro,
                "pecas_sem_custo": pecas_sem_custo,  # Lista de peças que não têm cost_price definido
                "services": [
                    {
                        "id": servico.id,
                        "name": servico.name,
                        "price": float(servico.price) if servico.price else 0.0,
                        "quantity": quantidades_servicos.get(servico.id, 1)
                    }
                    for servico in order.services
                ],
                "created_at": order.created_at.isoformat() if order.created_at else None,
                "completed_at": order.completed_at.isoformat() if order.completed_at else None
            })
        
        return templates.TemplateResponse(
            request,
            "financas.html",
            {
                "purchases": purchases_data,
                "service_orders": orders_data
            }
        )
    except Exception as e:
        print(f"[ERRO] Erro ao carregar página de finanças: {e}")
        return templates.TemplateResponse(
            request,
            "financas.html",
            {"purchases": [], "service_orders": [], "error": str(e)}
        )

# --- API: LISTAR COMPRAS ---
@app.get("/api/compras")
async def listar_compras(db: Session = Depends(get_db)):
    """Lista todas as compras"""
    if not can_use_database(db):
        return JSONResponse(
            status_code=503,
            content={"message": "Banco de dados não disponível"}
        )
    
    try:
        purchases = db.query(models.Purchase).options(
            joinedload(models.Purchase.items).joinedload(models.PurchaseItem.repair_part)
        ).order_by(desc(models.Purchase.created_at)).all()
        
        resultado = []
        for purchase in purchases:
            items_data = []
            for item in purchase.items:
                items_data.append({
                    "id": item.id,
                    "repair_part_id": item.repair_part_id,
                    "repair_part": {
                        "id": item.repair_part.id if item.repair_part else None,
                        "device_model": item.repair_part.device_model if item.repair_part else "N/A",
                        "part_name": item.repair_part.part_name if item.repair_part and hasattr(item.repair_part, 'part_name') else (item.repair_part.replaced_part if item.repair_part and hasattr(item.repair_part, 'replaced_part') else "N/A")
                    },
                    "quantity": item.quantity,
                    "unit_cost": float(item.unit_cost) if item.unit_cost else 0.0,
                    "total_cost": float(item.total_cost) if item.total_cost else 0.0
                })
            
            resultado.append({
                "id": purchase.id,
                "purchase_number": purchase.purchase_number,
                "supplier_name": purchase.supplier_name,
                "shipping_cost": float(purchase.shipping_cost) if purchase.shipping_cost else 0.0,
                "total_value": float(purchase.total_value) if purchase.total_value else 0.0,
                "notes": purchase.notes,
                "created_at": purchase.created_at.isoformat() if purchase.created_at else None,
                "items": items_data
            })
        
        return resultado
    except Exception as e:
        print(f"[ERRO] Erro ao listar compras: {e}")
        return JSONResponse(
            status_code=500,
            content={"message": f"Erro ao listar compras: {str(e)}"}
        )

# --- API: CRIAR COMPRA ---
@app.post("/api/compras")
async def criar_compra(compra: PurchaseCreate, db: Session = Depends(get_db)):
    """Cria uma nova compra de peças"""
    if not can_use_database(db):
        return JSONResponse(
            status_code=503,
            content={"message": "Banco de dados não disponível"}
        )
    
    try:
        # Valida se há itens na compra
        if not compra.items or len(compra.items) == 0:
            return JSONResponse(
                status_code=400,
                content={"message": "A compra deve ter pelo menos um item"}
            )
        
        # Valida dados dos itens
        for item_data in compra.items:
            if item_data.quantity <= 0:
                return JSONResponse(
                    status_code=400,
                    content={"message": f"Quantidade deve ser maior que zero para o item {item_data.repair_part_id}"}
                )
            if item_data.unit_cost < 0:
                return JSONResponse(
                    status_code=400,
                    content={"message": f"Custo unitário não pode ser negativo para o item {item_data.repair_part_id}"}
                )
            # Verifica se a peça existe
            peca = db.query(models.RepairPart).filter(models.RepairPart.id == item_data.repair_part_id).first()
            if not peca:
                return JSONResponse(
                    status_code=404,
                    content={"message": f"Peça com ID {item_data.repair_part_id} não encontrada"}
                )
        
        # Valida frete
        if compra.shipping_cost and compra.shipping_cost < 0:
            return JSONResponse(
                status_code=400,
                content={"message": "Frete não pode ser negativo"}
            )
        
        # Gera número da compra
        numero_compra = gerar_numero_compra(db)
        
        # Calcula valor total das peças
        valor_pecas = sum(item.unit_cost * item.quantity for item in compra.items)
        total = valor_pecas + (compra.shipping_cost or 0)
        
        # Usa data personalizada se fornecida, senão usa data atual
        data_compra = compra.created_at if compra.created_at else datetime.datetime.utcnow()
        
        # Cria a compra
        nova_compra = models.Purchase(
            purchase_number=numero_compra,
            supplier_name=compra.supplier_name,
            shipping_cost=compra.shipping_cost or 0,
            total_value=total,
            notes=compra.notes,
            created_at=data_compra
        )
        
        db.add(nova_compra)
        db.flush()  # Para obter o ID da compra
        
        # Adiciona os itens da compra
        for item_data in compra.items:
            peca = db.query(models.RepairPart).filter(models.RepairPart.id == item_data.repair_part_id).first()
            if peca:
                # Atualiza o cost_price da peça com o novo custo unitário
                peca.cost_price = item_data.unit_cost
                
                # Adiciona ao estoque
                peca.available_stock = (peca.available_stock or 0) + item_data.quantity
                
                # Cria o item da compra
                item_compra = models.PurchaseItem(
                    purchase_id=nova_compra.id,
                    repair_part_id=item_data.repair_part_id,
                    quantity=item_data.quantity,
                    unit_cost=item_data.unit_cost,
                    total_cost=item_data.unit_cost * item_data.quantity
                )
                db.add(item_compra)
        
        db.commit()
        db.refresh(nova_compra)
        
        return {
            "status": "sucesso",
            "message": "Compra registrada com sucesso",
            "id": nova_compra.id,
            "purchase_number": nova_compra.purchase_number
        }
    except Exception as e:
        try:
            if db is not None:
                db.rollback()
        except:
            pass
        print(f"[ERRO] Erro ao criar compra: {e}")
        return JSONResponse(
            status_code=500,
            content={"message": f"Erro ao criar compra: {str(e)}"}
        )

# --- API: ATUALIZAR CUSTO DE PEÇA ---
@app.put("/api/reparos/{peca_id}/custo")
async def atualizar_custo_peca(peca_id: int, request: Request, db: Session = Depends(get_db)):
    """Atualiza o custo de uma peça via JSON body"""
    if not can_use_database(db):
        return JSONResponse(
            status_code=503,
            content={"message": "Banco de dados não disponível"}
        )
    
    try:
        body = await request.json()
        cost_price = body.get("cost_price")
        
        if cost_price is None:
            return JSONResponse(
                status_code=400,
                content={"message": "Campo cost_price é obrigatório no body"}
            )
        
        cost_price = float(cost_price)
        
        if cost_price < 0:
            return JSONResponse(
                status_code=400,
                content={"message": "Custo não pode ser negativo"}
            )
        
        peca = db.query(models.RepairPart).filter(models.RepairPart.id == peca_id).first()
        if not peca:
            return JSONResponse(
                status_code=404,
                content={"message": "Peça não encontrada"}
            )
        
        peca.cost_price = cost_price
        db.commit()
        db.refresh(peca)
        
        return {
            "status": "sucesso",
            "message": "Custo da peça atualizado com sucesso",
            "id": peca.id,
            "cost_price": float(peca.cost_price)
        }
    except Exception as e:
        try:
            if db is not None:
                db.rollback()
        except:
            pass
        print(f"[ERRO] Erro ao atualizar custo da peça: {e}")
        return JSONResponse(
            status_code=500,
            content={"message": f"Erro ao atualizar custo: {str(e)}"}
        )

# --- API: OBTER COMPRA ---
@app.get("/api/compras/{compra_id}")
async def obter_compra(compra_id: int, db: Session = Depends(get_db)):
    """Obtém uma compra específica"""
    if not can_use_database(db):
        return JSONResponse(
            status_code=503,
            content={"message": "Banco de dados não disponível"}
        )
    
    try:
        compra = db.query(models.Purchase).options(
            joinedload(models.Purchase.items).joinedload(models.PurchaseItem.repair_part)
        ).filter(models.Purchase.id == compra_id).first()
        
        if not compra:
            return JSONResponse(
                status_code=404,
                content={"message": "Compra não encontrada"}
            )
        
        items_data = []
        for item in compra.items:
            items_data.append({
                "id": item.id,
                "repair_part_id": item.repair_part_id,
                "repair_part": {
                    "id": item.repair_part.id if item.repair_part else None,
                    "device_model": item.repair_part.device_model if item.repair_part else "N/A",
                    "replaced_part": item.repair_part.replaced_part if item.repair_part else "N/A"
                },
                "quantity": item.quantity,
                "unit_cost": float(item.unit_cost) if item.unit_cost else 0.0,
                "total_cost": float(item.total_cost) if item.total_cost else 0.0
            })
        
        return {
            "id": compra.id,
            "purchase_number": compra.purchase_number,
            "supplier_name": compra.supplier_name,
            "shipping_cost": float(compra.shipping_cost) if compra.shipping_cost else 0.0,
            "total_value": float(compra.total_value) if compra.total_value else 0.0,
            "notes": compra.notes,
            "created_at": compra.created_at.isoformat() if compra.created_at else None,
            "items": items_data
        }
    except Exception as e:
        print(f"[ERRO] Erro ao obter compra: {e}")
        return JSONResponse(
            status_code=500,
            content={"message": f"Erro ao obter compra: {str(e)}"}
        )