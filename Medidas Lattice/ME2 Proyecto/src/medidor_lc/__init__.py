"""Medidor de impedancia compleja para el proyecto de Medidas Electronicas II."""

from .calculos import (
    CalculoImpedancia,
    ErrorDeMedicion,
    MedicionOsciloscopio,
    calcular_impedancia,
    normalizar_fase,
)

__all__ = [
    "CalculoImpedancia",
    "ErrorDeMedicion",
    "MedicionOsciloscopio",
    "calcular_impedancia",
    "normalizar_fase",
]

