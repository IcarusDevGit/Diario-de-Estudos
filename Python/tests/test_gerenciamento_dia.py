from __future__ import annotations

import io
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

from pymongo.errors import ServerSelectionTimeoutError

from Python.Classes import RegistroDiario, Tarefa
from Python.cli import main
from Python.gerenciamento_dia import (
    COLLECTION_REGISTROS_DIARIOS,
    ErroGerenciamentoDia,
    GerenciadorDia,
    consultar_fui_dormir_anterior,
)
from Python.gerenciamento_tarefas import ErroGerenciamento
from Python.serializacao_yaml import ler_yaml, salvar_yaml


FUSO = timezone(-timedelta(hours=3), name="UTC-03:00")
INSTANTE = datetime(2026, 9, 15, 23, 41, 52, 987654, tzinfo=FUSO)
URI_SECRETA = "mongodb+srv://usuario:senha@cluster-secreto.example/"


def cliente_com_documentos(documentos: list[dict[str, object]]) -> tuple[MagicMock, MagicMock, MagicMock]:
    cliente = MagicMock()
    database = MagicMock()
    collection = MagicMock()
    cursor = MagicMock()
    cursor.limit.return_value = documentos
    collection.find.return_value = cursor
    cliente.__getitem__.return_value = database
    database.__getitem__.return_value = collection
    return cliente, collection, cursor


class ConsultaHistoricoTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temporario = tempfile.TemporaryDirectory()
        self.raiz = Path(self.temporario.name)
        (self.raiz / ".env").write_text(
            f"MONGODB_URI={URI_SECRETA}\nMONGODB_DATABASE=diario_estudos\n",
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.temporario.cleanup()

    def consultar(self, documentos: list[dict[str, object]]) -> tuple[time | None, MagicMock, MagicMock, MagicMock]:
        cliente, collection, cursor = cliente_com_documentos(documentos)
        resultado = consultar_fui_dormir_anterior(
            self.raiz,
            date(2026, 9, 14),
            fabrica=MagicMock(return_value=cliente),
        )
        return resultado, cliente, collection, cursor

    def test_consulta_por_data_com_projecao_limite_e_sem_escrita(self) -> None:
        resultado, cliente, collection, cursor = self.consultar(
            [{"relatorios": [{"classe": "RegistroDiario", "fui_dormir": "23:10:05"}]}]
        )
        self.assertEqual(resultado, time(23, 10))
        cliente.__getitem__.assert_called_once_with("diario_estudos")
        cliente.__getitem__.return_value.__getitem__.assert_called_once_with(
            COLLECTION_REGISTROS_DIARIOS
        )
        collection.find.assert_called_once_with(
            {"data": "2026-09-14"}, {"_id": 0, "relatorios": 1}
        )
        cursor.limit.assert_called_once_with(2)
        cliente.close.assert_called_once_with()
        self.assertFalse(any("insert" in str(chamada).lower() for chamada in collection.method_calls))
        self.assertFalse(any("index" in str(chamada).lower() for chamada in collection.method_calls))

    def test_historico_ausente_retorna_none(self) -> None:
        resultado, cliente, _, _ = self.consultar([])
        self.assertIsNone(resultado)
        cliente.close.assert_called_once_with()

    def test_historico_novo_e_legado_sao_normalizados_ao_minuto(self) -> None:
        for valor in ("23:10", "23:10:59", "23:10:59.999999"):
            with self.subTest(valor=valor):
                resultado, cliente, _, _ = self.consultar(
                    [{"relatorios": [{"classe": "RegistroDiario", "fui_dormir": valor}]}]
                )
                self.assertEqual(resultado, time(23, 10))
                cliente.close.assert_called_once_with()

    def test_rejeita_horario_ausente_invalido_e_duplicidade(self) -> None:
        for documentos, mensagem in (
            ([{}], "relatorios"),
            ([{"relatorios": [{"classe": "RegistroDiario", "fui_dormir": None}]}], "fui_dormir"),
            ([{"relatorios": [{"classe": "RegistroDiario", "fui_dormir": "25:00:00"}]}], "fui_dormir"),
            ([{"relatorios": [{"classe": "RegistroDiario", "fui_dormir": "23:1"}]}], "fui_dormir"),
            (
                [{"relatorios": []}, {"relatorios": []}],
                "mais de um relatório",
            ),
        ):
            with self.subTest(documentos=documentos):
                cliente, _, _ = cliente_com_documentos(documentos)
                with self.assertRaisesRegex(ErroGerenciamentoDia, mensagem):
                    consultar_fui_dormir_anterior(
                        self.raiz,
                        date(2026, 9, 14),
                        fabrica=MagicMock(return_value=cliente),
                    )
                cliente.close.assert_called_once_with()

    def test_falha_mongodb_e_sanitizada_e_fecha_cliente(self) -> None:
        cliente, collection, _ = cliente_com_documentos([])
        collection.find.side_effect = ServerSelectionTimeoutError(URI_SECRETA)
        with self.assertRaises(ErroGerenciamentoDia) as erro:
            consultar_fui_dormir_anterior(
                self.raiz,
                date(2026, 9, 14),
                fabrica=MagicMock(return_value=cliente),
            )
        cliente.close.assert_called_once_with()
        texto = str(erro.exception)
        for segredo in (URI_SECRETA, "usuario", "senha", "cluster-secreto"):
            self.assertNotIn(segredo, texto)


class GerenciadorDiaTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temporario = tempfile.TemporaryDirectory()
        self.raiz = Path(self.temporario.name)
        self.consulta = MagicMock(return_value=None)
        self.tarefas = MagicMock()
        self.tarefas.atividade_ativa.return_value = None
        self.persistencia = MagicMock()
        self.gerenciador = GerenciadorDia(
            self.raiz,
            relogio=lambda: INSTANTE,
            fuso=FUSO,
            consulta_sono=self.consulta,
            gerenciador_tarefas=self.tarefas,
            persistencia=self.persistencia,
        )

    def tearDown(self) -> None:
        self.temporario.cleanup()

    @property
    def caminho(self) -> Path:
        return self.raiz / "Relatórios" / "RD-2026-09-15.yaml"

    def relatorio_pronto(self) -> RegistroDiario:
        return RegistroDiario(
            data=date(2026, 9, 15),
            acordei=time(7),
            levantei_da_cama=time(7, 10),
            folga=False,
        )

    def test_inicia_com_nome_data_e_historico_usando_um_instante(self) -> None:
        self.consulta.return_value = time(23, 5, 9)
        caminho = self.gerenciador.iniciar_dia()
        self.assertEqual(caminho, self.caminho)
        self.consulta.assert_called_once_with(date(2026, 9, 14))
        relatorio = ler_yaml(caminho)
        self.assertIs(type(relatorio), RegistroDiario)
        self.assertEqual(relatorio.data, date(2026, 9, 15))
        self.assertEqual(relatorio.dormi_dia_anterior, time(23, 5))
        self.assertIsNone(relatorio.acordei)
        self.assertIsNone(relatorio.fui_dormir)

    def test_relatorio_existente_e_preservado_sem_consulta(self) -> None:
        self.caminho.parent.mkdir(parents=True)
        self.caminho.write_bytes(b"preservar")
        with self.assertRaisesRegex(ErroGerenciamentoDia, "já existe"):
            self.gerenciador.iniciar_dia()
        self.assertEqual(self.caminho.read_bytes(), b"preservar")
        self.consulta.assert_not_called()

    def test_falha_de_consulta_nao_cria_relatorio(self) -> None:
        self.consulta.side_effect = ErroGerenciamentoDia("consulta falhou")
        with self.assertRaisesRegex(ErroGerenciamentoDia, "consulta falhou"):
            self.gerenciador.iniciar_dia()
        self.assertFalse(self.caminho.exists())

    def test_carregamento_rejeita_ausente_yaml_classe_e_data(self) -> None:
        with self.assertRaisesRegex(ErroGerenciamentoDia, "não encontrado"):
            self.gerenciador.finalizar_dia()

        self.caminho.parent.mkdir(parents=True)
        self.caminho.write_text("classe: [", encoding="utf-8")
        for preparacao, mensagem in (
            (lambda: None, str(self.caminho)),
            (lambda: salvar_yaml(Tarefa(), self.caminho), "incompatível"),
            (
                lambda: salvar_yaml(
                    RegistroDiario(data=date(2026, 9, 14)), self.caminho
                ),
                "diverge",
            ),
        ):
            with self.subTest(mensagem=mensagem):
                preparacao()
                original = self.caminho.read_bytes()
                with self.assertRaises(ErroGerenciamentoDia) as erro:
                    self.gerenciador.finalizar_dia()
                self.assertIn(mensagem, str(erro.exception))
                self.assertEqual(self.caminho.read_bytes(), original)

    def test_lista_campos_obrigatorios_e_aceita_false(self) -> None:
        salvar_yaml(RegistroDiario(data=date(2026, 9, 15), folga=False), self.caminho)
        original = self.caminho.read_bytes()
        with self.assertRaises(ErroGerenciamentoDia) as erro:
            self.gerenciador.finalizar_dia()
        texto = str(erro.exception)
        self.assertIn("acordei", texto)
        self.assertIn("levantei_da_cama", texto)
        self.assertNotIn("folga", texto)
        self.assertEqual(self.caminho.read_bytes(), original)

    def test_atividade_ativa_e_estado_inconsistente_preservam_relatorio(self) -> None:
        salvar_yaml(self.relatorio_pronto(), self.caminho)
        original = self.caminho.read_bytes()
        for efeito, mensagem in (
            (((Path("tarefa.yaml"), Tarefa())), "em andamento"),
            (ErroGerenciamento("múltiplos arquivos"), "múltiplos arquivos"),
        ):
            with self.subTest(mensagem=mensagem):
                self.tarefas.atividade_ativa.reset_mock()
                if isinstance(efeito, Exception):
                    self.tarefas.atividade_ativa.side_effect = efeito
                    self.tarefas.atividade_ativa.return_value = None
                else:
                    self.tarefas.atividade_ativa.side_effect = None
                    self.tarefas.atividade_ativa.return_value = efeito
                with self.assertRaisesRegex(ErroGerenciamentoDia, mensagem):
                    self.gerenciador.finalizar_dia()
                self.assertEqual(self.caminho.read_bytes(), original)

    def test_finaliza_preserva_campos_e_arredonda_horario_ao_segundo(self) -> None:
        relatorio = self.relatorio_pronto()
        relatorio.motivacao = 4
        salvar_yaml(relatorio, self.caminho)
        resultado = self.gerenciador.finalizar_dia()
        self.assertEqual(resultado, self.caminho)
        finalizado = ler_yaml(self.caminho)
        self.assertEqual(finalizado.fui_dormir, time(23, 41))
        self.assertIn("fui_dormir: '23:41'", self.caminho.read_text(encoding="utf-8"))
        self.assertEqual(finalizado.motivacao, 4)
        self.assertFalse(finalizado.folga)

    def test_falha_de_gravacao_preserva_bytes(self) -> None:
        salvar_yaml(self.relatorio_pronto(), self.caminho)
        original = self.caminho.read_bytes()
        with patch(
            "Python.gerenciamento_dia.salvar_yaml", side_effect=OSError("falha")
        ):
            with self.assertRaisesRegex(ErroGerenciamentoDia, "finalizar"):
                self.gerenciador.finalizar_dia()
        self.assertEqual(self.caminho.read_bytes(), original)

    def test_segunda_finalizacao_preserva_horario(self) -> None:
        relatorio = self.relatorio_pronto()
        relatorio.fui_dormir = time(22, 30)
        salvar_yaml(relatorio, self.caminho)
        original = self.caminho.read_bytes()
        with self.assertRaisesRegex(ErroGerenciamentoDia, "já foi finalizado"):
            self.gerenciador.finalizar_dia()
        self.assertEqual(self.caminho.read_bytes(), original)


class GerenciamentoDiaCLITestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temporario = tempfile.TemporaryDirectory()
        self.raiz = Path(self.temporario.name)
        (self.raiz / ".env").write_text(
            "FUSO_HORARIO=UTC-03:00\nMONGODB_URI=mongodb://teste\nMONGODB_DATABASE=diario_estudos\n",
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.temporario.cleanup()

    def chamar(self, *argumentos: str) -> tuple[int, str, str]:
        saida, erro = io.StringIO(), io.StringIO()
        with redirect_stdout(saida), redirect_stderr(erro):
            codigo = main(["--raiz", str(self.raiz), *argumentos])
        return codigo, saida.getvalue(), erro.getvalue()

    def test_fluxo_cli_sem_historico_preenchimento_bloqueio_e_finalizacao(self) -> None:
        with patch(
            "Python.gerenciamento_dia.consultar_fui_dormir_anterior",
            return_value=None,
        ):
            codigo, saida, erro = self.chamar("iniciar", "dia")
        self.assertEqual((codigo, erro), (0, ""))
        caminho = Path(saida.strip())
        self.assertEqual(caminho.name, "RD-" + date.today().isoformat() + ".yaml")

        relatorio = ler_yaml(caminho)
        relatorio.acordei = time(7)
        relatorio.levantei_da_cama = time(7, 10)
        relatorio.folga = False
        salvar_yaml(relatorio, caminho)

        tarefa = self.raiz / "Tarefas" / "Tarefa em andamento" / "tarefa.yaml"
        salvar_yaml(Tarefa(inicio=datetime.now(FUSO), nome="ativa"), tarefa)
        codigo, _, erro = self.chamar("finalizar", "dia")
        self.assertNotEqual(codigo, 0)
        self.assertIn("em andamento", erro)
        tarefa.unlink()

        with patch("Python.gerenciamento_dia.persistir_dia"):
            codigo, saida, erro = self.chamar("finalizar", "dia")
        self.assertEqual((codigo, erro), (0, ""))
        self.assertEqual(Path(saida.strip()), caminho)
        self.assertIsNotNone(ler_yaml(caminho).fui_dormir)

    def test_cli_propaga_historico_e_sanitiza_falha(self) -> None:
        with patch(
            "Python.gerenciamento_dia.consultar_fui_dormir_anterior",
            return_value=time(22, 15),
        ):
            codigo, saida, erro = self.chamar("iniciar", "dia")
        self.assertEqual((codigo, erro), (0, ""))
        self.assertEqual(ler_yaml(Path(saida.strip())).dormi_dia_anterior, time(22, 15))

        Path(saida.strip()).unlink()
        with patch(
            "Python.gerenciamento_dia.consultar_fui_dormir_anterior",
            side_effect=ErroGerenciamentoDia("falha sanitizada"),
        ):
            codigo, saida, erro = self.chamar("iniciar", "dia")
        self.assertNotEqual(codigo, 0)
        self.assertEqual(saida, "")
        self.assertIn("falha sanitizada", erro)
        self.assertNotIn("mongodb://teste", erro)


if __name__ == "__main__":
    unittest.main()
