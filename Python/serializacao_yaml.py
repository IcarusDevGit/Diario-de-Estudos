"""Serialização segura entre os modelos gerados e documentos YAML."""

from __future__ import annotations

import os
import tempfile
import types
from dataclasses import MISSING, fields, is_dataclass
from datetime import date, datetime, time
from pathlib import Path
from typing import Any, Union, get_args, get_origin, get_type_hints

import yaml
from yaml.constructor import ConstructorError
from yaml.nodes import MappingNode

import Python.Classes as modelos
from Python.duracao import ErroDuracao, duracao_para_segundos


__all__ = [
    "ErroSerializacaoYAML",
    "carregar_yaml",
    "ler_yaml",
    "modelo_para_dados",
    "modelo_para_yaml",
    "salvar_yaml",
    "yaml_para_modelo",
]


class ErroSerializacaoYAML(ValueError):
    """Indica conteúdo incompatível com o contrato YAML dos modelos."""


REGISTRO_MODELOS: dict[str, type[Any]] = {
    nome: getattr(modelos, nome) for nome in modelos.__all__
}


class _LoaderSeguro(yaml.SafeLoader):
    """SafeLoader sem timestamps implícitos e sem chaves ambíguas."""


_LoaderSeguro.yaml_implicit_resolvers = {
    inicial: [
        (tag, expressao)
        for tag, expressao in resolvedores
        if tag != "tag:yaml.org,2002:timestamp"
    ]
    for inicial, resolvedores in yaml.SafeLoader.yaml_implicit_resolvers.items()
}


def _construir_mapeamento(
    loader: _LoaderSeguro, node: MappingNode, deep: bool = False
) -> dict[str, Any]:
    if not isinstance(node, MappingNode):
        raise ConstructorError(None, None, "era esperado um mapeamento", node.start_mark)
    resultado: dict[str, Any] = {}
    for node_chave, node_valor in node.value:
        chave = loader.construct_object(node_chave, deep=deep)
        if not isinstance(chave, str):
            raise ConstructorError(
                "ao construir um mapeamento",
                node.start_mark,
                "todas as chaves devem ser texto",
                node_chave.start_mark,
            )
        if chave in resultado:
            raise ConstructorError(
                "ao construir um mapeamento",
                node.start_mark,
                f"chave duplicada: {chave}",
                node_chave.start_mark,
            )
        resultado[chave] = loader.construct_object(node_valor, deep=deep)
    return resultado


_LoaderSeguro.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construir_mapeamento
)


def _mensagem(caminho: str, detalhe: str, origem: str | Path | None = None) -> str:
    prefixo = f"{origem}: " if origem is not None else ""
    return f"{prefixo}{caminho}: {detalhe}"


def _falhar(caminho: str, detalhe: str, origem: str | Path | None = None) -> None:
    raise ErroSerializacaoYAML(_mensagem(caminho, detalhe, origem))


def _sem_none(anotacao: Any) -> Any:
    origem = get_origin(anotacao)
    if origem in (Union, types.UnionType):
        argumentos = tuple(item for item in get_args(anotacao) if item is not type(None))
        if len(argumentos) == 1:
            return argumentos[0]
    return anotacao


def _modelo_registrado(valor: object) -> bool:
    classe = type(valor)
    return REGISTRO_MODELOS.get(classe.__name__) is classe


def _converter_para_dados(valor: Any, anotacao: Any, caminho: str) -> Any:
    if valor is None:
        return None
    esperado = _sem_none(anotacao)
    origem = get_origin(esperado)
    if origem is list:
        if not isinstance(valor, list):
            _falhar(caminho, "era esperada uma lista")
        (tipo_item,) = get_args(esperado)
        return [
            _converter_para_dados(item, tipo_item, f"{caminho}[{indice}]")
            for indice, item in enumerate(valor)
        ]
    if isinstance(esperado, type) and is_dataclass(esperado):
        if not isinstance(valor, esperado) or not _modelo_registrado(valor):
            _falhar(caminho, f"era esperado um objeto {esperado.__name__}")
        return modelo_para_dados(valor, _caminho=caminho)
    if esperado is datetime:
        if not isinstance(valor, datetime):
            _falhar(caminho, "era esperado datetime")
        return valor.isoformat()
    if esperado is date:
        if not isinstance(valor, date) or isinstance(valor, datetime):
            _falhar(caminho, "era esperado date")
        return valor.isoformat()
    if esperado is time:
        if not isinstance(valor, time):
            _falhar(caminho, "era esperado time")
        return valor.isoformat()
    if esperado is bool:
        valido = type(valor) is bool
    elif esperado is int:
        valido = type(valor) is int
    elif esperado is float:
        valido = type(valor) is float
    elif esperado is str:
        valido = type(valor) is str
    else:
        _falhar(caminho, f"anotação não suportada: {esperado!r}")
    if not valido:
        _falhar(caminho, f"era esperado {esperado.__name__}")
    return valor


