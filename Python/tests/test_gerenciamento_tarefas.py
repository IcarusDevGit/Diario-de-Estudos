from __future__ import annotations

import io
import re
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from Python.Classes import Pausa, SessaoEstudo, SessaoExercicio, Tarefa
from Python.cli import main
from Python.duracao import duracao_para_segundos, formatar_intervalo
from Python.gerenciamento_tarefas import (
    ErroGerenciamento,
    GerenciadorTarefas,
    carregar_fuso_horario,
    interpretar_fuso_horario,
)
from Python.serializacao_yaml import ler_yaml, salvar_yaml


FUSO = timezone(-timedelta(hours=3), name="UTC-03:00")


class GerenciamentoTarefasTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temporario = tempfile.TemporaryDirectory()
        self.raiz = Path(self.temporario.name)
        self.instante = datetime(2026, 9, 14, 9, 30, 15, tzinfo=FUSO)
        self.gerenciador = GerenciadorTarefas(
            self.raiz, relogio=lambda: self.instante, fuso=FUSO
        )

    def tearDown(self) -> None:
        self.temporario.cleanup()

    def test_configuracao_do_fuso_valida_ausente_duplicada_e_invalida(self) -> None:
        arquivo = self.raiz / ".env"
        arquivo.write_text(
            "# configuração local\nOUTRA=ignorada\nFUSO_HORARIO=UTC-03:00\n",
            encoding="utf-8",
        )
        self.assertEqual(
            carregar_fuso_horario(self.raiz).utcoffset(None), timedelta(hours=-3)
        )
        self.assertEqual(
            interpretar_fuso_horario("UTC+05:30").utcoffset(None),
            timedelta(hours=5, minutes=30),
        )
        casos = (
            ("OUTRA=x\n", "ausente"),
            ("FUSO_HORARIO=UTC-03:00\nFUSO_HORARIO=UTC+01:00\n", "duplicada"),
            ("FUSO_HORARIO=America/Sao_Paulo\n", "inválido"),
            ("FUSO_HORARIO=UTC+24:00\n", "menor que 24"),
        )
        for conteudo, mensagem in casos:
            with self.subTest(mensagem=mensagem):
                arquivo.write_text(conteudo, encoding="utf-8")
                with self.assertRaisesRegex(ErroGerenciamento, mensagem):
                    GerenciadorTarefas(self.raiz)
                self.assertFalse((self.raiz / "Tarefas").exists())

    def test_caminhos_relogio_e_inicio_das_tres_classes(self) -> None:
        casos = (Tarefa, SessaoEstudo, SessaoExercicio)
        for classe in casos:
            with self.subTest(classe=classe.__name__):
                caminho = self.gerenciador.iniciar_atividade(classe)
                self.assertEqual(
                    caminho,
                    self.raiz / "Tarefas" / "Tarefa em andamento" / "tarefa.yaml",
                )
                atividade = ler_yaml(caminho)
                self.assertIs(type(atividade), classe)
                self.assertEqual(atividade.inicio, self.instante)
                self.assertEqual(atividade.inicio.tzinfo, timezone(timedelta(hours=-3)))
                self.assertIsNone(atividade.fim)
                self.assertIsNone(atividade.duracao)
                caminho.unlink()

    def test_relogio_sem_fuso_e_classe_nao_permitida(self) -> None:
        invalido = GerenciadorTarefas(
            self.raiz, relogio=lambda: datetime(2026, 9, 14, 10), fuso=FUSO
        )
        with self.assertRaisesRegex(ErroGerenciamento, "fuso horário"):
            invalido.iniciar_atividade()
        with self.assertRaisesRegex(ErroGerenciamento, "não permitida"):
            self.gerenciador.iniciar_atividade(Pausa)  # type: ignore[arg-type]

    def test_descoberta_zero_um_multiplos_e_ordem_deterministica(self) -> None:
        diretorio = self.gerenciador.diretorio_ativas
        self.assertEqual(self.gerenciador._arquivos_yaml(diretorio), [])
        diretorio.mkdir(parents=True)
        (diretorio / "ignorar.txt").write_text("x", encoding="utf-8")
        (diretorio / "b.yml").write_text("x", encoding="utf-8")
        (diretorio / "A.yaml").write_text("x", encoding="utf-8")
        self.assertEqual(
            [item.name for item in self.gerenciador._arquivos_yaml(diretorio)],
            ["A.yaml", "b.yml"],
        )
        antes = {item.name: item.read_bytes() for item in diretorio.iterdir()}
        with self.assertRaisesRegex(ErroGerenciamento, "múltiplos arquivos"):
            self.gerenciador.iniciar_atividade()
        self.assertEqual(
            {item.name: item.read_bytes() for item in diretorio.iterdir()}, antes
        )

    def test_segunda_tarefa_valida_e_yaml_invalido_sao_preservados(self) -> None:
        caminho = self.gerenciador.iniciar_atividade(Tarefa, nome="primeira")
        original = caminho.read_bytes()
        with self.assertRaisesRegex(ErroGerenciamento, "já existe Tarefa"):
            self.gerenciador.iniciar_atividade(SessaoEstudo)
        self.assertEqual(caminho.read_bytes(), original)
        caminho.write_text("classe: [", encoding="utf-8")
        invalido = caminho.read_bytes()
        with self.assertRaisesRegex(ErroGerenciamento, re.escape(str(caminho))):
            self.gerenciador.iniciar_atividade()
        self.assertEqual(caminho.read_bytes(), invalido)

    def test_iniciar_pausa_exige_tarefa_e_impede_segunda(self) -> None:
        with self.assertRaisesRegex(ErroGerenciamento, "não existe tarefa"):
            self.gerenciador.iniciar_pausa()
        self.gerenciador.iniciar_atividade()
        caminho = self.gerenciador.iniciar_pausa()
        pausa = ler_yaml(caminho)
        self.assertIs(type(pausa), Pausa)
        self.assertEqual(pausa.inicio, self.instante)
        original = caminho.read_bytes()
        with self.assertRaisesRegex(ErroGerenciamento, "já existe pausa"):
            self.gerenciador.iniciar_pausa()
        self.assertEqual(caminho.read_bytes(), original)

    def test_finalizar_pausa_incorpora_em_ordem_e_remove_transitorio(self) -> None:
        tarefa_path = self.gerenciador.iniciar_atividade()
        primeira = Pausa(
            inicio=self.instante - timedelta(hours=2),
            fim=self.instante - timedelta(hours=1),
        )
        primeira.duracao = "01:00:00"
        tarefa = ler_yaml(tarefa_path)
        tarefa.pausas.append(primeira)
        salvar_yaml(tarefa, tarefa_path)
        pausa_path = self.gerenciador.iniciar_pausa()
        self.instante += timedelta(minutes=30)
        resultado = self.gerenciador.finalizar_pausa()
        self.assertEqual(resultado, tarefa_path)
        self.assertFalse(pausa_path.exists())
        tarefa = ler_yaml(tarefa_path)
        self.assertEqual(len(tarefa.pausas), 2)
        self.assertEqual(tarefa.pausas[1].duracao, "00:30:00")

    def test_finalizar_pausa_sem_pausa_e_falha_de_gravacao_preservam_estado(self) -> None:
        tarefa_path = self.gerenciador.iniciar_atividade()
        with self.assertRaisesRegex(ErroGerenciamento, "não existe pausa"):
            self.gerenciador.finalizar_pausa()
        pausa_path = self.gerenciador.iniciar_pausa()
        tarefa_original = tarefa_path.read_bytes()
        pausa_original = pausa_path.read_bytes()
        with patch(
            "Python.gerenciamento_tarefas.salvar_yaml",
            side_effect=OSError("falha simulada"),
        ):
            with self.assertRaisesRegex(ErroGerenciamento, "finalizar pausa"):
                self.gerenciador.finalizar_pausa()
        self.assertEqual(tarefa_path.read_bytes(), tarefa_original)
        self.assertEqual(pausa_path.read_bytes(), pausa_original)

    def test_duracao_na_linha_do_tempo_meia_noite_e_erro(self) -> None:
        inicio = datetime(2026, 9, 14, 23, 30, tzinfo=FUSO)
        fim = datetime(2026, 9, 15, 0, 30, tzinfo=FUSO)
        self.assertEqual(formatar_intervalo(inicio, fim, caminho="teste"), "01:00:00")
        antes = datetime(2026, 11, 1, 1, 30, tzinfo=timezone(timedelta(hours=-4)))
        depois = datetime(2026, 11, 1, 1, 30, tzinfo=timezone(timedelta(hours=-5)))
        self.assertEqual(formatar_intervalo(antes, depois, caminho="teste"), "01:00:00")
        with self.assertRaisesRegex(ErroGerenciamento, "anterior"):
            self.gerenciador._preparar_pausa(Pausa(inicio=fim), inicio, Path("teste"))

    def test_finalizar_tarefa_preserva_campos_e_usa_nome_nao_conflitante(self) -> None:
        inicio = self.instante
        tarefa_path = self.gerenciador.iniciar_atividade(SessaoEstudo, nome="Python")
        tarefa = ler_yaml(tarefa_path)
        tarefa.notas = "anotação manual"
        salvar_yaml(tarefa, tarefa_path)
        base = self.gerenciador.diretorio_concluidas / (
            "2026-09-14_09-30-15_SessaoEstudo.yaml"
        )
        base.parent.mkdir(parents=True)
        base.write_bytes(b"preservar")
        self.instante = inicio + timedelta(hours=2)
        destino = self.gerenciador.finalizar_atividade()
        self.assertEqual(destino.name, "2026-09-14_09-30-15_SessaoEstudo_2.yaml")
        self.assertEqual(base.read_bytes(), b"preservar")
        self.assertFalse(tarefa_path.exists())
        concluida = ler_yaml(destino)
        self.assertIs(type(concluida), SessaoEstudo)
        self.assertEqual(concluida.notas, "anotação manual")
        self.assertEqual(concluida.duracao, "02:00:00")

    def test_finalizar_tarefa_durante_pausa_calcula_duracao_liquida(self) -> None:
        inicio = self.instante
        tarefa_path = self.gerenciador.iniciar_atividade()
        self.instante += timedelta(hours=1)
        pausa_path = self.gerenciador.iniciar_pausa()
        self.instante += timedelta(minutes=30)
        destino = self.gerenciador.finalizar_atividade()
        self.assertFalse(tarefa_path.exists())
        self.assertFalse(pausa_path.exists())
        tarefa = ler_yaml(destino)
        self.assertEqual(tarefa.inicio, inicio)
        self.assertEqual(tarefa.duracao, "01:00:00")
        self.assertEqual(len(tarefa.pausas), 1)
        self.assertEqual(tarefa.pausas[0].duracao, "00:30:00")

    def test_finalizacao_rejeita_pausa_invalida_sem_alterar_arquivos(self) -> None:
        tarefa_path = self.gerenciador.iniciar_atividade()
        pausa_path = self.gerenciador.iniciar_pausa()
        tarefa = ler_yaml(tarefa_path)
        pausa = Pausa(inicio=self.instante, fim=self.instante + timedelta(hours=1))
        pausa.duracao = "03:00:00"
        tarefa.pausas.append(pausa)
        salvar_yaml(tarefa, tarefa_path)
        antes_tarefa = tarefa_path.read_bytes()
        antes_pausa = pausa_path.read_bytes()
        with self.assertRaisesRegex(ErroGerenciamento, "não corresponde"):
            self.gerenciador.finalizar_atividade()
        self.assertEqual(tarefa_path.read_bytes(), antes_tarefa)
        self.assertEqual(pausa_path.read_bytes(), antes_pausa)
        self.assertEqual(list(self.gerenciador.diretorio_concluidas.glob("*.yaml")), [])

    def test_compensacao_quando_remocao_da_pausa_falha(self) -> None:
        tarefa_path = self.gerenciador.iniciar_atividade()
        self.instante += timedelta(minutes=10)
        pausa_path = self.gerenciador.iniciar_pausa()
        original_tarefa = tarefa_path.read_bytes()
        original_pausa = pausa_path.read_bytes()
        unlink_real = Path.unlink

        def unlink_controlado(caminho: Path, *args: object, **kwargs: object) -> None:
            if caminho == pausa_path:
                raise OSError("falha simulada")
            unlink_real(caminho, *args, **kwargs)

        with patch.object(Path, "unlink", autospec=True, side_effect=unlink_controlado):
            with self.assertRaisesRegex(ErroGerenciamento, "finalizar tarefa"):
                self.gerenciador.finalizar_atividade()
        self.assertEqual(tarefa_path.read_bytes(), original_tarefa)
        self.assertEqual(pausa_path.read_bytes(), original_pausa)
        self.assertEqual(list(self.gerenciador.diretorio_concluidas.glob("*.yaml")), [])


class CLITestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temporario = tempfile.TemporaryDirectory()
        self.raiz = Path(self.temporario.name)
        (self.raiz / ".env").write_text(
            "FUSO_HORARIO=UTC-03:00\n", encoding="utf-8"
        )

    def tearDown(self) -> None:
        self.temporario.cleanup()

    def chamar(self, *argumentos: str) -> tuple[int, str, str]:
        saida = io.StringIO()
        erro = io.StringIO()
        with redirect_stdout(saida), redirect_stderr(erro):
            codigo = main(["--raiz", str(self.raiz), *argumentos])
        return codigo, saida.getvalue(), erro.getvalue()

    def test_cli_despacha_tarefa_sessoes_pausa_e_erros(self) -> None:
        for argumentos, classe in (
            (("iniciar", "tarefa", "--nome", "Geral"), Tarefa),
            (("iniciar", "sessao", "estudo"), SessaoEstudo),
            (("iniciar", "sessao", "exercicio"), SessaoExercicio),
        ):
            with self.subTest(argumentos=argumentos):
                codigo, saida, erro = self.chamar(*argumentos)
                self.assertEqual((codigo, erro), (0, ""))
                caminho = Path(saida.strip())
                self.assertTrue(caminho.exists())
                self.assertIs(type(ler_yaml(caminho)), classe)
                caminho.unlink()
        codigo, _, erro = self.chamar("iniciar", "pausa")
        self.assertNotEqual(codigo, 0)
        self.assertIn("não existe tarefa", erro)

    def test_fluxo_cli_com_multiplas_pausas_e_conclusao_durante_pausa(self) -> None:
        codigo, _, _ = self.chamar("iniciar", "sessao", "estudo", "--nome", "Teste")
        self.assertEqual(codigo, 0)
        for _ in range(2):
            self.assertEqual(self.chamar("iniciar", "pausa")[0], 0)
            self.assertEqual(self.chamar("finalizar", "pausa")[0], 0)
        self.assertEqual(self.chamar("iniciar", "pausa")[0], 0)
        codigo, saida, erro = self.chamar("finalizar", "tarefa")
        self.assertEqual((codigo, erro), (0, ""))
        concluida = ler_yaml(Path(saida.strip()))
        self.assertEqual(len(concluida.pausas), 3)
        self.assertGreaterEqual(duracao_para_segundos(concluida.duracao), 0)


if __name__ == "__main__":
    unittest.main()
