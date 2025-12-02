from sqlalchemy import Column, Integer, String, ForeignKey, Numeric, Table
from sqlalchemy.orm import relationship
from database import Base
from sqlalchemy import DateTime # Importe DateTime se não tiver
import datetime

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True) # Ex: Capa Silicone Premium Aveludada
    
    # NOVOS CAMPOS
    manufacturer = Column(String, default="Genérico") # Ex: CapaMax
    compatibility = Column(String, default="Universal") # Ex: iPhone 14, 14 Pro
    category = Column(String, default="Capas")
    
    variations = relationship("ColorVariation", back_populates="product", cascade="all, delete-orphan")

class ColorVariation(Base):
    __tablename__ = "color_variations"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    
    color_name = Column(String) # Ex: Preto Fosco
    full_sku = Column(String, unique=True, index=True) # Ex: CAP-SIL-IP14-BLK
    variation_price = Column(Numeric(10, 2)) # Ex: 25.90 (preço de venda)
    cost_price = Column(Numeric(10, 2), default=0) # Ex: 15.50 (custo de compra)
    available_stock = Column(Integer, default=0) # Ex: 15
    
    min_stock_alert = Column(Integer, default=10)
    status = Column(String, default="available")

    product = relationship("Product", back_populates="variations")


# Tabela de relacionamento many-to-many entre fornecedores e produtos
supplier_products = Table(
    'supplier_products',
    Base.metadata,
    Column('supplier_id', Integer, ForeignKey('suppliers.id'), primary_key=True),
    Column('product_id', Integer, ForeignKey('products.id'), primary_key=True)
)

class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True) # Ex: CapasMaster Importadora
    email = Column(String)
    phone = Column(String)
    contact_person = Column(String) # Ex: João Silva
    observations = Column(String)
    
    # Relacionamento many-to-many com produtos
    products = relationship("Product", secondary=supplier_products, backref="suppliers")

class StockMovement(Base):
    __tablename__ = "stock_movements"

    id = Column(Integer, primary_key=True, index=True)
    variation_id = Column(Integer, ForeignKey("color_variations.id"))
    
    movement_type = Column(String) # 'entrada', 'saida', 'ajuste'
    quantity = Column(Integer)     # Quantidade movimentada (ex: 30, 5, 2)
    
    # Snapshots (Fotos do momento da transação)
    previous_stock = Column(Integer)
    new_stock = Column(Integer)
    
    reason = Column(String) # Ex: "Venda", "Reposição", "Perda"
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relacionamento para saber qual produto foi movimentado
    variation = relationship("ColorVariation")

# =========================================
# PEÇAS FÍSICAS (Produtos que você compra e estoca)
# =========================================
class RepairPart(Base):
    __tablename__ = "repair_parts"

    id = Column(Integer, primary_key=True, index=True)
    device_model = Column(String, index=True)  # Ex: iPhone 13, Samsung Galaxy S21
    part_name = Column(String)  # Ex: Tela, Bateria, Conector de Carga
    price = Column(Numeric(10, 2))  # Preço de venda da peça
    cost_price = Column(Numeric(10, 2), default=0)  # Custo de compra
    available_stock = Column(Integer, default=0)  # Estoque disponível
    min_stock_alert = Column(Integer, default=5)  # Alerta de estoque mínimo
    status = Column(String, default="available")  # 'available', 'unavailable'
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relacionamento com ordens de serviço
    service_orders = relationship("ServiceOrder", secondary="service_order_parts", back_populates="parts")

# =========================================
# SERVIÇOS (Mão de obra - ações que você faz)
# =========================================
class Service(Base):
    __tablename__ = "services"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)  # Ex: Troca de Tela, Formatação, Limpeza Química
    description = Column(String)  # Descrição do serviço
    price = Column(Numeric(10, 2))  # Preço do serviço (mão de obra)
    estimated_time = Column(Integer, nullable=True)  # Tempo estimado em minutos (opcional)
    status = Column(String, default="active")  # 'active', 'inactive'
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relacionamento com ordens de serviço
    service_orders = relationship("ServiceOrder", secondary="service_order_services", back_populates="services")

# Tabela de relacionamento many-to-many entre ordens de serviço e peças
service_order_parts = Table(
    'service_order_parts',
    Base.metadata,
    Column('service_order_id', Integer, ForeignKey('service_orders.id'), primary_key=True),
    Column('repair_part_id', Integer, ForeignKey('repair_parts.id'), primary_key=True),
    Column('quantity', Integer, default=1)  # Quantidade de peças usadas
)

# Tabela de relacionamento many-to-many entre ordens de serviço e serviços
service_order_services = Table(
    'service_order_services',
    Base.metadata,
    Column('service_order_id', Integer, ForeignKey('service_orders.id'), primary_key=True),
    Column('service_id', Integer, ForeignKey('services.id'), primary_key=True),
    Column('quantity', Integer, default=1)  # Quantidade de vezes que o serviço foi realizado
)

class ServiceOrder(Base):
    __tablename__ = "service_orders"

    id = Column(Integer, primary_key=True, index=True)
    order_number = Column(String, unique=True, index=True)  # Número da ordem (ex: OS-2024-001)
    client_name = Column(String)  # Nome do cliente
    client_phone = Column(String)  # Telefone do cliente
    client_email = Column(String)  # Email do cliente (opcional)
    device_model = Column(String)  # Modelo do aparelho do cliente
    service_description = Column(String)  # Descrição geral do serviço realizado
    status = Column(String, default="em_andamento")  # 'em_andamento', 'concluido', 'cancelado'
    total_value = Column(Numeric(10, 2), default=0)  # Valor total do serviço (peças + serviços)
    notes = Column(String)  # Observações adicionais
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)  # Data de conclusão
    
    # Relacionamento many-to-many com peças físicas
    parts = relationship("RepairPart", secondary=service_order_parts, back_populates="service_orders")
    
    # Relacionamento many-to-many com serviços (mão de obra)
    services = relationship("Service", secondary=service_order_services, back_populates="service_orders")

# Modelos para Finanças - Compras de Peças
class Purchase(Base):
    __tablename__ = "purchases"

    id = Column(Integer, primary_key=True, index=True)
    purchase_number = Column(String, unique=True, index=True)  # Número da compra (ex: COMP-2024-001)
    supplier_name = Column(String)  # Nome do fornecedor
    shipping_cost = Column(Numeric(10, 2), default=0)  # Custo do frete
    total_value = Column(Numeric(10, 2), default=0)  # Valor total da compra (peças + frete)
    notes = Column(String)  # Observações adicionais
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relacionamento com itens da compra
    items = relationship("PurchaseItem", back_populates="purchase", cascade="all, delete-orphan")

class PurchaseItem(Base):
    __tablename__ = "purchase_items"

    id = Column(Integer, primary_key=True, index=True)
    purchase_id = Column(Integer, ForeignKey("purchases.id"))
    repair_part_id = Column(Integer, ForeignKey("repair_parts.id"))
    quantity = Column(Integer)  # Quantidade comprada
    unit_cost = Column(Numeric(10, 2))  # Custo unitário da peça na compra
    total_cost = Column(Numeric(10, 2))  # Custo total (quantity * unit_cost)
    
    # Relacionamentos
    purchase = relationship("Purchase", back_populates="items")
    repair_part = relationship("RepairPart")