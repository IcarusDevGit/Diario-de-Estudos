"""Representação e aritmética de durações no formato HH:MM:SS."""

from __future__ import annotations

import re
from datetime import UTC, datetime, timedelta


__all__ = [
    "ErroDuracao",
    "duracao_para_segundos",
    "formatar_intervalo",
    "formatar_microssegundos",
    "formatar_segundos",
    "intervalo_microssegundos",
]


_FORMATO = re.compile(r"(\d{2,}):([0-5]\d):([0-5]\d)")
_MICROSSEGUNDOS_POR_SEGUNDO = 1_000_000


class ErroDuracao(ValueError):
    """Indica uma duração negativa ou fora do formato canônico."""


def duracao_para_segundos(valor: str, *, caminho: str = "duracao") -> int:
    if not isinstance(valor, str):
        raise ErroDuracao(f"{caminho}: duração deve ser texto HH:MM:SS")
    correspondencia = _FORMATO.fullmatch(valor)
    if correspondencia is None:
        raise ErroDuracao(f"{caminho}: duração inválida; use HH:MM:SS")
    horas, minutos, segundos = map(int, correspondencia.groups())
    return horas * 3600 + minutos * 60 + segundos


def formatar_segundos(segundos: int) -> str:
    if type(segundos) is not int:
        raise ErroDuracao("segundos deve ser um inteiro")
    if segundos < 0:
        raise ErroDuracao("duração não pode ser negativa")
    horas, resto = divmod(segundos, 3600)
    minutos, segundos = divmod(resto, 60)
    return f"{horas:02d}:{minutos:02d}:{segundos:02d}"


def formatar_microssegundos(microssegundos: int) -> str:
    if type(microssegundos) is not int:
        raise ErroDuracao("microssegundos deve ser um inteiro")
    if microssegundos < 0:
        raise ErroDuracao("duração não pode ser negativa")
    segundos = (
        microssegundos + _MICROSSEGUNDOS_POR_SEGUNDO // 2
    ) // _MICROSSEGUNDOS_POR_SEGUNDO
    return formatar_segundos(segundos)


def _microssegundos(delta: timedelta) -> int:
    return (
        delta.days * 86_400 * _MICROSSEGUNDOS_POR_SEGUNDO
        + delta.seconds * _MICROSSEGUNDOS_POR_SEGUNDO
        + delta.microseconds
    )


def intervalo_microssegundos(
    inicio: datetime, fim: datetime, *, caminho: str = "intervalo"
) -> int:
    if not isinstance(inicio, datetime):
        raise ErroDuracao(f"{caminho}.inicio: deve ser datetime")
    if not isinstance(fim, datetime):
        raise ErroDuracao(f"{caminho}.fim: deve ser datetime")
    if inicio.tzinfo is None or inicio.utcoffset() is None:
        raise ErroDuracao(f"{caminho}.inicio: datetime deve possuir fuso horário")
    if fim.tzinfo is None or fim.utcoffset() is None:
        raise ErroDuracao(f"{caminho}.fim: datetime deve possuir fuso horário")
    resultado = _microssegundos(fim.astimezone(UTC) - inicio.astimezone(UTC))
    if resultado < 0:
        raise ErroDuracao(f"{caminho}: fim não pode ser anterior ao início")
    return resultado


def formatar_intervalo(
    inicio: datetime, fim: datetime, *, caminho: str = "intervalo"
) -> str:
    return formatar_microssegundos(
        intervalo_microssegundos(inicio, fim, caminho=caminho)
    )
