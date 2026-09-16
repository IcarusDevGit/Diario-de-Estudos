"""Montagem, persistência e limpeza do retrato agregado de um ciclo."""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Callable

from pymongo import MongoClient
from pymongo.errors import PyMongoError

from Python.Classes import RegistroDiario, Relatorio, Tarefa
from Python.ciclo_dia import ErroCicloDia, listar_registros
from Python.configuracao_mongodb import carregar_mongodb_database, criar_cliente_mongodb
from Python.serializacao_yaml import ErroSerializacaoYAML, ler_yaml, modelo_para_dados


COLLECTION_DIAS = "dias"
_DIRETORIO_LIMPEZAS = ".diario/limpezas-pendentes"


class ErroPersistenciaDia(RuntimeError):
    """Indica falha ao montar, persistir ou limpar um ciclo."""


@dataclass(frozen=True)
class SelecaoCiclo:
    documento: dict[str, Any]
    caminhos: tuple[Path, ...]


def _diretorios_permitidos(raiz: Path) -> tuple[Path, Path]:
    return (
        (raiz / "Relatórios").resolve(),
        (raiz / "Tarefas" / "Concluidas").resolve(),
    )


def _validar_caminho_selecionado(raiz: Path, caminho: Path) -> Path:
    raiz = raiz.resolve()
    resolvido = caminho.resolve()
    if not resolvido.is_relative_to(raiz) or not any(
        resolvido.is_relative_to(diretorio)
        for diretorio in _diretorios_permitidos(raiz)
    ):
        raise ErroPersistenciaDia(f"caminho fora dos diretórios permitidos: {caminho}")
    return resolvido


def selecionar_ciclo(raiz: str | Path, data_ciclo: date) -> SelecaoCiclo:
    raiz = Path(raiz).resolve()
    relatorios: list[dict[str, Any]] = []
    atividades: list[dict[str, Any]] = []
    diarios: list[RegistroDiario] = []
    caminhos: list[Path] = []
    try:
        for caminho in sorted((raiz / "Relatórios").glob("*.yaml")):
            modelo = ler_yaml(caminho)
            if not isinstance(modelo, Relatorio) or modelo.data != data_ciclo:
                continue
            relatorios.append(modelo_para_dados(modelo))
            caminhos.append(_validar_caminho_selecionado(raiz, caminho))
            if type(modelo) is RegistroDiario:
                diarios.append(modelo)

        for caminho in sorted((raiz / "Tarefas" / "Concluidas").glob("*.yaml")):
            modelo = ler_yaml(caminho)
            if not isinstance(modelo, Tarefa):
                raise ErroPersistenciaDia(f"atividade incompatível: {caminho}")
            if modelo.dia is None:
                raise ErroPersistenciaDia(f"atividade sem dia: {caminho}")
            if modelo.dia != data_ciclo:
                continue
            if modelo.fim is None or modelo.duracao is None:
                raise ErroPersistenciaDia(f"atividade incompleta: {caminho}")
            atividades.append(modelo_para_dados(modelo))
            caminhos.append(_validar_caminho_selecionado(raiz, caminho))
    except (ErroSerializacaoYAML, ErroCicloDia) as erro:
        raise ErroPersistenciaDia(str(erro)) from erro

    if len(diarios) != 1 or diarios[0].fui_dormir is None:
        raise ErroPersistenciaDia("ciclo exige exatamente um RegistroDiario finalizado")

    documento = {
        "versao": 1,
        "data": data_ciclo.isoformat(),
        "relatorios": relatorios,
        "atividades": atividades,
    }
    return SelecaoCiclo(documento=documento, caminhos=tuple(caminhos))


def montar_retrato(raiz: str | Path, data_ciclo: date) -> dict[str, Any]:
    """Mantém a interface pública que devolve somente o documento agregado."""
    return selecionar_ciclo(raiz, data_ciclo).documento


def _caminho_manifesto(raiz: Path, data_ciclo: date) -> Path:
    return raiz / _DIRETORIO_LIMPEZAS / f"{data_ciclo.isoformat()}.json"


def _relativo_validado(raiz: Path, valor: object) -> Path:
    if not isinstance(valor, str) or not valor:
        raise ErroPersistenciaDia("manifesto de limpeza contém caminho inválido")
    relativo = Path(valor)
    if relativo.is_absolute() or ".." in relativo.parts:
        raise ErroPersistenciaDia(f"manifesto de limpeza contém caminho inseguro: {valor!r}")
    candidato = _validar_caminho_selecionado(raiz, raiz / relativo)
    return candidato


