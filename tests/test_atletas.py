import unittest
from unittest.mock import patch

from app import create_app


class AtletasClubeRouteTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()

    def test_lista_atletas_do_clube_filtra_e_ordena_por_preco(self):
        mercado = {
            "atletas": [
                {"atleta_id": 10, "apelido": "A", "clube_id": 1, "posicao_id": 5, "preco_num": 8.0, "media_num": 5.0},
                {"atleta_id": 11, "apelido": "B", "clube_id": 1, "posicao_id": 4, "preco_num": 12.0, "media_num": 6.0},
                {"atleta_id": 12, "apelido": "Outro", "clube_id": 2, "posicao_id": 5, "preco_num": 9.0, "media_num": 5.5},
            ]
        }

        with patch("app.routes.atletas_routers.get_atletas_mercado", return_value=mercado), \
             patch("app.utils.formatadores.get_clube", return_value=None), \
             patch("app.utils.formatadores.get_posicao", return_value=None):
            resp = self.client.get("/atletas/clube/1")

        self.assertEqual(resp.status_code, 200)
        payload = resp.get_json()
        self.assertEqual(payload["clube_id"], 1)
        self.assertEqual(payload["quantidade"], 2)
        self.assertEqual([a["atleta_id"] for a in payload["atletas"]], [11, 10])

    def test_lista_atletas_do_clube_sem_atletas_retorna_lista_vazia(self):
        with patch("app.routes.atletas_routers.get_atletas_mercado", return_value={"atletas": []}):
            resp = self.client.get("/atletas/clube/99")

        self.assertEqual(resp.status_code, 200)
        payload = resp.get_json()
        self.assertEqual(payload["clube_id"], 99)
        self.assertEqual(payload["quantidade"], 0)
        self.assertEqual(payload["atletas"], [])


if __name__ == "__main__":
    unittest.main()
