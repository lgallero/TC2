"""Comunicacion SCPI con la familia UNI-T UTD2000CEX+."""

from __future__ import annotations

from dataclasses import dataclass
import glob
import math
import os
import re
import select
import statistics
import time
from typing import Protocol

from .calculos import ErrorDeMedicion, MedicionOsciloscopio, normalizar_fase


class ErrorDeConexion(RuntimeError):
    """No fue posible descubrir o consultar el instrumento."""


class InstrumentoSCPI(Protocol):
    recurso: str

    def query(self, comando: str) -> str: ...

    def close(self) -> None: ...


class InstrumentoUSBTMCLinux:
    """Acceso directo al dispositivo de caracteres /dev/usbtmcN."""

    def __init__(self, recurso: str, timeout_ms: int = 5000) -> None:
        if not recurso.startswith("/dev/usbtmc"):
            raise ErrorDeConexion(f"ruta USBTMC no valida: {recurso}")
        self.recurso = recurso
        self._timeout_s = timeout_ms / 1000.0
        try:
            self._fd = os.open(recurso, os.O_RDWR | os.O_NONBLOCK)
        except OSError as exc:
            raise ErrorDeConexion(f"no se pudo abrir {recurso}: {exc}") from exc

    def query(self, comando: str) -> str:
        datos = (comando.rstrip("\r\n") + "\n").encode("ascii")
        limite = time.monotonic() + self._timeout_s
        enviados = 0
        while enviados < len(datos):
            restante = limite - time.monotonic()
            if restante <= 0:
                raise ErrorDeConexion(f"timeout enviando {comando!r}")
            _, escritura, _ = select.select([], [self._fd], [], restante)
            if not escritura:
                raise ErrorDeConexion(f"timeout enviando {comando!r}")
            enviados += os.write(self._fd, datos[enviados:])

        respuesta = bytearray()
        while True:
            restante = limite - time.monotonic()
            if restante <= 0:
                raise ErrorDeConexion(f"timeout esperando respuesta a {comando!r}")
            lectura, _, _ = select.select([self._fd], [], [], restante)
            if not lectura:
                raise ErrorDeConexion(f"timeout esperando respuesta a {comando!r}")
            try:
                bloque = os.read(self._fd, 4096)
            except BlockingIOError:
                continue
            if not bloque:
                break
            respuesta.extend(bloque)
            if b"\n" in bloque:
                break

        try:
            return respuesta.decode("ascii", errors="strict").strip()
        except UnicodeDecodeError as exc:
            raise ErrorDeConexion(
                f"el instrumento devolvio una respuesta no ASCII a {comando!r}"
            ) from exc

    def close(self) -> None:
        if getattr(self, "_fd", None) is not None:
            os.close(self._fd)
            self._fd = None


class InstrumentoVISA:
    """Acceso USBTMC mediante PyVISA/PyVISA-py."""

    def __init__(
        self,
        recurso: str,
        *,
        backend: str = "@py",
        timeout_ms: int = 5000,
    ) -> None:
        self.recurso = recurso
        try:
            import pyvisa
        except ImportError as exc:
            raise ErrorDeConexion(
                "PyVISA no esta instalado; ejecute: python -m pip install -e '.[usb]'"
            ) from exc

        try:
            self._rm = pyvisa.ResourceManager(backend)
            self._instrumento = self._rm.open_resource(recurso)
            self._instrumento.timeout = timeout_ms
            self._instrumento.write_termination = "\n"
            self._instrumento.read_termination = "\n"
            self._instrumento.query_delay = 0.05
        except Exception as exc:
            try:
                self._rm.close()
            except Exception:
                pass
            raise ErrorDeConexion(f"no se pudo abrir {recurso}: {exc}") from exc

    def query(self, comando: str) -> str:
        try:
            return str(self._instrumento.query(comando)).strip()
        except Exception as exc:
            raise ErrorDeConexion(f"fallo la consulta {comando!r}: {exc}") from exc

    def close(self) -> None:
        try:
            self._instrumento.close()
        finally:
            self._rm.close()


@dataclass(frozen=True)
class RecursoDescubierto:
    recurso: str
    identificacion: str | None
    error: str | None


_PATRON_NUMERO = re.compile(
    r"^[\s]*([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)[\s]*[A-Za-z%]*[\s]*$"
)


def _parsear_numero(respuesta: str, comando: str) -> float:
    texto = respuesta.strip()
    if not texto or texto == "*":
        raise ErrorDeMedicion(f"{comando} no produjo una medicion valida: {texto!r}")
    coincidencia = _PATRON_NUMERO.fullmatch(texto)
    if not coincidencia:
        raise ErrorDeMedicion(f"respuesta inesperada para {comando}: {texto!r}")
    valor = float(coincidencia.group(1))
    if not math.isfinite(valor) or abs(valor) >= 1e30:
        raise ErrorDeMedicion(f"valor invalido para {comando}: {texto!r}")
    return valor


def _mediana_circular(grados: list[float]) -> float:
    """Mediana circular discreta, robusta frente a una lectura espuria."""

    if not grados:
        raise ErrorDeMedicion("no hay lecturas de fase validas")

    def distancia(a: float, b: float) -> float:
        return abs(normalizar_fase(a - b))

    return min(grados, key=lambda candidato: sum(distancia(candidato, x) for x in grados))


