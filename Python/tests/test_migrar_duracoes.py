from __future__ import annotations

import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from Python.migrar_duracoes import (
    ErroMigracaoDuracao,
    carregar_e_converter,
    descobrir_arquivos,
    horas_legadas_para_duracao,
    main,
    migrar_arquivo,
)


LEGADO = """classe: Tarefa
inicio: '2026-09-14T10:00:00-03:00'
fim: '2026-09-14T10:00:20-03:00'
pausas:
- classe: Pausa
  inicio: '2026-09-14T10:00:01-03:00'
  fim: '2026-09-14T10:00:14.828065-03:00'
  duracao: 0.003841129166666667
duracao: 0.001714426388888889
nome: teste
notas: ''
"""


class MigrarDuracoesTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temporario = tempfile.TemporaryDirectory()
        self.raiz = Path(self.temporario.name)
        self.arquivo = self.raiz / "Tarefas" / "Concluidas" / "tarefa.yaml"
        self.arquivo.parent.mkdir(parents=True)
        self.arquivo.write_text(LEGADO, encoding="utf-8")

    def tearDown(self) -> None:
        self.temporario.cleanup()

    def test_decimal_legado_arredonda_sem_ruido_binario(self) -> None:
        self.assertEqual(
            horas_legadas_para_duracao(0.003841129166666667), "00:00:14"
        )
        self.assertEqual(horas_legadas_para_duracao(27.034166666666668), "27:02:03")

    def test_percurso_converte_raiz_e_pausa_aninhada(self) -> None:
        dados, alterado = carregar_e_converter(self.arquivo)
        self.assertTrue(alterado)
        self.assertEqual(dados["duracao"], "00:00:06")
        self.assertEqual(dados["pausas"][0]["duracao"], "00:00:14")

    def test_rejeita_tag_campo_classe_negativo_e_texto_invalido(self) -> None:
        casos = (
            ("!!python/object/apply:os.system ['x']\n", "YAML inválido"),
            ("classe: Desconhecida\n", "classe ausente ou desconhecida"),
            ("classe: Pausa\nduracao: -1\n", "negativa"),
            ("classe: Pausa\nduracao: 1:2:3\n", "HH:MM:SS"),
            ("classe: Pausa\ncampo: x\n", "campo desconhecido"),
        )
        for texto, mensagem in casos:
            with self.subTest(mensagem=mensagem):
                self.arquivo.write_text(texto, encoding="utf-8")
                original = self.arquivo.read_bytes()
                with self.assertRaisesRegex(ErroMigracaoDuracao, mensagem):
                    migrar_arquivo(self.arquivo)
                self.assertEqual(self.arquivo.read_bytes(), original)

    def test_check_nao_escreve_migracao_e_segunda_execucao_idempotente(self) -> None:
        original = self.arquivo.read_bytes()
        self.assertTrue(migrar_arquivo(self.arquivo, verificar=True))
        self.assertEqual(self.arquivo.read_bytes(), original)
        self.assertTrue(migrar_arquivo(self.arquivo))
        migrado = self.arquivo.read_bytes()
        self.assertFalse(migrar_arquivo(self.arquivo))
        self.assertEqual(self.arquivo.read_bytes(), migrado)

    def test_falha_atomica_preserva_bytes(self) -> None:
        original = self.arquivo.read_bytes()
        with patch("Python.migrar_duracoes.os.replace", side_effect=OSError("falha")):
            with self.assertRaises(OSError):
                migrar_arquivo(self.arquivo)
        self.assertEqual(self.arquivo.read_bytes(), original)
        self.assertEqual(list(self.arquivo.parent.glob(".tarefa.yaml.*.tmp")), [])

    def test_descoberta_e_cli_check(self) -> None:
        outro = self.raiz / "Tarefas" / "Pausas" / "pausa.yml"
        outro.parent.mkdir(parents=True)
        outro.write_text("classe: Pausa\nduracao: null\n", encoding="utf-8")
        encontrados = descobrir_arquivos(self.raiz, [])
        self.assertEqual(encontrados, sorted([self.arquivo, outro], key=lambda p: str(p).casefold()))
        saida = io.StringIO()
        with redirect_stdout(saida):
            codigo = main(["--raiz", str(self.raiz), "--check"])
        self.assertEqual(codigo, 1)
        self.assertIn("PENDENTE", saida.getvalue())
        self.assertIn("ATUALIZADO", saida.getvalue())


if __name__ == "__main__":
    unittest.main()
