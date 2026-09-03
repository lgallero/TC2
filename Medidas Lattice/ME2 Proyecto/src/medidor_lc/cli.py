"""Interfaz de linea de comandos del medidor L/C."""

from __future__ import annotations

import argparse
import json
import math
import sys
from typing import Any

from .calculos import ErrorDeMedicion, MedicionOsciloscopio, calcular_impedancia
from .osciloscopio import (
    ErrorDeConexion,
    abrir_instrumento,
    descubrir,
    leer_medicion,
)


def _numero_positivo(texto: str) -> float:
    try:
        valor = float(texto)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("debe ser un numero") from exc
    if not math.isfinite(valor) or valor <= 0.0:
        raise argparse.ArgumentTypeError("debe ser positivo y finito")
    return valor


def _resistencia_paralela(texto: str) -> float:
    if texto.lower() in {"inf", "infinita", "ninguna"}:
        return math.inf
    return _numero_positivo(texto)


def _agregar_parametros_calculo(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--r-patron", required=True, type=_numero_positivo, metavar="OHM")
    parser.add_argument("--ganancia", required=True, type=_numero_positivo)
    parser.add_argument(
        "--correccion-fase",
        type=float,
        default=180.0,
        metavar="GRADOS",
        help="correccion sumada a la fase; 180 por la inversion del circuito del PDF",
    )
    parser.add_argument(
        "--invertir-signo-fase",
        action="store_true",
        help="usar -(fase CH carga - CH corriente) antes de corregir",
    )
    parser.add_argument(
        "--r-entrada-paralela",
        type=_resistencia_paralela,
        default=120_000.0,
        metavar="OHM|inf",
        help="carga resistiva sobre el DUT; 120000 para R4+R5 del PDF, 'inf' para ignorarla",
    )
    parser.add_argument(
        "--umbral-fase",
        type=float,
        default=1.0,
        metavar="GRADOS",
        help="por debajo de este modulo se informa resistivo/indeterminado (predeterminado: 1)",
    )
    parser.add_argument("--json", action="store_true", help="salida JSON")


def _construir_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="medidor-lc",
        description="Mide una impedancia serie L/C con un UNI-T UTD2000CEX+.",
    )
    subparsers = parser.add_subparsers(dest="comando", required=True)

    p_descubrir = subparsers.add_parser(
        "descubrir", help="listar instrumentos USBTMC y consultar *IDN?"
    )
    p_descubrir.add_argument("--backend", default="@py", help="backend VISA")
    p_descubrir.add_argument("--timeout-ms", type=int, default=2000)

    p_medir = subparsers.add_parser(
        "medir", help="leer el osciloscopio y calcular el componente"
    )
    _agregar_parametros_calculo(p_medir)
    p_medir.add_argument(
        "--resource",
        help="recurso VISA o /dev/usbtmcN; si se omite se descubre automaticamente",
    )
    p_medir.add_argument("--backend", default="@py", help="backend VISA")
    p_medir.add_argument("--timeout-ms", type=int, default=5000)
    p_medir.add_argument("--canal-carga", type=int, choices=(1, 2), default=1)
    p_medir.add_argument("--canal-corriente", type=int, choices=(1, 2), default=2)
    p_medir.add_argument("--muestras", type=int, default=5)
    p_medir.add_argument("--demora", type=float, default=0.15, metavar="SEGUNDOS")
    p_medir.add_argument(
        "--frecuencia",
        type=_numero_positivo,
        metavar="HZ",
        help="usar esta frecuencia en vez de consultarla al osciloscopio",
    )

    p_calcular = subparsers.add_parser(
        "calcular", help="probar las cuentas con valores cargados a mano"
    )
    _agregar_parametros_calculo(p_calcular)
    p_calcular.add_argument("--vpp-carga", required=True, type=_numero_positivo)
    p_calcular.add_argument("--vpp-corriente", required=True, type=_numero_positivo)
    p_calcular.add_argument("--fase-cruda", required=True, type=float)
    p_calcular.add_argument("--frecuencia", required=True, type=_numero_positivo)

    return parser


def _formato_si(valor: float, unidad: str, cifras: int = 6) -> str:
    if math.isinf(valor):
        return f"infinito {unidad}".rstrip()
    if valor == 0.0:
        return f"0 {unidad}".rstrip()
    prefijos = [
        (-12, "p"),
        (-9, "n"),
        (-6, "u"),
        (-3, "m"),
        (0, ""),
        (3, "k"),
        (6, "M"),
        (9, "G"),
    ]
    exponente = int(math.floor(math.log10(abs(valor)) / 3.0) * 3)
    exponente = min(9, max(-12, exponente))
    prefijo = dict(prefijos)[exponente]
    escalado = valor / (10.0**exponente)
    return f"{escalado:.{cifras}g} {prefijo}{unidad}".rstrip()


