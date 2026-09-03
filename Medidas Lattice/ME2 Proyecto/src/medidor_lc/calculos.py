"""Calculos electricos independientes del osciloscopio.

La tension de carga y la salida del acondicionador se miden como Vpp. Para una
senal senoidal, el cociente de ambas Vpp es igual al cociente de sus valores
RMS, por lo que el modulo de Z se obtiene sin conversion intermedia.
"""

from __future__ import annotations

from dataclasses import dataclass
import math


class ErrorDeMedicion(ValueError):
    """La medicion o la configuracion no permiten un resultado fisico valido."""


@dataclass(frozen=True)
class MedicionOsciloscopio:
    """Valores leidos del osciloscopio antes de las correcciones."""

    vpp_carga_v: float
    vpp_salida_corriente_v: float
    fase_cruda_grados: float
    frecuencia_hz: float


@dataclass(frozen=True)
class CalculoImpedancia:
    """Resultado completo del calculo de la impedancia del componente."""

    medicion: MedicionOsciloscopio
    fase_corregida_paralelo_grados: float
    fase_dut_grados: float
    corriente_referencia_pp_a: float
    corriente_referencia_rms_a: float
    corriente_dut_rms_a: float
    tension_carga_rms_v: float
    z_paralelo_ohm: complex
    z_dut_ohm: complex
    comportamiento: str
    valor_componente: float | None
    unidad_componente: str | None
    factor_merito_nombre: str | None
    factor_merito: float | None

    @property
    def modulo_z_ohm(self) -> float:
        return abs(self.z_dut_ohm)

    @property
    def resistencia_serie_ohm(self) -> float:
        return self.z_dut_ohm.real

    @property
    def reactancia_ohm(self) -> float:
        return self.z_dut_ohm.imag

    def como_diccionario(self) -> dict[str, object]:
        """Representacion serializable, con nombres y unidades explicitos."""

        return {
            "mediciones": {
                "vpp_carga_V": self.medicion.vpp_carga_v,
                "vpp_salida_corriente_V": self.medicion.vpp_salida_corriente_v,
                "fase_cruda_deg": self.medicion.fase_cruda_grados,
                "frecuencia_Hz": self.medicion.frecuencia_hz,
            },
            "fase_corregida_paralelo_deg": self.fase_corregida_paralelo_grados,
            "fase_dut_deg": self.fase_dut_grados,
            "tension_carga_rms_V": self.tension_carga_rms_v,
            "corriente_referencia_pp_A": self.corriente_referencia_pp_a,
            "corriente_referencia_rms_A": self.corriente_referencia_rms_a,
            "corriente_dut_rms_A": self.corriente_dut_rms_a,
            "z_paralelo": {
                "modulo_ohm": abs(self.z_paralelo_ohm),
                "real_ohm": self.z_paralelo_ohm.real,
                "imag_ohm": self.z_paralelo_ohm.imag,
            },
            "z_dut": {
                "modulo_ohm": self.modulo_z_ohm,
                "real_ohm": self.resistencia_serie_ohm,
                "imag_ohm": self.reactancia_ohm,
            },
            "comportamiento": self.comportamiento,
            "valor_componente": self.valor_componente,
            "unidad_componente": self.unidad_componente,
            "factor_merito": {
                "nombre": self.factor_merito_nombre,
                "valor": self.factor_merito,
            },
        }


def normalizar_fase(grados: float) -> float:
    """Normaliza un angulo al intervalo [-180, 180)."""

    normalizada = (grados + 180.0) % 360.0 - 180.0
    # Evita mostrar -0.0 y conserva +180 como -180 de forma determinista.
    return 0.0 if abs(normalizada) < 1e-12 else normalizada


def _validar_positivo(nombre: str, valor: float) -> None:
    if not math.isfinite(valor) or valor <= 0.0:
        raise ErrorDeMedicion(f"{nombre} debe ser un numero positivo y finito")


def _validar_medicion(medicion: MedicionOsciloscopio) -> None:
    _validar_positivo("Vpp de la carga", medicion.vpp_carga_v)
    _validar_positivo(
        "Vpp de la salida de corriente", medicion.vpp_salida_corriente_v
    )
    _validar_positivo("frecuencia", medicion.frecuencia_hz)
    if not math.isfinite(medicion.fase_cruda_grados):
        raise ErrorDeMedicion("la fase debe ser un numero finito")


