"""Gerenciamento e criação de relatórios genéricos locais."""

from __future__ import annotations

import os
import re
import tempfile
import unicodedata
from datetime import date, datetime
from pathlib import Path

from Python.Classes import Relatorio
from Python.gerenciamento_tarefas import ErroGerenciamento, carregar_fuso_horario
from Python.serializacao_yaml import (
    ErroSerializacaoYAML,
    modelo_para_dados,
    modelo_para_yaml,
    yaml_para_modelo,
)


class ErroGerenciamentoRelatorio(RuntimeError):
    """Indica uma falha na validação ou criação de relatórios."""


def normalizar_slug(nome: str) -> str:
    """Normaliza Unicode para ASCII, converte sequências não alfanuméricas em hífens."""
    nfkd = unicodedata.normalize("NFKD", nome)
    ascii_texto = nfkd.encode("ascii", "ignore").decode("ascii").lower()
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_texto).strip("-")
    return slug or "relatorio"


class GerenciadorRelatorios:
    """Gerencia a criação e o armazenamento atômico de relatórios genéricos."""

    def __init__(self, raiz: str | Path) -> None:
        self.raiz = Path(raiz)
        self.diretorio_relatorios = self.raiz / "Relatórios"

    def criar_relatorio(
        self,
        nome: str,
        data: date | str | None = None,
    ) -> Path:
        """Cria e salva atomicamente um Relatorio genérico sem sobrescrever destinos."""
        if not isinstance(nome, str):
            raise ErroGerenciamentoRelatorio("o nome do relatório deve ser texto")
        nome_normalizado = nome.strip()
        if not nome_normalizado:
            raise ErroGerenciamentoRelatorio("o nome do relatório não pode ser vazio")

        data_resolvida: date
        if data is None:
            try:
                fuso = carregar_fuso_horario(self.raiz)
            except ErroGerenciamento as erro:
                raise ErroGerenciamentoRelatorio(
                    f"configuração temporal inválida: {erro}"
                ) from erro
            data_resolvida = datetime.now(fuso).date()
        elif isinstance(data, str):
            try:
                data_resolvida = date.fromisoformat(data)
            except ValueError as erro:
                raise ErroGerenciamentoRelatorio(
                    f"data inválida: {data!r}. Use o formato ISO YYYY-MM-DD, por exemplo 2026-09-15"
                ) from erro
        elif isinstance(data, date):
            data_resolvida = data
        else:
            raise ErroGerenciamentoRelatorio(
                f"data inválida: {data!r}. Use o formato ISO YYYY-MM-DD, por exemplo 2026-09-15"
            )

        try:
            relatorio = Relatorio(data=data_resolvida, nome=nome_normalizado, notas=None)
        except (TypeError, ValueError) as erro:
            raise ErroGerenciamentoRelatorio(f"dados inválidos para Relatorio: {erro}") from erro

        slug = normalizar_slug(nome_normalizado)
        return self._salvar_sem_sobrescrita(relatorio, data_resolvida, slug)

    def _salvar_sem_sobrescrita(
        self, relatorio: Relatorio, data: date, slug: str
    ) -> Path:
        try:
            texto = modelo_para_yaml(relatorio)
            reconstruido = yaml_para_modelo(texto)
            if modelo_para_dados(reconstruido) != modelo_para_dados(relatorio):
                raise ErroGerenciamentoRelatorio(
                    "validação de ida e volta do modelo produziu dados diferentes"
                )
        except ErroSerializacaoYAML as erro:
            raise ErroGerenciamentoRelatorio(
                f"falha de serialização do relatório: {erro}"
            ) from erro

        self.diretorio_relatorios.mkdir(parents=True, exist_ok=True)
        indice = 1
        while True:
            sufixo = "" if indice == 1 else f"-{indice}"
            nome_arquivo = f"RG-{data.isoformat()}-{slug}{sufixo}.yaml"
            caminho_final = self.diretorio_relatorios / nome_arquivo
            if caminho_final.exists():
                indice += 1
                continue

            temporario: str | None = None
            try:
                with tempfile.NamedTemporaryFile(
                    "w",
                    encoding="utf-8",
                    newline="\n",
                    dir=self.diretorio_relatorios,
                    prefix=f".{nome_arquivo}.",
                    suffix=".tmp",
                    delete=False,
                ) as stream:
                    stream.write(texto)
                    stream.flush()
                    os.fsync(stream.fileno())
                    temporario = stream.name

                if caminho_final.exists():
                    Path(temporario).unlink(missing_ok=True)
                    temporario = None
                    indice += 1
                    continue

                os.replace(temporario, caminho_final)
                temporario = None
                return caminho_final
            except OSError as erro:
                raise ErroGerenciamentoRelatorio(
                    f"não foi possível gravar o relatório: {erro}"
                ) from erro
            finally:
                if temporario is not None:
                    Path(temporario).unlink(missing_ok=True)
