from __future__ import annotations

import tempfile
import unittest
import re
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path

from Python.Classes import (
    Pausa,
    RegistroDiario,
    Relatorio,
    SessaoEstudo,
    SessaoExercicio,
    Tarefa,
)
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
        self.assertTrue(texto.startswith("classe: Tarefa\ndia: null\ninicio: null\n"))
        self.assertIn("fim: null", texto)
        self.assertIn("duracao: null", texto)
        self.assertIn("Revisão", texto)
        self.assertTrue(texto.endswith("\n"))

    def test_ida_e_volta_dos_modelos_polimorficos(self) -> None:
        fuso = timezone(timedelta(hours=-3))
        pausa = Pausa(
            inicio=datetime(2026, 9, 13, 10, 0, tzinfo=fuso),
            fim=datetime(2026, 9, 13, 10, 15, tzinfo=fuso),
        )
        pausa.duracao = "00:15:00"
        relatorio_generico = Relatorio(
            data=date(2026, 9, 13),
            nome="Revisão geral: Ação & Atenção",
            notas="Observações com acentuação e cedilha: ótimo progresso!",
        )
        registro_diario_completo = RegistroDiario(
            data=date(2026, 9, 13),
            nome="Dia produtivo",
            notas="Notas herdadas de Relatorio",
            acordei=time(7, 30),
            concentracao=4,
        )
        objetos = [
            pausa,
            Tarefa(nome="Tarefa", pausas=[pausa]),
            SessaoEstudo(nome="Estudo", concentracao=5),
            SessaoExercicio(nome="Exercício", performance=4),
            relatorio_generico,
            registro_diario_completo,
        ]
        for objeto in objetos:
            with self.subTest(classe=type(objeto).__name__):
                texto = modelo_para_yaml(objeto)
                self.assertNotIn(r"\u", texto)
                carregado = yaml_para_modelo(texto)
                self.assertIs(type(carregado), type(objeto))
                self.assertEqual(modelo_para_dados(carregado), modelo_para_dados(objeto))

        texto_generico = modelo_para_yaml(relatorio_generico)
        self.assertTrue(texto_generico.startswith("classe: Relatorio\n"))
        self.assertIn("data: '2026-09-13'\n", texto_generico)
        self.assertIn("Revisão geral: Ação & Atenção", texto_generico)

    def test_registro_diario_legado_sem_nome_e_notas(self) -> None:
        yaml_legado = (
            "classe: RegistroDiario\n"
            "data: '2026-09-15'\n"
            "acordei: '07:00'\n"
            "levantei_da_cama: '07:10'\n"
            "folga: false\n"
        )
        modelo = yaml_para_modelo(yaml_legado)
        self.assertIsInstance(modelo, RegistroDiario)
        self.assertIsNone(modelo.nome)
        self.assertIsNone(modelo.notas)
        self.assertEqual(modelo.data, date(2026, 9, 15))
        self.assertEqual(modelo.acordei, time(7, 0))

        # Ida e volta determinística
        serializado1 = modelo_para_yaml(modelo)
        reconstruido = yaml_para_modelo(serializado1)
        serializado2 = modelo_para_yaml(reconstruido)
        self.assertEqual(serializado1, serializado2)

        # Não reescreve arquivos legados existentes durante leitura
        with tempfile.TemporaryDirectory() as temp_dir:
            caminho = Path(temp_dir) / "legado.yaml"
            caminho.write_text(yaml_legado, encoding="utf-8")
            mtime_antes = caminho.stat().st_mtime_ns
            conteudo_antes = caminho.read_bytes()
            carregado = ler_yaml(caminho)
            self.assertIsInstance(carregado, RegistroDiario)
            self.assertEqual(caminho.read_bytes(), conteudo_antes)
            self.assertEqual(caminho.stat().st_mtime_ns, mtime_antes)

    def test_datetime_preserva_deslocamento(self) -> None:
        inicio = datetime(2026, 9, 13, 12, 30, tzinfo=timezone(timedelta(hours=-3)))
        carregada = yaml_para_modelo(modelo_para_yaml(Tarefa(inicio=inicio)))
        self.assertEqual(carregada.inicio, inicio)
        self.assertEqual(carregada.inicio.utcoffset(), timedelta(hours=-3))

    def test_horario_de_relatorio_usa_minutos_sem_arredondar(self) -> None:
        relatorio = RegistroDiario(acordei=time(7, 8, 59, 999999))
        texto = modelo_para_yaml(relatorio)
        self.assertIn("acordei: 07:08\n", texto)
        self.assertNotIn("07:08:59", texto)
        self.assertEqual(yaml_para_modelo(texto).acordei, time(7, 8))

    def test_horarios_legados_sao_normalizados_e_invalidos_rejeitados(self) -> None:
        for valor in ("07:08", "07:08:59", "07:08:59.123456"):
            with self.subTest(valor=valor):
                relatorio = yaml_para_modelo(
                    f"classe: RegistroDiario\nacordei: '{valor}'\n"
                )
                self.assertEqual(relatorio.acordei, time(7, 8))
                self.assertIn("acordei: 07:08\n", modelo_para_yaml(relatorio))
        for valor in ("7:08", "07:8", "07:08:59Z", "07:08:59.1234567"):
            with self.subTest(valor=valor):
                with self.assertRaisesRegex(ErroSerializacaoYAML, r"\$\.acordei"):
                    yaml_para_modelo(
                        f"classe: RegistroDiario\nacordei: '{valor}'\n"
                    )

    def test_duracao_e_datetime_mantem_segundos(self) -> None:
        inicio = datetime(
            2026, 9, 15, 7, 8, 59, 123456, tzinfo=timezone(timedelta(hours=-3))
        )
        tarefa = Tarefa(inicio=inicio)
        tarefa.duracao = "00:01:59"
        texto = modelo_para_yaml(tarefa)
        self.assertIn("07:08:59.123456-03:00", texto)
        self.assertIn("duracao: 00:01:59", texto)
        carregada = yaml_para_modelo(texto)
        self.assertEqual(carregada.inicio, inicio)
        self.assertEqual(carregada.duracao, "00:01:59")

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
        tarefa = yaml_para_modelo("classe: Tarefa\nduracao: '27:02:03'\n")
        self.assertEqual(tarefa.duracao, "27:02:03")
        with self.assertRaisesRegex(ErroSerializacaoYAML, r"\$\.duracao"):
            yaml_para_modelo("classe: Tarefa\nduracao: 1.5\n")
        with self.assertRaisesRegex(ErroSerializacaoYAML, r"\$\.duracao"):
            yaml_para_modelo("classe: Tarefa\nduracao: '1:2:3'\n")

    def test_segunda_serializacao_e_deterministica(self) -> None:
        original = modelo_para_yaml(SessaoEstudo(nome="Python", concentracao=3))
        self.assertEqual(modelo_para_yaml(yaml_para_modelo(original)), original)
        self.assertEqual(modelo_para_yaml(SessaoEstudo()), modelo_para_yaml(SessaoEstudo()))

    def test_avaliacoes_intermediarias_e_inteiros_legados(self) -> None:
        legado = yaml_para_modelo("classe: SessaoEstudo\nconcentracao: 3\n")
        self.assertEqual(legado.concentracao, 3.0)
        self.assertIs(type(legado.concentracao), float)
        self.assertIn("concentracao: 3.0\n", modelo_para_yaml(legado))

        intermediaria = yaml_para_modelo(
            "classe: SessaoEstudo\nconcentracao: 3.5\n"
        )
        self.assertEqual(intermediaria.concentracao, 3.5)
        serializado = modelo_para_yaml(intermediaria)
        self.assertIn("concentracao: 3.5\n", serializado)
        self.assertEqual(modelo_para_yaml(yaml_para_modelo(serializado)), serializado)

    def test_avaliacoes_rejeitam_passo_texto_e_booleano(self) -> None:
        casos = ("2.3", "'3.5'", "'3,5'", "true")
        for valor in casos:
            with self.subTest(valor=valor):
                with self.assertRaisesRegex(
                    ErroSerializacaoYAML, r"\$\.concentracao"
                ):
                    yaml_para_modelo(
                        f"classe: SessaoEstudo\nconcentracao: {valor}\n"
                    )

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
