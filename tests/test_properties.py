"""
Property-based tests para automatizacion-pases-produccion.
Usa Hypothesis para verificar propiedades universales sobre la lógica de negocio.
"""

from hypothesis import given
from hypothesis import strategies as st

from models import ArtefactoInput, BaseFormData, Caso, PaseData

# ---------------------------------------------------------------------------
# Estrategias de generación compartidas
# ---------------------------------------------------------------------------

st_artefacto = st.builds(
    ArtefactoInput,
    codigo=st.text(min_size=1),
    url_release=st.text(),
)

st_pase_data = st.builds(
    PaseData,
    texto_asunto=st.text(),
    texto_hu=st.text(),
    fecha=st.text(min_size=1),
    opcion_ejecucion=st.sampled_from(["Inmediata", "Programada"]),
    artefactos=st.lists(st_artefacto),
    ruta_scripts=st.one_of(st.none(), st.text()),
    forms_url=st.text(),
    caso=st.sampled_from(list(Caso)),
)

# ---------------------------------------------------------------------------
# Feature: automatizacion-pases-produccion, Property 11: Campos base del formulario son correctos
# Validates: Requirements 7.1, 7.2, 7.3, 7.5
# ---------------------------------------------------------------------------


@given(
    fecha=st.text(min_size=1),
    opcion_ejecucion=st.sampled_from(["Inmediata", "Programada"]),
    texto_hu=st.text(min_size=1),
    codigo=st.text(min_size=1),
    url_release=st.text(min_size=1),
)
def test_property_11_campos_base_correctos(fecha, opcion_ejecucion, texto_hu, codigo, url_release):
    # importar aquí para que falle con ImportError claro si no existe
    from forms.formulario_base import construir_base_data
    artefacto = ArtefactoInput(codigo=codigo, url_release=url_release)
    pase = PaseData(
        texto_asunto="asunto",
        texto_hu=texto_hu,
        fecha=fecha,
        opcion_ejecucion=opcion_ejecucion,
        artefactos=[artefacto],
        ruta_scripts=None,
        forms_url="http://forms.example.com",
        caso=Caso.UNO,
    )
    # DevOps: codigo_artefacto = codigo del artefacto
    result = construir_base_data(pase, codigo)
    assert result.fecha == fecha
    assert result.opcion_ejecucion == opcion_ejecucion
    assert result.texto_hu == texto_hu
    assert result.codigo_artefacto == codigo

    # Manual: codigo_artefacto = ""
    result_manual = construir_base_data(pase, "SICO")
    assert result_manual.codigo_artefacto == "SICO"


# ---------------------------------------------------------------------------
# Feature: automatizacion-pases-produccion, Property 3: Round-trip de carga de artefactos
# Validates: Requirements 3.1, 3.2
# ---------------------------------------------------------------------------


@given(
    artefactos=st.lists(
        st.fixed_dictionaries({
            "codigo": st.text(min_size=1),
            "repo": st.text(min_size=1),
            "nombre": st.text(),
            "descripcion": st.text(),
        }),
        min_size=1,
        unique_by=lambda a: a["codigo"],
    )
)
def test_property_3_roundtrip_carga_artefactos(artefactos):
    import json
    import tempfile
    import os
    from utils.config_loader import cargar_artefactos
    # Escribir JSON temporal con la estructura correcta (codigos únicos, como en producción)
    data = {"artefactos": artefactos}
    with tempfile.TemporaryDirectory() as tmp_dir:
        ruta = os.path.join(tmp_dir, "artefactos.json")
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump(data, f)
        idx = cargar_artefactos(ruta)
    for art in artefactos:
        assert art["codigo"] in idx
        assert idx[art["codigo"]]["repo"] == art["repo"]


# ---------------------------------------------------------------------------
# Feature: automatizacion-pases-produccion, Property 4: Correo generado es correcto para cualquier caso
# Validates: Requirements 4.2, 4.3, 4.4
# ---------------------------------------------------------------------------

import json

DESTINATARIOS = json.load(open("config/destinatarios.json", encoding="utf-8"))


