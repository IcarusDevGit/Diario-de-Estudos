"""Associa atividades legadas ao RegistroDiario da data de início."""
from __future__ import annotations
from pathlib import Path
from Python.Classes import Tarefa
from Python.ciclo_dia import listar_registros
from Python.gerenciamento_tarefas import carregar_fuso_horario
from Python.serializacao_yaml import ler_yaml, salvar_yaml

class ErroMigracaoVinculo(RuntimeError): pass

def migrar(raiz: str|Path)->list[Path]:
    raiz=Path(raiz); fuso=carregar_fuso_horario(raiz)
    datas={r.data for _,r in listar_registros(raiz)}; alterados=[]
    diretorios=[raiz/"Tarefas"/"Concluidas",raiz/"Tarefas"/"Tarefa em andamento"]
    for diretorio in diretorios:
        for caminho in sorted(diretorio.glob("*.yaml")):
            modelo=ler_yaml(caminho)
            if not isinstance(modelo,Tarefa): raise ErroMigracaoVinculo(f"atividade incompatível: {caminho}")
            if modelo.dia is not None: continue
            if modelo.inicio is None: raise ErroMigracaoVinculo(f"atividade sem inicio: {caminho}")
            data_inicio=modelo.inicio.astimezone(fuso).date()
            if data_inicio not in datas: raise ErroMigracaoVinculo(f"nenhum ciclo para atividade: {caminho}")
            modelo.dia=data_inicio; salvar_yaml(modelo,caminho); alterados.append(caminho)
    return alterados

def main()->int:
    try:
        for caminho in migrar(Path.cwd()): print(caminho)
        return 0
    except Exception as erro:
        print(f"Erro: {erro}"); return 1

if __name__=="__main__": raise SystemExit(main())
