-- ============================================
-- SCRIPT PARA CRIAR TODAS AS TABELAS
-- ============================================
-- Execute este script no SQL Editor do Supabase
-- para criar todas as tabelas do sistema
-- ============================================

-- ============================================
-- 1. TABELA: products (Produtos)
-- ============================================
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL,
    manufacturer VARCHAR DEFAULT 'Genérico',
    compatibility VARCHAR DEFAULT 'Universal',
    category VARCHAR DEFAULT 'Capas'
);

CREATE INDEX IF NOT EXISTS idx_products_name ON products(name);

COMMENT ON TABLE products IS 'Tabela de produtos (ex: Capas, Películas)';
COMMENT ON COLUMN products.name IS 'Nome do produto (ex: Capa Silicone Premium)';
COMMENT ON COLUMN products.manufacturer IS 'Fabricante do produto';
COMMENT ON COLUMN products.compatibility IS 'Compatibilidade (ex: iPhone 14, 14 Pro)';
COMMENT ON COLUMN products.category IS 'Categoria do produto (ex: Capas)';

-- ============================================
-- 2. TABELA: color_variations (Variações de Cor)
-- ============================================
CREATE TABLE IF NOT EXISTS color_variations (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    color_name VARCHAR NOT NULL,
    full_sku VARCHAR UNIQUE NOT NULL,
    variation_price NUMERIC(10, 2) NOT NULL,
    cost_price NUMERIC(10, 2) DEFAULT 0,
    available_stock INTEGER DEFAULT 0,
    min_stock_alert INTEGER DEFAULT 10,
    status VARCHAR DEFAULT 'available'
);

CREATE INDEX IF NOT EXISTS idx_color_variations_sku ON color_variations(full_sku);
CREATE INDEX IF NOT EXISTS idx_color_variations_product ON color_variations(product_id);
CREATE INDEX IF NOT EXISTS idx_color_variations_status ON color_variations(status);

COMMENT ON TABLE color_variations IS 'Variações de cor dos produtos (ex: Preto, Branco)';
COMMENT ON COLUMN color_variations.full_sku IS 'SKU completo (ex: CAP-SIL-IP14-BLK)';
COMMENT ON COLUMN color_variations.variation_price IS 'Preço de venda';
COMMENT ON COLUMN color_variations.cost_price IS 'Custo de compra';

-- ============================================
-- 3. TABELA: suppliers (Fornecedores)
-- ============================================
CREATE TABLE IF NOT EXISTS suppliers (
    id SERIAL PRIMARY KEY,
    name VARCHAR UNIQUE NOT NULL,
    email VARCHAR,
    phone VARCHAR,
    contact_person VARCHAR,
    observations VARCHAR
);

CREATE INDEX IF NOT EXISTS idx_suppliers_name ON suppliers(name);

COMMENT ON TABLE suppliers IS 'Tabela de fornecedores';
COMMENT ON COLUMN suppliers.name IS 'Nome do fornecedor';
COMMENT ON COLUMN suppliers.contact_person IS 'Pessoa de contato';

