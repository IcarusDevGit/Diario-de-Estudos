"""Montagem e persistência do retrato agregado de um ciclo."""
from __future__ import annotations
from datetime import date
from pathlib import Path
from typing import Any, Callable
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from Python.Classes import RegistroDiario, Relatorio, Tarefa
from Python.ciclo_dia import listar_registros, ErroCicloDia
from Python.configuracao_mongodb import carregar_mongodb_database, criar_cliente_mongodb
from Python.serializacao_yaml import ler_yaml, modelo_para_dados, ErroSerializacaoYAML

COLLECTION_DIAS="dias"
class ErroPersistenciaDia(RuntimeError): pass

def montar_retrato(raiz: str|Path, data_ciclo: date)->dict[str,Any]:
    raiz=Path(raiz); relatorios=[]; diarios=[]
    try:
        for caminho in sorted((raiz/"Relatórios").glob("*.yaml")):
            modelo=ler_yaml(caminho)
            if not isinstance(modelo, Relatorio):
                continue
            if modelo.data==data_ciclo:
                relatorios.append(modelo_para_dados(modelo))
                if type(modelo) is RegistroDiario: diarios.append(modelo)
        atividades=[]
        for caminho in sorted((raiz/"Tarefas"/"Concluidas").glob("*.yaml")):
            modelo=ler_yaml(caminho)
            if not isinstance(modelo,Tarefa): raise ErroPersistenciaDia(f"atividade incompatível: {caminho}")
            if modelo.dia is None: raise ErroPersistenciaDia(f"atividade sem dia: {caminho}")
            if modelo.dia==data_ciclo:
                if modelo.fim is None or modelo.duracao is None: raise ErroPersistenciaDia(f"atividade incompleta: {caminho}")
                atividades.append(modelo_para_dados(modelo))
    except (ErroSerializacaoYAML,ErroCicloDia) as erro: raise ErroPersistenciaDia(str(erro)) from erro
    if len(diarios)!=1 or diarios[0].fui_dormir is None: raise ErroPersistenciaDia("ciclo exige exatamente um RegistroDiario finalizado")
    return {"versao":1,"data":data_ciclo.isoformat(),"relatorios":relatorios,"atividades":atividades}

def persistir_dia(raiz: str|Path, data_ciclo: date|None=None, *, fabrica:Callable[...,Any]=MongoClient)->date:
    try: registros=listar_registros(raiz)
    except ErroCicloDia as erro: raise ErroPersistenciaDia(str(erro)) from erro
    if data_ciclo is None:
        finais=[r.data for _,r in registros if r.fui_dormir is not None]
        if not finais: raise ErroPersistenciaDia("nenhum ciclo finalizado")
        data_ciclo=max(finais)
    documento=montar_retrato(raiz,data_ciclo)
    database=carregar_mongodb_database(raiz)
    cliente=criar_cliente_mongodb(raiz,fabrica=fabrica)
    try:
        colecao=cliente[database][COLLECTION_DIAS]
        colecao.create_index("data",unique=True)
        colecao.replace_one({"data":data_ciclo.isoformat()},documento,upsert=True)
    except PyMongoError as erro: raise ErroPersistenciaDia("falha ao persistir dia no MongoDB") from erro
    finally: cliente.close()
    return data_ciclo
