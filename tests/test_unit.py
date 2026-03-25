import os
import tempfile
from pathlib import Path

import pytest

from exceptions import ConfigError
from utils.config_loader import cargar_artefactos, cargar_destinatarios, inicializar_db


# --- cargar_artefactos ---


def test_cargar_artefactos_retorna_dict():
    """Verifica que cargar_artefactos retorne un diccionario."""
    artefactos = cargar_artefactos()
    assert isinstance(artefactos, dict)


def test_cargar_artefactos_tiene_campos():
    """Verifica que los artefactos tengan los campos esperados."""
    artefactos = cargar_artefactos()
    if artefactos:
        primer_artefacto = next(iter(artefactos.values()))
        assert "id" in primer_artefacto
        assert "repo" in primer_artefacto
        assert "nombre" in primer_artefacto
        assert "descripcion" in primer_artefacto


# --- cargar_destinatarios ---


def test_cargar_destinatarios_retorna_dict():
    """Verifica que cargar_destinatarios retorne un diccionario."""
    destinatarios = cargar_destinatarios()
    assert isinstance(destinatarios, dict)
    assert "casos" in destinatarios


def test_cargar_destinatarios_tiene_campos():
    """Verifica que los destinatarios tengan los campos esperados."""
    destinatarios = cargar_destinatarios()
    casos = destinatarios.get("casos", {})
    if casos:
        primer_caso = next(iter(casos.values()))
        assert "id" in primer_caso
        assert "nombre" in primer_caso
        assert "para" in primer_caso
        assert "cc" in primer_caso


# --- correo.py ---

from unittest.mock import MagicMock
from outlook.correo import esperar_login, enviar_correo
from exceptions import LoginTimeoutError, OutlookError
from models import CorreoData


def test_esperar_login_lanza_login_timeout_error():
    """Verifica que LoginTimeoutError se lanza cuando page.wait_for_url falla."""
    page = MagicMock()
    page.wait_for_url.side_effect = Exception("Timeout")
    with pytest.raises(LoginTimeoutError):
        esperar_login(page, timeout_ms=100)


def test_enviar_correo_lanza_outlook_error():
    """Verifica que OutlookError se lanza cuando page.click falla."""
    page = MagicMock()
    page.click.side_effect = Exception("Playwright error")
    correo = CorreoData(
        asunto="Test",
        para=["test@example.com"],
        cc=[],
        cuerpo="Cuerpo de prueba",
    )
    with pytest.raises(OutlookError):
        enviar_correo(page, correo)


# --- formulario_devops.py ---

from forms.formulario_devops import completar_formulario_devops
from exceptions import FormsError
from models import PaseData, ArtefactoInput, Caso


def test_completar_formulario_devops_lanza_forms_error_con_nombre_artefacto():
    """Verifica que FormsError se lanza con el código del artefacto cuando page.goto falla."""
    page = MagicMock()
    page.goto.side_effect = Exception("Error de navegación")
    artefacto = ArtefactoInput(
        codigo="cosicocomun", url_release="http://example.com/v1.0"
    )
    artefactos_idx = {
        "cosicocomun": {"repo": "msc-sicocomun", "nombre": "X", "descripcion": "Y"}
    }
    pase = PaseData(
        texto_asunto="test",
        texto_hu="HU-1",
        fecha="1/1/2025",
        opcion_ejecucion="Inmediata",
        artefactos=[artefacto],
        ruta_scripts=None,
        forms_url="http://forms.example.com",
        caso=Caso.UNO,
    )
    with pytest.raises(FormsError) as exc_info:
        completar_formulario_devops(
            page, "http://forms.example.com", pase, artefacto, artefactos_idx
        )
    assert "cosicocomun" in str(exc_info.value)


# --- main.py — orquestador ---

from unittest.mock import MagicMock, patch, call
from main import _ejecutar_pase
from exceptions import OutlookError, FormsError
from models import PaseData, ArtefactoInput, Caso


