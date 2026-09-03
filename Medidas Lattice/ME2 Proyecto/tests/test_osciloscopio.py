from __future__ import annotations

import unittest

from medidor_lc.osciloscopio import leer_medicion


class InstrumentoFalso:
    recurso = "FAKE::INSTR"

    def __init__(self, respuestas: dict[str, list[str]]) -> None:
        self.respuestas = {comando: list(valores) for comando, valores in respuestas.items()}
        self.comandos: list[str] = []

    def query(self, comando: str) -> str:
        self.comandos.append(comando)
        return self.respuestas[comando].pop(0)

    def close(self) -> None:
        pass


class TestLecturaOsciloscopio(unittest.TestCase):
    def test_usa_comandos_documentados_y_medianas(self) -> None:
        respuestas = {
            ":MEASure:VPP? CHANnel1": ["3.0", "30.0", "3.2"],
            ":MEASure:VPP? CHANnel2": ["1.0", "10.0", "1.1"],
            ":MEASure:PHASe? CHANnel1,CHANnel2": ["179", "-179", "178"],
            ":MEASure:FREQuency? CHANnel1": ["1000", "5000", "1001"],
        }
        instrumento = InstrumentoFalso(respuestas)

        medicion = leer_medicion(instrumento, muestras=3, demora_s=0.0)

        self.assertEqual(medicion.vpp_carga_v, 3.2)
        self.assertEqual(medicion.vpp_salida_corriente_v, 1.1)
        self.assertEqual(medicion.frecuencia_hz, 1001.0)
        self.assertIn(medicion.fase_cruda_grados, (179.0, -179.0))
        self.assertEqual(len(instrumento.comandos), 12)

    def test_frecuencia_fija_no_consulta_el_equipo(self) -> None:
        respuestas = {
            ":MEASure:VPP? CHANnel2": ["2.0"],
            ":MEASure:VPP? CHANnel1": ["1.0"],
            ":MEASure:PHASe? CHANnel2,CHANnel1": ["-80.0"],
        }
        instrumento = InstrumentoFalso(respuestas)

        medicion = leer_medicion(
            instrumento,
            canal_carga=2,
            canal_corriente=1,
            muestras=1,
            frecuencia_fija_hz=1234.0,
        )

        self.assertEqual(medicion.frecuencia_hz, 1234.0)
        self.assertFalse(any("FREQuency" in comando for comando in instrumento.comandos))


if __name__ == "__main__":
    unittest.main()
