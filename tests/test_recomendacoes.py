import unittest
from unittest.mock import patch

from app import create_app
from app.services import recomendacoes_service


class RecomendacoesServiceTestCase(unittest.TestCase):
    def test_recomendacao_valorizacao_filtra_e_ordena_por_folga(self):
        atletas = {
            "atletas": [
                {
                    "atleta_id": 1,
                    "apelido": "Valorizador A",
                    "clube_id": 10,
                    "posicao_id": 2,
                    "preco_num": 10.0,
                    "media_num": 6.0,
                },
                {
                    "atleta_id": 2,
                    "apelido": "Valorizador B",
                    "clube_id": 20,
                    "posicao_id": 2,
                    "preco_num": 12.0,
                    "media_num": 7.0,
                },
                {
                    "atleta_id": 3,
                    "apelido": "Nao Valoriza",
                    "clube_id": 30,
                    "posicao_id": 2,
                    "preco_num": 20.0,
                    "media_num": 5.0,
                },
            ]
        }

        with patch.object(recomendacoes_service, "get_atletas_mercado", return_value=atletas), patch.object(
            recomendacoes_service,
            "_carregar_clubes_seguro",
            return_value={
                10: {"nome": "Clube A", "abreviacao": "CLA"},
                20: {"nome": "Clube B", "abreviacao": "CLB"},
                30: {"nome": "Clube C", "abreviacao": "CLC"},
            },
        ):
            resultado = recomendacoes_service.recomendacao_valorizacao(posicao_id=2, limite=10)

        self.assertEqual(resultado["criterio"], "valorizacao")
        self.assertEqual(resultado["quantidade"], 2)
        self.assertEqual(resultado["recomendacoes"][0]["atleta_id"], 1)
        self.assertEqual(resultado["recomendacoes"][1]["atleta_id"], 2)
        self.assertTrue(resultado["recomendacoes"][0]["atinge_minimo_valorizacao"])
        self.assertAlmostEqual(resultado["recomendacoes"][0]["pontos_minimos_valorizacao"], 4.5)
        self.assertAlmostEqual(resultado["recomendacoes"][0]["folga_valorizacao"], 1.5)

    def test_recomendacao_valorizacao_aplica_preco_max(self):
        atletas = {
            "atletas": [
                {
                    "atleta_id": 1,
                    "apelido": "Ate 10",
                    "clube_id": 10,
                    "posicao_id": 2,
                    "preco_num": 10.0,
                    "media_num": 6.0,
                },
                {
                    "atleta_id": 2,
                    "apelido": "Acima de 10",
                    "clube_id": 20,
                    "posicao_id": 2,
                    "preco_num": 11.0,
                    "media_num": 8.0,
                },
            ]
        }

        with patch.object(recomendacoes_service, "get_atletas_mercado", return_value=atletas), patch.object(
            recomendacoes_service,
            "_carregar_clubes_seguro",
            return_value={10: {"nome": "Clube A", "abreviacao": "CLA"}, 20: {"nome": "Clube B", "abreviacao": "CLB"}},
        ):
            resultado = recomendacoes_service.recomendacao_valorizacao(posicao_id=2, limite=10, preco_max=10.0)

        self.assertEqual(resultado["quantidade"], 1)
        self.assertEqual(resultado["preco_max"], 10.0)
        self.assertEqual(resultado["recomendacoes"][0]["atleta_id"], 1)

    def test_recomendacao_mista_ordena_e_aplica_penalizacao(self):
        atletas = {
            "atletas": [
                {
                    "atleta_id": 1,
                    "apelido": "Seguro",
                    "clube_id": 10,
                    "posicao_id": 2,
                    "preco_num": 10.0,
                    "media_num": 7.0,
                },
                {
                    "atleta_id": 2,
                    "apelido": "Explosivo",
                    "clube_id": 20,
                    "posicao_id": 2,
                    "preco_num": 8.0,
                    "media_num": 7.5,
                },
            ]
        }

        historicos = {
            1: {
                "historico": [
                    {"entrou_em_campo": True, "pontuacao_calculada": 7.0},
                    {"entrou_em_campo": True, "pontuacao_calculada": 7.2},
                    {"entrou_em_campo": True, "pontuacao_calculada": 6.8},
                    {"entrou_em_campo": True, "pontuacao_calculada": 7.1},
                    {"entrou_em_campo": True, "pontuacao_calculada": 6.9},
                ]
            },
            2: {
                "historico": [
                    {"entrou_em_campo": True, "pontuacao_calculada": 9.5},
                    {"entrou_em_campo": True, "pontuacao_calculada": 2.0},
                    {"entrou_em_campo": True, "pontuacao_calculada": 8.5},
                ]
            },
        }

        with patch.object(recomendacoes_service, "get_atletas_mercado", return_value=atletas), patch.object(
            recomendacoes_service,
            "_precarregar_cache_historico_misto",
            return_value=(38, 5, {}),
        ), patch.object(
            recomendacoes_service,
            "get_historico_atleta",
            side_effect=lambda atleta_id, rodadas, **kwargs: historicos[atleta_id],
        ), patch.object(
            recomendacoes_service,
            "_carregar_clubes_seguro",
            return_value={10: {"nome": "Flamengo", "abreviacao": "FLA"}, 20: {"nome": "Palmeiras", "abreviacao": "PAL"}},
        ):
            resultado = recomendacoes_service.recomendacao_mista(posicao_id=2, limite=10, rodadas=5)

        self.assertEqual(resultado["criterio"], "misto")
        self.assertEqual(resultado["quantidade"], 2)
        self.assertEqual(resultado["recomendacoes"][0]["apelido"], "Seguro")
        self.assertAlmostEqual(resultado["recomendacoes"][0]["penalizacao_amostra"], 0.0)
        self.assertAlmostEqual(resultado["recomendacoes"][1]["penalizacao_amostra"], 0.2)
        self.assertGreater(
            resultado["recomendacoes"][0]["score_recomendacao"],
            resultado["recomendacoes"][1]["score_recomendacao"],
        )

    def test_recomendacao_mista_retorna_vazio_sem_historico_aproveitavel(self):
        atletas = {
            "atletas": [
                {
                    "atleta_id": 1,
                    "apelido": "SemHistorico",
                    "clube_id": 10,
                    "posicao_id": 2,
                    "preco_num": 10.0,
                    "media_num": 7.0,
                }
            ]
        }

        with patch.object(recomendacoes_service, "get_atletas_mercado", return_value=atletas), patch.object(
            recomendacoes_service,
            "_precarregar_cache_historico_misto",
            return_value=(38, 5, {}),
        ), patch.object(
            recomendacoes_service,
            "get_historico_atleta",
            return_value={"historico": [{"entrou_em_campo": False, "pontuacao_calculada": 5.0}]},
        ), patch.object(
            recomendacoes_service,
            "_carregar_clubes_seguro",
            return_value={},
        ):
            resultado = recomendacoes_service.recomendacao_mista(posicao_id=2, limite=10, rodadas=5)

        self.assertEqual(resultado["quantidade"], 0)
        self.assertEqual(resultado["recomendacoes"], [])

    def test_precarregar_cache_historico_misto_busca_rodadas_uma_vez(self):
        with patch.object(recomendacoes_service, "get_mercado_status", return_value={"rodada_atual": 7}), patch.object(
            recomendacoes_service,
            "get_pontuados_por_rodada",
            return_value={"atletas": {}},
        ) as mock_pontuados:
            rodada_atual, rodadas_consideradas, cache = recomendacoes_service._precarregar_cache_historico_misto(5)

        self.assertEqual(rodada_atual, 7)
        self.assertEqual(rodadas_consideradas, 5)
        self.assertEqual(len(cache), 5)
        self.assertEqual(mock_pontuados.call_count, 5)

    def test_recomendacao_confronto_hibrido_ordena_por_score_final(self):
        atletas_mercado = {
            "atletas": [
                {
                    "atleta_id": 1,
                    "apelido": "Atleta A",
                    "clube_id": 1,
                    "posicao_id": 2,
                    "preco_num": 12.0,
                    "media_num": 7.0,
                },
                {
                    "atleta_id": 2,
                    "apelido": "Atleta B",
                    "clube_id": 2,
                    "posicao_id": 2,
                    "preco_num": 10.0,
                    "media_num": 6.8,
                },
            ],
            "partidas": {
                "1": {"clube_casa_id": 1, "clube_visitante_id": 2}
            },
        }

        cache = {}
        for rodada in range(1, 11):
            cache[rodada] = {
                "atletas": {
                    f"20{rodada}": {"clube_id": 2, "posicao_id": 2, "entrou_em_campo": True, "pontuacao": 8.0},
                    f"10{rodada}": {"clube_id": 1, "posicao_id": 2, "entrou_em_campo": True, "pontuacao": 3.0},
                }
            }

        with patch.object(recomendacoes_service, "get_atletas_mercado", return_value=atletas_mercado), patch.object(
            recomendacoes_service,
            "_precarregar_cache_historico_misto",
            return_value=(10, 10, cache),
        ), patch.object(
            recomendacoes_service,
            "_carregar_clubes_seguro",
            return_value={
                1: {"nome": "Time A", "abreviacao": "A"},
                2: {"nome": "Time B", "abreviacao": "B"},
            },
        ):
            resultado = recomendacoes_service.recomendacao_confronto_hibrido(
                posicao_id=2,
                limite=10,
                janela_curta=5,
                janela_longa=10,
                peso_curta=0.7,
                peso_longa=0.3,
            )

        self.assertEqual(resultado["criterio"], "confronto_hibrido")
        self.assertEqual(resultado["quantidade"], 2)
        self.assertEqual(resultado["recomendacoes"][0]["atleta_id"], 1)
        self.assertEqual(resultado["recomendacoes"][0]["adversario_nome"], "Time B")
        self.assertIn("score_recomendacao", resultado["recomendacoes"][0])

    def test_recomendacao_confronto_hibrido_sem_adversario_usa_score_individual(self):
        atletas_mercado = {
            "atletas": [
                {
                    "atleta_id": 1,
                    "apelido": "Atleta A",
                    "clube_id": 1,
                    "posicao_id": 2,
                    "preco_num": 12.0,
                    "media_num": 7.0,
                }
            ],
            "partidas": {},
        }

        with patch.object(recomendacoes_service, "get_atletas_mercado", return_value=atletas_mercado), patch.object(
            recomendacoes_service,
            "_precarregar_cache_historico_misto",
            return_value=(10, 10, {}),
        ):
            resultado = recomendacoes_service.recomendacao_confronto_hibrido(posicao_id=2, limite=10)

        self.assertEqual(resultado["quantidade"], 1)
        self.assertEqual(resultado["recomendacoes"][0]["atleta_id"], 1)
        self.assertIsNone(resultado["recomendacoes"][0]["adversario_id"])

    def test_recomendacao_confronto_hibrido_busca_partidas_no_status_quando_mercado_nao_traz(self):
        atletas_mercado = {
            "atletas": [
                {
                    "atleta_id": 1,
                    "apelido": "Atleta A",
                    "clube_id": 1,
                    "posicao_id": 2,
                    "preco_num": 12.0,
                    "media_num": 7.0,
                }
            ],
            "partidas": {},
        }
        cache = {}
        for rodada in range(1, 6):
            cache[rodada] = {
                "atletas": {
                    f"20{rodada}": {"clube_id": 2, "posicao_id": 2, "entrou_em_campo": True, "pontuacao": 6.0},
                }
            }

        with patch.object(recomendacoes_service, "get_atletas_mercado", return_value=atletas_mercado), patch.object(
            recomendacoes_service,
            "_precarregar_cache_historico_misto",
            return_value=(5, 5, cache),
        ), patch.object(
            recomendacoes_service,
            "get_mercado_status",
            return_value={"partidas": {"1": {"clube_casa_id": 1, "clube_visitante_id": 2}}},
        ), patch.object(
            recomendacoes_service,
            "_carregar_clubes_seguro",
            return_value={1: {"nome": "Time A", "abreviacao": "A"}, 2: {"nome": "Time B", "abreviacao": "B"}},
        ):
            resultado = recomendacoes_service.recomendacao_confronto_hibrido(posicao_id=2, limite=10, janela_curta=5, janela_longa=5)

        self.assertEqual(resultado["quantidade"], 1)
        self.assertEqual(resultado["recomendacoes"][0]["adversario_id"], 2)

    def test_recomendacao_confronto_hibrido_busca_partidas_por_rodada_quando_status_sem_partidas(self):
        atletas_mercado = {
            "atletas": [
                {
                    "atleta_id": 1,
                    "apelido": "Atleta A",
                    "clube_id": 1,
                    "posicao_id": 2,
                    "preco_num": 12.0,
                    "media_num": 7.0,
                }
            ],
            "partidas": {},
        }
        cache = {}
        for rodada in range(1, 6):
            cache[rodada] = {
                "atletas": {
                    f"20{rodada}": {"clube_id": 2, "posicao_id": 2, "entrou_em_campo": True, "pontuacao": 6.0},
                }
            }

        with patch.object(recomendacoes_service, "get_atletas_mercado", return_value=atletas_mercado), patch.object(
            recomendacoes_service,
            "_precarregar_cache_historico_misto",
            return_value=(5, 5, cache),
        ), patch.object(
            recomendacoes_service,
            "get_mercado_status",
            return_value={"rodada_atual": 5, "partidas": {}},
        ), patch.object(
            recomendacoes_service,
            "get_partidas_por_rodada",
            return_value={"partidas": {"1": {"clube_casa_id": 1, "clube_visitante_id": 2}}},
        ), patch.object(
            recomendacoes_service,
            "_carregar_clubes_seguro",
            return_value={1: {"nome": "Time A", "abreviacao": "A"}, 2: {"nome": "Time B", "abreviacao": "B"}},
        ):
            resultado = recomendacoes_service.recomendacao_confronto_hibrido(posicao_id=2, limite=10, janela_curta=5, janela_longa=5)

        self.assertEqual(resultado["quantidade"], 1)
        self.assertEqual(resultado["recomendacoes"][0]["adversario_id"], 2)

    def test_recomendacoes_incluem_nomenclaturas_sem_remover_ids(self):
        atletas = {
            "atletas": [
                {
                    "atleta_id": 1,
                    "apelido": "Seguro",
                    "clube_id": 10,
                    "posicao_id": 2,
                    "preco_num": 10.0,
                    "media_num": 7.0,
                }
            ]
        }

        with patch.object(recomendacoes_service, "get_atletas_mercado", return_value=atletas), patch.object(
            recomendacoes_service,
            "_precarregar_cache_historico_misto",
            return_value=(38, 5, {}),
        ), patch.object(
            recomendacoes_service,
            "get_historico_atleta",
            return_value={"historico": [{"entrou_em_campo": True, "pontuacao_calculada": 7.0}]},
        ), patch.object(
            recomendacoes_service,
            "_carregar_clubes_seguro",
            return_value={10: {"nome": "Flamengo", "abreviacao": "FLA"}},
        ):
            resultado = recomendacoes_service.recomendacao_mista(posicao_id=2, limite=10, rodadas=5)

        item = resultado["recomendacoes"][0]
        self.assertEqual(item["clube_id"], 10)
        self.assertEqual(item["posicao_id"], 2)
        self.assertEqual(item["clube_nome"], "Flamengo")
        self.assertEqual(item["clube_sigla"], "FLA")
        self.assertEqual(item["posicao_nome"], "Lateral")


class RecomendacoesRouteTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()

    def test_get_recomendacoes_exige_criterio(self):
        response = self.client.get("/recomendacoes")

        self.assertEqual(response.status_code, 400)
        self.assertIn("criterio", response.get_json()["erro"])

    def test_get_recomendacoes_aceita_criterio_misto(self):
        payload = {
            "criterio": "misto",
            "perfil": "equilibrado",
            "rodadas": 5,
            "posicao_id": None,
            "limite": 10,
            "quantidade": 0,
            "recomendacoes": [],
        }

        with patch("app.routes.recomendacoes_routes.recomendacao_por_criterio", return_value=payload) as mock_recomendacao:
            response = self.client.get("/recomendacoes?criterio=misto&rodadas=5&limite=10")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["criterio"], "misto")
        mock_recomendacao.assert_called_once()

    def test_get_recomendacoes_aceita_criterio_confronto_hibrido(self):
        payload = {
            "criterio": "confronto_hibrido",
            "janela_curta": 5,
            "janela_longa": 10,
            "peso_curta": 0.7,
            "peso_longa": 0.3,
            "quantidade": 0,
            "recomendacoes": [],
        }

        with patch("app.routes.recomendacoes_routes.recomendacao_por_criterio", return_value=payload) as mock_recomendacao:
            response = self.client.get(
                "/recomendacoes?criterio=confronto_hibrido&janela_curta=5&janela_longa=10&peso_curta=0.7&peso_longa=0.3"
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["criterio"], "confronto_hibrido")
        mock_recomendacao.assert_called_once()

    def test_get_recomendacoes_aceita_criterio_valorizacao(self):
        payload = {
            "criterio": "valorizacao",
            "formula_minima": "pontos_minimos_valorizacao = preco_num * 0.45",
            "preco_max": 10.0,
            "posicao_id": None,
            "limite": 10,
            "quantidade": 0,
            "recomendacoes": [],
        }

        with patch("app.routes.recomendacoes_routes.recomendacao_por_criterio", return_value=payload) as mock_recomendacao:
            response = self.client.get("/recomendacoes?criterio=valorizacao&limite=10&preco_max=10")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["criterio"], "valorizacao")
        self.assertEqual(mock_recomendacao.call_args.kwargs["preco_max"], 10.0)
        mock_recomendacao.assert_called_once()


class DocsRouteTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()

    def test_docs_index_returns_links(self):
        response = self.client.get("/docs")

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertIn("arquivos", payload)
        self.assertEqual(payload["arquivos"]["openapi"], "/docs/openapi.yaml")

    def test_openapi_yaml_is_served(self):
        response = self.client.get("/docs/openapi.yaml")

        self.assertEqual(response.status_code, 200)
        self.assertIn("openapi: 3.0.3", response.get_data(as_text=True))

    def test_api_endpoints_markdown_is_served(self):
        response = self.client.get("/docs/api-endpoints")

        self.assertEqual(response.status_code, 200)
        self.assertIn("# Documentacao da API", response.get_data(as_text=True))


if __name__ == "__main__":
    unittest.main()
