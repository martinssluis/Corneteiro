from app.services.clubes_service import get_clube
from app.utils.posicoes import get_posicao

def anexar_clube_e_posicao(atleta: dict) -> dict:
    # Clube
    clube = get_clube(atleta.get("clube_id"))
    if clube:
        atleta["clube_nome"] = clube.get("nome_fantasia")     # nome amigável
        atleta["clube_abreviacao"] = clube.get("nome")        # sua regra: "nome" como sigla

    # Posição
    posicao = get_posicao(atleta.get("posicao_id"))
    if posicao:
        atleta["posicao_nome"] = posicao.get("nome")
        atleta["posicao_abreviacao"] = posicao.get("abreviacao")

    return atleta