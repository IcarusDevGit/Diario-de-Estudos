from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone

from Python.duracao import (
    ErroDuracao,
    duracao_para_segundos,
    formatar_intervalo,
    formatar_microssegundos,
    formatar_segundos,
    intervalo_microssegundos,
)


class DuracaoTestCase(unittest.TestCase):
    def test_validar_e_converter_formato_canonico(self) -> None:
        self.assertEqual(duracao_para_segundos("00:00:14"), 14)
        self.assertEqual(duracao_para_segundos("27:02:03"), 97_323)
        for invalida in ("1:02:03", "01:60:00", "01:00:60", "-01:00:00", "00:00:01.5"):
            with self.subTest(invalida=invalida):
                with self.assertRaisesRegex(ErroDuracao, "HH:MM:SS"):
                    duracao_para_segundos(invalida, caminho="$.duracao")

    def test_formatar_segundos_e_rejeitar_negativos(self) -> None:
        self.assertEqual(formatar_segundos(0), "00:00:00")
        self.assertEqual(formatar_segundos(97_323), "27:02:03")
        with self.assertRaisesRegex(ErroDuracao, "negativa"):
            formatar_segundos(-1)
        with self.assertRaisesRegex(ErroDuracao, "inteiro"):
            formatar_segundos(1.0)  # type: ignore[arg-type]

    def test_arredondamento_half_up(self) -> None:
        self.assertEqual(formatar_microssegundos(13_400_000), "00:00:13")
        self.assertEqual(formatar_microssegundos(13_500_000), "00:00:14")
        self.assertEqual(formatar_microssegundos(13_828_065), "00:00:14")

    def test_intervalo_por_linha_do_tempo(self) -> None:
        fuso = timezone(timedelta(hours=-3))
        inicio = datetime(2026, 9, 14, 23, 59, 59, 400_000, tzinfo=fuso)
        fim = datetime(2026, 9, 15, 0, 0, 13, 228_065, tzinfo=fuso)
        self.assertEqual(intervalo_microssegundos(inicio, fim), 13_828_065)
        self.assertEqual(formatar_intervalo(inicio, fim), "00:00:14")
        with self.assertRaisesRegex(ErroDuracao, "anterior"):
            intervalo_microssegundos(fim, inicio)


if __name__ == "__main__":
    unittest.main()
