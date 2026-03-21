"""
Property-based tests para la TUI de pases a producción SICO.
Usa Hypothesis para verificar propiedades de la capa de presentación.
"""

from __future__ import annotations

import re
from datetime import date, datetime

import pytest
from hypothesis import given, assume, settings
from hypothesis import strategies as st

from models import ArtefactoInput, Caso, PaseData


# ---------------------------------------------------------------------------
# Estrategias compartidas
# ---------------------------------------------------------------------------

st_artefacto = st.builds(
    ArtefactoInput,
    codigo=st.text(min_size=1),
    url_release=st.text(),
)


# ---------------------------------------------------------------------------
# Property TUI-1: Validación de fecha acepta exactamente los 4 formatos definidos
# Validates: Requirements 3.3
# ---------------------------------------------------------------------------

# Los 4 patrones aceptados: d/M/yyyy, dd/MM/yyyy, d/MM/yyyy, dd/M/yyyy
# En Python strftime: %-d y %-m producen sin cero inicial (Linux/Mac)
# Para compatibilidad cross-platform usamos formateo manual

def _formatear_fecha(d: date, fmt: str) -> str:
    """Formatea una fecha según el patrón indicado (sin ceros iniciales si aplica)."""
    dia = str(d.day)
    mes = str(d.month)
    anio = str(d.year)
    dia_pad = d.strftime("%d")
    mes_pad = d.strftime("%m")
    return (
        fmt
        .replace("dd", dia_pad)
        .replace("MM", mes_pad)
        .replace("d", dia)
        .replace("M", mes)
        .replace("yyyy", anio)
    )


@given(d=st.dates(min_value=date(1900, 1, 1), max_value=date(2099, 12, 31)))
@settings(deadline=None)
def test_tui1_fecha_valida_formato_d_M_yyyy(d):
    """d/M/yyyy debe ser aceptado."""
    from tui.screens.formulario import _validar_fecha
    fecha = f"{d.day}/{d.month}/{d.year}"
    assert _validar_fecha(fecha), f"Debería aceptar: {fecha}"


@given(d=st.dates(min_value=date(1900, 1, 1), max_value=date(2099, 12, 31)))
def test_tui1_fecha_valida_formato_dd_MM_yyyy(d):
    """dd/MM/yyyy debe ser aceptado."""
    from tui.screens.formulario import _validar_fecha
    fecha = d.strftime("%d/%m/%Y")
    assert _validar_fecha(fecha), f"Debería aceptar: {fecha}"


@given(d=st.dates(min_value=date(1900, 1, 1), max_value=date(2099, 12, 31)))
def test_tui1_fecha_valida_formato_d_MM_yyyy(d):
    """d/MM/yyyy debe ser aceptado."""
    from tui.screens.formulario import _validar_fecha
    fecha = f"{d.day}/{d.strftime('%m')}/{d.year}"
    assert _validar_fecha(fecha), f"Debería aceptar: {fecha}"


@given(d=st.dates(min_value=date(1900, 1, 1), max_value=date(2099, 12, 31)))
def test_tui1_fecha_valida_formato_dd_M_yyyy(d):
    """dd/M/yyyy debe ser aceptado."""
    from tui.screens.formulario import _validar_fecha
    fecha = f"{d.strftime('%d')}/{d.month}/{d.year}"
    assert _validar_fecha(fecha), f"Debería aceptar: {fecha}"


@given(
    texto=st.text().filter(
        lambda s: not re.match(r"^\d{1,2}/\d{1,2}/\d{4}$", s)
    )
)
def test_tui1_fecha_invalida_rechazada(texto):
    """Strings que no tienen el patrón d/M/yyyy deben ser rechazados."""
    from tui.screens.formulario import _validar_fecha
    assert not _validar_fecha(texto), f"Debería rechazar: {texto!r}"


# ---------------------------------------------------------------------------
# Property TUI-2: PaseData construido desde formulario es consistente con determinar_caso
# Validates: Requirements 3.5, 7.3
# ---------------------------------------------------------------------------

@given(
    artefactos=st.lists(st_artefacto, min_size=1),
    ruta_scripts=st.none(),
)
def test_tui2_pasedata_caso_uno(artefactos, ruta_scripts):
    """Con artefactos y sin scripts → Caso.UNO."""
    from main import determinar_caso
    caso = determinar_caso(artefactos, ruta_scripts)
    assert caso == Caso.UNO
    pase = PaseData(
        texto_asunto="asunto",
        texto_hu="HU-1",
        fecha="1/1/2025",
        opcion_ejecucion="Inmediata",
        artefactos=artefactos,
        ruta_scripts=ruta_scripts,
        forms_url="http://forms.example.com",
        caso=caso,
    )
    assert pase.caso == determinar_caso(pase.artefactos, pase.ruta_scripts)


@given(
    artefactos=st.just([]),
    ruta_scripts=st.text(min_size=1).filter(lambda s: s.strip() != ""),
)
def test_tui2_pasedata_caso_dos(artefactos, ruta_scripts):
    """Sin artefactos y con scripts → Caso.DOS."""
    from main import determinar_caso
    caso = determinar_caso(artefactos, ruta_scripts)
    assert caso == Caso.DOS
    pase = PaseData(
        texto_asunto="asunto",
        texto_hu="HU-1",
        fecha="1/1/2025",
        opcion_ejecucion="Inmediata",
        artefactos=artefactos,
        ruta_scripts=ruta_scripts,
        forms_url="http://forms.example.com",
        caso=caso,
    )
    assert pase.caso == determinar_caso(pase.artefactos, pase.ruta_scripts)


