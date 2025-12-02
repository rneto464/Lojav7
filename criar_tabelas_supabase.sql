-- ============================================
-- SCRIPT DE CRIAÇÃO DE TABELAS PARA SUPABASE
-- ============================================
-- Execute este script no SQL Editor do Supabase
-- para criar todas as tabelas necessárias

-- ============================================
-- 1. TABELA: products (Produtos)
-- ============================================
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL,
    manufacturer VARCHAR DEFAULT 'Genérico',
    compatibility VARCHAR DEFAULT 'Universal',
    category VARCHAR DEFAULT 'Capas',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índice para busca rápida por nome
CREATE INDEX IF NOT EXISTS idx_products_name ON products(name);

-- ============================================
-- 2. TABELA: color_variations (Variações de Cor)
-- ============================================
CREATE TABLE IF NOT EXISTS color_variations (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL,
    color_name VARCHAR,
    full_sku VARCHAR UNIQUE NOT NULL,
    variation_price NUMERIC(10, 2),
    cost_price NUMERIC(10, 2) DEFAULT 0,
    available_stock INTEGER DEFAULT 0,
    min_stock_alert INTEGER DEFAULT 10,
    status VARCHAR DEFAULT 'available',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Chave estrangeira para products
    CONSTRAINT fk_product 
        FOREIGN KEY (product_id) 
        REFERENCES products(id) 
        ON DELETE CASCADE
);

-- Índices para busca rápida
CREATE INDEX IF NOT EXISTS idx_color_variations_product_id ON color_variations(product_id);
CREATE INDEX IF NOT EXISTS idx_color_variations_sku ON color_variations(full_sku);
CREATE INDEX IF NOT EXISTS idx_color_variations_stock ON color_variations(available_stock);

-- ============================================
-- 3. TABELA: suppliers (Fornecedores)
-- ============================================
CREATE TABLE IF NOT EXISTS suppliers (
    id SERIAL PRIMARY KEY,
    name VARCHAR UNIQUE NOT NULL,
    email VARCHAR,
    phone VARCHAR,
    contact_person VARCHAR,
    observations TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índice para busca rápida por nome
CREATE INDEX IF NOT EXISTS idx_suppliers_name ON suppliers(name);

-- ============================================
-- 4. TABELA: stock_movements (Movimentações de Estoque)
-- ============================================
CREATE TABLE IF NOT EXISTS stock_movements (
    id SERIAL PRIMARY KEY,
    variation_id INTEGER NOT NULL,
    movement_type VARCHAR NOT NULL CHECK (movement_type IN ('entrada', 'saida', 'ajuste')),
    quantity INTEGER NOT NULL,
    previous_stock INTEGER,
    new_stock INTEGER,
    reason VARCHAR,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Chave estrangeira para color_variations
    CONSTRAINT fk_variation 
        FOREIGN KEY (variation_id) 
        REFERENCES color_variations(id) 
        ON DELETE CASCADE
);

-- Índices para busca rápida
CREATE INDEX IF NOT EXISTS idx_stock_movements_variation_id ON stock_movements(variation_id);
CREATE INDEX IF NOT EXISTS idx_stock_movements_created_at ON stock_movements(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_stock_movements_type ON stock_movements(movement_type);

-- ============================================
-- COMENTÁRIOS DAS TABELAS (Opcional - para documentação)
-- ============================================
COMMENT ON TABLE products IS 'Tabela principal de produtos do sistema';
COMMENT ON TABLE color_variations IS 'Variações de cor/preço/estoque de cada produto';
COMMENT ON TABLE suppliers IS 'Cadastro de fornecedores';
COMMENT ON TABLE stock_movements IS 'Histórico de todas as movimentações de estoque';

-- ============================================
-- VERIFICAÇÃO: Ver se as tabelas foram criadas
-- ============================================
-- Execute esta query para verificar se tudo foi criado:
-- SELECT table_name 
-- FROM information_schema.tables 
-- WHERE table_schema = 'public' 
--   AND table_name IN ('products', 'color_variations', 'suppliers', 'stock_movements')
-- ORDER BY table_name;

