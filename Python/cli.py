"""Interface de linha de comando do diário de estudos."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

from Python.Classes import SessaoEstudo, SessaoExercicio, Tarefa
from Python.configuracao_mongodb import ErroConfiguracaoMongoDB, diagnosticar_mongodb
from Python.gerenciamento_dia import ErroGerenciamentoDia, GerenciadorDia
from Python.gerenciamento_tarefas import ErroGerenciamento, GerenciadorTarefas


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

    diagnosticar = acoes.add_parser("diagnosticar")
    tipos_diagnostico = diagnosticar.add_subparsers(
        dest="tipo_diagnostico", required=True
    )
    tipos_diagnostico.add_parser("mongodb")
    return parser


def executar(argumentos: argparse.Namespace) -> Path | str:
    if argumentos.acao == "diagnosticar" and argumentos.tipo_diagnostico == "mongodb":
        diagnosticar_mongodb(argumentos.raiz)
        return "Conexão com MongoDB estabelecida."
    if argumentos.acao == "iniciar" and argumentos.tipo == "dia":
        return GerenciadorDia(argumentos.raiz).iniciar_dia()
    if argumentos.acao == "finalizar" and argumentos.tipo == "dia":
        return GerenciadorDia(argumentos.raiz).finalizar_dia()
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
    except (ErroGerenciamento, ErroGerenciamentoDia, ErroConfiguracaoMongoDB) as erro:
        print(f"Erro: {erro}", file=sys.stderr)
        return 1
    print(caminho)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
