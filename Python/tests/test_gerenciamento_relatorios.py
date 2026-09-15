from __future__ import annotations

import io
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from Python.Classes import Relatorio
from Python.cli import main
from Python.gerenciamento_relatorios import (
    ErroGerenciamentoRelatorio,
    GerenciadorRelatorios,
    normalizar_slug,
)
from Python.serializacao_yaml import ler_yaml


FUSO = timezone(-timedelta(hours=3), name="UTC-03:00")


class GerenciamentoRelatoriosTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temporario = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporario.cleanup)
        self.raiz = Path(self.temporario.name)
        (self.raiz / ".env").write_text("FUSO_HORARIO=UTC-03:00\n", encoding="utf-8")
        self.gerenciador = GerenciadorRelatorios(self.raiz)

    def test_normalizar_slug_com_acentos_simbolos_e_fallback(self) -> None:
        casos = [
            ("Revisão de Projeto", "revisao-de-projeto"),
            ("Ação & Reação 100%!", "acao-reacao-100"),
            ("   Espaços nas bordas   ", "espacos-nas-bordas"),
            ("---traços---", "tracos"),
            ("!@#$%^&*()", "relatorio"),
            ("🎉🎉", "relatorio"),
            ("ÁÉÍÓÚ çãõ", "aeiou-cao"),
        ]
        for entrada, esperado in casos:
            with self.subTest(entrada=entrada):
                self.assertEqual(normalizar_slug(entrada), esperado)

    def test_cria_relatorio_com_data_padrao_pelo_fuso(self) -> None:
        instante = datetime(2026, 9, 15, 14, 30, tzinfo=FUSO)
        with patch("Python.gerenciamento_relatorios.datetime") as mock_dt:
            mock_dt.now.return_value = instante
            caminho = self.gerenciador.criar_relatorio("Revisão do Dia")

        self.assertTrue(caminho.exists())
        self.assertEqual(caminho.name, "RG-2026-09-15-revisao-do-dia.yaml")

        relatorio = ler_yaml(caminho)
        self.assertIsInstance(relatorio, Relatorio)
        self.assertEqual(relatorio.data, date(2026, 9, 15))
        self.assertEqual(relatorio.nome, "Revisão do Dia")
        self.assertIsNone(relatorio.notas)

        # Verifica formato do arquivo no disco
        conteudo = caminho.read_text(encoding="utf-8")
        self.assertTrue(conteudo.startswith("classe: Relatorio\n"))
        self.assertIn("data: '2026-09-15'\n", conteudo)
        self.assertIn("nome: Revisão do Dia\n", conteudo)
        self.assertIn("notas: null\n", conteudo)

    def test_cria_relatorio_com_data_explicita(self) -> None:
        caminho = self.gerenciador.criar_relatorio(
            "Planejamento Semanal", data=date(2026, 9, 14)
        )
        self.assertEqual(caminho.name, "RG-2026-09-14-planejamento-semanal.yaml")
        relatorio = ler_yaml(caminho)
        self.assertEqual(relatorio.data, date(2026, 9, 14))

        # Aceita também string no formato ISO YYYY-MM-DD
        caminho2 = self.gerenciador.criar_relatorio("Outro", data="2026-09-10")
        self.assertEqual(caminho2.name, "RG-2026-09-10-outro.yaml")
        self.assertEqual(ler_yaml(caminho2).data, date(2026, 9, 10))

    def test_rejeita_nome_vazio_ou_em_branco(self) -> None:
        for nome in ("", "   ", "\t\n  "):
            with self.subTest(nome=repr(nome)):
                with self.assertRaisesRegex(
                    ErroGerenciamentoRelatorio, "nome.*não pode ser vazio"
                ):
                    self.gerenciador.criar_relatorio(nome)
        self.assertFalse((self.raiz / "Relatórios").exists())

    def test_rejeita_configuracao_temporal_invalida_ou_ausente(self) -> None:
        (self.raiz / ".env").write_text("FUSO_HORARIO=Invalido\n", encoding="utf-8")
        with self.assertRaises(ErroGerenciamentoRelatorio):
            self.gerenciador.criar_relatorio("Teste")

        (self.raiz / ".env").unlink()
        with self.assertRaises(ErroGerenciamentoRelatorio):
            self.gerenciador.criar_relatorio("Teste")

    def test_rejeita_data_invalida(self) -> None:
        for data_invalida in ("2026-99-99", "invalida", "15/09/2026", 12345):
            with self.subTest(data=data_invalida):
                with self.assertRaisesRegex(
                    ErroGerenciamentoRelatorio, "data inválida"
                ):
                    self.gerenciador.criar_relatorio("Teste", data=data_invalida)

    def test_colisao_gera_sufixo_incremental_sem_sobrescrita(self) -> None:
        data_relatorio = date(2026, 9, 15)
        primeiro = self.gerenciador.criar_relatorio(
            "Revisão", data=data_relatorio
        )
        self.assertEqual(primeiro.name, "RG-2026-09-15-revisao.yaml")
        conteudo_primeiro = primeiro.read_bytes()

        # Nome equivalente gera mesmo slug e colide deterministicamente
        segundo = self.gerenciador.criar_relatorio(
            "revisão!", data=data_relatorio
        )
        self.assertEqual(segundo.name, "RG-2026-09-15-revisao-2.yaml")

        terceiro = self.gerenciador.criar_relatorio(
            "REVISÃO", data=data_relatorio
        )
        self.assertEqual(terceiro.name, "RG-2026-09-15-revisao-3.yaml")

        # O primeiro arquivo não foi sobrescrito
        self.assertEqual(primeiro.read_bytes(), conteudo_primeiro)

    def test_falha_de_escrita_nao_deixa_arquivo_parcial(self) -> None:
        diretorio = self.raiz / "Relatórios"
        diretorio.mkdir(parents=True, exist_ok=True)
        with patch(
            "tempfile.NamedTemporaryFile", side_effect=OSError("disco cheio")
        ):
            with self.assertRaises(ErroGerenciamentoRelatorio):
                self.gerenciador.criar_relatorio("Falha", data=date(2026, 9, 15))

        # Nenhum arquivo permanente nem temporário resta no diretório
        arquivos = list(diretorio.glob("*"))
        self.assertEqual(arquivos, [])

    def test_cli_criar_relatorio_sucesso_e_caminho_impresso(self) -> None:
        saida, erro = io.StringIO(), io.StringIO()
        with redirect_stdout(saida), redirect_stderr(erro):
            codigo = main(
                [
                    "--raiz",
                    str(self.raiz),
                    "criar",
                    "relatorio",
                    "Anotações de Estudo",
                    "--data",
                    "2026-09-15",
                ]
            )
        self.assertEqual(codigo, 0)
        self.assertEqual(erro.getvalue(), "")
        caminho_gerado = Path(saida.getvalue().strip())
        self.assertTrue(caminho_gerado.exists())
        self.assertEqual(
            caminho_gerado.name, "RG-2026-09-15-anotacoes-de-estudo.yaml"
        )

    def test_cli_criar_relatorio_falhas_e_codigos_de_saida(self) -> None:
        # Nome vazio
        saida, erro = io.StringIO(), io.StringIO()
        with redirect_stdout(saida), redirect_stderr(erro):
            codigo = main(
                ["--raiz", str(self.raiz), "criar", "relatorio", "   "]
            )
        self.assertEqual(codigo, 1)
        self.assertIn("não pode ser vazio", erro.getvalue())

        # Data inválida
        saida, erro = io.StringIO(), io.StringIO()
        with redirect_stdout(saida), redirect_stderr(erro):
            codigo = main(
                [
                    "--raiz",
                    str(self.raiz),
                    "criar",
                    "relatorio",
                    "Válido",
                    "--data",
                    "9999-99-99",
                ]
            )
        self.assertEqual(codigo, 1)
        self.assertIn("data inválida", erro.getvalue())

    def test_fluxo_completo_diretorio_temporario(self) -> None:
        from Python.Classes import RegistroDiario
        from Python.persistencia_dia import montar_retrato
        from Python.serializacao_yaml import salvar_yaml

        data_hoje = date(2026, 9, 15)
        instante = datetime(2026, 9, 15, 10, 0, tzinfo=FUSO)

        # 1. Salva RegistroDiario finalizado para data_hoje
        salvar_yaml(
            RegistroDiario(
                data=data_hoje,
                acordei=time(7, 0),
                levantei_da_cama=time(7, 15),
                folga=False,
                fui_dormir=time(23, 0),
            ),
            self.raiz / "Relatórios" / f"RD-{data_hoje.isoformat()}.yaml",
        )

        # 2. Cria relatório genérico com data padrão (fuso)
        with patch("Python.gerenciamento_relatorios.datetime") as mock_dt:
            mock_dt.now.return_value = instante
            caminho_padrao = self.gerenciador.criar_relatorio("Revisão de Estudos")
        self.assertEqual(caminho_padrao.name, "RG-2026-09-15-revisao-de-estudos.yaml")

        # 3. Cria relatório com data explícita (dia anterior)
        caminho_ontem = self.gerenciador.criar_relatorio(
            "Planejamento Semanal", data="2026-09-14"
        )
        self.assertEqual(caminho_ontem.name, "RG-2026-09-14-planejamento-semanal.yaml")

        # 4. Provoca colisão para a data padrão
        with patch("Python.gerenciamento_relatorios.datetime") as mock_dt:
            mock_dt.now.return_value = instante
            caminho_colisao = self.gerenciador.criar_relatorio("revisão-de-estudos")
        self.assertEqual(caminho_colisao.name, "RG-2026-09-15-revisao-de-estudos-2.yaml")

        # 5. Carrega os YAMLs e verifica conteúdos e nomes
        rel1 = ler_yaml(caminho_padrao)
        self.assertEqual(rel1.nome, "Revisão de Estudos")
        self.assertEqual(rel1.data, data_hoje)
        self.assertIsNone(rel1.notas)

        rel_colisao = ler_yaml(caminho_colisao)
        self.assertEqual(rel_colisao.nome, "revisão-de-estudos")
        self.assertEqual(rel_colisao.data, data_hoje)

        rel_ontem = ler_yaml(caminho_ontem)
        self.assertEqual(rel_ontem.nome, "Planejamento Semanal")
        self.assertEqual(rel_ontem.data, date(2026, 9, 14))

        # 6. Monta o retrato do dia de hoje
        retrato = montar_retrato(self.raiz, data_hoje)
        self.assertEqual(retrato["data"], "2026-09-15")
        self.assertEqual(len(retrato["relatorios"]), 3)

        classes_relatorios = [r["classe"] for r in retrato["relatorios"]]
        self.assertEqual(classes_relatorios.count("Relatorio"), 2)
        self.assertEqual(classes_relatorios.count("RegistroDiario"), 1)

        nomes_relatorios = {r.get("nome") for r in retrato["relatorios"]}
        self.assertIn("Revisão de Estudos", nomes_relatorios)
        self.assertIn("revisão-de-estudos", nomes_relatorios)
        self.assertNotIn("Planejamento Semanal", nomes_relatorios)


if __name__ == "__main__":
    unittest.main()
