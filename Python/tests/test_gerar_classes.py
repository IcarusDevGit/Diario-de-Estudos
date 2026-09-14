from __future__ import annotations

import contextlib
import copy
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from dataclasses import fields
from pathlib import Path
from unittest import mock

from Python import gerar_classes


class GeradorTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temporario = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporario.cleanup)
        self.raiz = Path(self.temporario.name)
        self.esquemas = self.raiz / "Esquemas"
        self.esquemas.mkdir()
        self.destino = self.raiz / "Classes" / "geradas.py"

    def escrever(self, nome: str, documento: object) -> Path:
        caminho = self.esquemas / nome
        caminho.write_text(
            json.dumps(documento, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return caminho

    def esquema(self, classe: str = "Base", **extras: object) -> dict[str, object]:
        documento: dict[str, object] = {
            "versao": 1,
            "classe": classe,
            "campos": {"nome": {"tipo": "str"}},
        }
        documento.update(extras)
        return documento

    def carregar_modulo(self):
        nome = f"modelo_teste_{id(self)}"
        spec = importlib.util.spec_from_file_location(nome, self.destino)
        assert spec is not None and spec.loader is not None
        modulo = importlib.util.module_from_spec(spec)
        sys.modules[nome] = modulo
        try:
            spec.loader.exec_module(modulo)
        finally:
            sys.modules.pop(nome, None)
        return modulo

    def test_carrega_os_cinco_esquemas_reais(self) -> None:
        modelos = gerar_classes.carregar_esquemas(gerar_classes.DIRETORIO_ESQUEMAS)
        self.assertEqual(
            {modelo.classe for modelo in modelos},
            {"Pausa", "Tarefa", "SessaoEstudo", "SessaoExercicio", "RegistroDiario"},
        )

    def test_json_invalido_identifica_arquivo(self) -> None:
        (self.esquemas / "quebrado.json").write_text("{", encoding="utf-8")
        with self.assertRaisesRegex(gerar_classes.ErroEsquema, "quebrado.json"):
            gerar_classes.carregar_esquemas(self.esquemas)

    def test_rejeita_herda_de_versao_e_raiz_invalidas(self) -> None:
        casos = [
            (self.esquema(herda_de="Base"), "classe_mae"),
            (self.esquema(versao=2), "versão 1"),
            ([], "raiz"),
        ]
        for indice, (documento, mensagem) in enumerate(casos):
            with self.subTest(indice=indice):
                for arquivo in self.esquemas.glob("*.json"):
                    arquivo.unlink()
                self.escrever("caso.json", documento)
                with self.assertRaisesRegex(gerar_classes.ErroEsquema, mensagem):
                    gerar_classes.carregar_esquemas(self.esquemas)

    def test_valida_identificadores_duplicidade_tipos_atributos_e_referencias(self) -> None:
        casos = [
            ([self.esquema("classe inválida")], "nome de classe inválido"),
            ([self.esquema("Base"), self.esquema("Base")], "classe duplicada"),
            ([self.esquema(campos={"x": {"tipo": "decimal"}})], "tipo desconhecido"),
            ([self.esquema(campos={"x": {"tipo": "str", "extra": 1}})], "atributos desconhecidos"),
            ([self.esquema(campos={"x": {"tipo": "list", "itens": "Ausente"}})], "itens inexistente"),
            ([self.esquema(classe_mae="Ausente")], "classe_mae inexistente"),
            ([self.esquema(campos={"x": {"tipo": "int", "minimo": 5, "maximo": 1}})], "minimo"),
        ]
        for indice, (documentos, mensagem) in enumerate(casos):
            with self.subTest(indice=indice):
                for arquivo in self.esquemas.glob("*.json"):
                    arquivo.unlink()
                for numero, documento in enumerate(documentos):
                    self.escrever(f"{numero}.json", documento)
                with self.assertRaisesRegex(gerar_classes.ErroEsquema, mensagem):
                    gerar_classes.carregar_esquemas(self.esquemas)

    def test_ordena_heranca_e_rejeita_ciclo(self) -> None:
        self.escrever("filha.json", self.esquema("Filha", classe_mae="Base"))
        self.escrever("base.json", self.esquema("Base"))
        modelos = gerar_classes.carregar_esquemas(self.esquemas)
        self.assertLess(
            [modelo.classe for modelo in modelos].index("Base"),
            [modelo.classe for modelo in modelos].index("Filha"),
        )
        for arquivo in self.esquemas.glob("*.json"):
            arquivo.unlink()
        self.escrever("a.json", self.esquema("A", classe_mae="B"))
        self.escrever("b.json", self.esquema("B", classe_mae="A"))
        with self.assertRaisesRegex(gerar_classes.ErroEsquema, "ciclo"):
            gerar_classes.carregar_esquemas(self.esquemas)

    def test_gera_modelos_reais_importaveis(self) -> None:
        self.assertEqual(
            gerar_classes.executar(gerar_classes.DIRETORIO_ESQUEMAS, self.destino), 0
        )
        modulo = self.carregar_modulo()
        self.assertEqual(
            set(modulo.__all__),
            {"Pausa", "Tarefa", "SessaoEstudo", "SessaoExercicio", "RegistroDiario"},
        )
        self.assertTrue(issubclass(modulo.SessaoEstudo, modulo.Tarefa))
        self.assertTrue(issubclass(modulo.SessaoExercicio, modulo.Tarefa))

    def test_padrao_mutavel_calculado_metadados_e_none(self) -> None:
        gerar_classes.executar(gerar_classes.DIRETORIO_ESQUEMAS, self.destino)
        modulo = self.carregar_modulo()
        primeira = modulo.Tarefa()
        segunda = modulo.Tarefa()
        primeira.pausas.append(modulo.Pausa())
        self.assertEqual(segunda.pausas, [])
        self.assertIsNone(primeira.inicio)
        mapa = {campo.name: campo for campo in fields(modulo.Tarefa)}
        self.assertFalse(mapa["duracao"].init)
        self.assertEqual(mapa["duracao"].type, "str | None")
        self.assertEqual(mapa["duracao"].metadata["unidade"], "HH:MM:SS")
        mapa_pausa = {campo.name: campo for campo in fields(modulo.Pausa)}
        self.assertEqual(mapa_pausa["duracao"].type, "str | None")
        self.assertEqual(mapa_pausa["duracao"].metadata["unidade"], "HH:MM:SS")
        self.assertIn("opcional", mapa["inicio"].metadata)
        with self.assertRaises(TypeError):
            modulo.Tarefa(duracao="00:00:01")

    def test_valida_limites_e_aceita_none(self) -> None:
        gerar_classes.executar(gerar_classes.DIRETORIO_ESQUEMAS, self.destino)
        modulo = self.carregar_modulo()
        modulo.SessaoEstudo(concentracao=None)
        modulo.SessaoEstudo(concentracao=1)
        modulo.SessaoEstudo(concentracao=5)
        with self.assertRaisesRegex(ValueError, "SessaoEstudo.concentracao.*minimo=1"):
            modulo.SessaoEstudo(concentracao=0)
        with self.assertRaisesRegex(ValueError, "SessaoEstudo.concentracao.*maximo=5"):
            modulo.SessaoEstudo(concentracao=6)

    def test_determinismo_check_e_cabecalho(self) -> None:
        self.escrever("base.json", self.esquema())
        gerar_classes.executar(self.esquemas, self.destino)
        primeiro = self.destino.read_bytes()
        gerar_classes.executar(self.esquemas, self.destino)
        self.assertEqual(primeiro, self.destino.read_bytes())
        self.assertIn("NÃO EDITE MANUALMENTE", primeiro.decode("utf-8"))
        self.assertEqual(gerar_classes.executar(self.esquemas, self.destino, verificar=True), 0)
        alterado = self.esquema(campos={"outro": {"tipo": "int"}})
        self.escrever("base.json", alterado)
        antes = self.destino.read_bytes()
        self.assertEqual(gerar_classes.executar(self.esquemas, self.destino, verificar=True), 1)
        self.assertEqual(antes, self.destino.read_bytes())

    def test_falha_preserva_arquivo_anterior_e_main_retorna_dois(self) -> None:
        self.escrever("base.json", self.esquema())
        gerar_classes.executar(self.esquemas, self.destino)
        anterior = self.destino.read_bytes()
        self.escrever("base.json", self.esquema(classe_mae="Ausente"))
        with self.assertRaises(gerar_classes.ErroEsquema):
            gerar_classes.executar(self.esquemas, self.destino)
        self.assertEqual(anterior, self.destino.read_bytes())
        with contextlib.redirect_stdout(io.StringIO()):
            with mock.patch.object(
                gerar_classes,
                "executar",
                side_effect=gerar_classes.ErroEsquema("inválido"),
            ):
                self.assertEqual(gerar_classes.main([]), 2)


if __name__ == "__main__":
    unittest.main()