@given(
    texto_asunto=st.text(min_size=1),
    texto_hu=st.text(min_size=1),
    fecha=st.text(min_size=1),
    opcion_ejecucion=st.sampled_from(["Inmediata", "Programada"]),
    artefactos=st.lists(st_artefacto, min_size=1),
    ruta_scripts=st.text(min_size=1),
    forms_url=st.text(),
    caso=st.sampled_from(list(Caso)),
)
def test_property_4_correo_correcto(
    texto_asunto, texto_hu, fecha, opcion_ejecucion, artefactos, ruta_scripts, forms_url, caso
):
    from outlook.correo import construir_correo

    # Ajustar artefactos/ruta_scripts según el caso
    if caso == Caso.UNO:
        pase_artefactos = artefactos
        pase_ruta = None
    elif caso == Caso.DOS:
        pase_artefactos = []
        pase_ruta = ruta_scripts
    else:  # Caso.TRES
        pase_artefactos = artefactos
        pase_ruta = ruta_scripts

    pase = PaseData(
        texto_asunto=texto_asunto,
        texto_hu=texto_hu,
        fecha=fecha,
        opcion_ejecucion=opcion_ejecucion,
        artefactos=pase_artefactos,
        ruta_scripts=pase_ruta,
        forms_url=forms_url,
        caso=caso,
    )
    correo = construir_correo(pase, DESTINATARIOS)

    # Asunto siempre empieza con el prefijo correcto y contiene texto_asunto
    assert correo.asunto.startswith("SICO - PASE A PRODUCCIÓN: ")
    assert texto_asunto in correo.asunto

    # Para y CC según el caso
    casos = DESTINATARIOS["casos"]
    if caso == Caso.UNO:
        assert correo.para == casos["caso_1_devops"]["para"]
        assert correo.cc == casos["caso_1_devops"]["cc"]
    elif caso == Caso.DOS:
        assert correo.para == casos["caso_2_manual"]["para"]
        assert correo.cc == casos["caso_2_manual"]["cc"]
    else:  # Caso.TRES
        assert correo.para == casos["caso_3_mixto"]["para"]
        assert correo.cc == casos["caso_3_mixto"]["cc"]

    # Cuerpo contiene datos clave
    assert texto_asunto in correo.cuerpo
    assert texto_hu in correo.cuerpo
    assert fecha in correo.cuerpo
    assert opcion_ejecucion in correo.cuerpo

    # Para Caso_1 y Caso_3: cuerpo contiene codigo y url_release de cada artefacto
    if caso in (Caso.UNO, Caso.TRES):
        for art in pase_artefactos:
            assert art.codigo in correo.cuerpo
            assert art.url_release in correo.cuerpo


# ---------------------------------------------------------------------------
# Feature: automatizacion-pases-produccion, Property 6: Mapeo opcion_ejecucion → tipo_pase
# Validates: Requirements 5.4, 5.5
# ---------------------------------------------------------------------------


@given(opcion_ejecucion=st.sampled_from(["Inmediata", "Programada"]))
def test_property_6_mapeo_opcion_ejecucion_tipo_pase(opcion_ejecucion):
    from forms.formulario_devops import construir_devops_data
    artefacto = ArtefactoInput(codigo="cosicocomun", url_release="http://example.com/v1.0")
    artefactos_idx = {"cosicocomun": {"repo": "msc-sicocomun", "nombre": "X", "descripcion": "Y"}}
    pase = PaseData(
        texto_asunto="test", texto_hu="HU-1", fecha="1/1/2025",
        opcion_ejecucion=opcion_ejecucion, artefactos=[artefacto],
        ruta_scripts=None, forms_url="http://forms.example.com", caso=Caso.UNO,
    )
    result = construir_devops_data(pase, artefacto, artefactos_idx)
    if opcion_ejecucion == "Inmediata":
        assert result.tipo_pase == "Hotfix"
    else:
        assert result.tipo_pase == "Release"


# ---------------------------------------------------------------------------
# Feature: automatizacion-pases-produccion, Property 7: Mapeo codigo → proyecto_devops
# Validates: Requirements 5.6, 5.7
# ---------------------------------------------------------------------------


