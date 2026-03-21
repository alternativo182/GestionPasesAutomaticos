from urllib.parse import urlparse, urlencode, parse_qs, urlunparse

from models import PaseData, BaseFormData

# Selector del primer campo del formulario (Fecha)
_SELECTOR_FECHA = 'input#DatePicker0-label'

# Timeout para esperar que el usuario complete el login en Forms (incluye MFA)
_FORMS_LOGIN_TIMEOUT_MS = 300_000  # 5 minutos para MFA

# Timeout para esperar que Forms cargue una vez ya autenticado
_FORMS_LOAD_TIMEOUT_MS = 60_000


def _limpiar_forms_url(url: str) -> str:
    """Elimina parámetros embed/mobile de la URL de Forms que alteran el DOM."""
    parsed = urlparse(url)
    params = parse_qs(parsed.query, keep_blank_values=True)
    params.pop("mobile", None)
    params.pop("embed", None)
    query = urlencode({k: v[0] for k, v in params.items()})
    return urlunparse(parsed._replace(query=query))


def esperar_login_forms(page, forms_url: str) -> None:
    """Navega a forms_url y espera que el usuario complete el login en Forms (con MFA).

    Flujo:
    1. Navega a forms_url -> puede redirigir a login o cargar directo si hay sesión
    2. Si hay sesión activa, el formulario carga directamente
    3. Si no hay sesión, el usuario completa el login + MFA (hasta 5 minutos)
    4. Una vez en forms.office.com, navega al formulario y espera que sea visible
    """
    url = _limpiar_forms_url(forms_url)
    page.goto(url)

    # Esperar hasta que el formulario sea visible O hasta que estemos en forms.office.com
    # Si ya hay sesión activa, el formulario carga directamente
    try:
        page.wait_for_selector(_SELECTOR_FECHA, state="visible", timeout=_FORMS_LOAD_TIMEOUT_MS)
        return  # Sesión activa, formulario cargó directamente
    except Exception:
        pass  # No hay sesión activa, hay que hacer login

    # Esperar que el usuario complete el login + MFA y llegue a forms.office.com
    page.wait_for_url("**/forms.office.com/**", timeout=_FORMS_LOGIN_TIMEOUT_MS)

    # Navegar al formulario desde forms.office.com (evita nuevo ciclo OAuth)
    current_url = page.url
    if "ResponsePage" not in current_url:
        page.goto(url)

    # Esperar que el formulario sea visible
    page.wait_for_selector(_SELECTOR_FECHA, state="visible", timeout=_FORMS_LOAD_TIMEOUT_MS)


def esperar_formulario_listo(page, forms_url: str) -> None:
    """Navega a forms_url y espera que el formulario cargue completamente.

    Asume que el usuario ya esta autenticado en forms.office.com.
    """
    url = _limpiar_forms_url(forms_url)
    page.goto(url, wait_until="networkidle")
    page.wait_for_selector(_SELECTOR_FECHA, state="visible", timeout=_FORMS_LOAD_TIMEOUT_MS)


def esperar_envio_manual(page, timeout_ms: int = 300_000) -> None:
    """Espera a que el usuario haga clic en Enviar manualmente.

    Detecta la pantalla de confirmación de Microsoft Forms usando el
    elemento data-automation-id="submitAnother" que aparece tras el envío.

    Args:
        timeout_ms: Tiempo máximo de espera (default 5 minutos).

    Raises:
        FormsError: Si el usuario no envía el formulario en el tiempo dado.
    """
    from exceptions import FormsError
    try:
        page.wait_for_selector(
            '[data-automation-id="submitAnother"]',
            state="visible",
            timeout=timeout_ms,
        )
    except Exception as e:
        raise FormsError(f"Timeout esperando envío manual del formulario: {e}") from e


def construir_base_data(pase: PaseData, codigo_artefacto: str) -> BaseFormData:
    """Funcion pura. Construye los datos para los campos comunes del formulario."""
    return BaseFormData(
        fecha=pase.fecha,
        opcion_ejecucion=pase.opcion_ejecucion,
        texto_hu=pase.texto_hu,
        codigo_artefacto=codigo_artefacto,
    )


def completar_campos_base(page, data: BaseFormData) -> None:
    """Completa los inputs 1-8 en el formulario activo.

    - Input 1: Fecha
    - Input 2: Opcion de ejecucion (radio button)
    - Input 3: HU
    - Input 4: Agora (siempre "No")
    - Input 5: Endpoint/codigo artefacto
    - Input 6: Responsable (dropdown -> "Marco Mosqueira")
    - Input 7: Donde cambio (click "Aplicacion/BD" -> espera inputs 8-9)
    - Input 8: Sistema (click "SICO")
    """
    # Input 1 — Fecha
    page.fill('input#DatePicker0-label', data.fecha)

    # Input 2 — Ejecucion (radio button)
    page.click(f'input[name="rf62c7c231241404fb3c72296c6e372b1"][value="{data.opcion_ejecucion}"]')

    # Input 3 — HU (aria-labelledby contiene el QuestionId)
    page.fill(
        'input[aria-labelledby*="QuestionId_re8a9340464d1401897c22d9dc3a9399f"]',
        data.texto_hu,
    )

    # Input 4 — Agora (siempre "No")
    page.click('input[name="r04057fb07c984f109a1c2a6d67114e5e"][value="No"]')

    # Input 5 — Endpoint / codigo artefacto (aria-labelledby contiene el QuestionId)
    page.fill(
        'input[aria-labelledby*="QuestionId_reb7dee5f8d714426afe0d2de2c50e43c"]',
        data.codigo_artefacto,
    )

    # Input 6 — Responsable (dropdown -> "Marco Mosqueira")
    page.click('div[aria-labelledby^="QuestionId_r5739e22cfbc641829dde6e4cc23f83bb"]')
    page.wait_for_selector('[role="listbox"]', state="visible")
    page.click('[role="option"]:has-text("Marco Mosqueira")')    # Input 7 — Donde cambio: click "Aplicación/BD" y esperar que inputs 8-9 sean visibles
    page.click('input[name="r112deb4a9605429e824664e088c3ad1e"][value="Aplicación/BD"]')
    page.wait_for_selector(
        'input[name="r0409ad20e573453fbe6834322be198a1"][value="SICO"]',
        state="visible",
    )
    page.wait_for_selector('#QuestionId_r1fd586e16e944bf4924ce92e32790e87', state="visible")

    # Input 8 — Sistema: click "SICO"
    page.click('input[name="r0409ad20e573453fbe6834322be198a1"][value="SICO"]')
