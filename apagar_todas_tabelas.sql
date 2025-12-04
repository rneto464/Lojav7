-- ============================================
-- SCRIPT PARA APAGAR TODAS AS TABELAS
-- ============================================
-- ATENÇÃO: Este script apaga TODAS as tabelas do banco de dados
-- Execute apenas se tiver certeza que deseja perder todos os dados!
-- ============================================

-- Remove as tabelas na ordem correta (respeitando dependências de foreign keys)
-- Começando pelas tabelas de relacionamento many-to-many

DROP TABLE IF EXISTS service_sale_history CASCADE;
DROP TABLE IF EXISTS service_order_services CASCADE;
DROP TABLE IF EXISTS service_order_parts CASCADE;
DROP TABLE IF EXISTS supplier_products CASCADE;
DROP TABLE IF EXISTS purchase_items CASCADE;
DROP TABLE IF EXISTS stock_movements CASCADE;
DROP TABLE IF EXISTS color_variations CASCADE;
DROP TABLE IF EXISTS service_orders CASCADE;
DROP TABLE IF EXISTS services CASCADE;
DROP TABLE IF EXISTS repair_parts CASCADE;
DROP TABLE IF EXISTS purchases CASCADE;
DROP TABLE IF EXISTS suppliers CASCADE;
DROP TABLE IF EXISTS products CASCADE;

-- Verifica se há outras tabelas e remove
DO $$ 
DECLARE
    r RECORD;
BEGIN
    FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') 
    LOOP
        EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
    END LOOP;
END $$;

-- Remove sequências (SERIAL) se existirem
DROP SEQUENCE IF EXISTS products_id_seq CASCADE;
DROP SEQUENCE IF EXISTS color_variations_id_seq CASCADE;
DROP SEQUENCE IF EXISTS suppliers_id_seq CASCADE;
DROP SEQUENCE IF EXISTS stock_movements_id_seq CASCADE;
DROP SEQUENCE IF EXISTS repair_parts_id_seq CASCADE;
DROP SEQUENCE IF EXISTS services_id_seq CASCADE;
DROP SEQUENCE IF EXISTS service_orders_id_seq CASCADE;
DROP SEQUENCE IF EXISTS purchases_id_seq CASCADE;
DROP SEQUENCE IF EXISTS purchase_items_id_seq CASCADE;
DROP SEQUENCE IF EXISTS service_sale_history_id_seq CASCADE;

-- Mensagem de confirmação
DO $$ 
BEGIN
    RAISE NOTICE 'Todas as tabelas foram removidas com sucesso!';
END $$;