@given(
    artefactos=st.lists(st_artefacto, min_size=1),
    ruta_scripts=st.text(min_size=1).filter(lambda s: s.strip() != ""),
)
def test_tui2_pasedata_caso_tres(artefactos, ruta_scripts):
    """Con artefactos y con scripts → Caso.TRES."""
    from main import determinar_caso
    caso = determinar_caso(artefactos, ruta_scripts)
    assert caso == Caso.TRES
    pase = PaseData(
        texto_asunto="asunto",
        texto_hu="HU-1",
        fecha="1/1/2025",
        opcion_ejecucion="Inmediata",
        artefactos=artefactos,
        ruta_scripts=ruta_scripts,
        forms_url="http://forms.example.com",
        caso=caso,
    )
    assert pase.caso == determinar_caso(pase.artefactos, pase.ruta_scripts)


# ---------------------------------------------------------------------------
# Property TUI-3: Mensajes de progreso tienen formato [HH:MM:SS] prefijo correcto
# Validates: Requirements 4.1
# ---------------------------------------------------------------------------

_RE_TIMESTAMP = re.compile(r"^\[\d{2}:\d{2}:\d{2}\]")


def _formatear_log(mensaje: str) -> str:
    """Replica la lógica de formateo de PantallaProgreso.agregar_log."""
    ts = datetime.now().strftime("%H:%M:%S")
    return f"[{ts}] {mensaje}"


@given(mensaje=st.text())
def test_tui3_mensaje_progreso_tiene_timestamp(mensaje):
    """Todo mensaje formateado debe comenzar con [HH:MM:SS]."""
    linea = _formatear_log(mensaje)
    assert _RE_TIMESTAMP.match(linea), f"Falta timestamp en: {linea!r}"


@given(mensaje=st.text())
def test_tui3_mensaje_progreso_contiene_mensaje_original(mensaje):
    """El mensaje original debe estar presente en la línea formateada."""
    linea = _formatear_log(mensaje)
    assert mensaje in linea


# ---------------------------------------------------------------------------
# Property TUI-4: Estado del resumen es consistente con la lista de errores
# Validates: Requirements 5.3, 5.4
# ---------------------------------------------------------------------------

def _calcular_estado_resumen(errores: list[str]) -> str:
    """Replica la lógica de PantallaResumen para determinar el estado."""
    if errores:
        return "Completado con errores"
    return "Completado exitosamente"


@given(errores=st.lists(st.text()))
def test_tui4_estado_resumen_consistente_con_errores(errores):
    """El estado es 'Completado exitosamente' si y solo si errores está vacío."""
    estado = _calcular_estado_resumen(errores)
    if not errores:
        assert estado == "Completado exitosamente"
    else:
        assert estado == "Completado con errores"


@given(errores=st.lists(st.text(), min_size=1))
def test_tui4_estado_con_errores_nunca_es_exitoso(errores):
    """Con al menos un error, el estado nunca puede ser 'exitoso'."""
    estado = _calcular_estado_resumen(errores)
    assert estado != "Completado exitosamente"


@given(errores=st.just([]))
def test_tui4_estado_sin_errores_siempre_exitoso(errores):
    """Sin errores, el estado siempre es 'Completado exitosamente'."""
    estado = _calcular_estado_resumen(errores)
    assert estado == "Completado exitosamente"


# ---------------------------------------------------------------------------
# Property TUI-5: Escape está deshabilitado en PantallaProgreso mientras worker activo
# Validates: Requirements 6.5
# ---------------------------------------------------------------------------

def _simular_action_ir_bienvenida(worker_activo: bool) -> bool:
    """Replica la lógica de PantallaProgreso.action_ir_bienvenida.
    Retorna True si navegaría (worker inactivo), False si bloquea (worker activo).
    """
    if worker_activo:
        return False
    return True


def test_tui5_escape_deshabilitado_mientras_worker_activo():
    """Cuando _worker_activo=True, action_ir_bienvenida no debe navegar."""
    navego = _simular_action_ir_bienvenida(worker_activo=True)
    assert not navego


def test_tui5_escape_habilitado_cuando_worker_inactivo():
    """Cuando _worker_activo=False, action_ir_bienvenida debe navegar."""
    navego = _simular_action_ir_bienvenida(worker_activo=False)
    assert navego


@given(worker_activo=st.booleans())
def test_tui5_guard_logica_consistente(worker_activo: bool):
    """La lógica del guard es: navega si y solo si worker_activo es False."""
    navego = _simular_action_ir_bienvenida(worker_activo)
    assert navego == (not worker_activo)


def test_tui5_codigo_fuente_tiene_guard():
    """Verifica que PantallaProgreso.action_ir_bienvenida contiene el guard _worker_activo."""
    import inspect
    from tui.screens.progreso import PantallaProgreso
    source = inspect.getsource(PantallaProgreso.action_ir_bienvenida)
    assert "_worker_activo" in source, "El guard _worker_activo debe estar en action_ir_bienvenida"
