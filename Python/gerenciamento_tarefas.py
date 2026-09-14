"""Ciclo de vida de tarefas, sessões e pausas persistidas em YAML."""

from __future__ import annotations

import os
import re
import tempfile
from collections.abc import Callable
from datetime import datetime, timedelta, timezone, tzinfo
from pathlib import Path
from typing import TypeAlias

from Python.Classes import Pausa, SessaoEstudo, SessaoExercicio, Tarefa
from Python.duracao import (
    ErroDuracao,
    formatar_intervalo,
    formatar_microssegundos,
    intervalo_microssegundos,
)
from Python.serializacao_yaml import ErroSerializacaoYAML, ler_yaml, salvar_yaml


__all__ = [
    "ErroGerenciamento",
    "GerenciadorTarefas",
    "TipoAtividade",
    "carregar_fuso_horario",
    "interpretar_fuso_horario",
]


TipoAtividade: TypeAlias = type[Tarefa]
TIPOS_ATIVIDADE: tuple[type[Tarefa], ...] = (Tarefa, SessaoEstudo, SessaoExercicio)
_PADRAO_FUSO = re.compile(r"UTC([+-])(\d{2}):(\d{2})")


class ErroGerenciamento(RuntimeError):
    """Indica uma operação inválida no ciclo de vida das atividades."""


def interpretar_fuso_horario(valor: str) -> timezone:
    """Interpreta um deslocamento estrito no formato UTC±HH:MM."""
    correspondencia = _PADRAO_FUSO.fullmatch(valor)
    if correspondencia is None:
        raise ErroGerenciamento(
            "FUSO_HORARIO inválido: use o formato UTC±HH:MM, por exemplo UTC-03:00"
        )
    sinal, horas_texto, minutos_texto = correspondencia.groups()
    horas, minutos = int(horas_texto), int(minutos_texto)
    if horas > 23 or minutos > 59:
        raise ErroGerenciamento(
            "FUSO_HORARIO inválido: deslocamento deve ser menor que 24 horas"
        )
    deslocamento = timedelta(hours=horas, minutes=minutos)
    if sinal == "-":
        deslocamento = -deslocamento
    try:
        return timezone(deslocamento, name=valor)
    except ValueError as erro:
        raise ErroGerenciamento(f"FUSO_HORARIO inválido: {erro}") from erro


def carregar_fuso_horario(raiz: str | Path) -> timezone:
    """Lê somente FUSO_HORARIO do .env da raiz informada."""
    caminho = Path(raiz) / ".env"
    try:
        linhas = caminho.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as erro:
        raise ErroGerenciamento(
            f"FUSO_HORARIO: não foi possível ler {caminho}: {erro}"
        ) from erro
    valores: list[str] = []
    for numero, linha in enumerate(linhas, start=1):
        limpa = linha.strip()
        if not limpa or limpa.startswith("#"):
            continue
        if "=" not in limpa:
            continue
        chave, valor = limpa.split("=", 1)
        if chave.strip() == "FUSO_HORARIO":
            if not valor.strip():
                raise ErroGerenciamento(
                    f"{caminho}:{numero}: FUSO_HORARIO não pode ser vazio"
                )
            valores.append(valor.strip())
    if not valores:
        raise ErroGerenciamento(f"{caminho}: variável FUSO_HORARIO ausente")
    if len(valores) > 1:
        raise ErroGerenciamento(f"{caminho}: variável FUSO_HORARIO duplicada")
    return interpretar_fuso_horario(valores[0])


def _gravar_bytes_atomico(caminho: Path, conteudo: bytes) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    temporario: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "wb",
            dir=caminho.parent,
            prefix=f".{caminho.name}.",
            suffix=".tmp",
            delete=False,
        ) as stream:
            stream.write(conteudo)
            stream.flush()
            os.fsync(stream.fileno())
            temporario = stream.name
        os.replace(temporario, caminho)
        temporario = None
    finally:
        if temporario is not None:
            Path(temporario).unlink(missing_ok=True)