def _make_pase(caso=Caso.UNO, n_artefactos=1):
    artefactos = [
        ArtefactoInput(codigo=f"art{i}", url_release=f"http://url{i}")
        for i in range(n_artefactos)
    ]
    ruta = "scripts/" if caso in (Caso.DOS, Caso.TRES) else None
    if caso == Caso.DOS:
        artefactos = []
    return PaseData(
        texto_asunto="test",
        texto_hu="HU-1",
        fecha="1/1/2025",
        opcion_ejecucion="Inmediata",
        artefactos=artefactos,
        ruta_scripts=ruta,
        forms_url="http://forms.example.com",
        caso=caso,
    )


_ARTEFACTOS_IDX = {
    f"art{i}": {"repo": f"repo{i}", "nombre": f"N{i}", "descripcion": ""}
    for i in range(5)
}
_DESTINATARIOS = {}


@patch("main.completar_formulario_manual")
@patch("main.completar_formulario_devops")
@patch("main.enviar_correo")
@patch("main.construir_correo")
def test_enviar_correo_antes_que_formularios(
    mock_construir, mock_enviar, mock_devops, mock_manual
):
    """Req 4.1: enviar_correo se llama antes que cualquier completar_formulario_*."""
    page = MagicMock()
    call_order = []
    mock_enviar.side_effect = lambda *a, **kw: call_order.append("enviar_correo")
    mock_devops.side_effect = lambda *a, **kw: call_order.append(
        "completar_formulario_devops"
    )

    pase = _make_pase(Caso.UNO, n_artefactos=1)
    _ejecutar_pase(page, pase, _ARTEFACTOS_IDX, _DESTINATARIOS)

    assert "enviar_correo" in call_order
    assert "completar_formulario_devops" in call_order
    assert call_order.index("enviar_correo") < call_order.index(
        "completar_formulario_devops"
    )


@patch("main.completar_formulario_manual")
@patch("main.completar_formulario_devops")
@patch("main.enviar_correo")
@patch("main.construir_correo")
def test_caso3_devops_antes_que_manual(
    mock_construir, mock_enviar, mock_devops, mock_manual
):
    """Req 8.1/8.2: en Caso_3 todos los formularios DevOps se crean antes del Manual."""
    page = MagicMock()
    call_order = []
    mock_devops.side_effect = lambda *a, **kw: call_order.append("devops")
    mock_manual.side_effect = lambda *a, **kw: call_order.append("manual")

    pase = _make_pase(Caso.TRES, n_artefactos=2)
    _ejecutar_pase(page, pase, _ARTEFACTOS_IDX, _DESTINATARIOS)

    devops_indices = [i for i, v in enumerate(call_order) if v == "devops"]
    manual_indices = [i for i, v in enumerate(call_order) if v == "manual"]

    assert len(devops_indices) == 2
    assert len(manual_indices) == 1
    assert max(devops_indices) < manual_indices[0]


@patch("main.completar_formulario_manual")
@patch("main.completar_formulario_devops")
@patch("main.enviar_correo")
@patch("main.construir_correo")
def test_outlook_error_detiene_ejecucion(
    mock_construir, mock_enviar, mock_devops, mock_manual
):
    """Req 5.11: OutlookError en enviar_correo detiene la ejecución sin llamar a ningún formulario."""
    page = MagicMock()
    mock_enviar.side_effect = OutlookError("fallo outlook")

    pase = _make_pase(Caso.UNO, n_artefactos=1)
    with pytest.raises(OutlookError):
        _ejecutar_pase(page, pase, _ARTEFACTOS_IDX, _DESTINATARIOS)

    mock_devops.assert_not_called()
    mock_manual.assert_not_called()


@patch("main.completar_formulario_manual")
@patch("main.completar_formulario_devops")
@patch("main.enviar_correo")
@patch("main.construir_correo")
def test_forms_error_no_impide_siguiente_artefacto(
    mock_construir, mock_enviar, mock_devops, mock_manual
):
    """Req 5.11: FormsError en artefacto N no impide procesar el artefacto N+1."""
    page = MagicMock()
    call_count = {"n": 0}

    def devops_side_effect(*a, **kw):
        call_count["n"] += 1
        if call_count["n"] == 1:
            raise FormsError("error en art0")

    mock_devops.side_effect = devops_side_effect

    pase = _make_pase(Caso.UNO, n_artefactos=2)
    errores = _ejecutar_pase(page, pase, _ARTEFACTOS_IDX, _DESTINATARIOS)

    assert mock_devops.call_count == 2
    assert len(errores) == 1
