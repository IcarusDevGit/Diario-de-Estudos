"""Descoberta e validação dos ciclos diários locais."""
from __future__ import annotations
import re
from datetime import date
from pathlib import Path
from Python.Classes import RegistroDiario
from Python.serializacao_yaml import ErroSerializacaoYAML, ler_yaml

_NOME = re.compile(r"RD-(\d{4}-\d{2}-\d{2})\.yaml")

class ErroCicloDia(RuntimeError): pass

def listar_registros(raiz: str | Path) -> list[tuple[Path, RegistroDiario]]:
    resultado=[]
    for caminho in sorted((Path(raiz)/"Relatórios").glob("RD-*.yaml")):
        match=_NOME.fullmatch(caminho.name)
        try: modelo=ler_yaml(caminho)
        except ErroSerializacaoYAML as erro: raise ErroCicloDia(str(erro)) from erro
        if match is None or type(modelo) is not RegistroDiario:
            raise ErroCicloDia(f"relatório diário incompatível: {caminho}")
        if modelo.data != date.fromisoformat(match.group(1)):
            raise ErroCicloDia(f"data diverge do nome: {caminho}")
        resultado.append((caminho,modelo))
    return resultado

def ciclo_aberto(raiz: str | Path, *, obrigatorio: bool=True):
    abertos=[item for item in listar_registros(raiz) if item[1].fui_dormir is None]
    if len(abertos)>1: raise ErroCicloDia("múltiplos ciclos diários abertos")
    if not abertos:
        if obrigatorio: raise ErroCicloDia("nenhum ciclo diário aberto")
        return None
    return abertos[0]