def _escrever_manifesto(raiz: Path, data_ciclo: date, caminhos: tuple[Path, ...]) -> Path:
    destino = _caminho_manifesto(raiz, data_ciclo)
    relativos = []
    for caminho in caminhos:
        validado = _validar_caminho_selecionado(raiz, caminho)
        relativos.append(validado.relative_to(raiz.resolve()).as_posix())
    documento = {"versao": 1, "data": data_ciclo.isoformat(), "caminhos": relativos}
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
            json.dump(documento, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
            temporario = stream.name
        os.replace(temporario, destino)
        temporario = None
    except (OSError, TypeError) as erro:
        raise ErroPersistenciaDia(
            f"persistência confirmada, mas não foi possível registrar a limpeza: {destino}"
        ) from erro
    finally:
        if temporario is not None:
            Path(temporario).unlink(missing_ok=True)
    return destino


def _ler_manifesto(raiz: Path, data_ciclo: date) -> tuple[Path, tuple[Path, ...]] | None:
    caminho = _caminho_manifesto(raiz, data_ciclo)
    if not caminho.exists():
        return None
    try:
        documento = json.loads(caminho.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as erro:
        raise ErroPersistenciaDia(f"manifesto de limpeza inválido: {caminho}") from erro
    if (
        not isinstance(documento, dict)
        or documento.get("versao") != 1
        or documento.get("data") != data_ciclo.isoformat()
        or not isinstance(documento.get("caminhos"), list)
    ):
        raise ErroPersistenciaDia(f"manifesto de limpeza inválido: {caminho}")
    selecionados = tuple(_relativo_validado(raiz, item) for item in documento["caminhos"])
    if len(set(selecionados)) != len(selecionados):
        raise ErroPersistenciaDia(f"manifesto de limpeza possui caminhos duplicados: {caminho}")
    return caminho, selecionados


def _limpar_manifesto(raiz: Path, data_ciclo: date) -> None:
    carregado = _ler_manifesto(raiz, data_ciclo)
    if carregado is None:
        return
    manifesto, caminhos = carregado
    for caminho in caminhos:
        try:
            caminho.unlink(missing_ok=True)
        except OSError:
            pass
    remanescentes = [caminho for caminho in caminhos if caminho.exists()]
    if remanescentes:
        lista = ", ".join(str(caminho) for caminho in remanescentes)
        raise ErroPersistenciaDia(
            f"persistência confirmada; falha ao limpar arquivos locais: {lista}"
        )
    try:
        manifesto.unlink()
    except OSError as erro:
        raise ErroPersistenciaDia(
            f"arquivos removidos, mas não foi possível concluir a limpeza: {manifesto}"
        ) from erro


def _datas_com_manifesto(raiz: Path) -> list[date]:
    datas: list[date] = []
    for caminho in sorted((raiz / _DIRETORIO_LIMPEZAS).glob("*.json")):
        try:
            datas.append(date.fromisoformat(caminho.stem))
        except ValueError as erro:
            raise ErroPersistenciaDia(f"manifesto de limpeza inválido: {caminho}") from erro
    return datas


def persistir_dia(
    raiz: str | Path,
    data_ciclo: date | None = None,
    *,
    fabrica: Callable[..., Any] = MongoClient,
) -> date:
    raiz = Path(raiz).resolve()
    pendentes = _datas_com_manifesto(raiz)
    if data_ciclo is not None and data_ciclo in pendentes:
        _limpar_manifesto(raiz, data_ciclo)
        return data_ciclo
    if data_ciclo is None and pendentes:
        data_ciclo = max(pendentes)
        _limpar_manifesto(raiz, data_ciclo)
        return data_ciclo

    try:
        registros = listar_registros(raiz)
    except ErroCicloDia as erro:
        raise ErroPersistenciaDia(str(erro)) from erro
    if data_ciclo is None:
        finais = [registro.data for _, registro in registros if registro.fui_dormir is not None]
        if not finais:
            raise ErroPersistenciaDia("nenhum ciclo finalizado")
        data_ciclo = max(finais)

    selecao = selecionar_ciclo(raiz, data_ciclo)
    database = carregar_mongodb_database(raiz)
    cliente = criar_cliente_mongodb(raiz, fabrica=fabrica)
    try:
        colecao = cliente[database][COLLECTION_DIAS]
        colecao.create_index("data", unique=True)
        colecao.replace_one(
            {"data": data_ciclo.isoformat()}, selecao.documento, upsert=True
        )
    except PyMongoError as erro:
        raise ErroPersistenciaDia("falha ao persistir dia no MongoDB") from erro
    finally:
        cliente.close()

    _escrever_manifesto(raiz, data_ciclo, selecao.caminhos)
    _limpar_manifesto(raiz, data_ciclo)
    return data_ciclo
