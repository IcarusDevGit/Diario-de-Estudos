from __future__ import annotations
import tempfile, unittest
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock
from pymongo.errors import OperationFailure
from Python.Classes import RegistroDiario, Relatorio, SessaoEstudo, Tarefa
from Python.ciclo_dia import ErroCicloDia, ciclo_aberto, listar_registros
from Python.migrar_vinculos_dia import ErroMigracaoVinculo, migrar
from Python.persistencia_dia import ErroPersistenciaDia, montar_retrato, persistir_dia
from Python.serializacao_yaml import ler_yaml, salvar_yaml
from Python.cli import main
from unittest.mock import patch
import io
from contextlib import redirect_stdout, redirect_stderr

FUSO=timezone(-timedelta(hours=3))

class PersistenciaDiaTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.raiz=Path(self.tmp.name)
        (self.raiz/".env").write_text("FUSO_HORARIO=UTC-03:00\nMONGODB_URI=mongodb://segredo\nMONGODB_DATABASE=diario_estudos\n",encoding="utf-8")
        self.data=date(2026,9,15); self.rel=self.raiz/"Relatórios"/"RD-2026-09-15.yaml"

    def salvar_relatorio(self, final=True):
        salvar_yaml(RegistroDiario(data=self.data,acordei=time(7),levantei_da_cama=time(7,10),folga=False,fui_dormir=time(23,40) if final else None),self.rel)

    def test_ciclo_valida_aberto_fechado_e_inconsistente(self):
        self.assertEqual(listar_registros(self.raiz),[])
        self.salvar_relatorio(False); self.assertEqual(ciclo_aberto(self.raiz)[1].data,self.data)
        salvar_yaml(RegistroDiario(data=date(2026,9,14)),self.raiz/"Relatórios"/"RD-2026-09-14.yaml")
        with self.assertRaisesRegex(ErroCicloDia,"múltiplos"): ciclo_aberto(self.raiz)

    def test_monta_retrato_com_atividade_e_pausa_preservadas(self):
        self.salvar_relatorio()
        tarefa=SessaoEstudo(dia=self.data,inicio=datetime(2026,9,15,23,tzinfo=FUSO),fim=datetime(2026,9,16,0,tzinfo=FUSO),nome="estudo")
        tarefa.duracao="01:00:00"; salvar_yaml(tarefa,self.raiz/"Tarefas"/"Concluidas"/"a.yaml")
        doc=montar_retrato(self.raiz,self.data)
        self.assertEqual((doc["versao"],doc["data"]),(1,"2026-09-15"))
        self.assertEqual(doc["relatorios"][0]["fui_dormir"],"23:40")
        self.assertEqual(doc["atividades"][0]["classe"],"SessaoEstudo")
        self.assertEqual(doc["atividades"][0]["duracao"],"01:00:00")

    def test_rejeita_local_antes_de_cliente(self):
        self.salvar_relatorio(False); fabrica=MagicMock()
        with self.assertRaises(ErroPersistenciaDia): persistir_dia(self.raiz,self.data,fabrica=fabrica)
        fabrica.assert_not_called()

    def test_upsert_indice_fechamento_e_erro_sanitizado(self):
        self.salvar_relatorio(); cliente=MagicMock(); colecao=cliente.__getitem__.return_value.__getitem__.return_value
        persistir_dia(self.raiz,self.data,fabrica=MagicMock(return_value=cliente))
        colecao.create_index.assert_called_once_with("data",unique=True)
        args=colecao.replace_one.call_args; self.assertEqual(args.args[0],{"data":"2026-09-15"}); self.assertTrue(args.kwargs["upsert"])
        cliente.close.assert_called_once()
        colecao.create_index.side_effect=OperationFailure("mongodb://usuario:senha@host")
        cliente.reset_mock()
        with self.assertRaises(ErroPersistenciaDia) as erro: persistir_dia(self.raiz,self.data,fabrica=MagicMock(return_value=cliente))
        self.assertNotIn("senha",str(erro.exception)); cliente.close.assert_called_once()

    def test_migracao_legada(self):
        self.salvar_relatorio(False); caminho=self.raiz/"Tarefas"/"Concluidas"/"a.yaml"
        salvar_yaml(Tarefa(inicio=datetime(2026,9,15,10,tzinfo=FUSO)),caminho)
        self.assertEqual(migrar(self.raiz),[caminho]); self.assertEqual(ler_yaml(caminho).dia,self.data)
        outro=self.raiz/"Tarefas"/"Concluidas"/"b.yaml"; salvar_yaml(Tarefa(inicio=datetime(2026,9,14,10,tzinfo=FUSO)),outro)
        with self.assertRaises(ErroMigracaoVinculo): migrar(self.raiz)
        self.assertIsNone(ler_yaml(outro).dia)

    def test_cli_persistir_com_data_e_mais_recente(self):
        self.salvar_relatorio()
        for argumentos, esperado in ((["persistir","dia","--data","2026-09-15"],self.data),(["persistir","dia"],None)):
            saida,erro=io.StringIO(),io.StringIO()
            with patch("Python.cli.persistir_dia",return_value=self.data) as chamada, redirect_stdout(saida), redirect_stderr(erro):
                codigo=main(["--raiz",str(self.raiz),*argumentos])
            self.assertEqual((codigo,erro.getvalue()),(0,"")); self.assertEqual(saida.getvalue().strip(),"2026-09-15")
            chamada.assert_called_once_with(self.raiz,esperado)

    def test_selecao_padrao_usa_finalizado_mais_recente(self):
        self.salvar_relatorio()
        antigo=self.raiz/"Relatórios"/"RD-2026-09-14.yaml"
        salvar_yaml(RegistroDiario(data=date(2026,9,14),fui_dormir=time(22)),antigo)
        cliente=MagicMock()
        self.assertEqual(persistir_dia(self.raiz,fabrica=MagicMock(return_value=cliente)),self.data)
        cliente.__getitem__.return_value.__getitem__.return_value.replace_one.assert_called_once()

    def test_selecao_relatorios_aceita_somente_relatorio_e_subclasses(self):
        self.salvar_relatorio()
        rel_generico = Relatorio(data=self.data, nome="Revisão geral", notas="Alguma nota")
        salvar_yaml(rel_generico, self.raiz / "Relatórios" / "RG-2026-09-15-revisao.yaml")
        # Modelo datado que não deriva de Relatorio não deve entrar
        modelo_datado = Tarefa(dia=self.data, nome="Não é relatório")
        salvar_yaml(modelo_datado, self.raiz / "Relatórios" / "OUTRO.yaml")

        doc = montar_retrato(self.raiz, self.data)
        classes_relatorios = [r["classe"] for r in doc["relatorios"]]
        self.assertIn("RegistroDiario", classes_relatorios)
        self.assertIn("Relatorio", classes_relatorios)
        self.assertNotIn("Tarefa", classes_relatorios)
        self.assertEqual(len(doc["relatorios"]), 2)

    def test_exige_registro_diario_finalizado_e_ignora_generico_para_ciclo(self):
        # Apenas relatório genérico sem RegistroDiario
        rel_generico = Relatorio(data=self.data, nome="Revisão", notas=None)
        salvar_yaml(rel_generico, self.raiz / "Relatórios" / "RG-2026-09-15-revisao.yaml")
        with self.assertRaisesRegex(ErroPersistenciaDia, "ciclo exige exatamente um RegistroDiario"):
            montar_retrato(self.raiz, self.data)

        # RegistroDiario não finalizado mesmo com relatório genérico
        self.salvar_relatorio(final=False)
        with self.assertRaisesRegex(ErroPersistenciaDia, "ciclo exige exatamente um RegistroDiario"):
            montar_retrato(self.raiz, self.data)

        # Relatórios genéricos não alteram identificação do ciclo
        registros = listar_registros(self.raiz)
        self.assertEqual(len(registros), 1)
        self.assertIsInstance(registros[0][1], RegistroDiario)

    def test_persistir_dia_com_relatorio_generico_mantem_arquivos_locais(self):
        self.salvar_relatorio()
        caminho_generico = self.raiz / "Relatórios" / "RG-2026-09-15-planejamento.yaml"
        salvar_yaml(Relatorio(data=self.data, nome="Planejamento", notas="Notas do planejamento"), caminho_generico)

        conteudo_diario = self.rel.read_bytes()
        conteudo_generico = caminho_generico.read_bytes()

        cliente = MagicMock()
        colecao = cliente.__getitem__.return_value.__getitem__.return_value
        data_persistida = persistir_dia(self.raiz, self.data, fabrica=MagicMock(return_value=cliente))

        self.assertEqual(data_persistida, self.data)
        args, kwargs = colecao.replace_one.call_args
        documento = args[1]
        self.assertEqual(documento["data"], "2026-09-15")

        rel_doc = next(r for r in documento["relatorios"] if r["classe"] == "Relatorio")
        self.assertEqual(rel_doc["nome"], "Planejamento")
        self.assertEqual(rel_doc["notas"], "Notas do planejamento")
        self.assertEqual(rel_doc["data"], "2026-09-15")

        # Arquivos locais inalterados
        self.assertEqual(self.rel.read_bytes(), conteudo_diario)
        self.assertEqual(caminho_generico.read_bytes(), conteudo_generico)

if __name__=="__main__": unittest.main()
