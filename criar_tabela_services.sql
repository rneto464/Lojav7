-- ============================================
-- SCRIPT DE CRIAÇÃO DA TABELA SERVICES
-- ============================================
-- Execute este script no SQL Editor do Supabase
-- para criar a tabela de serviços (mão de obra)

-- ============================================
-- TABELA: services (Serviços/Mão de Obra)
-- ============================================
CREATE TABLE IF NOT EXISTS services (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL,  -- Nome do serviço (ex: Troca de Tela, Formatação)
    description VARCHAR,  -- Descrição do serviço
    price NUMERIC(10, 2) NOT NULL,  -- Preço do serviço
    estimated_time INTEGER,  -- Tempo estimado em minutos (opcional)
    status VARCHAR DEFAULT 'active',  -- 'active' ou 'inactive'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para busca rápida
CREATE INDEX IF NOT EXISTS idx_services_name ON services(name);
CREATE INDEX IF NOT EXISTS idx_services_status ON services(status);

-- Comentário na tabela para documentação
COMMENT ON TABLE services IS 'Tabela de serviços (mão de obra) - ações que você faz';
COMMENT ON COLUMN services.name IS 'Nome do serviço (ex: Troca de Tela, Formatação, Limpeza Química)';
COMMENT ON COLUMN services.description IS 'Descrição detalhada do serviço';
COMMENT ON COLUMN services.price IS 'Preço do serviço (mão de obra)';
COMMENT ON COLUMN services.estimated_time IS 'Tempo estimado em minutos (opcional)';
COMMENT ON COLUMN services.status IS 'Status: active ou inactive';

-- ============================================
-- TABELA: service_order_services
-- (Relacionamento many-to-many entre ordens de serviço e serviços)
-- ============================================
CREATE TABLE IF NOT EXISTS service_order_services (
    service_order_id INTEGER NOT NULL REFERENCES service_orders(id) ON DELETE CASCADE,
    service_id INTEGER NOT NULL REFERENCES services(id) ON DELETE CASCADE,
    quantity INTEGER DEFAULT 1,  -- Quantidade de vezes que o serviço foi realizado
    PRIMARY KEY (service_order_id, service_id)
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_service_order_services_order ON service_order_services(service_order_id);
CREATE INDEX IF NOT EXISTS idx_service_order_services_service ON service_order_services(service_id);

COMMENT ON TABLE service_order_services IS 'Relacionamento many-to-many entre ordens de serviço e serviços';

