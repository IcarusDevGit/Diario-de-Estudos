"""Gera dataclasses Python a partir dos documentos em ``Esquemas``."""

from __future__ import annotations

import argparse
import json
import keyword
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any


RAIZ_PROJETO = Path(__file__).resolve().parent.parent
DIRETORIO_ESQUEMAS = RAIZ_PROJETO / "Esquemas"
ARQUIVO_GERADO = Path(__file__).resolve().parent / "Classes" / "geradas.py"
TIPOS_SUPORTADOS = frozenset(
    {"str", "bool", "int", "float", "date", "time", "datetime", "list"}
)
CHAVES_ESQUEMA = frozenset({"versao", "classe", "classe_mae", "campos"})
CHAVES_CAMPO = frozenset(
    {
        "tipo",
        "opcional",
        "padrao",
        "calculado",
        "unidade",
        "itens",
        "minimo",
        "maximo",
    }
)


class ErroEsquema(ValueError):
    """Indica que um esquema não obedece ao contrato suportado."""


@dataclass(frozen=True)
class ModeloEsquema:
    arquivo: Path
    classe: str
    classe_mae: str | None
    campos: dict[str, dict[str, Any]]


def _erro(arquivo: Path, mensagem: str) -> ErroEsquema:
    return ErroEsquema(f"{arquivo.name}: {mensagem}")


def _identificador_valido(valor: object) -> bool:
    return isinstance(valor, str) and valor.isidentifier() and not keyword.iskeyword(valor)


def _validar_padrao(arquivo: Path, nome: str, campo: dict[str, Any]) -> None:
    if "padrao" not in campo:
        return
    valor = campo["padrao"]
    tipo = campo["tipo"]
    validadores = {
        "str": lambda item: isinstance(item, str),
        "bool": lambda item: isinstance(item, bool),
        "int": lambda item: isinstance(item, int) and not isinstance(item, bool),
        "float": lambda item: isinstance(item, (int, float)) and not isinstance(item, bool),
        "list": lambda item: isinstance(item, list),
    }
    if tipo in {"date", "time", "datetime"}:
        raise _erro(arquivo, f"campo {nome!r}: padrão temporal não é suportado")
    if not validadores[tipo](valor):
        raise _erro(arquivo, f"campo {nome!r}: padrão incompatível com {tipo!r}")


def _normalizar_documento(arquivo: Path, documento: object) -> ModeloEsquema:
    if not isinstance(documento, dict):
        raise _erro(arquivo, "a raiz deve ser um objeto JSON")
    if "herda_de" in documento:
        raise _erro(arquivo, "use 'classe_mae' no lugar de 'herda_de'")
    desconhecidas = set(documento) - CHAVES_ESQUEMA
    if desconhecidas:
        raise _erro(arquivo, f"metadados desconhecidos: {sorted(desconhecidas)}")
    if documento.get("versao") != 1:
        raise _erro(arquivo, "somente a versão 1 é suportada")
    classe = documento.get("classe")
    if not _identificador_valido(classe):
        raise _erro(arquivo, f"nome de classe inválido: {classe!r}")
    classe_mae = documento.get("classe_mae")
    if classe_mae is not None and not _identificador_valido(classe_mae):
        raise _erro(arquivo, f"classe_mae inválida: {classe_mae!r}")
    campos_brutos = documento.get("campos")
    if not isinstance(campos_brutos, dict):
        raise _erro(arquivo, "'campos' deve ser um objeto")

    campos: dict[str, dict[str, Any]] = {}
    for nome, valor in campos_brutos.items():
        if not _identificador_valido(nome):
            raise _erro(arquivo, f"nome de campo inválido: {nome!r}")
        if not isinstance(valor, dict):
            raise _erro(arquivo, f"campo {nome!r}: definição deve ser um objeto")
        desconhecidas = set(valor) - CHAVES_CAMPO
        if desconhecidas:
            raise _erro(
                arquivo,
                f"campo {nome!r}: atributos desconhecidos: {sorted(desconhecidas)}",
            )
        tipo = valor.get("tipo")
        if tipo not in TIPOS_SUPORTADOS:
            raise _erro(arquivo, f"campo {nome!r}: tipo desconhecido {tipo!r}")
        for chave in ("opcional", "calculado"):
            if chave in valor and not isinstance(valor[chave], bool):
                raise _erro(arquivo, f"campo {nome!r}: {chave!r} deve ser booleano")
        if valor.get("calculado") and "padrao" in valor:
            raise _erro(arquivo, f"campo {nome!r}: calculado não pode possuir padrão")
        if tipo == "list":
            if not _identificador_valido(valor.get("itens")):
                raise _erro(arquivo, f"campo {nome!r}: lista exige 'itens' válido")
        elif "itens" in valor:
            raise _erro(arquivo, f"campo {nome!r}: 'itens' só é válido para list")
        for limite in ("minimo", "maximo"):
            if limite in valor:
                numero = valor[limite]
                if tipo not in {"int", "float"} or not isinstance(numero, (int, float)) or isinstance(numero, bool):
                    raise _erro(
                        arquivo,
                        f"campo {nome!r}: {limite!r} exige tipo numérico",
                    )
        if "minimo" in valor and "maximo" in valor and valor["minimo"] > valor["maximo"]:
            raise _erro(arquivo, f"campo {nome!r}: minimo não pode superar maximo")
        if "unidade" in valor and not isinstance(valor["unidade"], str):
            raise _erro(arquivo, f"campo {nome!r}: 'unidade' deve ser texto")
        _validar_padrao(arquivo, nome, valor)
        campos[nome] = dict(valor)

    return ModeloEsquema(arquivo, classe, classe_mae, campos)