class GerenciadorTarefas:
    """Coordena transições entre os arquivos YAML operacionais."""

    def __init__(
        self,
        raiz: str | Path,
        *,
        relogio: Callable[[], datetime] | None = None,
        fuso: tzinfo | None = None,
    ) -> None:
        self.raiz = Path(raiz)
        self.diretorio_ativas = self.raiz / "Tarefas" / "Tarefa em andamento"
        self.diretorio_pausas = self.raiz / "Tarefas" / "Pausas"
        self.diretorio_concluidas = self.raiz / "Tarefas" / "Concluidas"
        self.fuso = fuso or carregar_fuso_horario(self.raiz)
        self._relogio = relogio or (lambda: datetime.now(self.fuso))

    def _agora(self) -> datetime:
        instante = self._relogio()
        if not isinstance(instante, datetime):
            raise ErroGerenciamento("relógio deve retornar datetime")
        if instante.tzinfo is None or instante.utcoffset() is None:
            raise ErroGerenciamento("relógio deve retornar datetime com fuso horário")
        return instante.astimezone(self.fuso)

    @staticmethod
    def _arquivos_yaml(diretorio: Path) -> list[Path]:
        if not diretorio.exists():
            return []
        if not diretorio.is_dir():
            raise ErroGerenciamento(f"{diretorio}: era esperado um diretório")
        return sorted(
            (
                item
                for item in diretorio.iterdir()
                if item.is_file() and item.suffix.lower() in {".yaml", ".yml"}
            ),
            key=lambda item: (item.name.casefold(), item.name),
        )

    def _descobrir_unico(
        self, diretorio: Path, descricao: str, *, obrigatorio: bool
    ) -> Path | None:
        arquivos = self._arquivos_yaml(diretorio)
        if len(arquivos) > 1:
            nomes = ", ".join(str(item) for item in arquivos)
            raise ErroGerenciamento(
                f"estado inconsistente: múltiplos arquivos de {descricao}: {nomes}"
            )
        if not arquivos:
            if obrigatorio:
                raise ErroGerenciamento(f"não existe {descricao} em andamento")
            return None
        return arquivos[0]

    @staticmethod
    def _carregar_como(caminho: Path, esperado: type[object], descricao: str) -> object:
        try:
            modelo = ler_yaml(caminho)
        except ErroSerializacaoYAML as erro:
            raise ErroGerenciamento(str(erro)) from erro
        if not isinstance(modelo, esperado):
            raise ErroGerenciamento(
                f"{caminho}: classe {type(modelo).__name__} incompatível com {descricao}"
            )
        return modelo

    def _atividade_ativa(self, *, obrigatoria: bool) -> tuple[Path, Tarefa] | None:
        caminho = self._descobrir_unico(
            self.diretorio_ativas, "tarefa ou sessão", obrigatorio=obrigatoria
        )
        if caminho is None:
            return None
        return caminho, self._carregar_como(caminho, Tarefa, "tarefa ou sessão")  # type: ignore[return-value]

    def _pausa_ativa(self, *, obrigatoria: bool) -> tuple[Path, Pausa] | None:
        caminho = self._descobrir_unico(
            self.diretorio_pausas, "pausa", obrigatorio=obrigatoria
        )
        if caminho is None:
            return None
        pausa = self._carregar_como(caminho, Pausa, "pausa")
        if type(pausa) is not Pausa:
            raise ErroGerenciamento(f"{caminho}: classe incompatível com pausa")
        return caminho, pausa  # type: ignore[return-value]

    def iniciar_atividade(
        self, classe: TipoAtividade = Tarefa, *, nome: str | None = None
    ) -> Path:
        if classe not in TIPOS_ATIVIDADE:
            raise ErroGerenciamento(f"classe de atividade não permitida: {classe!r}")
        existente = self._atividade_ativa(obrigatoria=False)
        if existente is not None:
            caminho, atividade = existente
            raise ErroGerenciamento(
                f"já existe {type(atividade).__name__} em andamento: {caminho}"
            )
        caminho = self.diretorio_ativas / "tarefa.yaml"
        atividade = classe(inicio=self._agora(), nome=nome)
        try:
            salvar_yaml(atividade, caminho)
        except ErroSerializacaoYAML as erro:
            raise ErroGerenciamento(str(erro)) from erro
        return caminho

    def iniciar_pausa(self) -> Path:
        self._atividade_ativa(obrigatoria=True)
        existente = self._pausa_ativa(obrigatoria=False)
        if existente is not None:
            caminho, _ = existente
            raise ErroGerenciamento(f"já existe pausa em andamento: {caminho}")
        caminho = self.diretorio_pausas / "pausa.yaml"
        try:
            salvar_yaml(Pausa(inicio=self._agora()), caminho)
        except ErroSerializacaoYAML as erro:
            raise ErroGerenciamento(str(erro)) from erro
        return caminho

    @staticmethod
    def _preparar_pausa(pausa: Pausa, fim: datetime, caminho: Path) -> None:
        pausa.fim = fim
        try:
            pausa.duracao = formatar_intervalo(
                pausa.inicio, fim, caminho=str(caminho)  # type: ignore[arg-type]
            )
        except ErroDuracao as erro:
            raise ErroGerenciamento(str(erro)) from erro

    @staticmethod
    def _anexar_pausa(atividade: Tarefa, pausa: Pausa, caminho: Path) -> None:
        if atividade.pausas is None:
            atividade.pausas = []
        if not isinstance(atividade.pausas, list) or not all(
            type(item) is Pausa for item in atividade.pausas
        ):
            raise ErroGerenciamento(f"{caminho}.pausas: lista de pausas inválida")
        atividade.pausas.append(pausa)

    def finalizar_pausa(self) -> Path:
        caminho_tarefa, atividade = self._atividade_ativa(obrigatoria=True)  # type: ignore[misc]
        caminho_pausa, pausa = self._pausa_ativa(obrigatoria=True)  # type: ignore[misc]
        original_tarefa = caminho_tarefa.read_bytes()
        original_pausa = caminho_pausa.read_bytes()
        self._preparar_pausa(pausa, self._agora(), caminho_pausa)
        self._anexar_pausa(atividade, pausa, caminho_tarefa)
        try:
            salvar_yaml(atividade, caminho_tarefa)
            caminho_pausa.unlink()
        except (OSError, ErroSerializacaoYAML) as erro:
            try:
                _gravar_bytes_atomico(caminho_tarefa, original_tarefa)
                _gravar_bytes_atomico(caminho_pausa, original_pausa)
            except OSError as restauracao:
                raise ErroGerenciamento(
                    f"falha ao finalizar pausa ({erro}) e ao restaurar estado ({restauracao})"
                ) from restauracao
            raise ErroGerenciamento(f"não foi possível finalizar pausa: {erro}") from erro
        return caminho_tarefa

    @staticmethod
    def _validar_pausas_concluidas(atividade: Tarefa, caminho: Path) -> int:
        if atividade.pausas is None:
            atividade.pausas = []
        if not isinstance(atividade.pausas, list):
            raise ErroGerenciamento(f"{caminho}.pausas: era esperada uma lista")
        total_microssegundos = 0
        for indice, pausa in enumerate(atividade.pausas):
            contexto = f"{caminho}.pausas[{indice}]"
            if type(pausa) is not Pausa:
                raise ErroGerenciamento(f"{contexto}: item não é Pausa")
            try:
                microssegundos = intervalo_microssegundos(
                    pausa.inicio, pausa.fim, caminho=contexto  # type: ignore[arg-type]
                )
                calculada = formatar_microssegundos(microssegundos)
            except ErroDuracao as erro:
                raise ErroGerenciamento(str(erro)) from erro
            if pausa.duracao != calculada:
                raise ErroGerenciamento(f"{contexto}.duracao: não corresponde ao intervalo")
            total_microssegundos += microssegundos
        return total_microssegundos

    def _destino_concluida(self, atividade: Tarefa) -> Path:
        if not isinstance(atividade.inicio, datetime):
            raise ErroGerenciamento("atividade.inicio: campo deve ser preenchido")
        base = f"{atividade.inicio.strftime('%Y-%m-%d_%H-%M-%S')}_{type(atividade).__name__}"
        candidato = self.diretorio_concluidas / f"{base}.yaml"
        numero = 2
        while candidato.exists():
            candidato = self.diretorio_concluidas / f"{base}_{numero}.yaml"
            numero += 1
        return candidato

    def finalizar_atividade(self) -> Path:
        caminho_tarefa, atividade = self._atividade_ativa(obrigatoria=True)  # type: ignore[misc]
        pausa_ativa = self._pausa_ativa(obrigatoria=False)
        original_tarefa = caminho_tarefa.read_bytes()
        original_pausa: bytes | None = None
        caminho_pausa: Path | None = None
        fim = self._agora()
        if pausa_ativa is not None:
            caminho_pausa, pausa = pausa_ativa
            original_pausa = caminho_pausa.read_bytes()
            self._preparar_pausa(pausa, fim, caminho_pausa)
            self._anexar_pausa(atividade, pausa, caminho_tarefa)
        total_pausas = self._validar_pausas_concluidas(atividade, caminho_tarefa)
        atividade.fim = fim
        try:
            total_atividade = intervalo_microssegundos(
                atividade.inicio, fim, caminho=str(caminho_tarefa)  # type: ignore[arg-type]
            )
        except ErroDuracao as erro:
            raise ErroGerenciamento(str(erro)) from erro
        duracao_liquida = total_atividade - total_pausas
        if duracao_liquida < 0:
            raise ErroGerenciamento(f"{caminho_tarefa}.duracao: duração líquida negativa")
        atividade.duracao = formatar_microssegundos(duracao_liquida)
        destino = self._destino_concluida(atividade)
        removeu_tarefa = False
        removeu_pausa = False
        try:
            salvar_yaml(atividade, destino)
            caminho_tarefa.unlink()
            removeu_tarefa = True
            if caminho_pausa is not None:
                caminho_pausa.unlink()
                removeu_pausa = True
        except (OSError, ErroSerializacaoYAML) as erro:
            try:
                if removeu_tarefa or not caminho_tarefa.exists():
                    _gravar_bytes_atomico(caminho_tarefa, original_tarefa)
                if caminho_pausa is not None and original_pausa is not None:
                    if removeu_pausa or not caminho_pausa.exists():
                        _gravar_bytes_atomico(caminho_pausa, original_pausa)
                destino.unlink(missing_ok=True)
            except OSError as restauracao:
                raise ErroGerenciamento(
                    f"falha ao finalizar tarefa ({erro}) e ao restaurar estado ({restauracao})"
                ) from restauracao
            raise ErroGerenciamento(f"não foi possível finalizar tarefa: {erro}") from erro
        return destino
