-- ============================================
-- SCRIPT DE CRIAÇÃO DA TABELA REPAIR_PARTS
-- ============================================
-- Execute este script no SQL Editor do Supabase
-- para criar a tabela de peças de reparo

-- ============================================
-- TABELA: repair_parts (Peças de Reparo)
-- ============================================
CREATE TABLE IF NOT EXISTS repair_parts (
    id SERIAL PRIMARY KEY,
    device_model VARCHAR NOT NULL,  -- Modelo do aparelho (ex: iPhone 13, Samsung Galaxy S21)
    replaced_part VARCHAR NOT NULL,  -- Peça substituída (ex: Tela, Bateria, Conector)
    price NUMERIC(10, 2) NOT NULL,  -- Preço da peça
    cost_price NUMERIC(10, 2) DEFAULT 0,  -- Custo de compra
    subcategory VARCHAR DEFAULT 'substituicao_pecas',  -- 'substituicao_pecas' ou 'reparo'
    available_stock INTEGER DEFAULT 0,  -- Estoque disponível
    min_stock_alert INTEGER DEFAULT 5,  -- Alerta de estoque mínimo
    status VARCHAR DEFAULT 'available',  -- 'available' ou 'unavailable'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para busca rápida
CREATE INDEX IF NOT EXISTS idx_repair_parts_device_model ON repair_parts(device_model);
CREATE INDEX IF NOT EXISTS idx_repair_parts_subcategory ON repair_parts(subcategory);
CREATE INDEX IF NOT EXISTS idx_repair_parts_status ON repair_parts(status);

-- Comentário na tabela para documentação
COMMENT ON TABLE repair_parts IS 'Tabela de peças de reparo e substituição';
COMMENT ON COLUMN repair_parts.device_model IS 'Modelo do aparelho (ex: iPhone 13, Samsung Galaxy S21)';
COMMENT ON COLUMN repair_parts.replaced_part IS 'Peça substituída (ex: Tela, Bateria, Conector de Carga)';
COMMENT ON COLUMN repair_parts.subcategory IS 'Subcategoria: substituicao_pecas ou reparo';