def carregar_esquemas(diretorio: Path = DIRETORIO_ESQUEMAS) -> list[ModeloEsquema]:
    arquivos = sorted(diretorio.glob("*.json"), key=lambda item: item.name.casefold())
    if not arquivos:
        raise ErroEsquema(f"nenhum esquema JSON encontrado em {diretorio}")
    modelos: list[ModeloEsquema] = []
    for arquivo in arquivos:
        try:
            with arquivo.open("r", encoding="utf-8") as stream:
                documento = json.load(stream)
        except (UnicodeDecodeError, json.JSONDecodeError) as erro:
            raise _erro(arquivo, f"JSON inválido: {erro}") from erro
        modelos.append(_normalizar_documento(arquivo, documento))
    return ordenar_e_validar_referencias(modelos)


def ordenar_e_validar_referencias(modelos: list[ModeloEsquema]) -> list[ModeloEsquema]:
    por_classe: dict[str, ModeloEsquema] = {}
    for modelo in modelos:
        if modelo.classe in por_classe:
            raise _erro(modelo.arquivo, f"classe duplicada: {modelo.classe}")
        por_classe[modelo.classe] = modelo

    for modelo in modelos:
        if modelo.classe_mae and modelo.classe_mae not in por_classe:
            raise _erro(modelo.arquivo, f"classe_mae inexistente: {modelo.classe_mae}")
        for nome, campo in modelo.campos.items():
            if campo["tipo"] == "list" and campo["itens"] not in por_classe:
                raise _erro(
                    modelo.arquivo,
                    f"campo {nome!r}: classe de itens inexistente: {campo['itens']}",
                )

    ordenados: list[ModeloEsquema] = []
    estados: dict[str, int] = {}

    def visitar(modelo: ModeloEsquema) -> None:
        estado = estados.get(modelo.classe, 0)
        if estado == 1:
            raise _erro(modelo.arquivo, f"ciclo de herança envolvendo {modelo.classe}")
        if estado == 2:
            return
        estados[modelo.classe] = 1
        if modelo.classe_mae:
            visitar(por_classe[modelo.classe_mae])
        estados[modelo.classe] = 2
        ordenados.append(modelo)

    for modelo in sorted(modelos, key=lambda item: item.classe):
        visitar(modelo)
    return ordenados


def _anotacao(campo: dict[str, Any]) -> str:
    if campo["tipo"] == "list":
        return f"list[{campo['itens']}] | None"
    return f"{campo['tipo']} | None"


