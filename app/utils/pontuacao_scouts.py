#Tabela base (https://ge.globo.com/cartola/noticia/2025/03/17/quanto-vale-a-pontuacao-de-cada-scout-no-cartola.ghtml)

PONTOS_SCOUT = {
     # Ataque
    "G": 8.0,      # Gol
    "A": 5.0,      # Assistência
    "FT": 3.0,     # Finalização na trave
    "FD": 0.5,     # Falta sofrida
    "PS": 1.0,     # Pênalti sofrido
    "I": -0.1,     # Impedimento

    # Finalizações (atenção: alguns anos diferenciam FS/FF)
    "FF": 0.8,     # Finalização para fora
    "FS": 1.2,     # Finalização certa/defendida (ajuste se necessário)

    # Defesa
    "SG": 5.0,     # Jogo sem sofrer gols (defensores)
    "DP": 7.0,     # Defesa de pênalti
    "DE": 1.3,     # Defesa (goleiro)
    "DS": 1.5,     # Desarme

    # Penalidades
    "GC": -3.0,    # Gol contra
    "CV": -3.0,    # Cartão vermelho
    "CA": -1.0,    # Cartão amarelo
    "GS": -1.0,    # Gol sofrido
    "FC": -0.3,    # Falta cometida
    "PC": -1.0,    # Pênalti cometido

    # Pênalti perdido (se o retorno vier como PP genérico)
    "PP": -3.2,
}