def calcular_impedancia(
    medicion: MedicionOsciloscopio,
    resistencia_patron_ohm: float,
    ganancia: float,
    *,
    correccion_fase_grados: float = 180.0,
    signo_fase: int = 1,
    resistencia_entrada_paralela_ohm: float = math.inf,
    umbral_fase_grados: float = 1.0,
) -> CalculoImpedancia:
    """Calcula el modelo serie del DUT a partir de Vpp y fase.

    ``fase_cruda`` se interpreta como fase(carga) - fase(salida_corriente), que
    corresponde al orden ``:MEASure:PHASe? CHANcarga,CHANcorriente``. El
    acondicionador del PDF entrega -G*V_R; por eso la correccion predeterminada
    es +180 grados.

    Si se informa una resistencia de entrada paralela finita, se descuenta del
    resultado la rama resistiva que carga al DUT. En el esquema del PDF es
    R4 + R5 = 20 kohm + 100 kohm = 120 kohm.
    """

    _validar_medicion(medicion)
    _validar_positivo("resistencia patron", resistencia_patron_ohm)
    _validar_positivo("ganancia", ganancia)
    if signo_fase not in (-1, 1):
        raise ErrorDeMedicion("signo_fase debe ser +1 o -1")
    if not math.isfinite(correccion_fase_grados):
        raise ErrorDeMedicion("la correccion de fase debe ser finita")
    if not math.isfinite(umbral_fase_grados) or not 0.0 <= umbral_fase_grados < 90.0:
        raise ErrorDeMedicion("el umbral de fase debe estar entre 0 y 90 grados")
    if not (
        math.isinf(resistencia_entrada_paralela_ohm)
        or (
            math.isfinite(resistencia_entrada_paralela_ohm)
            and resistencia_entrada_paralela_ohm > 0.0
        )
    ):
        raise ErrorDeMedicion(
            "la resistencia de entrada paralela debe ser positiva o infinita"
        )

    fase_paralelo = normalizar_fase(
        signo_fase * medicion.fase_cruda_grados + correccion_fase_grados
    )

    corriente_pp = medicion.vpp_salida_corriente_v / (
        resistencia_patron_ohm * ganancia
    )
    corriente_rms = corriente_pp / (2.0 * math.sqrt(2.0))
    tension_rms = medicion.vpp_carga_v / (2.0 * math.sqrt(2.0))

    modulo_z_paralelo = (
        resistencia_patron_ohm
        * ganancia
        * medicion.vpp_carga_v
        / medicion.vpp_salida_corriente_v
    )
    fase_rad = math.radians(fase_paralelo)
    z_paralelo = complex(
        modulo_z_paralelo * math.cos(fase_rad),
        modulo_z_paralelo * math.sin(fase_rad),
    )

    if math.isinf(resistencia_entrada_paralela_ohm):
        z_dut = z_paralelo
    else:
        admitancia_dut = 1.0 / z_paralelo - 1.0 / resistencia_entrada_paralela_ohm
        if abs(admitancia_dut) < 1e-18:
            raise ErrorDeMedicion(
                "la admitancia calculada del DUT es practicamente cero; "
                "revise la resistencia de entrada paralela"
            )
        z_dut = 1.0 / admitancia_dut

    tolerancia_resistencia = max(1e-12, abs(z_dut) * 1e-9)
    if z_dut.real < -tolerancia_resistencia:
        raise ErrorDeMedicion(
            "se obtuvo una resistencia serie negativa. Revise el orden de canales, "
            "el signo/correccion de fase y la polaridad del acondicionador"
        )
    if z_dut.real < 0.0:
        z_dut = complex(0.0, z_dut.imag)

    fase_dut = normalizar_fase(math.degrees(math.atan2(z_dut.imag, z_dut.real)))
    omega = 2.0 * math.pi * medicion.frecuencia_hz

    if abs(fase_dut) <= umbral_fase_grados:
        comportamiento = "resistivo/indeterminado"
        valor_componente = None
        unidad_componente = None
        factor_nombre = None
        factor_merito = None
    elif z_dut.imag < 0.0:
        comportamiento = "capacitivo"
        reactancia = abs(z_dut.imag)
        valor_componente = 1.0 / (omega * reactancia)
        unidad_componente = "F"
        factor_nombre = "D"
        factor_merito = z_dut.real / reactancia
    else:
        comportamiento = "inductivo"
        reactancia = z_dut.imag
        valor_componente = reactancia / omega
        unidad_componente = "H"
        factor_nombre = "Q"
        factor_merito = (
            math.inf if z_dut.real == 0.0 else reactancia / z_dut.real
        )

    corriente_dut_rms = abs(tension_rms / z_dut)

    return CalculoImpedancia(
        medicion=medicion,
        fase_corregida_paralelo_grados=fase_paralelo,
        fase_dut_grados=fase_dut,
        corriente_referencia_pp_a=corriente_pp,
        corriente_referencia_rms_a=corriente_rms,
        corriente_dut_rms_a=corriente_dut_rms,
        tension_carga_rms_v=tension_rms,
        z_paralelo_ohm=z_paralelo,
        z_dut_ohm=z_dut,
        comportamiento=comportamiento,
        valor_componente=valor_componente,
        unidad_componente=unidad_componente,
        factor_merito_nombre=factor_nombre,
        factor_merito=factor_merito,
    )

