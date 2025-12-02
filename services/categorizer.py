def processar_texto_modelos(texto_bruto: str) -> list:
    """
    Simula a lógica de limpeza e categorização que farias no n8n.
    """
    # 1. Limpeza básica (separar por pipes ou quebras de linha)
    linhas = [item.strip() for item in texto_bruto.replace('\n', '|').split('|') if item.strip()]
    
    resultados = []
    
    for item in linhas:
        item_lower = item.lower()
        
        # Lógica de Identificação de Marca
        marca = "Outros"
        if "iphone" in item_lower or "apple" in item_lower:
            marca = "Apple"
        elif "samsung" in item_lower or "sansung" in item_lower: # Corrigindo erro comum
            marca = "Samsung"
        elif "moto" in item_lower:
            marca = "Motorola"
            
        # Lógica de Categorização (Regra de Negócio)
        demanda = "Baixa"
        estrategia = "Liquidação"
        
        # Exemplo da tua regra: iPhone 12+ é Alta Demanda
        if marca == "Apple" and any(x in item_lower for x in ['12', '13', '14', '15', '16']):
            demanda = "Alta"
            estrategia = "Manter estoque 15-25 un"
        
        # Exemplo: Samsung S é Alta
        elif marca == "Samsung" and "s2" in item_lower: # pega s20, s21...
            demanda = "Alta"
            estrategia = "Manter estoque 15-25 un"
            
        resultados.append({
            "marca": marca,
            "modelo": item.title(), # Deixa Bonito (Iphone 14)
            "categoria_demanda": demanda,
            "estrategia": estrategia
        })
        
    return resultados