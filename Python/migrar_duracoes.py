"""Migra durações YAML de horas decimais para HH:MM:SS."""

from __future__ import annotations

import argparse
import os
import re
import tempfile
from dataclasses import fields
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Sequence

import yaml

from Python.duracao import ErroDuracao, duracao_para_segundos, formatar_segundos
from Python.serializacao_yaml import (
    REGISTRO_MODELOS,
    _LoaderSeguro,
    _validar_sem_ciclos,
)


class _LoaderMigracao(_LoaderSeguro):
    """Loader seguro sem a notação sexagesimal implícita do YAML 1.1."""


_LoaderMigracao.yaml_implicit_resolvers = {
    inicial: list(resolvedores)
    for inicial, resolvedores in _LoaderSeguro.yaml_implicit_resolvers.items()
}
for inicial, resolvedores in _LoaderMigracao.yaml_implicit_resolvers.items():
    _LoaderMigracao.yaml_implicit_resolvers[inicial] = [
        (tag, expressao)
        for tag, expressao in resolvedores
        if tag != "tag:yaml.org,2002:int"
    ]
_LoaderMigracao.add_implicit_resolver(
    "tag:yaml.org,2002:int",
    re.compile(r"^[-+]?(?:0|[1-9][0-9_]*)$"),
    list("-+0123456789"),
)


class ErroMigracaoDuracao(ValueError):
    """Indica um arquivo que não pode ser migrado com segurança."""


def _erro(origem: Path, caminho: str, detalhe: str) -> ErroMigracaoDuracao:
    return ErroMigracaoDuracao(f"{origem}: {caminho}: {detalhe}")


def horas_legadas_para_duracao(valor: int | float) -> str:
    if isinstance(valor, bool) or not isinstance(valor, (int, float)):
        raise ErroMigracaoDuracao("duração legada deve ser numérica")
    try:
        horas = Decimal(str(valor))
    except InvalidOperation as erro:
        raise ErroMigracaoDuracao("duração legada inválida") from erro
    if not horas.is_finite() or horas < 0:
        raise ErroMigracaoDuracao("duração legada não pode ser negativa ou não finita")
    segundos = int((horas * Decimal(3600)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    return formatar_segundos(segundos)


def _converter_duracao(valor: Any, origem: Path, caminho: str) -> tuple[Any, bool]:
    if valor is None:
        return None, False
    if isinstance(valor, bool):
        raise _erro(origem, caminho, "duração booleana é inválida")
    if isinstance(valor, (int, float)):
        try:
            return horas_legadas_para_duracao(valor), True
        except ErroMigracaoDuracao as erro:
            raise _erro(origem, caminho, str(erro)) from erro
    if isinstance(valor, str):
        try:
            duracao_para_segundos(valor, caminho=caminho)
        except ErroDuracao as erro:
            raise _erro(origem, caminho, str(erro)) from erro
        return valor, False
    raise _erro(origem, caminho, "duração deve ser número legado, HH:MM:SS ou null")


def _converter_modelo(dados: Any, origem: Path, caminho: str = "$") -> bool:
    if not isinstance(dados, dict):
        raise _erro(origem, caminho, "era esperado um mapeamento de modelo")
    nome = dados.get("classe")
    if not isinstance(nome, str) or nome not in REGISTRO_MODELOS:
        raise _erro(origem, f"{caminho}.classe", f"classe ausente ou desconhecida: {nome!r}")
    classe = REGISTRO_MODELOS[nome]
    permitidos = {campo.name for campo in fields(classe)} | {"classe"}
    extras = [chave for chave in dados if chave not in permitidos]
    if extras:
        raise _erro(origem, f"{caminho}.{extras[0]}", "campo desconhecido")
    alterado = False
    if "duracao" in dados:
        dados["duracao"], mudou = _converter_duracao(
            dados["duracao"], origem, f"{caminho}.duracao"
        )
        alterado = alterado or mudou
    if "pausas" in dados and dados["pausas"] is not None:
        if not isinstance(dados["pausas"], list):
            raise _erro(origem, f"{caminho}.pausas", "era esperada uma lista")
        for indice, pausa in enumerate(dados["pausas"]):
            alterado = _converter_modelo(
                pausa, origem, f"{caminho}.pausas[{indice}]"
            ) or alterado
            if pausa.get("classe") != "Pausa":
                raise _erro(
                    origem,
                    f"{caminho}.pausas[{indice}].classe",
                    "era esperada Pausa",
                )
    return alterado


def carregar_e_converter(caminho: str | Path) -> tuple[dict[str, Any], bool]:
    origem = Path(caminho)
    try:
        texto = origem.read_text(encoding="utf-8")
        dados = yaml.load(texto, Loader=_LoaderMigracao)
    except (OSError, UnicodeError, yaml.YAMLError) as erro:
        raise _erro(origem, "$", f"YAML inválido: {erro}") from erro
    try:
        _validar_sem_ciclos(dados, "$", origem)
    except ValueError as erro:
        raise ErroMigracaoDuracao(str(erro)) from erro
    alterado = _converter_modelo(dados, origem)
    return dados, alterado


def _salvar_dados_atomico(caminho: Path, dados: dict[str, Any]) -> None:
    texto = yaml.safe_dump(
        dados,
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
    )
    temporario: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            newline="\n",
            dir=caminho.parent,
            prefix=f".{caminho.name}.",
            suffix=".tmp",
            delete=False,
        ) as stream:
            stream.write(texto)
            stream.flush()
            os.fsync(stream.fileno())
            temporario = stream.name
        os.replace(temporario, caminho)
        temporario = None
    finally:
        if temporario is not None:
            Path(temporario).unlink(missing_ok=True)


def migrar_arquivo(caminho: str | Path, *, verificar: bool = False) -> bool:
    arquivo = Path(caminho)
    dados, alterado = carregar_e_converter(arquivo)
    if alterado and not verificar:
        _salvar_dados_atomico(arquivo, dados)
    return alterado


def descobrir_arquivos(raiz: str | Path, caminhos: Sequence[str | Path]) -> list[Path]:
    candidatos: list[Path] = []
    selecionados = [Path(item) for item in caminhos]
    if not selecionados:
        selecionados = [Path(raiz) / "Tarefas"]
    for selecionado in selecionados:
        if selecionado.is_dir():
            candidatos.extend(
                item
                for item in selecionado.rglob("*")
                if item.is_file() and item.suffix.lower() in {".yaml", ".yml"}
            )
        elif selecionado.is_file():
            if selecionado.suffix.lower() not in {".yaml", ".yml"}:
                raise ErroMigracaoDuracao(f"{selecionado}: extensão deve ser .yaml ou .yml")
            candidatos.append(selecionado)
        else:
            raise ErroMigracaoDuracao(f"{selecionado}: caminho não existe")
    return sorted(set(candidatos), key=lambda item: str(item).casefold())


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("caminhos", nargs="*", type=Path)
    parser.add_argument("--raiz", type=Path, default=Path.cwd())
    parser.add_argument("--check", action="store_true")
    argumentos = parser.parse_args(argv)
    try:
        arquivos = descobrir_arquivos(argumentos.raiz, argumentos.caminhos)
        pendentes = 0
        for arquivo in arquivos:
            alterado = migrar_arquivo(arquivo, verificar=argumentos.check)
            if alterado:
                pendentes += 1
                acao = "PENDENTE" if argumentos.check else "MIGRADO"
            else:
                acao = "ATUALIZADO"
            print(f"{acao}: {arquivo}")
        return 1 if argumentos.check and pendentes else 0
    except ErroMigracaoDuracao as erro:
        print(f"ERRO: {erro}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
