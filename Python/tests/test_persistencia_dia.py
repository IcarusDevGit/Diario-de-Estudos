from __future__ import annotations
import tempfile, unittest
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock
from pymongo.errors import OperationFailure
from Python.Classes import RegistroDiario, Relatorio, SessaoEstudo, Tarefa
from Python.ciclo_dia import ErroCicloDia, ciclo_aberto, listar_registros
from Python.migrar_vinculos_dia import ErroMigracaoVinculo, migrar
from Python.persistencia_dia import (
    ErroPersistenciaDia,
    montar_retrato,
    persistir_dia,
    selecionar_ciclo,
)
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
        self.salvar_relatorio()
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

    def test_persistir_dia_com_relatorio_generico_remove_selecao(self):
        self.salvar_relatorio()
        caminho_generico = self.raiz / "Relatórios" / "RG-2026-09-15-planejamento.yaml"
        salvar_yaml(Relatorio(data=self.data, nome="Planejamento", notas="Notas do planejamento"), caminho_generico)

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

        self.assertFalse(self.rel.exists())
        self.assertFalse(caminho_generico.exists())
        self.assertTrue((self.raiz / "Relatórios").is_dir())

    def test_selecao_reune_documento_e_somente_caminhos_da_data(self):
        self.salvar_relatorio()
        outra_data = self.raiz / "Relatórios" / "RG-2026-09-14-outro.yaml"
        salvar_yaml(Relatorio(data=date(2026, 9, 14), nome="Outro"), outra_data)
        concluida = self.raiz / "Tarefas" / "Concluidas" / "concluida.yaml"
        tarefa = Tarefa(
            dia=self.data,
            inicio=datetime(2026, 9, 15, 10, tzinfo=FUSO),
            fim=datetime(2026, 9, 15, 11, tzinfo=FUSO),
        )
        tarefa.duracao = "01:00:00"
        salvar_yaml(tarefa, concluida)
        ativa = self.raiz / "Tarefas" / "Tarefa em andamento" / "ativa.yaml"
        salvar_yaml(Tarefa(dia=self.data), ativa)
        pausa = self.raiz / "Tarefas" / "Pausas" / "pausa.yaml"
        pausa.parent.mkdir(parents=True, exist_ok=True)
        pausa.write_text("transitória", encoding="utf-8")

        selecao = selecionar_ciclo(self.raiz, self.data)

        self.assertEqual(selecao.documento["data"], "2026-09-15")
        self.assertEqual(set(selecao.caminhos), {self.rel.resolve(), concluida.resolve()})
        self.assertNotIn(outra_data.resolve(), selecao.caminhos)
        self.assertNotIn(ativa.resolve(), selecao.caminhos)
        self.assertNotIn(pausa.resolve(), selecao.caminhos)

    def test_sucesso_preserva_arquivos_fora_da_selecao_e_diretorios(self):
        self.salvar_relatorio()
        outro = self.raiz / "Relatórios" / "RG-2026-09-14-outro.yaml"
        salvar_yaml(Relatorio(data=date(2026, 9, 14), nome="Outro"), outro)
        ativa = self.raiz / "Tarefas" / "Tarefa em andamento" / "ativa.yaml"
        salvar_yaml(Tarefa(dia=self.data), ativa)

        persistir_dia(self.raiz, self.data, fabrica=MagicMock(return_value=MagicMock()))

        self.assertFalse(self.rel.exists())
        self.assertTrue(outro.exists())
        self.assertTrue(ativa.exists())
        self.assertTrue((self.raiz / "Relatórios").is_dir())
        self.assertTrue((self.raiz / "Tarefas" / "Tarefa em andamento").is_dir())

    def test_falha_remota_preserva_bytes_e_nao_cria_manifesto(self):
        self.salvar_relatorio()
        original = self.rel.read_bytes()
        cliente = MagicMock()
        colecao = cliente.__getitem__.return_value.__getitem__.return_value
        colecao.replace_one.side_effect = OperationFailure("falha")

        with self.assertRaisesRegex(ErroPersistenciaDia, "MongoDB"):
            persistir_dia(self.raiz, self.data, fabrica=MagicMock(return_value=cliente))

        self.assertEqual(self.rel.read_bytes(), original)
        self.assertFalse((self.raiz / ".diario" / "limpezas-pendentes" / "2026-09-15.json").exists())

    def test_falha_parcial_de_limpeza_e_retomada_nao_acessa_mongodb(self):
        self.salvar_relatorio()
        caminho_generico = self.raiz / "Relatórios" / "RG-2026-09-15-plano.yaml"
        salvar_yaml(Relatorio(data=self.data, nome="Plano"), caminho_generico)
        cliente = MagicMock()
        unlink_real = Path.unlink
        falhou = False

        def unlink_controlado(caminho, *args, **kwargs):
            nonlocal falhou
            if Path(caminho) == caminho_generico and not falhou:
                falhou = True
                raise PermissionError("ocupado")
            return unlink_real(caminho, *args, **kwargs)

        with patch.object(Path, "unlink", autospec=True, side_effect=unlink_controlado):
            with self.assertRaisesRegex(ErroPersistenciaDia, "falha ao limpar"):
                persistir_dia(
                    self.raiz, self.data, fabrica=MagicMock(return_value=cliente)
                )

        manifesto = self.raiz / ".diario" / "limpezas-pendentes" / "2026-09-15.json"
        self.assertTrue(manifesto.exists())
        self.assertFalse(self.rel.exists())
        self.assertTrue(caminho_generico.exists())
        replace_one = cliente.__getitem__.return_value.__getitem__.return_value.replace_one
        replace_one.assert_called_once()

        fabrica = MagicMock()
        self.assertEqual(persistir_dia(self.raiz, self.data, fabrica=fabrica), self.data)
        fabrica.assert_not_called()
        self.assertFalse(caminho_generico.exists())
        self.assertFalse(manifesto.exists())

    def test_manifesto_inseguro_e_rejeitado_sem_acesso_remoto(self):
        manifesto = self.raiz / ".diario" / "limpezas-pendentes" / "2026-09-15.json"
        manifesto.parent.mkdir(parents=True)
        for caminho in (
            "../fora.yaml",
            "C:/fora.yaml",
            "Tarefas/Tarefa em andamento/ativa.yaml",
        ):
            with self.subTest(caminho=caminho):
                manifesto.write_text(
                    '{"versao": 1, "data": "2026-09-15", '
                    f'"caminhos": [{caminho!r}]}}\n'.replace("'", '"'),
                    encoding="utf-8",
                )
                fabrica = MagicMock()
                with self.assertRaisesRegex(
                    ErroPersistenciaDia, "inseguro|fora dos diretórios"
                ):
                    persistir_dia(self.raiz, self.data, fabrica=fabrica)
                fabrica.assert_not_called()

    def test_arquivo_criado_depois_da_selecao_nao_e_removido(self):
        self.salvar_relatorio()
        posterior = self.raiz / "Relatórios" / "RG-2026-09-15-posterior.yaml"
        cliente = MagicMock()
        colecao = cliente.__getitem__.return_value.__getitem__.return_value

        def criar_depois_da_selecao(*args, **kwargs):
            salvar_yaml(Relatorio(data=self.data, nome="Posterior"), posterior)

        colecao.replace_one.side_effect = criar_depois_da_selecao
        persistir_dia(self.raiz, self.data, fabrica=MagicMock(return_value=cliente))

        self.assertFalse(self.rel.exists())
        self.assertTrue(posterior.exists())

    def test_falha_ao_gravar_manifesto_preserva_selecao_apos_upsert(self):
        self.salvar_relatorio()
        original = self.rel.read_bytes()
        cliente = MagicMock()

        with patch(
            "Python.persistencia_dia.os.replace", side_effect=OSError("sem espaço")
        ):
            with self.assertRaisesRegex(ErroPersistenciaDia, "registrar a limpeza"):
                persistir_dia(
                    self.raiz, self.data, fabrica=MagicMock(return_value=cliente)
                )

        cliente.__getitem__.return_value.__getitem__.return_value.replace_one.assert_called_once()
        self.assertEqual(self.rel.read_bytes(), original)
        self.assertFalse(
            (self.raiz / ".diario" / "limpezas-pendentes" / "2026-09-15.json").exists()
        )

if __name__=="__main__": unittest.main()
