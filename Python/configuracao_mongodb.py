"""Configuração segura e diagnóstico de conectividade com MongoDB."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from pymongo import MongoClient
from pymongo.errors import PyMongoError
from pymongo.server_api import ServerApi


__all__ = [
    "ErroConfiguracaoMongoDB",
    "TEMPO_LIMITE_SELECAO_MS",
    "carregar_mongodb_database",
    "carregar_mongodb_uri",
    "criar_cliente_mongodb",
    "diagnosticar_mongodb",
]


TEMPO_LIMITE_SELECAO_MS = 5_000
FabricaCliente = Callable[..., Any]


class ErroConfiguracaoMongoDB(RuntimeError):
    """Indica configuração inválida ou falha no diagnóstico do MongoDB."""


def _carregar_variavel_env(raiz: str | Path, nome: str) -> str:
    caminho = Path(raiz) / ".env"
    try:
        linhas = caminho.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as erro:
        raise ErroConfiguracaoMongoDB(
            f"{nome}: não foi possível ler {caminho}"
        ) from erro

    valores: list[str] = []
    for linha in linhas:
        limpa = linha.strip()
        if not limpa or limpa.startswith("#") or "=" not in limpa:
            continue
        chave, valor = limpa.split("=", 1)
        if chave.strip() == nome:
            valores.append(valor.strip())

    if not valores:
        raise ErroConfiguracaoMongoDB(f"{caminho}: variável {nome} ausente")
    if len(valores) > 1:
        raise ErroConfiguracaoMongoDB(f"{caminho}: variável {nome} duplicada")

    valor = valores[0]
    if not valor:
        raise ErroConfiguracaoMongoDB(
            f"{caminho}: variável {nome} não pode ser vazia"
        )
    return valor


def carregar_mongodb_uri(raiz: str | Path) -> str:
    """Lê e valida MONGODB_URI sem expor o valor em mensagens de erro."""
    uri = _carregar_variavel_env(raiz, "MONGODB_URI")
    if not uri.startswith(("mongodb://", "mongodb+srv://")):
        raise ErroConfiguracaoMongoDB(
            f"{Path(raiz) / '.env'}: MONGODB_URI deve usar mongodb:// ou mongodb+srv://"
        )
    return uri


def carregar_mongodb_database(raiz: str | Path) -> str:
    """Lê o nome não vazio da database usada pela aplicação."""
    return _carregar_variavel_env(raiz, "MONGODB_DATABASE")


def criar_cliente_mongodb(
    raiz: str | Path, *, fabrica: FabricaCliente = MongoClient
) -> Any:
    """Cria um cliente sem executar comandos ou selecionar banco de dados."""
    uri = carregar_mongodb_uri(raiz)
    try:
        return fabrica(
            uri,
            server_api=ServerApi("1"),
            serverSelectionTimeoutMS=TEMPO_LIMITE_SELECAO_MS,
        )
    except (PyMongoError, ValueError, TypeError) as erro:
        raise ErroConfiguracaoMongoDB(
            "não foi possível preparar o cliente MongoDB"
        ) from erro


def diagnosticar_mongodb(
    raiz: str | Path, *, fabrica: FabricaCliente = MongoClient
) -> None:
    """Executa somente ping e sempre encerra um cliente que foi criado."""
    cliente = criar_cliente_mongodb(raiz, fabrica=fabrica)
    try:
        cliente.admin.command({"ping": 1})
    except PyMongoError as erro:
        raise ErroConfiguracaoMongoDB(
            "falha ao conectar ao MongoDB: verifique rede, acesso e credenciais"
        ) from erro
    finally:
        cliente.close()
