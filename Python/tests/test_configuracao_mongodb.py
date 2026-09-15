from __future__ import annotations

import io
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import MagicMock, call, patch

from pymongo.errors import ServerSelectionTimeoutError

from Python.cli import main
from Python.configuracao_mongodb import (
    ErroConfiguracaoMongoDB,
    TEMPO_LIMITE_SELECAO_MS,
    carregar_mongodb_database,
    carregar_mongodb_uri,
    criar_cliente_mongodb,
    diagnosticar_mongodb,
)


URI_SECRETA = "mongodb+srv://usuario-secreto:senha-secreta@cluster-secreto.example/"


class ConfiguracaoMongoDBTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temporario = tempfile.TemporaryDirectory()
        self.raiz = Path(self.temporario.name)

    def tearDown(self) -> None:
        self.temporario.cleanup()

    def escrever_env(self, conteudo: str) -> None:
        (self.raiz / ".env").write_text(conteudo, encoding="utf-8")

    def test_carrega_uri_valida_sem_criar_cliente(self) -> None:
        self.escrever_env(f"OUTRA=x\nMONGODB_URI={URI_SECRETA}\n")
        fabrica = MagicMock()
        self.assertEqual(carregar_mongodb_uri(self.raiz), URI_SECRETA)
        fabrica.assert_not_called()

    def test_rejeita_configuracoes_invalidas_sem_revelar_segredos(self) -> None:
        casos = (
            ("OUTRA=x\n", "ausente"),
            ("MONGODB_URI=\n", "vazia"),
            (
                f"MONGODB_URI={URI_SECRETA}\nMONGODB_URI=mongodb://outra\n",
                "duplicada",
            ),
            ("MONGODB_URI=https://usuario:senha@host-secreto\n", "mongodb://"),
        )
        for conteudo, mensagem in casos:
            with self.subTest(mensagem=mensagem):
                self.escrever_env(conteudo)
                with self.assertRaisesRegex(ErroConfiguracaoMongoDB, mensagem) as erro:
                    carregar_mongodb_uri(self.raiz)
                texto = str(erro.exception)
                for segredo in (URI_SECRETA, "usuario", "senha", "host-secreto"):
                    self.assertNotIn(segredo, texto)

    def test_arquivo_env_ausente(self) -> None:
        with self.assertRaisesRegex(ErroConfiguracaoMongoDB, "não foi possível ler"):
            carregar_mongodb_uri(self.raiz)

    def test_carrega_database_valida_ausente_duplicada_e_vazia(self) -> None:
        arquivo = self.raiz / ".env"
        arquivo.write_text("MONGODB_DATABASE=diario_estudos\n", encoding="utf-8")
        self.assertEqual(carregar_mongodb_database(self.raiz), "diario_estudos")
        for conteudo, mensagem in (
            ("OUTRA=x\n", "ausente"),
            ("MONGODB_DATABASE=\n", "vazia"),
            (
                "MONGODB_DATABASE=diario_estudos\nMONGODB_DATABASE=outra\n",
                "duplicada",
            ),
        ):
            with self.subTest(mensagem=mensagem):
                arquivo.write_text(conteudo, encoding="utf-8")
                with self.assertRaisesRegex(ErroConfiguracaoMongoDB, mensagem):
                    carregar_mongodb_database(self.raiz)

    def test_diagnostico_nao_exige_database(self) -> None:
        self.escrever_env(f"MONGODB_URI={URI_SECRETA}\n")
        cliente = MagicMock()
        diagnosticar_mongodb(self.raiz, fabrica=MagicMock(return_value=cliente))
        cliente.admin.command.assert_called_once_with({"ping": 1})

    def test_cria_cliente_com_stable_api_e_timeout_sem_operacoes(self) -> None:
        self.escrever_env(f"MONGODB_URI={URI_SECRETA}\n")
        cliente = MagicMock()
        fabrica = MagicMock(return_value=cliente)
        resultado = criar_cliente_mongodb(self.raiz, fabrica=fabrica)
        self.assertIs(resultado, cliente)
        fabrica.assert_called_once()
        argumentos, opcoes = fabrica.call_args
        self.assertEqual(argumentos, (URI_SECRETA,))
        self.assertEqual(opcoes["server_api"].version, "1")
        self.assertEqual(
            opcoes["serverSelectionTimeoutMS"], TEMPO_LIMITE_SELECAO_MS
        )
        cliente.admin.command.assert_not_called()
        cliente.close.assert_not_called()

    def test_falha_ao_criar_cliente_e_sanitizada(self) -> None:
        self.escrever_env(f"MONGODB_URI={URI_SECRETA}\n")
        fabrica = MagicMock(side_effect=ValueError(URI_SECRETA))
        with self.assertRaises(ErroConfiguracaoMongoDB) as erro:
            criar_cliente_mongodb(self.raiz, fabrica=fabrica)
        self.assertNotIn(URI_SECRETA, str(erro.exception))
        self.assertNotIn("senha-secreta", str(erro.exception))

    def test_diagnostico_executa_somente_ping_e_fecha_no_sucesso(self) -> None:
        self.escrever_env(f"MONGODB_URI={URI_SECRETA}\n")
        cliente = MagicMock()
        fabrica = MagicMock(return_value=cliente)
        diagnosticar_mongodb(self.raiz, fabrica=fabrica)
        cliente.admin.command.assert_called_once_with({"ping": 1})
        cliente.close.assert_called_once_with()
        self.assertEqual(cliente.method_calls, [
            call.admin.command({"ping": 1}),
            call.close(),
        ])

    def test_diagnostico_fecha_na_falha_e_sanitiza_erro(self) -> None:
        self.escrever_env(f"MONGODB_URI={URI_SECRETA}\n")
        cliente = MagicMock()
        cliente.admin.command.side_effect = ServerSelectionTimeoutError(URI_SECRETA)
        with self.assertRaises(ErroConfiguracaoMongoDB) as erro:
            diagnosticar_mongodb(self.raiz, fabrica=MagicMock(return_value=cliente))
        cliente.close.assert_called_once_with()
        texto = str(erro.exception)
        self.assertIn("rede, acesso e credenciais", texto)
        self.assertNotIn(URI_SECRETA, texto)
        self.assertNotIn("cluster-secreto", texto)


class ConfiguracaoMongoDBCLITestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temporario = tempfile.TemporaryDirectory()
        self.raiz = Path(self.temporario.name)
        (self.raiz / ".env").write_text(
            f"MONGODB_URI={URI_SECRETA}\n", encoding="utf-8"
        )

    def tearDown(self) -> None:
        self.temporario.cleanup()

    def chamar(self) -> tuple[int, str, str]:
        saida, erro = io.StringIO(), io.StringIO()
        with redirect_stdout(saida), redirect_stderr(erro):
            codigo = main(
                ["--raiz", str(self.raiz), "diagnosticar", "mongodb"]
            )
        return codigo, saida.getvalue(), erro.getvalue()

    def test_cli_diagnostica_com_sucesso_e_usa_raiz(self) -> None:
        with patch("Python.cli.diagnosticar_mongodb") as diagnosticar:
            codigo, saida, erro = self.chamar()
        self.assertEqual(codigo, 0)
        self.assertEqual(erro, "")
        self.assertIn("Conexão com MongoDB estabelecida", saida)
        diagnosticar.assert_called_once_with(self.raiz)
        self.assertNotIn(URI_SECRETA, saida)

    def test_cli_falha_sem_revelar_uri(self) -> None:
        with patch(
            "Python.cli.diagnosticar_mongodb",
            side_effect=ErroConfiguracaoMongoDB("falha sanitizada"),
        ):
            codigo, saida, erro = self.chamar()
        self.assertNotEqual(codigo, 0)
        self.assertEqual(saida, "")
        self.assertIn("falha sanitizada", erro)
        for segredo in (URI_SECRETA, "usuario-secreto", "senha-secreta"):
            self.assertNotIn(segredo, erro)


if __name__ == "__main__":
    unittest.main()