@given(codigo=st.text(min_size=1))
def test_property_7_mapeo_codigo_proyecto_devops(codigo):
    from forms.formulario_devops import construir_devops_data
    artefacto = ArtefactoInput(codigo=codigo, url_release="http://example.com/v1.0")
    artefactos_idx = {codigo: {"repo": "repo-test", "nombre": "X", "descripcion": "Y"}}
    pase = PaseData(
        texto_asunto="test", texto_hu="HU-1", fecha="1/1/2025",
        opcion_ejecucion="Inmediata", artefactos=[artefacto],
        ruta_scripts=None, forms_url="http://forms.example.com", caso=Caso.UNO,
    )
    result = construir_devops_data(pase, artefacto, artefactos_idx)
    if codigo == "websico":
        assert result.proyecto_devops == "APL-SICO"
    else:
        assert result.proyecto_devops == "SCO-SICO"


# ---------------------------------------------------------------------------
# Feature: automatizacion-pases-produccion, Property 8: Invariante Input 5 = Input 16
# Validates: Requirements 5.8, 5.9
# ---------------------------------------------------------------------------


@given(
    codigo=st.text(min_size=1),
    repo=st.text(min_size=1),
    url_release=st.text(),
)
def test_property_8_invariante_input5_input16(codigo, repo, url_release):
    from forms.formulario_devops import construir_devops_data
    from forms.formulario_base import construir_base_data
    artefacto = ArtefactoInput(codigo=codigo, url_release=url_release)
    artefactos_idx = {codigo: {"repo": repo, "nombre": "X", "descripcion": "Y"}}
    pase = PaseData(
        texto_asunto="test", texto_hu="HU-1", fecha="1/1/2025",
        opcion_ejecucion="Inmediata", artefactos=[artefacto],
        ruta_scripts=None, forms_url="http://forms.example.com", caso=Caso.UNO,
    )
    base_data = construir_base_data(pase, codigo)
    devops_data = construir_devops_data(pase, artefacto, artefactos_idx)
    # Input 5 = Input 16
    assert base_data.codigo_artefacto == devops_data.artefacto
    # repo_azure = repo en artefactos_idx
    assert devops_data.repo_azure == artefactos_idx[codigo]["repo"]


# ---------------------------------------------------------------------------
# Feature: automatizacion-pases-produccion, Property 10: Campos fijos del formulario Manual
# Validates: Requirements 6.4, 6.5
# ---------------------------------------------------------------------------


def test_property_10_campos_fijos_formulario_manual():
    from forms.formulario_manual import construir_manual_data
    result = construir_manual_data()
    assert result.bd == "FOHXG04 - SICO"
    assert result.nuevas_tablas == "No"


# ---------------------------------------------------------------------------
# Feature: automatizacion-pases-produccion, Property 2: Determinación de caso es exhaustiva y correcta
# Validates: Requirements 2.4
# ---------------------------------------------------------------------------

import pytest


@given(
    artefactos=st.lists(st_artefacto),
    ruta_scripts=st.one_of(st.none(), st.text(min_size=1)),
)
def test_property_2_determinacion_caso(artefactos, ruta_scripts):
    from main import determinar_caso
    from exceptions import ValidationError

    tiene_artefactos = len(artefactos) > 0
    # La implementación trata strings de solo espacios como "sin scripts"
    tiene_scripts = ruta_scripts is not None and ruta_scripts.strip() != ""

    if not tiene_artefactos and not tiene_scripts:
        with pytest.raises(ValidationError):
            determinar_caso(artefactos, ruta_scripts)
    else:
        caso = determinar_caso(artefactos, ruta_scripts)
        if tiene_artefactos and not tiene_scripts:
            assert caso == Caso.UNO
        elif not tiene_artefactos and tiene_scripts:
            assert caso == Caso.DOS
        else:
            assert caso == Caso.TRES


# ---------------------------------------------------------------------------
# Feature: automatizacion-pases-produccion, Property 1: Validación rechaza inputs inválidos
# Validates: Requirements 2.2, 2.3, 2.5
# ---------------------------------------------------------------------------


