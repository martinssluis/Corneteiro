import unittest
from unittest.mock import patch

from app import create_app
from app.services import recomendacoes_service


class RecomendacoesServiceTestCase(unittest.TestCase):
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
