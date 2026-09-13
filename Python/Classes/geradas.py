"""ARQUIVO GERADO AUTOMATICAMENTE. NÃO EDITE MANUALMENTE."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time

__all__ = ('Pausa', 'RegistroDiario', 'Tarefa', 'SessaoEstudo', 'SessaoExercicio')

@dataclass(kw_only=True)
class Pausa:
    inicio: datetime | None = field(default=None, metadata={'opcional': False})
    fim: datetime | None = field(default=None, metadata={'opcional': True})
    duracao: float | None = field(default=None, init=False, metadata={'opcional': False, 'calculado': True, 'unidade': 'horas'})

    def __post_init__(self) -> None:
        pass

@dataclass(kw_only=True)
class RegistroDiario:
    data: date | None = field(default=None, metadata={'opcional': False})
    dormi_dia_anterior: time | None = field(default=None, metadata={'opcional': True})
    acordei: time | None = field(default=None, metadata={'opcional': False})
    levantei_da_cama: time | None = field(default=None, metadata={'opcional': False})
    cafe_da_manha: time | None = field(default=None, metadata={'opcional': True})
    remedio: time | None = field(default=None, metadata={'opcional': True})
    almoco: time | None = field(default=None, metadata={'opcional': True})
    folga: bool | None = field(default=None, metadata={'opcional': False})
    concentracao: int | None = field(default=None, metadata={'opcional': True, 'minimo': 1, 'maximo': 5})
    exercicio_fisico: int | None = field(default=None, metadata={'opcional': True, 'minimo': 1, 'maximo': 5})
    ativacao_mental: int | None = field(default=None, metadata={'opcional': True, 'minimo': 1, 'maximo': 5})
    procrastinacao: int | None = field(default=None, metadata={'opcional': True, 'minimo': 1, 'maximo': 5})
    compulsao_alimentar: int | None = field(default=None, metadata={'opcional': True, 'minimo': 1, 'maximo': 5})
    estresse: int | None = field(default=None, metadata={'opcional': True, 'minimo': 1, 'maximo': 5})
    qualidade_do_sono: int | None = field(default=None, metadata={'opcional': True, 'minimo': 1, 'maximo': 5})
    alcool: int | None = field(default=None, metadata={'opcional': True, 'minimo': 1, 'maximo': 5})
    sexo_e_masturbacao: int | None = field(default=None, metadata={'opcional': True, 'minimo': 1, 'maximo': 5})
    motivacao: int | None = field(default=None, metadata={'opcional': True, 'minimo': 1, 'maximo': 5})
    fui_dormir: time | None = field(default=None, metadata={'opcional': True})

    def __post_init__(self) -> None:
        if self.concentracao is not None and self.concentracao < 1:
            raise ValueError('RegistroDiario' + '.concentracao viola minimo=1')
        if self.concentracao is not None and self.concentracao > 5:
            raise ValueError('RegistroDiario' + '.concentracao viola maximo=5')
        if self.exercicio_fisico is not None and self.exercicio_fisico < 1:
            raise ValueError('RegistroDiario' + '.exercicio_fisico viola minimo=1')
        if self.exercicio_fisico is not None and self.exercicio_fisico > 5:
            raise ValueError('RegistroDiario' + '.exercicio_fisico viola maximo=5')
        if self.ativacao_mental is not None and self.ativacao_mental < 1:
            raise ValueError('RegistroDiario' + '.ativacao_mental viola minimo=1')
        if self.ativacao_mental is not None and self.ativacao_mental > 5:
            raise ValueError('RegistroDiario' + '.ativacao_mental viola maximo=5')
        if self.procrastinacao is not None and self.procrastinacao < 1:
            raise ValueError('RegistroDiario' + '.procrastinacao viola minimo=1')
        if self.procrastinacao is not None and self.procrastinacao > 5:
            raise ValueError('RegistroDiario' + '.procrastinacao viola maximo=5')
        if self.compulsao_alimentar is not None and self.compulsao_alimentar < 1:
            raise ValueError('RegistroDiario' + '.compulsao_alimentar viola minimo=1')
        if self.compulsao_alimentar is not None and self.compulsao_alimentar > 5:
            raise ValueError('RegistroDiario' + '.compulsao_alimentar viola maximo=5')
        if self.estresse is not None and self.estresse < 1:
            raise ValueError('RegistroDiario' + '.estresse viola minimo=1')
        if self.estresse is not None and self.estresse > 5:
            raise ValueError('RegistroDiario' + '.estresse viola maximo=5')
        if self.qualidade_do_sono is not None and self.qualidade_do_sono < 1:
            raise ValueError('RegistroDiario' + '.qualidade_do_sono viola minimo=1')
        if self.qualidade_do_sono is not None and self.qualidade_do_sono > 5:
            raise ValueError('RegistroDiario' + '.qualidade_do_sono viola maximo=5')
        if self.alcool is not None and self.alcool < 1:
            raise ValueError('RegistroDiario' + '.alcool viola minimo=1')
        if self.alcool is not None and self.alcool > 5:
            raise ValueError('RegistroDiario' + '.alcool viola maximo=5')
        if self.sexo_e_masturbacao is not None and self.sexo_e_masturbacao < 1:
            raise ValueError('RegistroDiario' + '.sexo_e_masturbacao viola minimo=1')
        if self.sexo_e_masturbacao is not None and self.sexo_e_masturbacao > 5:
            raise ValueError('RegistroDiario' + '.sexo_e_masturbacao viola maximo=5')
        if self.motivacao is not None and self.motivacao < 1:
            raise ValueError('RegistroDiario' + '.motivacao viola minimo=1')
        if self.motivacao is not None and self.motivacao > 5:
            raise ValueError('RegistroDiario' + '.motivacao viola maximo=5')

@dataclass(kw_only=True)
class Tarefa:
    inicio: datetime | None = field(default=None, metadata={'opcional': False})
    fim: datetime | None = field(default=None, metadata={'opcional': True})
    pausas: list[Pausa] | None = field(default_factory=list, metadata={'opcional': False})
    duracao: float | None = field(default=None, init=False, metadata={'opcional': False, 'calculado': True, 'unidade': 'horas'})
    nome: str | None = field(default=None, metadata={'opcional': False})
    notas: str | None = field(default='', metadata={'opcional': False})

    def __post_init__(self) -> None:
        pass

@dataclass(kw_only=True)
class SessaoEstudo(Tarefa):
    concentracao: int | None = field(default=None, metadata={'opcional': True, 'minimo': 1, 'maximo': 5})
    motivacao: int | None = field(default=None, metadata={'opcional': True, 'minimo': 1, 'maximo': 5})
    procrastinacao: int | None = field(default=None, metadata={'opcional': True, 'minimo': 1, 'maximo': 5})
    ativacao_mental: int | None = field(default=None, metadata={'opcional': True, 'minimo': 1, 'maximo': 5})

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.concentracao is not None and self.concentracao < 1:
            raise ValueError('SessaoEstudo' + '.concentracao viola minimo=1')
        if self.concentracao is not None and self.concentracao > 5:
            raise ValueError('SessaoEstudo' + '.concentracao viola maximo=5')
        if self.motivacao is not None and self.motivacao < 1:
            raise ValueError('SessaoEstudo' + '.motivacao viola minimo=1')
        if self.motivacao is not None and self.motivacao > 5:
            raise ValueError('SessaoEstudo' + '.motivacao viola maximo=5')
        if self.procrastinacao is not None and self.procrastinacao < 1:
            raise ValueError('SessaoEstudo' + '.procrastinacao viola minimo=1')
        if self.procrastinacao is not None and self.procrastinacao > 5:
            raise ValueError('SessaoEstudo' + '.procrastinacao viola maximo=5')
        if self.ativacao_mental is not None and self.ativacao_mental < 1:
            raise ValueError('SessaoEstudo' + '.ativacao_mental viola minimo=1')
        if self.ativacao_mental is not None and self.ativacao_mental > 5:
            raise ValueError('SessaoEstudo' + '.ativacao_mental viola maximo=5')

@dataclass(kw_only=True)
class SessaoExercicio(Tarefa):
    performance: int | None = field(default=None, metadata={'opcional': True, 'minimo': 1, 'maximo': 5})
    motivacao: int | None = field(default=None, metadata={'opcional': True, 'minimo': 1, 'maximo': 5})
    procrastinacao: int | None = field(default=None, metadata={'opcional': True, 'minimo': 1, 'maximo': 5})

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.performance is not None and self.performance < 1:
            raise ValueError('SessaoExercicio' + '.performance viola minimo=1')
        if self.performance is not None and self.performance > 5:
            raise ValueError('SessaoExercicio' + '.performance viola maximo=5')
        if self.motivacao is not None and self.motivacao < 1:
            raise ValueError('SessaoExercicio' + '.motivacao viola minimo=1')
        if self.motivacao is not None and self.motivacao > 5:
            raise ValueError('SessaoExercicio' + '.motivacao viola maximo=5')
        if self.procrastinacao is not None and self.procrastinacao < 1:
            raise ValueError('SessaoExercicio' + '.procrastinacao viola minimo=1')
        if self.procrastinacao is not None and self.procrastinacao > 5:
            raise ValueError('SessaoExercicio' + '.procrastinacao viola maximo=5')
