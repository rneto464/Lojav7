-- Script SQL para adicionar o campo cost_price na tabela color_variations
-- Execute este script no seu banco de dados PostgreSQL

-- Adiciona a coluna cost_price se ela não existir
ALTER TABLE color_variations 
ADD COLUMN IF NOT EXISTS cost_price NUMERIC(10, 2) DEFAULT 0;

-- Atualiza registros existentes para ter custo 0 se for NULL
UPDATE color_variations 
SET cost_price = 0 
WHERE cost_price IS NULL;

-- Adiciona comentário na coluna para documentação
COMMENT ON COLUMN color_variations.cost_price IS 'Custo de compra do produto (usado para cálculo de lucro)';

