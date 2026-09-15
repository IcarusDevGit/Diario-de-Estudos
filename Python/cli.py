"""Interface de linha de comando do diário de estudos."""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path
from typing import Sequence

from Python.Classes import SessaoEstudo, SessaoExercicio, Tarefa
from Python.configuracao_mongodb import ErroConfiguracaoMongoDB, diagnosticar_mongodb
from Python.gerenciamento_dia import ErroGerenciamentoDia, GerenciadorDia
from Python.gerenciamento_relatorios import (
    ErroGerenciamentoRelatorio,
    GerenciadorRelatorios,
)
from Python.gerenciamento_tarefas import ErroGerenciamento, GerenciadorTarefas
from Python.persistencia_dia import ErroPersistenciaDia, persistir_dia


def criar_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="diario-estudos")
    parser.add_argument("--raiz", type=Path, default=Path.cwd())
    acoes = parser.add_subparsers(dest="acao", required=True)

    iniciar = acoes.add_parser("iniciar")
    tipos_inicio = iniciar.add_subparsers(dest="tipo", required=True)
    tarefa = tipos_inicio.add_parser("tarefa")
    tarefa.add_argument("--nome")
    sessao = tipos_inicio.add_parser("sessao")
    sessao.add_argument("sessao", choices=("estudo", "exercicio"))
    sessao.add_argument("--nome")
    tipos_inicio.add_parser("pausa")
    tipos_inicio.add_parser("dia")

    finalizar = acoes.add_parser("finalizar")
    tipos_final = finalizar.add_subparsers(dest="tipo", required=True)
    tipos_final.add_parser("tarefa")
    tipos_final.add_parser("pausa")
    tipos_final.add_parser("dia")

    persistir = acoes.add_parser("persistir")
    tipos_persistir = persistir.add_subparsers(dest="tipo", required=True)
    persistir_dia_parser = tipos_persistir.add_parser("dia")
    persistir_dia_parser.add_argument("--data", type=date.fromisoformat)

    diagnosticar = acoes.add_parser("diagnosticar")
    tipos_diagnostico = diagnosticar.add_subparsers(
        dest="tipo_diagnostico", required=True
    )
    tipos_diagnostico.add_parser("mongodb")

    criar = acoes.add_parser("criar")
    tipos_criar = criar.add_subparsers(dest="tipo", required=True)
    relatorio_parser = tipos_criar.add_parser("relatorio")
    relatorio_parser.add_argument("nome")
    relatorio_parser.add_argument("--data")
    return parser


def executar(argumentos: argparse.Namespace) -> Path | str:
    if argumentos.acao == "criar" and argumentos.tipo == "relatorio":
        return GerenciadorRelatorios(argumentos.raiz).criar_relatorio(
            nome=argumentos.nome, data=argumentos.data
        )
    if argumentos.acao == "diagnosticar" and argumentos.tipo_diagnostico == "mongodb":
        diagnosticar_mongodb(argumentos.raiz)
        return "Conexão com MongoDB estabelecida."
    if argumentos.acao == "iniciar" and argumentos.tipo == "dia":
        return GerenciadorDia(argumentos.raiz).iniciar_dia()
    if argumentos.acao == "finalizar" and argumentos.tipo == "dia":
        return GerenciadorDia(argumentos.raiz).finalizar_dia()
    if argumentos.acao == "persistir" and argumentos.tipo == "dia":
        return persistir_dia(argumentos.raiz, argumentos.data).isoformat()
    gerenciador = GerenciadorTarefas(argumentos.raiz)
    if argumentos.acao == "iniciar" and argumentos.tipo == "tarefa":
        return gerenciador.iniciar_atividade(Tarefa, nome=argumentos.nome)
    if argumentos.acao == "iniciar" and argumentos.tipo == "sessao":
        classe = SessaoEstudo if argumentos.sessao == "estudo" else SessaoExercicio
        return gerenciador.iniciar_atividade(classe, nome=argumentos.nome)
    if argumentos.acao == "iniciar" and argumentos.tipo == "pausa":
        return gerenciador.iniciar_pausa()
    if argumentos.acao == "finalizar" and argumentos.tipo == "pausa":
        return gerenciador.finalizar_pausa()
    if argumentos.acao == "finalizar" and argumentos.tipo == "tarefa":
        return gerenciador.finalizar_atividade()
    raise ErroGerenciamento("comando não reconhecido")


def main(argv: Sequence[str] | None = None) -> int:
    parser = criar_parser()
    try:
        argumentos = parser.parse_args(argv)
        caminho = executar(argumentos)
    except (
        ErroGerenciamento,
        ErroGerenciamentoDia,
        ErroConfiguracaoMongoDB,
        ErroPersistenciaDia,
        ErroGerenciamentoRelatorio,
    ) as erro:
        print(f"Erro: {erro}", file=sys.stderr)
        return 1
    print(caminho)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
