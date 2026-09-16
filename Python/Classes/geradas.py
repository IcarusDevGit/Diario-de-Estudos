"""ARQUIVO GERADO AUTOMATICAMENTE. NÃO EDITE MANUALMENTE."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time
from math import isclose

__all__ = ('Pausa', 'Relatorio', 'RegistroDiario', 'Tarefa', 'SessaoEstudo', 'SessaoExercicio')

@dataclass(kw_only=True)
class Pausa:
    inicio: datetime | None = field(default=None, metadata={'opcional': False})
    fim: datetime | None = field(default=None, metadata={'opcional': True})
    duracao: str | None = field(default=None, init=False, metadata={'opcional': False, 'calculado': True, 'unidade': 'HH:MM:SS'})

    def __post_init__(self) -> None:
        pass

@dataclass(kw_only=True)
class Relatorio:
    data: date | None = field(default=None, metadata={'opcional': False})
    nome: str | None = field(default=None, metadata={'opcional': True})
    notas: str | None = field(default=None, metadata={'opcional': True})

    def __post_init__(self) -> None:
        pass

@dataclass(kw_only=True)
class RegistroDiario(Relatorio):
    dormi_dia_anterior: time | None = field(default=None, metadata={'opcional': True, 'unidade': 'HH:MM'})
    acordei: time | None = field(default=None, metadata={'opcional': False, 'unidade': 'HH:MM'})
    levantei_da_cama: time | None = field(default=None, metadata={'opcional': False, 'unidade': 'HH:MM'})
    cafe_da_manha: time | None = field(default=None, metadata={'opcional': True, 'unidade': 'HH:MM'})
    remedio: time | None = field(default=None, metadata={'opcional': True, 'unidade': 'HH:MM'})
    almoco: time | None = field(default=None, metadata={'opcional': True, 'unidade': 'HH:MM'})
    folga: bool | None = field(default=None, metadata={'opcional': False})
    concentracao: float | None = field(default=None, metadata={'opcional': True, 'minimo': 1, 'maximo': 5, 'passo': 0.5})
    exercicio_fisico: float | None = field(default=None, metadata={'opcional': True, 'minimo': 1, 'maximo': 5, 'passo': 0.5})
    ativacao_mental: float | None = field(default=None, metadata={'opcional': True, 'minimo': 1, 'maximo': 5, 'passo': 0.5})
    procrastinacao: float | None = field(default=None, metadata={'opcional': True, 'minimo': 1, 'maximo': 5, 'passo': 0.5})
    compulsao_alimentar: float | None = field(default=None, metadata={'opcional': True, 'minimo': 1, 'maximo': 5, 'passo': 0.5})
    estresse: float | None = field(default=None, metadata={'opcional': True, 'minimo': 1, 'maximo': 5, 'passo': 0.5})
    qualidade_do_sono: float | None = field(default=None, metadata={'opcional': True, 'minimo': 1, 'maximo': 5, 'passo': 0.5})
    alcool: float | None = field(default=None, metadata={'opcional': True, 'minimo': 1, 'maximo': 5, 'passo': 0.5})
    sexo_e_masturbacao: float | None = field(default=None, metadata={'opcional': True, 'minimo': 1, 'maximo': 5, 'passo': 0.5})
    motivacao: float | None = field(default=None, metadata={'opcional': True, 'minimo': 1, 'maximo': 5, 'passo': 0.5})
    fui_dormir: time | None = field(default=None, metadata={'opcional': True, 'unidade': 'HH:MM'})

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.concentracao is not None and self.concentracao < 1:
            raise ValueError('RegistroDiario' + '.concentracao viola minimo=1')
        if self.concentracao is not None and self.concentracao > 5:
            raise ValueError('RegistroDiario' + '.concentracao viola maximo=5')
        if self.concentracao is not None and not isclose((self.concentracao - 1) / 0.5, round((self.concentracao - 1) / 0.5), abs_tol=1e-9):
            raise ValueError('RegistroDiario' + '.concentracao viola passo=0.5')
        if self.exercicio_fisico is not None and self.exercicio_fisico < 1:
            raise ValueError('RegistroDiario' + '.exercicio_fisico viola minimo=1')
        if self.exercicio_fisico is not None and self.exercicio_fisico > 5:
            raise ValueError('RegistroDiario' + '.exercicio_fisico viola maximo=5')
        if self.exercicio_fisico is not None and not isclose((self.exercicio_fisico - 1) / 0.5, round((self.exercicio_fisico - 1) / 0.5), abs_tol=1e-9):
            raise ValueError('RegistroDiario' + '.exercicio_fisico viola passo=0.5')
        if self.ativacao_mental is not None and self.ativacao_mental < 1:
            raise ValueError('RegistroDiario' + '.ativacao_mental viola minimo=1')
        if self.ativacao_mental is not None and self.ativacao_mental > 5:
            raise ValueError('RegistroDiario' + '.ativacao_mental viola maximo=5')
        if self.ativacao_mental is not None and not isclose((self.ativacao_mental - 1) / 0.5, round((self.ativacao_mental - 1) / 0.5), abs_tol=1e-9):
            raise ValueError('RegistroDiario' + '.ativacao_mental viola passo=0.5')
        if self.procrastinacao is not None and self.procrastinacao < 1:
            raise ValueError('RegistroDiario' + '.procrastinacao viola minimo=1')
        if self.procrastinacao is not None and self.procrastinacao > 5:
            raise ValueError('RegistroDiario' + '.procrastinacao viola maximo=5')
        if self.procrastinacao is not None and not isclose((self.procrastinacao - 1) / 0.5, round((self.procrastinacao - 1) / 0.5), abs_tol=1e-9):
            raise ValueError('RegistroDiario' + '.procrastinacao viola passo=0.5')
        if self.compulsao_alimentar is not None and self.compulsao_alimentar < 1:
            raise ValueError('RegistroDiario' + '.compulsao_alimentar viola minimo=1')
        if self.compulsao_alimentar is not None and self.compulsao_alimentar > 5:
            raise ValueError('RegistroDiario' + '.compulsao_alimentar viola maximo=5')
        if self.compulsao_alimentar is not None and not isclose((self.compulsao_alimentar - 1) / 0.5, round((self.compulsao_alimentar - 1) / 0.5), abs_tol=1e-9):
            raise ValueError('RegistroDiario' + '.compulsao_alimentar viola passo=0.5')
        if self.estresse is not None and self.estresse < 1:
            raise ValueError('RegistroDiario' + '.estresse viola minimo=1')
        if self.estresse is not None and self.estresse > 5:
            raise ValueError('RegistroDiario' + '.estresse viola maximo=5')
        if self.estresse is not None and not isclose((self.estresse - 1) / 0.5, round((self.estresse - 1) / 0.5), abs_tol=1e-9):
            raise ValueError('RegistroDiario' + '.estresse viola passo=0.5')
        if self.qualidade_do_sono is not None and self.qualidade_do_sono < 1:
            raise ValueError('RegistroDiario' + '.qualidade_do_sono viola minimo=1')
        if self.qualidade_do_sono is not None and self.qualidade_do_sono > 5:
            raise ValueError('RegistroDiario' + '.qualidade_do_sono viola maximo=5')
        if self.qualidade_do_sono is not None and not isclose((self.qualidade_do_sono - 1) / 0.5, round((self.qualidade_do_sono - 1) / 0.5), abs_tol=1e-9):
            raise ValueError('RegistroDiario' + '.qualidade_do_sono viola passo=0.5')
        if self.alcool is not None and self.alcool < 1:
            raise ValueError('RegistroDiario' + '.alcool viola minimo=1')
        if self.alcool is not None and self.alcool > 5:
            raise ValueError('RegistroDiario' + '.alcool viola maximo=5')
        if self.alcool is not None and not isclose((self.alcool - 1) / 0.5, round((self.alcool - 1) / 0.5), abs_tol=1e-9):
            raise ValueError('RegistroDiario' + '.alcool viola passo=0.5')
        if self.sexo_e_masturbacao is not None and self.sexo_e_masturbacao < 1:
            raise ValueError('RegistroDiario' + '.sexo_e_masturbacao viola minimo=1')
        if self.sexo_e_masturbacao is not None and self.sexo_e_masturbacao > 5:
            raise ValueError('RegistroDiario' + '.sexo_e_masturbacao viola maximo=5')
        if self.sexo_e_masturbacao is not None and not isclose((self.sexo_e_masturbacao - 1) / 0.5, round((self.sexo_e_masturbacao - 1) / 0.5), abs_tol=1e-9):
            raise ValueError('RegistroDiario' + '.sexo_e_masturbacao viola passo=0.5')
        if self.motivacao is not None and self.motivacao < 1:
            raise ValueError('RegistroDiario' + '.motivacao viola minimo=1')
        if self.motivacao is not None and self.motivacao > 5:
            raise ValueError('RegistroDiario' + '.motivacao viola maximo=5')
        if self.motivacao is not None and not isclose((self.motivacao - 1) / 0.5, round((self.motivacao - 1) / 0.5), abs_tol=1e-9):
            raise ValueError('RegistroDiario' + '.motivacao viola passo=0.5')

@dataclass(kw_only=True)
class Tarefa:
    dia: date | None = field(default=None, metadata={'opcional': True})
    inicio: datetime | None = field(default=None, metadata={'opcional': False})
    fim: datetime | None = field(default=None, metadata={'opcional': True})
    pausas: list[Pausa] | None = field(default_factory=list, metadata={'opcional': False})
    duracao: str | None = field(default=None, init=False, metadata={'opcional': False, 'calculado': True, 'unidade': 'HH:MM:SS'})
    nome: str | None = field(default=None, metadata={'opcional': False})
    notas: str | None = field(default='', metadata={'opcional': False})

    def __post_init__(self) -> None:
        pass

@dataclass(kw_only=True)
class SessaoEstudo(Tarefa):
    concentracao: float | None = field(default=None, metadata={'opcional': True, 'minimo': 1, 'maximo': 5, 'passo': 0.5})
    motivacao: float | None = field(default=None, metadata={'opcional': True, 'minimo': 1, 'maximo': 5, 'passo': 0.5})
    procrastinacao: float | None = field(default=None, metadata={'opcional': True, 'minimo': 1, 'maximo': 5, 'passo': 0.5})
    ativacao_mental: float | None = field(default=None, metadata={'opcional': True, 'minimo': 1, 'maximo': 5, 'passo': 0.5})

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.concentracao is not None and self.concentracao < 1:
            raise ValueError('SessaoEstudo' + '.concentracao viola minimo=1')
        if self.concentracao is not None and self.concentracao > 5:
            raise ValueError('SessaoEstudo' + '.concentracao viola maximo=5')
        if self.concentracao is not None and not isclose((self.concentracao - 1) / 0.5, round((self.concentracao - 1) / 0.5), abs_tol=1e-9):
            raise ValueError('SessaoEstudo' + '.concentracao viola passo=0.5')
        if self.motivacao is not None and self.motivacao < 1:
            raise ValueError('SessaoEstudo' + '.motivacao viola minimo=1')
        if self.motivacao is not None and self.motivacao > 5:
            raise ValueError('SessaoEstudo' + '.motivacao viola maximo=5')
        if self.motivacao is not None and not isclose((self.motivacao - 1) / 0.5, round((self.motivacao - 1) / 0.5), abs_tol=1e-9):
            raise ValueError('SessaoEstudo' + '.motivacao viola passo=0.5')
        if self.procrastinacao is not None and self.procrastinacao < 1:
            raise ValueError('SessaoEstudo' + '.procrastinacao viola minimo=1')
        if self.procrastinacao is not None and self.procrastinacao > 5:
            raise ValueError('SessaoEstudo' + '.procrastinacao viola maximo=5')
        if self.procrastinacao is not None and not isclose((self.procrastinacao - 1) / 0.5, round((self.procrastinacao - 1) / 0.5), abs_tol=1e-9):
            raise ValueError('SessaoEstudo' + '.procrastinacao viola passo=0.5')
        if self.ativacao_mental is not None and self.ativacao_mental < 1:
            raise ValueError('SessaoEstudo' + '.ativacao_mental viola minimo=1')
        if self.ativacao_mental is not None and self.ativacao_mental > 5:
            raise ValueError('SessaoEstudo' + '.ativacao_mental viola maximo=5')
        if self.ativacao_mental is not None and not isclose((self.ativacao_mental - 1) / 0.5, round((self.ativacao_mental - 1) / 0.5), abs_tol=1e-9):
            raise ValueError('SessaoEstudo' + '.ativacao_mental viola passo=0.5')

@dataclass(kw_only=True)
class SessaoExercicio(Tarefa):
    performance: float | None = field(default=None, metadata={'opcional': True, 'minimo': 1, 'maximo': 5, 'passo': 0.5})
    motivacao: float | None = field(default=None, metadata={'opcional': True, 'minimo': 1, 'maximo': 5, 'passo': 0.5})
    procrastinacao: float | None = field(default=None, metadata={'opcional': True, 'minimo': 1, 'maximo': 5, 'passo': 0.5})

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.performance is not None and self.performance < 1:
            raise ValueError('SessaoExercicio' + '.performance viola minimo=1')
        if self.performance is not None and self.performance > 5:
            raise ValueError('SessaoExercicio' + '.performance viola maximo=5')
        if self.performance is not None and not isclose((self.performance - 1) / 0.5, round((self.performance - 1) / 0.5), abs_tol=1e-9):
            raise ValueError('SessaoExercicio' + '.performance viola passo=0.5')
        if self.motivacao is not None and self.motivacao < 1:
            raise ValueError('SessaoExercicio' + '.motivacao viola minimo=1')
        if self.motivacao is not None and self.motivacao > 5:
            raise ValueError('SessaoExercicio' + '.motivacao viola maximo=5')
        if self.motivacao is not None and not isclose((self.motivacao - 1) / 0.5, round((self.motivacao - 1) / 0.5), abs_tol=1e-9):
            raise ValueError('SessaoExercicio' + '.motivacao viola passo=0.5')
        if self.procrastinacao is not None and self.procrastinacao < 1:
            raise ValueError('SessaoExercicio' + '.procrastinacao viola minimo=1')
        if self.procrastinacao is not None and self.procrastinacao > 5:
            raise ValueError('SessaoExercicio' + '.procrastinacao viola maximo=5')
        if self.procrastinacao is not None and not isclose((self.procrastinacao - 1) / 0.5, round((self.procrastinacao - 1) / 0.5), abs_tol=1e-9):
            raise ValueError('SessaoExercicio' + '.procrastinacao viola passo=0.5')