def modelo_para_dados(modelo: object, *, _caminho: str = "$") -> dict[str, Any]:
    """Converte uma instância registrada em estruturas primitivas ordenadas."""
    if not is_dataclass(modelo) or isinstance(modelo, type) or not _modelo_registrado(modelo):
        _falhar(_caminho, "era esperada uma instância de modelo registrada")
    classe = type(modelo)
    dicas = get_type_hints(classe)
    resultado: dict[str, Any] = {"classe": classe.__name__}
    for campo in fields(modelo):
        _validar_metadados(
            getattr(modelo, campo.name), campo.metadata, f"{_caminho}.{campo.name}"
        )
        resultado[campo.name] = _converter_para_dados(
            getattr(modelo, campo.name), dicas[campo.name], f"{_caminho}.{campo.name}"
        )
    return resultado


def modelo_para_yaml(modelo: object) -> str:
    """Serializa um modelo em YAML determinístico e legível."""
    texto = yaml.safe_dump(
        modelo_para_dados(modelo),
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
    )
    return texto if texto.endswith("\n") else texto + "\n"


def _carregar_dados_yaml(texto: str, origem: str | Path | None) -> Any:
    try:
        return yaml.load(texto, Loader=_LoaderSeguro)
    except yaml.YAMLError as erro:
        _falhar("$", f"YAML inválido: {erro}", origem)


def _validar_sem_ciclos(
    valor: Any,
    caminho: str,
    origem: str | Path | None,
    ancestrais: set[int] | None = None,
) -> None:
    if not isinstance(valor, (dict, list)):
        return
    ancestrais = set() if ancestrais is None else ancestrais
    identidade = id(valor)
    if identidade in ancestrais:
        _falhar(caminho, "aliases YAML cíclicos não são permitidos", origem)
    ancestrais.add(identidade)
    if isinstance(valor, dict):
        for chave, item in valor.items():
            _validar_sem_ciclos(item, f"{caminho}.{chave}", origem, ancestrais)
    else:
        for indice, item in enumerate(valor):
            _validar_sem_ciclos(item, f"{caminho}[{indice}]", origem, ancestrais)
    ancestrais.remove(identidade)


def _converter_temporal(
    valor: Any,
    esperado: type[date] | type[time] | type[datetime],
    caminho: str,
    origem: str | Path | None,
) -> date | time | datetime:
    if not isinstance(valor, str):
        _falhar(caminho, f"era esperado texto ISO 8601 para {esperado.__name__}", origem)
    try:
        convertido = esperado.fromisoformat(valor)
    except ValueError as erro:
        _falhar(caminho, f"{esperado.__name__} ISO 8601 inválido: {valor!r}", origem)
    if esperado is date and isinstance(convertido, datetime):
        _falhar(caminho, "era esperado date sem horário", origem)
    return convertido


def _converter_para_modelo(
    valor: Any,
    anotacao: Any,
    caminho: str,
    origem_arquivo: str | Path | None,
) -> Any:
    if valor is None:
        return None
    esperado = _sem_none(anotacao)
    origem = get_origin(esperado)
    if origem is list:
        if not isinstance(valor, list):
            _falhar(caminho, "era esperada uma lista", origem_arquivo)
        (tipo_item,) = get_args(esperado)
        return [
            _converter_para_modelo(item, tipo_item, f"{caminho}[{indice}]", origem_arquivo)
            for indice, item in enumerate(valor)
        ]
    if isinstance(esperado, type) and is_dataclass(esperado):
        return _construir_modelo(valor, esperado, caminho, origem_arquivo)
    if esperado in (date, time, datetime):
        return _converter_temporal(valor, esperado, caminho, origem_arquivo)
    if esperado is bool:
        valido = type(valor) is bool
    elif esperado is int:
        valido = type(valor) is int
    elif esperado is float:
        valido = type(valor) is float
    elif esperado is str:
        valido = type(valor) is str
    else:
        _falhar(caminho, f"anotação não suportada: {esperado!r}", origem_arquivo)
    if not valido:
        _falhar(caminho, f"era esperado {esperado.__name__}", origem_arquivo)
    return valor


