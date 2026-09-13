from __future__ import annotations

import tempfile
import unittest
import re
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path

from Python.Classes import Pausa, RegistroDiario, SessaoEstudo, SessaoExercicio, Tarefa
from Python.serializacao_yaml import (
    ErroSerializacaoYAML,
    ler_yaml,
    modelo_para_dados,
    modelo_para_yaml,
    salvar_yaml,
    yaml_para_modelo,
)


class SerializacaoYAMLTestCase(unittest.TestCase):
    def test_tarefa_incompleta_unicode_e_ordem(self) -> None:
        texto = modelo_para_yaml(Tarefa(nome="Revisão", notas="Atenção à sintaxe"))
        self.assertTrue(texto.startswith("classe: Tarefa\ninicio: null\n"))
        self.assertIn("fim: null", texto)
        self.assertIn("duracao: null", texto)
        self.assertIn("Revisão", texto)
        self.assertTrue(texto.endswith("\n"))

    def test_ida_e_volta_das_cinco_classes(self) -> None:
        fuso = timezone(timedelta(hours=-3))
        pausa = Pausa(
            inicio=datetime(2026, 9, 13, 10, 0, tzinfo=fuso),
            fim=datetime(2026, 9, 13, 10, 15, tzinfo=fuso),
        )
        pausa.duracao = 0.25
        objetos = [
            pausa,
            Tarefa(nome="Tarefa", pausas=[pausa]),
            SessaoEstudo(nome="Estudo", concentracao=5),
            SessaoExercicio(nome="Exercício", performance=4),
            RegistroDiario(
                data=date(2026, 9, 13),
                acordei=time(7, 30),
                concentracao=4,
            ),
        ]
        for objeto in objetos:
            with self.subTest(classe=type(objeto).__name__):
                carregado = yaml_para_modelo(modelo_para_yaml(objeto))
                self.assertIs(type(carregado), type(objeto))
                self.assertEqual(modelo_para_dados(carregado), modelo_para_dados(objeto))

    def test_datetime_preserva_deslocamento(self) -> None:
        inicio = datetime(2026, 9, 13, 12, 30, tzinfo=timezone(timedelta(hours=-3)))
        carregada = yaml_para_modelo(modelo_para_yaml(Tarefa(inicio=inicio)))
        self.assertEqual(carregada.inicio, inicio)
        self.assertEqual(carregada.inicio.utcoffset(), timedelta(hours=-3))

    def test_pausas_aninhadas_e_listas_independentes(self) -> None:
        texto = modelo_para_yaml(Tarefa(pausas=[Pausa(), Pausa()]))
        self.assertEqual(texto.count("classe: Pausa"), 2)
        primeira = yaml_para_modelo(texto)
        segunda = yaml_para_modelo(texto)
        self.assertTrue(all(isinstance(item, Pausa) for item in primeira.pausas))
        primeira.pausas.append(Pausa())
        self.assertEqual(len(segunda.pausas), 2)

    def test_campos_omitidos_usam_defaults_e_calculado_e_carregado(self) -> None:
        tarefa = yaml_para_modelo("classe: Tarefa\nnome: teste\n")
        self.assertEqual(tarefa.pausas, [])
        self.assertIsNone(tarefa.inicio)
        tarefa = yaml_para_modelo("classe: Tarefa\nduracao: 1.5\n")
        self.assertEqual(tarefa.duracao, 1.5)

    def test_segunda_serializacao_e_deterministica(self) -> None:
        original = modelo_para_yaml(SessaoEstudo(nome="Python", concentracao=3))
        self.assertEqual(modelo_para_yaml(yaml_para_modelo(original)), original)
        self.assertEqual(modelo_para_yaml(SessaoEstudo()), modelo_para_yaml(SessaoEstudo()))

    def test_rejeita_classe_ausente_desconhecida_e_incompativel(self) -> None:
        casos = [
            ("nome: teste\n", "$.classe"),
            ("classe: Outra\n", "classe desconhecida"),
            (
                "classe: Tarefa\npausas:\n- classe: SessaoEstudo\n",
                "$.pausas[0].classe",
            ),
        ]
        for texto, mensagem in casos:
            with self.subTest(mensagem=mensagem):
                with self.assertRaisesRegex(ErroSerializacaoYAML, re.escape(mensagem)):
                    yaml_para_modelo(texto)

    def test_rejeita_tipos_escalares_e_temporais_invalidos(self) -> None:
        casos = [
            ("classe: SessaoEstudo\nconcentracao: '4'\n", "$.concentracao"),
            ("classe: SessaoEstudo\nconcentracao: true\n", "$.concentracao"),
            ("classe: RegistroDiario\ndata: 13/09/2026\n", "$.data"),
            ("classe: RegistroDiario\nacordei: 25:00\n", "$.acordei"),
        ]
        for texto, caminho in casos:
            with self.subTest(caminho=caminho):
                with self.assertRaisesRegex(ErroSerializacaoYAML, re.escape(caminho)):
                    yaml_para_modelo(texto)

    def test_rejeita_raiz_chaves_campos_e_tags_inseguros(self) -> None:
        casos = [
            ("- item\n", "$"),
            ("classe: Tarefa\nnome: um\nnome: dois\n", "chave duplicada"),
            ("classe: Tarefa\n1: valor\n", "chaves devem ser texto"),
            ("classe: Tarefa\ndesconhecido: 1\n", "$.desconhecido"),
            ("!!python/object/apply:os.system ['echo inseguro']\n", "YAML inválido"),
        ]
        for texto, mensagem in casos:
            with self.subTest(mensagem=mensagem):
                with self.assertRaises(ErroSerializacaoYAML) as contexto:
                    yaml_para_modelo(texto)
                self.assertIn(mensagem, str(contexto.exception))

    def test_erro_aninhado_e_arquivo_de_origem(self) -> None:
        with tempfile.TemporaryDirectory() as diretorio:
            caminho = Path(diretorio) / "tarefa.yaml"
            caminho.write_text(
                "classe: Tarefa\npausas:\n- classe: Pausa\n  campo: x\n",
                encoding="utf-8",
            )
            with self.assertRaises(ErroSerializacaoYAML) as contexto:
                ler_yaml(caminho)
            mensagem = str(contexto.exception)
            self.assertIn(str(caminho), mensagem)
            self.assertIn("$.pausas[0].campo", mensagem)

    def test_salvar_atomico_e_preservar_em_falha(self) -> None:
        with tempfile.TemporaryDirectory() as diretorio:
            caminho = Path(diretorio) / "modelo.yaml"
            caminho.write_bytes(b"anterior\n")
            invalida = Tarefa()
            invalida.inicio = "não é datetime"
            with self.assertRaises(ErroSerializacaoYAML):
                salvar_yaml(invalida, caminho)
            self.assertEqual(caminho.read_bytes(), b"anterior\n")
            self.assertEqual(list(caminho.parent.glob(".modelo.yaml.*.tmp")), [])

            valida = Tarefa(nome="Nova")
            salvar_yaml(valida, caminho)
            self.assertEqual(ler_yaml(caminho), valida)
            self.assertEqual(list(caminho.parent.glob(".modelo.yaml.*.tmp")), [])


if __name__ == "__main__":
    unittest.main()