-- ============================================
-- 4. TABELA: supplier_products (Relacionamento Fornecedor-Produto)
-- ============================================
CREATE TABLE IF NOT EXISTS supplier_products (
    supplier_id INTEGER NOT NULL REFERENCES suppliers(id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    PRIMARY KEY (supplier_id, product_id)
);

CREATE INDEX IF NOT EXISTS idx_supplier_products_supplier ON supplier_products(supplier_id);
CREATE INDEX IF NOT EXISTS idx_supplier_products_product ON supplier_products(product_id);

COMMENT ON TABLE supplier_products IS 'Relacionamento many-to-many entre fornecedores e produtos';

-- ============================================
-- 5. TABELA: stock_movements (Movimentações de Estoque)
-- ============================================
CREATE TABLE IF NOT EXISTS stock_movements (
    id SERIAL PRIMARY KEY,
    variation_id INTEGER NOT NULL REFERENCES color_variations(id) ON DELETE CASCADE,
    movement_type VARCHAR NOT NULL,
    quantity INTEGER NOT NULL,
    previous_stock INTEGER,
    new_stock INTEGER,
    reason VARCHAR,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_stock_movements_variation ON stock_movements(variation_id);
CREATE INDEX IF NOT EXISTS idx_stock_movements_type ON stock_movements(movement_type);
CREATE INDEX IF NOT EXISTS idx_stock_movements_created ON stock_movements(created_at);

COMMENT ON TABLE stock_movements IS 'Histórico de movimentações de estoque';
COMMENT ON COLUMN stock_movements.movement_type IS 'Tipo: entrada, saida ou ajuste';
COMMENT ON COLUMN stock_movements.previous_stock IS 'Estoque antes da movimentação';
COMMENT ON COLUMN stock_movements.new_stock IS 'Estoque após a movimentação';

-- ============================================
-- 6. TABELA: repair_parts (Peças Físicas - Catálogo de Peças)
-- ============================================
CREATE TABLE IF NOT EXISTS repair_parts (
    id SERIAL PRIMARY KEY,
    device_model VARCHAR NOT NULL,
    part_name VARCHAR NOT NULL,
    price NUMERIC(10, 2) NOT NULL,
    cost_price NUMERIC(10, 2) DEFAULT 0,
    available_stock INTEGER DEFAULT 0,
    min_stock_alert INTEGER DEFAULT 5,
    status VARCHAR DEFAULT 'available',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_repair_parts_device_model ON repair_parts(device_model);
CREATE INDEX IF NOT EXISTS idx_repair_parts_status ON repair_parts(status);

COMMENT ON TABLE repair_parts IS 'Tabela de peças físicas (produtos que você compra e estoca)';
COMMENT ON COLUMN repair_parts.device_model IS 'Modelo do aparelho (ex: iPhone 13, Samsung Galaxy S21)';
COMMENT ON COLUMN repair_parts.part_name IS 'Nome da peça (ex: Tela, Bateria, Conector de Carga)';
COMMENT ON COLUMN repair_parts.price IS 'Preço de venda da peça';
COMMENT ON COLUMN repair_parts.cost_price IS 'Custo de compra da peça';
COMMENT ON COLUMN repair_parts.available_stock IS 'Estoque disponível';

-- ============================================
-- 7. TABELA: services (Serviços - Mão de Obra)
-- ============================================
CREATE TABLE IF NOT EXISTS services (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL,
    description VARCHAR,
    price NUMERIC(10, 2) NOT NULL,
    estimated_time INTEGER,
    status VARCHAR DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_services_name ON services(name);
CREATE INDEX IF NOT EXISTS idx_services_status ON services(status);

COMMENT ON TABLE services IS 'Tabela de serviços (mão de obra) - ações que você faz';
COMMENT ON COLUMN services.name IS 'Nome do serviço (ex: Troca de Tela, Formatação, Limpeza Química)';
COMMENT ON COLUMN services.description IS 'Descrição detalhada do serviço';
COMMENT ON COLUMN services.price IS 'Preço do serviço (mão de obra)';
COMMENT ON COLUMN services.estimated_time IS 'Tempo estimado em minutos (opcional)';
COMMENT ON COLUMN services.status IS 'Status: active ou inactive';

-- ============================================
-- 8. TABELA: service_orders (Ordens de Serviço)
-- ============================================
CREATE TABLE IF NOT EXISTS service_orders (
    id SERIAL PRIMARY KEY,
    order_number VARCHAR UNIQUE NOT NULL,
    client_name VARCHAR NOT NULL,
    client_phone VARCHAR,
    client_email VARCHAR,
    device_model VARCHAR NOT NULL,
    service_description VARCHAR NOT NULL,
    status VARCHAR DEFAULT 'em_andamento',
    total_value NUMERIC(10, 2) DEFAULT 0,
    profit NUMERIC(10, 2),
    notes VARCHAR,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_service_orders_number ON service_orders(order_number);
CREATE INDEX IF NOT EXISTS idx_service_orders_status ON service_orders(status);
CREATE INDEX IF NOT EXISTS idx_service_orders_created ON service_orders(created_at);

COMMENT ON TABLE service_orders IS 'Tabela de ordens de serviço';
COMMENT ON COLUMN service_orders.order_number IS 'Número da ordem (ex: OS-2024-001)';
COMMENT ON COLUMN service_orders.status IS 'Status: em_andamento, concluido ou cancelado';
COMMENT ON COLUMN service_orders.total_value IS 'Valor total (peças + serviços)';
COMMENT ON COLUMN service_orders.profit IS 'Lucro calculado: (Preço Venda Peça + Preço Serviço) - (Custo Compra Peça)';

-- ============================================
-- 9. TABELA: service_order_parts (Relacionamento Ordem-Peça)
-- ============================================
CREATE TABLE IF NOT EXISTS service_order_parts (
    service_order_id INTEGER NOT NULL REFERENCES service_orders(id) ON DELETE CASCADE,
    repair_part_id INTEGER NOT NULL REFERENCES repair_parts(id) ON DELETE CASCADE,
    quantity INTEGER DEFAULT 1,
    PRIMARY KEY (service_order_id, repair_part_id)
);

CREATE INDEX IF NOT EXISTS idx_service_order_parts_order ON service_order_parts(service_order_id);
CREATE INDEX IF NOT EXISTS idx_service_order_parts_part ON service_order_parts(repair_part_id);

COMMENT ON TABLE service_order_parts IS 'Relacionamento many-to-many entre ordens de serviço e peças físicas';
COMMENT ON COLUMN service_order_parts.quantity IS 'Quantidade de peças usadas';

-- ============================================
-- 10. TABELA: service_order_services (Relacionamento Ordem-Serviço)
-- ============================================
CREATE TABLE IF NOT EXISTS service_order_services (
    service_order_id INTEGER NOT NULL REFERENCES service_orders(id) ON DELETE CASCADE,
    service_id INTEGER NOT NULL REFERENCES services(id) ON DELETE CASCADE,
    quantity INTEGER DEFAULT 1,
    PRIMARY KEY (service_order_id, service_id)
);

CREATE INDEX IF NOT EXISTS idx_service_order_services_order ON service_order_services(service_order_id);
CREATE INDEX IF NOT EXISTS idx_service_order_services_service ON service_order_services(service_id);

COMMENT ON TABLE service_order_services IS 'Relacionamento many-to-many entre ordens de serviço e serviços';
COMMENT ON COLUMN service_order_services.quantity IS 'Quantidade de vezes que o serviço foi realizado';

-- ============================================
-- 11. TABELA: purchases (Compras de Peças)
-- ============================================
CREATE TABLE IF NOT EXISTS purchases (
    id SERIAL PRIMARY KEY,
    purchase_number VARCHAR UNIQUE NOT NULL,
    supplier_name VARCHAR NOT NULL,
    shipping_cost NUMERIC(10, 2) DEFAULT 0,
    total_value NUMERIC(10, 2) DEFAULT 0,
    notes VARCHAR,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_purchases_number ON purchases(purchase_number);
CREATE INDEX IF NOT EXISTS idx_purchases_created ON purchases(created_at);

COMMENT ON TABLE purchases IS 'Tabela de compras de peças (para controle financeiro)';
COMMENT ON COLUMN purchases.purchase_number IS 'Número da compra (ex: COMP-2024-001)';
COMMENT ON COLUMN purchases.supplier_name IS 'Nome do fornecedor';
COMMENT ON COLUMN purchases.shipping_cost IS 'Custo do frete';
COMMENT ON COLUMN purchases.total_value IS 'Valor total da compra (peças + frete)';

-- ============================================
-- 12. TABELA: purchase_items (Itens da Compra)
-- ============================================
CREATE TABLE IF NOT EXISTS purchase_items (
    id SERIAL PRIMARY KEY,
    purchase_id INTEGER NOT NULL REFERENCES purchases(id) ON DELETE CASCADE,
    repair_part_id INTEGER NOT NULL REFERENCES repair_parts(id) ON DELETE CASCADE,
    quantity INTEGER NOT NULL,
    unit_cost NUMERIC(10, 2) NOT NULL,
    total_cost NUMERIC(10, 2) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_purchase_items_purchase ON purchase_items(purchase_id);
CREATE INDEX IF NOT EXISTS idx_purchase_items_part ON purchase_items(repair_part_id);

COMMENT ON TABLE purchase_items IS 'Itens de uma compra de peças';
COMMENT ON COLUMN purchase_items.unit_cost IS 'Custo unitário da peça na compra';
COMMENT ON COLUMN purchase_items.total_cost IS 'Custo total (quantity × unit_cost)';

-- ============================================
-- MENSAGEM DE CONFIRMAÇÃO
-- ============================================
DO $$ 
BEGIN
    RAISE NOTICE 'Todas as tabelas foram criadas com sucesso!';
    RAISE NOTICE 'Tabelas criadas:';
    RAISE NOTICE '  - products';
    RAISE NOTICE '  - color_variations';
    RAISE NOTICE '  - suppliers';
    RAISE NOTICE '  - supplier_products';
    RAISE NOTICE '  - stock_movements';
    RAISE NOTICE '  - repair_parts';
    RAISE NOTICE '  - services (NOVA)';
    RAISE NOTICE '  - service_orders';
    RAISE NOTICE '  - service_order_parts';
    RAISE NOTICE '  - service_order_services (NOVA)';
    RAISE NOTICE '  - purchases';
    RAISE NOTICE '  - purchase_items';
END $$;