def _validar_metadados(
    valor: Any,
    metadados: Any,
    caminho: str,
    origem: str | Path | None = None,
) -> None:
    if valor is None:
        return
    if "minimo" in metadados and valor < metadados["minimo"]:
        _falhar(caminho, f"valor abaixo de minimo={metadados['minimo']}", origem)
    if "maximo" in metadados and valor > metadados["maximo"]:
        _falhar(caminho, f"valor acima de maximo={metadados['maximo']}", origem)
    if metadados.get("unidade") == "HH:MM:SS":
        try:
            duracao_para_segundos(valor, caminho=caminho)
        except ErroDuracao as erro:
            _falhar(caminho, str(erro), origem)


def _construir_modelo(
    dados: Any,
    esperado: type[Any] | None,
    caminho: str,
    origem: str | Path | None,
) -> Any:
    if not isinstance(dados, dict):
        _falhar(caminho, "era esperado um mapeamento de modelo", origem)
    nome_classe = dados.get("classe")
    if not isinstance(nome_classe, str):
        _falhar(f"{caminho}.classe", "discriminador ausente ou não textual", origem)
    classe = REGISTRO_MODELOS.get(nome_classe)
    if classe is None:
        _falhar(f"{caminho}.classe", f"classe desconhecida: {nome_classe!r}", origem)
    if esperado is not None and not issubclass(classe, esperado):
        _falhar(
            f"{caminho}.classe",
            f"{nome_classe} não é compatível com {esperado.__name__}",
            origem,
        )
    campos = {campo.name: campo for campo in fields(classe)}
    extras = [chave for chave in dados if chave != "classe" and chave not in campos]
    if extras:
        _falhar(f"{caminho}.{extras[0]}", "campo desconhecido", origem)
    dicas = get_type_hints(classe)
    argumentos: dict[str, Any] = {}
    posteriores: dict[str, Any] = {}
    for nome, campo in campos.items():
        if nome not in dados:
            if campo.default is MISSING and campo.default_factory is MISSING:
                _falhar(f"{caminho}.{nome}", "campo obrigatório ausente", origem)
            continue
        convertido = _converter_para_modelo(
            dados[nome], dicas[nome], f"{caminho}.{nome}", origem
        )
        _validar_metadados(convertido, campo.metadata, f"{caminho}.{nome}", origem)
        (argumentos if campo.init else posteriores)[nome] = convertido
    try:
        modelo = classe(**argumentos)
    except (TypeError, ValueError) as erro:
        _falhar(caminho, f"não foi possível criar {nome_classe}: {erro}", origem)
    for nome, valor in posteriores.items():
        setattr(modelo, nome, valor)
    return modelo


def yaml_para_modelo(texto: str, *, origem: str | Path | None = None) -> Any:
    """Reconstrói um modelo a partir de texto YAML seguro."""
    if not isinstance(texto, str):
        _falhar("$", "o conteúdo YAML deve ser texto", origem)
    dados = _carregar_dados_yaml(texto, origem)
    _validar_sem_ciclos(dados, "$", origem)
    return _construir_modelo(dados, None, "$", origem)


def ler_yaml(caminho: str | Path) -> Any:
    """Lê um arquivo YAML UTF-8 e reconstrói seu modelo."""
    arquivo = Path(caminho)
    try:
        texto = arquivo.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as erro:
        _falhar("$", f"não foi possível ler UTF-8: {erro}", arquivo)
    return yaml_para_modelo(texto, origem=arquivo)


carregar_yaml = ler_yaml


def salvar_yaml(modelo: object, caminho: str | Path) -> None:
    """Salva um modelo como YAML usando substituição atômica."""
    destino = Path(caminho)
    texto = modelo_para_yaml(modelo)
    reconstruido = yaml_para_modelo(texto)
    if modelo_para_dados(reconstruido) != modelo_para_dados(modelo):
        _falhar("$", "a validação de ida e volta produziu dados diferentes", destino)
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
            stream.write(texto)
            stream.flush()
            os.fsync(stream.fileno())
            temporario = stream.name
        os.replace(temporario, destino)
        temporario = None
    except OSError as erro:
        raise ErroSerializacaoYAML(
            _mensagem("$", f"não foi possível salvar: {erro}", destino)
        ) from erro
    finally:
        if temporario is not None:
            Path(temporario).unlink(missing_ok=True)