def _metadados(campo: dict[str, Any]) -> str:
    valores: dict[str, Any] = {"opcional": bool(campo.get("opcional", False))}
    for chave in ("calculado", "unidade", "minimo", "maximo"):
        if chave in campo:
            valores[chave] = campo[chave]
    conteudo = ", ".join(f"{chave!r}: {valor!r}" for chave, valor in valores.items())
    return "{" + conteudo + "}"


def _declaracao_campo(nome: str, campo: dict[str, Any]) -> str:
    anotacao = _anotacao(campo)
    metadados = _metadados(campo)
    if campo.get("calculado"):
        valor = f"field(default=None, init=False, metadata={metadados})"
    elif isinstance(campo.get("padrao"), list):
        valor = f"field(default_factory=list, metadata={metadados})"
    elif "padrao" in campo:
        valor = f"field(default={campo['padrao']!r}, metadata={metadados})"
    else:
        valor = f"field(default=None, metadata={metadados})"
    return f"    {nome}: {anotacao} = {valor}"


def renderizar(modelos: list[ModeloEsquema]) -> str:
    linhas = [
        '"""ARQUIVO GERADO AUTOMATICAMENTE. NÃO EDITE MANUALMENTE."""',
        "",
        "from __future__ import annotations",
        "",
        "from dataclasses import dataclass, field",
        "from datetime import date, datetime, time",
        "",
        f"__all__ = {tuple(modelo.classe for modelo in modelos)!r}",
        "",
    ]
    for modelo in modelos:
        base = f"({modelo.classe_mae})" if modelo.classe_mae else ""
        linhas.extend(["@dataclass(kw_only=True)", f"class {modelo.classe}{base}:"])
        if modelo.campos:
            for nome, campo in modelo.campos.items():
                linhas.append(_declaracao_campo(nome, campo))
        else:
            linhas.append("    pass")
        linhas.extend(["", "    def __post_init__(self) -> None:"])
        if modelo.classe_mae:
            linhas.append("        super().__post_init__()")
        verificacoes = 0
        for nome, campo in modelo.campos.items():
            for chave, operador in (("minimo", "<"), ("maximo", ">")):
                if chave not in campo:
                    continue
                verificacoes += 1
                limite = campo[chave]
                linhas.extend(
                    [
                        f"        if self.{nome} is not None and self.{nome} {operador} {limite!r}:",
                        f"            raise ValueError({modelo.classe!r} + '.{nome} viola {chave}={limite}')",
                    ]
                )
        if not modelo.classe_mae and verificacoes == 0:
            linhas.append("        pass")
        linhas.append("")
    conteudo = "\n".join(linhas)
    compile(conteudo, str(ARQUIVO_GERADO), "exec")
    return conteudo


def escrever_atomicamente(destino: Path, conteudo: str) -> None:
    destino.parent.mkdir(parents=True, exist_ok=True)
    temporario: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            newline="\n",
            dir=destino.parent,
            prefix=f".{destino.name}.",
            suffix=".tmp",
            delete=False,
        ) as stream:
            stream.write(conteudo)
            temporario = stream.name
        os.replace(temporario, destino)
        temporario = None
    finally:
        if temporario is not None:
            Path(temporario).unlink(missing_ok=True)


def executar(
    diretorio: Path = DIRETORIO_ESQUEMAS,
    destino: Path = ARQUIVO_GERADO,
    *,
    verificar: bool = False,
) -> int:
    conteudo = renderizar(carregar_esquemas(diretorio))
    atual = destino.read_text(encoding="utf-8") if destino.exists() else None
    if verificar:
        if atual == conteudo:
            print("Classes geradas estão atualizadas.")
            return 0
        print("Classes geradas estão ausentes ou desatualizadas.")
        return 1
    if atual == conteudo:
        print(f"Classes já estavam atualizadas: {destino}")
        return 0
    escrever_atomicamente(destino, conteudo)
    print(f"Classes geradas: {destino}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="verifica se o módulo gerado está atualizado sem escrever",
    )
    argumentos = parser.parse_args(argv)
    try:
        return executar(verificar=argumentos.check)
    except ErroEsquema as erro:
        print(f"Erro de esquema: {erro}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
