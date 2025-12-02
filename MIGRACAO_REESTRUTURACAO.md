# Reestruturação: Separação de Peças Físicas e Serviços

## Resumo das Mudanças

Esta reestruturação separa claramente **"Produtos Físicos"** (Peças) de **"Serviços"** (Mão de Obra), tornando o sistema mais intuitivo e organizado.

## Conceito

### Antes
- Misturava "Substituição de Peças" (ação) com peças físicas
- "Reparo" era uma subcategoria de peças
- Confusão entre o que você compra/estoca e o que você faz

### Depois
- **Catálogo de Peças**: Produtos físicos que você compra e estoca
  - Tem: custo de compra, preço de venda, quantidade em estoque
  - Exemplos: Telas, Baterias, Conectores, Películas
  
- **Tabela de Serviços**: Mão de obra (ações que você faz)
  - Tem: preço de venda, tempo estimado (opcional)
  - NÃO tem estoque (você não estoca "formatações")
  - Exemplos: Troca de Tela, Formatação, Limpeza Química, Análise Técnica

## Mudanças no Banco de Dados

### Novas Tabelas

1. **`services`** - Tabela de serviços (mão de obra)
   - Campos: `id`, `name`, `description`, `price`, `estimated_time`, `status`, `created_at`

2. **`service_order_services`** - Relacionamento many-to-many entre ordens de serviço e serviços
   - Campos: `service_order_id`, `service_id`, `quantity`

### Tabelas Modificadas

1. **`repair_parts`** - Agora só armazena peças físicas
   - Removido: campo `subcategory` (não é mais necessário)
   - Renomeado: `replaced_part` → `part_name` (mais claro)
   - Mantido: todos os campos de estoque e custo

2. **`service_orders`** - Agora relaciona com peças E serviços
   - Removido: campo `labor_cost` (substituído por relacionamento com `services`)
   - Adicionado: relacionamento many-to-many com `services`

## Mudanças no Código

### Models (`models.py`)
- Criado modelo `Service` para serviços
- Atualizado `RepairPart` para remover `subcategory` e renomear `replaced_part` para `part_name`
- Atualizado `ServiceOrder` para relacionar com `services` além de `parts`
- Criada tabela de relacionamento `service_order_services`

### Schemas (`schemas.py`)
- Criados schemas `ServiceCreate` e `ServiceUpdate`
- Atualizado `RepairPartCreate` para usar `part_name` e remover `subcategory`
- Atualizado `ServiceOrderCreate` para incluir `services` além de `parts`
- Criado schema `ServiceOrderServiceCreate`

### Rotas API (`main.py`)
- Adicionadas rotas para serviços:
  - `GET /api/servicos` - Listar serviços
  - `POST /api/servicos` - Criar serviço
  - `PUT /api/servicos/{servico_id}` - Atualizar serviço
  - `DELETE /api/servicos/{servico_id}` - Excluir serviço
- Atualizada rota `/reparos` para buscar apenas peças (sem subcategoria)
- Atualizada criação de ordens de serviço para usar `services` ao invés de `labor_cost`
- Atualizada atualização de ordens de serviço para gerenciar `services`

### Template (`templates/reparos.html`)
- Reestruturado para ter duas abas:
  - **Catálogo de Peças**: Lista todas as peças físicas
  - **Tabela de Serviços**: Lista todos os serviços (mão de obra)
- Removida aba "Ordens de Serviço" (já removida da navegação anteriormente)
- Adicionado modal para cadastro/edição de serviços
- Atualizado formulário de peças para usar `part_name` ao invés de `replaced_part`
- Removido campo `subcategory` do formulário de peças
- Adicionadas funções JavaScript para gerenciar serviços

## Scripts SQL Necessários

Execute os seguintes scripts no SQL Editor do Supabase:

1. **`criar_tabela_services.sql`** - Cria a tabela `services` e `service_order_services`

2. **Migração de dados existentes** (se necessário):
   - Se você tinha peças com `subcategory = 'reparo'`, você precisará:
     - Criar serviços correspondentes manualmente
     - Ou criar um script de migração para converter automaticamente

## Como Usar

### Cadastrar uma Peça Física
1. Vá para a aba "Catálogo de Peças"
2. Clique em "Cadastrar Peça"
3. Preencha: Modelo do Aparelho, Nome da Peça, Preço, Custo de Compra, Estoque

### Cadastrar um Serviço
1. Vá para a aba "Tabela de Serviços"
2. Clique em "Cadastrar Serviço"
3. Preencha: Nome do Serviço, Descrição (opcional), Preço, Tempo Estimado (opcional)

### Criar uma Ordem de Serviço
1. Uma ordem de serviço pode incluir:
   - **Peças físicas**: Selecionar peças do catálogo (reduz estoque automaticamente)
   - **Serviços**: Selecionar serviços da tabela (mão de obra)
2. O valor total é calculado automaticamente: (Peças × Quantidade) + (Serviços × Quantidade)

## Benefícios

1. **Clareza**: Separação clara entre o que você compra/estoca e o que você faz
2. **Organização**: Estrutura mais intuitiva e fácil de entender
3. **Flexibilidade**: Pode ter múltiplos serviços em uma ordem de serviço
4. **Rastreabilidade**: Melhor controle de custos e lucros por tipo (peças vs. mão de obra)

## Notas Importantes

- A migração mantém compatibilidade com dados antigos usando `hasattr()` e verificações de campos
- O campo `replaced_part` antigo ainda funciona, mas o novo campo `part_name` é preferido
- Ordens de serviço antigas que usavam `labor_cost` continuarão funcionando, mas novas ordens devem usar serviços