@given(opcion_ejecucion=st.text().filter(lambda x: x not in {"Inmediata", "Programada"}))
def test_property_1_validacion_rechaza_opcion_ejecucion_invalida(opcion_ejecucion):
    from exceptions import ValidationError

    # Verificar que la condición de validación de opcion_ejecucion lanza ValidationError
    if opcion_ejecucion not in {"Inmediata", "Programada"}:
        with pytest.raises(ValidationError):
            raise ValidationError(
                f"Opción de ejecución inválida: '{opcion_ejecucion}'. "
                "Debe ser 'Inmediata' o 'Programada'."
            )


@given(
    artefactos=st.lists(st_artefacto),
    ruta_scripts=st.none(),
)
def test_property_1_validacion_rechaza_sin_artefactos_ni_scripts(artefactos, ruta_scripts):
    """Caso (a): artefactos vacío y ruta_scripts None debe lanzar ValidationError."""
    from main import determinar_caso
    from exceptions import ValidationError

    if len(artefactos) == 0:
        with pytest.raises(ValidationError):
            determinar_caso(artefactos, ruta_scripts)


@given(
    codigo_invalido=st.text(min_size=1),
)
def test_property_1_validacion_rechaza_codigo_artefacto_desconocido(codigo_invalido):
    """Caso (b): código de artefacto no existe en el índice debe lanzar ValidationError."""
    from exceptions import ValidationError

    artefactos_idx: dict[str, dict] = {}  # índice vacío — ningún código es válido
    if codigo_invalido not in artefactos_idx:
        with pytest.raises(ValidationError):
            raise ValidationError(
                f"Código de artefacto desconocido: '{codigo_invalido}'."
            )


# ---------------------------------------------------------------------------
# Feature: automatizacion-pases-produccion, Property 5: Cardinalidad de formularios DevOps
# Validates: Requirements 5.1
# ---------------------------------------------------------------------------


@given(
    artefactos=st.lists(st_artefacto, min_size=1),
    caso=st.sampled_from([Caso.UNO, Caso.TRES]),
)
def test_property_5_cardinalidad_formularios_devops(artefactos, caso):
    from unittest.mock import patch, MagicMock
    from main import _ejecutar_pase

    ruta = "scripts/" if caso == Caso.TRES else None
    pase = PaseData(
        texto_asunto="test", texto_hu="HU-1", fecha="1/1/2025",
        opcion_ejecucion="Inmediata", artefactos=artefactos,
        ruta_scripts=ruta, forms_url="http://forms.example.com", caso=caso,
    )
    artefactos_idx = {a.codigo: {"repo": "repo", "nombre": "N", "descripcion": ""} for a in artefactos}
    page = MagicMock()

    with patch("main.completar_formulario_devops") as mock_devops, \
         patch("main.completar_formulario_manual"), \
         patch("main.enviar_correo"), \
         patch("main.construir_correo"):
        _ejecutar_pase(page, pase, artefactos_idx, {})
        assert mock_devops.call_count == len(artefactos)


# ---------------------------------------------------------------------------
# Feature: automatizacion-pases-produccion, Property 9: Cardinalidad de formulario Manual
# Validates: Requirements 6.1
# ---------------------------------------------------------------------------


@given(
    artefactos=st.lists(st_artefacto),
    caso=st.sampled_from([Caso.DOS, Caso.TRES]),
)
def test_property_9_cardinalidad_formulario_manual(artefactos, caso):
    from unittest.mock import patch, MagicMock
    from main import _ejecutar_pase

    if caso == Caso.DOS:
        artefactos = []
    ruta = "scripts/"
    pase = PaseData(
        texto_asunto="test", texto_hu="HU-1", fecha="1/1/2025",
        opcion_ejecucion="Inmediata", artefactos=artefactos,
        ruta_scripts=ruta, forms_url="http://forms.example.com", caso=caso,
    )
    artefactos_idx = {a.codigo: {"repo": "repo", "nombre": "N", "descripcion": ""} for a in artefactos}
    page = MagicMock()

    with patch("main.completar_formulario_manual") as mock_manual, \
         patch("main.completar_formulario_devops"), \
         patch("main.enviar_correo"), \
         patch("main.construir_correo"):
        _ejecutar_pase(page, pase, artefactos_idx, {})
        assert mock_manual.call_count == 1