def leer_medicion(
    instrumento: InstrumentoSCPI,
    *,
    canal_carga: int = 1,
    canal_corriente: int = 2,
    muestras: int = 5,
    demora_s: float = 0.15,
    frecuencia_fija_hz: float | None = None,
) -> MedicionOsciloscopio:
    """Lee Vpp, fase y frecuencia varias veces y combina por mediana."""

    if canal_carga not in (1, 2) or canal_corriente not in (1, 2):
        raise ErrorDeMedicion("los canales deben ser 1 o 2")
    if canal_carga == canal_corriente:
        raise ErrorDeMedicion("carga y corriente deben usar canales diferentes")
    if muestras < 1:
        raise ErrorDeMedicion("muestras debe ser al menos 1")
    if demora_s < 0.0:
        raise ErrorDeMedicion("la demora entre muestras no puede ser negativa")

    carga = f"CHANnel{canal_carga}"
    corriente = f"CHANnel{canal_corriente}"
    vpp_carga: list[float] = []
    vpp_corriente: list[float] = []
    fases: list[float] = []
    frecuencias: list[float] = []

    for indice in range(muestras):
        vpp_carga.append(
            _parsear_numero(
                instrumento.query(f":MEASure:VPP? {carga}"), "Vpp de carga"
            )
        )
        vpp_corriente.append(
            _parsear_numero(
                instrumento.query(f":MEASure:VPP? {corriente}"),
                "Vpp de salida de corriente",
            )
        )
        fases.append(
            _parsear_numero(
                instrumento.query(f":MEASure:PHASe? {carga},{corriente}"), "fase"
            )
        )
        if frecuencia_fija_hz is None:
            frecuencias.append(
                _parsear_numero(
                    instrumento.query(f":MEASure:FREQuency? {carga}"), "frecuencia"
                )
            )
        if indice + 1 < muestras and demora_s:
            time.sleep(demora_s)

    frecuencia = (
        frecuencia_fija_hz
        if frecuencia_fija_hz is not None
        else statistics.median(frecuencias)
    )
    return MedicionOsciloscopio(
        vpp_carga_v=statistics.median(vpp_carga),
        vpp_salida_corriente_v=statistics.median(vpp_corriente),
        fase_cruda_grados=_mediana_circular(fases),
        frecuencia_hz=frecuencia,
    )


def _recursos_visa(backend: str) -> tuple[str, ...]:
    try:
        import pyvisa
    except ImportError:
        return ()
    try:
        administrador = pyvisa.ResourceManager(backend)
        try:
            return tuple(administrador.list_resources("USB?*::INSTR"))
        finally:
            administrador.close()
    except Exception:
        return ()


def recursos_disponibles(backend: str = "@py") -> list[str]:
    rutas = sorted(glob.glob("/dev/usbtmc*"))
    visa = list(_recursos_visa(backend))
    return rutas + [recurso for recurso in visa if recurso not in rutas]


def abrir_instrumento(
    recurso: str | None,
    *,
    backend: str = "@py",
    timeout_ms: int = 5000,
) -> InstrumentoSCPI:
    """Abre un recurso explicito o descubre automaticamente un UNI-T."""

    if recurso:
        if recurso.startswith("/dev/usbtmc"):
            return InstrumentoUSBTMCLinux(recurso, timeout_ms=timeout_ms)
        return InstrumentoVISA(recurso, backend=backend, timeout_ms=timeout_ms)

    candidatos = recursos_disponibles(backend)
    if not candidatos:
        raise ErrorDeConexion(
            "no se encontraron recursos USBTMC. Ejecute 'medidor-lc descubrir' y "
            "revise lsusb, el driver usbtmc y las reglas udev"
        )

    errores: list[str] = []
    for candidato in candidatos:
        instrumento: InstrumentoSCPI | None = None
        conservar_abierto = False
        try:
            instrumento = abrir_instrumento(
                candidato, backend=backend, timeout_ms=timeout_ms
            )
            identificacion = instrumento.query("*IDN?")
            if "UNI-T" in identificacion.upper() or "UTD" in identificacion.upper():
                conservar_abierto = True
                return instrumento
            errores.append(f"{candidato}: no parece UNI-T ({identificacion})")
        except Exception as exc:
            errores.append(f"{candidato}: {exc}")
        finally:
            if instrumento is not None and not conservar_abierto:
                instrumento.close()

    detalle = "; ".join(errores)
    raise ErrorDeConexion(f"ningun recurso respondio como UNI-T: {detalle}")


def descubrir(backend: str = "@py", timeout_ms: int = 2000) -> list[RecursoDescubierto]:
    resultados: list[RecursoDescubierto] = []
    for recurso in recursos_disponibles(backend):
        instrumento: InstrumentoSCPI | None = None
        try:
            instrumento = abrir_instrumento(
                recurso, backend=backend, timeout_ms=timeout_ms
            )
            identificacion = instrumento.query("*IDN?")
            resultados.append(RecursoDescubierto(recurso, identificacion, None))
        except Exception as exc:
            resultados.append(RecursoDescubierto(recurso, None, str(exc)))
        finally:
            if instrumento is not None:
                instrumento.close()
    return resultados