def _json_seguro(valor: Any) -> Any:
    if isinstance(valor, float) and not math.isfinite(valor):
        return "infinito" if valor > 0 else "-infinito"
    if isinstance(valor, dict):
        return {clave: _json_seguro(elemento) for clave, elemento in valor.items()}
    if isinstance(valor, list):
        return [_json_seguro(elemento) for elemento in valor]
    return valor


def _mostrar_resultado(resultado: Any, *, como_json: bool, identificacion: str | None) -> None:
    if como_json:
        salida = resultado.como_diccionario()
        if identificacion is not None:
            salida = {"instrumento": identificacion, **salida}
        print(json.dumps(_json_seguro(salida), indent=2, ensure_ascii=False))
        return

    if identificacion:
        print(f"Instrumento: {identificacion}")
    print("\nMedidas usadas")
    print(f"  Vpp carga:              {_formato_si(resultado.medicion.vpp_carga_v, 'V')}")
    print(
        "  Vpp salida corriente:  "
        f"{_formato_si(resultado.medicion.vpp_salida_corriente_v, 'V')}"
    )
    print(f"  Frecuencia:             {_formato_si(resultado.medicion.frecuencia_hz, 'Hz')}")
    print(f"  Fase cruda:             {resultado.medicion.fase_cruda_grados:.6g} grados")
    print(
        "  Fase Z corregida:       "
        f"{resultado.fase_dut_grados:.6g} grados"
    )

    print("\nResultado")
    print(f"  Comportamiento:         {resultado.comportamiento}")
    print(f"  |Z| del DUT:            {_formato_si(resultado.modulo_z_ohm, 'ohm')}")
    print(f"  R serie / ESR:          {_formato_si(resultado.resistencia_serie_ohm, 'ohm')}")
    print(f"  X serie:                {_formato_si(resultado.reactancia_ohm, 'ohm')}")
    print(
        "  Z compleja:             "
        f"{resultado.resistencia_serie_ohm:.9g} "
        f"{resultado.reactancia_ohm:+.9g}j ohm"
    )
    if resultado.valor_componente is not None:
        etiqueta = "C" if resultado.unidad_componente == "F" else "L"
        print(
            f"  {etiqueta}:                     "
            f"{_formato_si(resultado.valor_componente, resultado.unidad_componente)}"
        )
    if resultado.factor_merito_nombre is not None:
        valor = resultado.factor_merito
        texto = "infinito" if math.isinf(valor) else f"{valor:.9g}"
        print(f"  {resultado.factor_merito_nombre}:                     {texto}")

    print("\nMagnitudes auxiliares")
    print(
        "  I por R patron (RMS):   "
        f"{_formato_si(resultado.corriente_referencia_rms_a, 'A')}"
    )
    print(
        "  I del DUT (RMS):        "
        f"{_formato_si(resultado.corriente_dut_rms_a, 'A')}"
    )
    print(
        "  V carga (RMS):          "
        f"{_formato_si(resultado.tension_carga_rms_v, 'V')}"
    )


def _calcular_desde_args(args: argparse.Namespace, medicion: MedicionOsciloscopio):
    return calcular_impedancia(
        medicion,
        args.r_patron,
        args.ganancia,
        correccion_fase_grados=args.correccion_fase,
        signo_fase=-1 if args.invertir_signo_fase else 1,
        resistencia_entrada_paralela_ohm=args.r_entrada_paralela,
        umbral_fase_grados=args.umbral_fase,
    )


def main(argv: list[str] | None = None) -> int:
    parser = _construir_parser()
    args = parser.parse_args(argv)

    try:
        if args.comando == "descubrir":
            resultados = descubrir(args.backend, args.timeout_ms)
            if not resultados:
                print("No se encontraron recursos USBTMC.")
                return 1
            for resultado in resultados:
                if resultado.error:
                    print(f"{resultado.recurso}: ERROR - {resultado.error}")
                else:
                    print(f"{resultado.recurso}: {resultado.identificacion}")
            return 0 if any(not r.error for r in resultados) else 1

        if args.comando == "calcular":
            medicion = MedicionOsciloscopio(
                vpp_carga_v=args.vpp_carga,
                vpp_salida_corriente_v=args.vpp_corriente,
                fase_cruda_grados=args.fase_cruda,
                frecuencia_hz=args.frecuencia,
            )
            resultado = _calcular_desde_args(args, medicion)
            _mostrar_resultado(resultado, como_json=args.json, identificacion=None)
            return 0

        instrumento = abrir_instrumento(
            args.resource, backend=args.backend, timeout_ms=args.timeout_ms
        )
        try:
            identificacion = instrumento.query("*IDN?")
            medicion = leer_medicion(
                instrumento,
                canal_carga=args.canal_carga,
                canal_corriente=args.canal_corriente,
                muestras=args.muestras,
                demora_s=args.demora,
                frecuencia_fija_hz=args.frecuencia,
            )
        finally:
            instrumento.close()
        resultado = _calcular_desde_args(args, medicion)
        _mostrar_resultado(
            resultado, como_json=args.json, identificacion=identificacion
        )
        return 0
    except (ErrorDeMedicion, ErrorDeConexion, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

