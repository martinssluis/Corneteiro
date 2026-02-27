from app.utils.pontuacao_scouts import PONTOS_SCOUT

def calcular_pontuacao_por_scout(scout) -> float:
    if not scout:
        return 0.0
    
    total = 0.0
    for codigo, quantidade in scout.items():
        pontos = PONTOS_SCOUT.get(codigo, 0.0)
        total += pontos * quantidade
        
    # arredondar para manter o padrão visual parecido com o Cartola
    return round(total, 2)