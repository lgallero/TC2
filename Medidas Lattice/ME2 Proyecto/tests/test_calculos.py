from __future__ import annotations

import math
import unittest

from medidor_lc.calculos import (
    ErrorDeMedicion,
    MedicionOsciloscopio,
    calcular_impedancia,
    normalizar_fase,
)


def medicion_sintetica(
    z_dut: complex,
    *,
    frecuencia_hz: float,
    resistencia_patron_ohm: float = 10.0,
    ganancia: float = 5.0,
    vpp_salida_corriente_v: float = 1.0,
    resistencia_entrada_paralela_ohm: float = math.inf,
) -> MedicionOsciloscopio:
    if math.isinf(resistencia_entrada_paralela_ohm):
        z_paralelo = z_dut
    else:
        z_paralelo = 1.0 / (
            1.0 / z_dut + 1.0 / resistencia_entrada_paralela_ohm
        )
    vpp_carga = (
        abs(z_paralelo)
        * vpp_salida_corriente_v
        / (resistencia_patron_ohm * ganancia)
    )
    fase_z = math.degrees(math.atan2(z_paralelo.imag, z_paralelo.real))
    # La salida de corriente del circuito esta invertida 180 grados.
    fase_cruda = normalizar_fase(fase_z - 180.0)
    return MedicionOsciloscopio(
        vpp_carga_v=vpp_carga,
        vpp_salida_corriente_v=vpp_salida_corriente_v,
        fase_cruda_grados=fase_cruda,
        frecuencia_hz=frecuencia_hz,
    )


class TestCalculos(unittest.TestCase):
    def test_normalizar_fase(self) -> None:
        self.assertAlmostEqual(normalizar_fase(270.0), -90.0)
        self.assertAlmostEqual(normalizar_fase(-270.0), 90.0)
        self.assertEqual(normalizar_fase(360.0), 0.0)

    def test_capacitor_serie(self) -> None:
        frecuencia = 1_000.0
        capacitancia = 1.0e-6
        esr = 2.0
        xc = -1.0 / (2.0 * math.pi * frecuencia * capacitancia)
        medicion = medicion_sintetica(complex(esr, xc), frecuencia_hz=frecuencia)

        resultado = calcular_impedancia(
            medicion,
            10.0,
            5.0,
            resistencia_entrada_paralela_ohm=math.inf,
        )

        self.assertEqual(resultado.comportamiento, "capacitivo")
        self.assertAlmostEqual(resultado.resistencia_serie_ohm, esr, places=9)
        self.assertAlmostEqual(resultado.reactancia_ohm, xc, places=9)
        self.assertAlmostEqual(resultado.valor_componente, capacitancia, places=15)
        self.assertEqual(resultado.factor_merito_nombre, "D")
        self.assertAlmostEqual(resultado.factor_merito, esr / abs(xc), places=12)

    def test_inductor_serie(self) -> None:
        frecuencia = 1_000.0
        inductancia = 10.0e-3
        esr = 5.0
        xl = 2.0 * math.pi * frecuencia * inductancia
        medicion = medicion_sintetica(complex(esr, xl), frecuencia_hz=frecuencia)

        resultado = calcular_impedancia(
            medicion,
            10.0,
            5.0,
            resistencia_entrada_paralela_ohm=math.inf,
        )

        self.assertEqual(resultado.comportamiento, "inductivo")
        self.assertAlmostEqual(resultado.resistencia_serie_ohm, esr, places=9)
        self.assertAlmostEqual(resultado.valor_componente, inductancia, places=12)
        self.assertEqual(resultado.factor_merito_nombre, "Q")
        self.assertAlmostEqual(resultado.factor_merito, xl / esr, places=12)

    def test_descuenta_entrada_paralela_del_acondicionador(self) -> None:
        frecuencia = 10_000.0
        z_dut = complex(100.0, -500.0)
        r_entrada = 120_000.0
        medicion = medicion_sintetica(
            z_dut,
            frecuencia_hz=frecuencia,
            resistencia_entrada_paralela_ohm=r_entrada,
        )

        resultado = calcular_impedancia(
            medicion,
            10.0,
            5.0,
            resistencia_entrada_paralela_ohm=r_entrada,
        )

        self.assertAlmostEqual(resultado.z_dut_ohm.real, z_dut.real, places=8)
        self.assertAlmostEqual(resultado.z_dut_ohm.imag, z_dut.imag, places=8)

    def test_rechaza_resistencia_serie_negativa(self) -> None:
        medicion = MedicionOsciloscopio(1.0, 1.0, 10.0, 1_000.0)
        with self.assertRaises(ErrorDeMedicion):
            calcular_impedancia(
                medicion,
                10.0,
                5.0,
                correccion_fase_grados=180.0,
                resistencia_entrada_paralela_ohm=math.inf,
            )


if __name__ == "__main__":
    unittest.main()

