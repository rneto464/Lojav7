from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# =========================================
# 1. MODELOS PARA A IA / PROCESSAMENTO DE TEXTO
# (Usados na rota /categorizar-modelos)
# =========================================

class ListaModelosInput(BaseModel):
    texto_bruto: str  # Ex: "apple | sansung j | ..."

# =========================================
# 2. SCHEMAS PARA MOVIMENTAÇÕES DE ESTOQUE
# =========================================

class MovementCreate(BaseModel):
    sku: str              # O usuário vai digitar o SKU (ex: CAP-SIL-IP14-BLK)
    movement_type: str    # 'entrada', 'saida' ou 'ajuste'
    quantity: int         # Valor positivo
    reason: Optional[str] = ""  # Motivo da movimentação (opcional)

# =========================================
# 3. SCHEMAS PARA FORNECEDORES
# =========================================

class SupplierCreate(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    contact_person: Optional[str] = None
    observations: Optional[str] = None
    product_ids: Optional[List[int]] = []  # IDs dos produtos que o fornecedor vende

# =========================================
# 4. SCHEMAS PARA PRODUTOS (opcionais, para uso futuro)
# =========================================

class CorCreate(BaseModel):
    color_name: str
    full_sku: Optional[str] = None  # Será gerado automaticamente se não fornecido
    variation_price: Optional[float] = None
    price: Optional[float] = None  # Campo do formulário (mapeado para variation_price)
    cost_price: Optional[float] = None  # Custo de compra
    cost: Optional[float] = None  # Campo do formulário (mapeado para cost_price)
    available_stock: Optional[int] = None
    stock: Optional[int] = None  # Campo do formulário (mapeado para available_stock)
    min_stock_alert: int = 10

class CorUpdate(BaseModel):
    id: Optional[int] = None  # ID da variação existente (None para nova cor)
    color_name: str
    full_sku: Optional[str] = None
    variation_price: Optional[float] = None
    price: Optional[float] = None
    cost_price: Optional[float] = None
    cost: Optional[float] = None  # Campo do formulário (mapeado para cost_price)
    available_stock: Optional[int] = None
    stock: Optional[int] = None
    min_stock_alert: int = 10

class ProdutoCreate(BaseModel):
    name: str
    manufacturer: Optional[str] = "Genérico"
    compatibility: Optional[str] = "Universal"
    category: Optional[str] = "Capas"
    colors: List[CorCreate] = []

class ProdutoUpdate(BaseModel):
    name: str
    manufacturer: Optional[str] = "Genérico"
    compatibility: Optional[str] = "Universal"
    category: Optional[str] = "Capas"
    colors: List[CorUpdate] = []

# =========================================
# 5. SCHEMAS PARA CONFIGURAÇÕES
# =========================================

class ConfigUpdate(BaseModel):
    mensagem_fornecedor: str
    mensagens_fornecedores: Optional[dict] = None  # {fornecedor_id: mensagem}

# =========================================
# 6. SCHEMAS PARA PEÇAS FÍSICAS (Catálogo de Peças)
# =========================================

class RepairPartCreate(BaseModel):
    device_model: str  # Modelo do aparelho (ex: iPhone 13)
    part_name: str  # Nome da peça (ex: Tela, Bateria, Conector)
    price: float  # Preço de venda
    cost_price: Optional[float] = 0  # Custo de compra
    available_stock: Optional[int] = 0  # Estoque disponível
    min_stock_alert: Optional[int] = 5  # Alerta de estoque mínimo
    created_at: Optional[datetime] = None  # Data de cadastro (opcional, usa data atual se não informado)

class RepairPartUpdate(BaseModel):
    device_model: Optional[str] = None
    part_name: Optional[str] = None
    price: Optional[float] = None
    cost_price: Optional[float] = None
    available_stock: Optional[int] = None
    min_stock_alert: Optional[int] = None
    status: Optional[str] = None

# =========================================
# 6.1. SCHEMAS PARA SERVIÇOS (Tabela de Serviços/Mão de Obra)
# =========================================

class ServiceCreate(BaseModel):
    name: str  # Nome do serviço (ex: Troca de Tela, Formatação)
    description: Optional[str] = None  # Descrição do serviço
    price: float  # Preço do serviço
    estimated_time: Optional[int] = None  # Tempo estimado em minutos
    status: Optional[str] = "active"  # 'active' ou 'inactive'
    linked_part_id: Optional[int] = None  # ID da peça vinculada para cálculo de custo
    created_at: Optional[datetime] = None  # Data de cadastro (opcional, usa data atual se não informado)

class ServiceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    estimated_time: Optional[int] = None
    status: Optional[str] = None
    linked_part_id: Optional[int] = None  # ID da peça vinculada para cálculo de custo

# =========================================
# 7. SCHEMAS PARA ORDENS DE SERVIÇO
# =========================================

class ServiceOrderPartCreate(BaseModel):
    repair_part_id: int  # ID da peça física
    quantity: int = 1  # Quantidade de peças utilizadas

class ServiceOrderServiceCreate(BaseModel):
    service_id: int  # ID do serviço (mão de obra)
    quantity: int = 1  # Quantidade de vezes que o serviço foi realizado

class ServiceOrderCreate(BaseModel):
    client_name: str  # Nome do cliente
    client_phone: Optional[str] = None  # Telefone
    client_email: Optional[str] = None  # Email
    device_model: str  # Modelo do aparelho
    service_description: str  # Descrição geral do serviço
    parts: List[ServiceOrderPartCreate] = []  # Lista de peças físicas utilizadas
    services: List[ServiceOrderServiceCreate] = []  # Lista de serviços (mão de obra) realizados
    notes: Optional[str] = None  # Observações
    created_at: Optional[datetime] = None  # Data de criação (opcional, usa data atual se não informado)
    completed_at: Optional[datetime] = None  # Data de conclusão (opcional)

class ServiceOrderUpdate(BaseModel):
    client_name: Optional[str] = None
    client_phone: Optional[str] = None
    client_email: Optional[str] = None
    device_model: Optional[str] = None
    service_description: Optional[str] = None
    status: Optional[str] = None  # 'em_andamento', 'concluido', 'cancelado'
    parts: Optional[List[ServiceOrderPartCreate]] = None
    services: Optional[List[ServiceOrderServiceCreate]] = None
    notes: Optional[str] = None

# =========================================
# 8. SCHEMAS PARA COMPRAS DE PEÇAS (FINANÇAS)
# =========================================

class PurchaseItemCreate(BaseModel):
    repair_part_id: int  # ID da peça comprada
    quantity: int  # Quantidade comprada
    unit_cost: float  # Custo unitário da peça

class PurchaseCreate(BaseModel):
    supplier_name: str  # Nome do fornecedor
    shipping_cost: Optional[float] = 0  # Custo do frete
    items: List[PurchaseItemCreate]  # Lista de itens comprados
    notes: Optional[str] = None  # Observações
    created_at: Optional[datetime] = None  # Data da compra (opcional, usa data atual se não informado)

class PurchaseUpdate(BaseModel):
    supplier_name: Optional[str] = None
    shipping_cost: Optional[float] = None
    items: Optional[List[PurchaseItemCreate]] = None
    notes: Optional[str] = None