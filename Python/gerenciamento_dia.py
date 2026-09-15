"""Ciclo de vida local do registro diário e leitura de seu histórico."""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import fields
from datetime import date, datetime, time, timedelta, tzinfo
from pathlib import Path
from typing import Any

from pymongo import MongoClient
from pymongo.errors import PyMongoError

from Python.Classes import RegistroDiario
from Python.configuracao_mongodb import (
    ErroConfiguracaoMongoDB,
    carregar_mongodb_database,
    criar_cliente_mongodb,
)
from Python.gerenciamento_tarefas import (
    ErroGerenciamento,
    GerenciadorTarefas,
    carregar_fuso_horario,
)
from Python.serializacao_yaml import ErroSerializacaoYAML, ler_yaml, salvar_yaml


__all__ = [
    "COLLECTION_REGISTROS_DIARIOS",
    "ErroGerenciamentoDia",
    "GerenciadorDia",
    "consultar_fui_dormir_anterior",
]


COLLECTION_REGISTROS_DIARIOS = "registros_diarios"
_HORARIO_ISO = re.compile(r"\d{2}:\d{2}(?::\d{2}(?:\.\d{1,6})?)?")
ConsultaSono = Callable[[date], time | None]


class ErroGerenciamentoDia(RuntimeError):
    """Indica uma transição inválida no ciclo do registro diário."""


def _converter_horario_remoto(valor: object) -> time:
    if not isinstance(valor, str) or _HORARIO_ISO.fullmatch(valor) is None:
        raise ErroGerenciamentoDia(
            "histórico MongoDB inválido: fui_dormir deve usar HH:MM ou HH:MM:SS"
        )
    try:
        return time.fromisoformat(valor).replace(second=0, microsecond=0)
    except ValueError as erro:
        raise ErroGerenciamentoDia(
            "histórico MongoDB inválido: fui_dormir deve usar HH:MM ou HH:MM:SS"
        ) from erro


def consultar_fui_dormir_anterior(
    raiz: str | Path,
    data_anterior: date,
    *,
    fabrica: Callable[..., Any] = MongoClient,
) -> time | None:
    """Consulta até dois registros por data, sem criar ou alterar estruturas."""
    database = carregar_mongodb_database(raiz)
    cliente = criar_cliente_mongodb(raiz, fabrica=fabrica)
    try:
        collection = cliente[database][COLLECTION_REGISTROS_DIARIOS]
        cursor = collection.find(
            {"data": data_anterior.isoformat()},
            {"_id": 0, "fui_dormir": 1},
        ).limit(2)
        documentos = list(cursor)
    except PyMongoError as erro:
        raise ErroGerenciamentoDia(
            "falha ao consultar o histórico MongoDB: verifique rede, acesso e credenciais"
        ) from erro
    finally:
        cliente.close()

    if not documentos:
        return None
    if len(documentos) > 1:
        raise ErroGerenciamentoDia(
            "histórico MongoDB inconsistente: mais de um relatório para a mesma data"
        )
    return _converter_horario_remoto(documentos[0].get("fui_dormir"))


class GerenciadorDia:
    """Coordena início e finalização do RegistroDiario local."""

    def __init__(
        self,
        raiz: str | Path,
        *,
        relogio: Callable[[], datetime] | None = None,
        fuso: tzinfo | None = None,
        consulta_sono: ConsultaSono | None = None,
        gerenciador_tarefas: GerenciadorTarefas | None = None,
    ) -> None:
        self.raiz = Path(raiz)
        self.diretorio_relatorios = self.raiz / "Relatórios"
        self.fuso = fuso or carregar_fuso_horario(self.raiz)
        self._relogio = relogio or (lambda: datetime.now(self.fuso))
        self._consulta_sono = consulta_sono or (
            lambda data_anterior: consultar_fui_dormir_anterior(
                self.raiz, data_anterior
            )
        )
        self._gerenciador_tarefas = gerenciador_tarefas or GerenciadorTarefas(
            self.raiz, fuso=self.fuso
        )

    def _agora(self) -> datetime:
        instante = self._relogio()
        if not isinstance(instante, datetime):
            raise ErroGerenciamentoDia("relógio deve retornar datetime")
        if instante.tzinfo is None or instante.utcoffset() is None:
            raise ErroGerenciamentoDia(
                "relógio deve retornar datetime com fuso horário"
            )
        return instante.astimezone(self.fuso)

    def _caminho_relatorio(self, data_relatorio: date) -> Path:
        return self.diretorio_relatorios / f"RD-{data_relatorio.isoformat()}.yaml"

    def iniciar_dia(self) -> Path:
        instante = self._agora()
        hoje = instante.date()
        caminho = self._caminho_relatorio(hoje)
        if caminho.exists():
            raise ErroGerenciamentoDia(f"relatório diário já existe: {caminho}")
        try:
            sono_anterior = self._consulta_sono(hoje - timedelta(days=1))
        except (ErroConfiguracaoMongoDB, ErroGerenciamentoDia):
            raise
        relatorio = RegistroDiario(data=hoje, dormi_dia_anterior=sono_anterior)
        try:
            salvar_yaml(relatorio, caminho)
        except (ErroSerializacaoYAML, OSError) as erro:
            raise ErroGerenciamentoDia(
                f"não foi possível criar o relatório diário: {caminho}"
            ) from erro
        return caminho

    def _carregar_relatorio(self, hoje: date, caminho: Path) -> RegistroDiario:
        if not caminho.exists():
            raise ErroGerenciamentoDia(f"relatório diário não encontrado: {caminho}")
        try:
            relatorio = ler_yaml(caminho)
        except ErroSerializacaoYAML as erro:
            raise ErroGerenciamentoDia(str(erro)) from erro
        if type(relatorio) is not RegistroDiario:
            raise ErroGerenciamentoDia(
                f"{caminho}: classe incompatível com relatório diário"
            )
        if relatorio.data != hoje:
            raise ErroGerenciamentoDia(
                f"{caminho}: data do relatório não corresponde ao dia atual"
            )
        return relatorio

    @staticmethod
    def _campos_obrigatorios_ausentes(relatorio: RegistroDiario) -> list[str]:
        return [
            campo.name
            for campo in fields(relatorio)
            if campo.metadata.get("opcional") is False
            and getattr(relatorio, campo.name) is None
        ]

    def finalizar_dia(self) -> Path:
        instante = self._agora()
        hoje = instante.date()
        caminho = self._caminho_relatorio(hoje)
        relatorio = self._carregar_relatorio(hoje, caminho)
        if relatorio.fui_dormir is not None:
            raise ErroGerenciamentoDia(f"dia já foi finalizado: {caminho}")
        ausentes = self._campos_obrigatorios_ausentes(relatorio)
        if ausentes:
            raise ErroGerenciamentoDia(
                "campos obrigatórios não preenchidos: " + ", ".join(ausentes)
            )
        try:
            atividade = self._gerenciador_tarefas.atividade_ativa()
        except ErroGerenciamento as erro:
            raise ErroGerenciamentoDia(str(erro)) from erro
        if atividade is not None:
            caminho_atividade, modelo = atividade
            raise ErroGerenciamentoDia(
                f"ainda existe {type(modelo).__name__} em andamento: {caminho_atividade}"
            )
        relatorio.fui_dormir = instante.time().replace(
            tzinfo=None, second=0, microsecond=0
        )
        try:
            salvar_yaml(relatorio, caminho)
        except (ErroSerializacaoYAML, OSError) as erro:
            raise ErroGerenciamentoDia(
                f"não foi possível finalizar o relatório diário: {caminho}"
            ) from erro
        return caminho
