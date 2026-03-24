from playwright.sync_api import Page

from exceptions import FormsError
from forms.formulario_base import construir_base_data, completar_campos_base, esperar_formulario_listo, esperar_envio_manual
from models import PaseData, ManualFormData


def construir_manual_data() -> ManualFormData:
    """Función pura. Retorna los datos fijos para el formulario Manual.

    Returns:
        ManualFormData con bd="FOHXG04 - SICO" y nuevas_tablas="No".
    """
    return ManualFormData(bd="FOHXG04 - SICO", nuevas_tablas="No")


def completar_formulario_manual(page: Page, forms_url: str, pase: PaseData) -> None:
    """Navega a forms_url, completa campos base + Manual y envía el formulario.

    Secuencia:
    1. Navegar a forms_url
    2. Construir base_data con codigo_artefacto="" y completar inputs 1-8
    3. Seleccionar "Manual" en Input 9 y esperar visibilidad de inputs 10-11
    4. Completar inputs 10-11 con los datos fijos del formulario Manual
    5. Clic en submit

    Args:
        page: Objeto Page de Playwright.
        forms_url: URL del formulario de Microsoft Forms.
        pase: Datos del pase a producción.

    Raises:
        FormsError: Si ocurre cualquier error durante la automatización.
    """
    try:
        # 1. Navegar al formulario y esperar que cargue
        esperar_formulario_listo(page, forms_url)

        # 2. Completar campos base (inputs 1-8) con codigo_artefacto=""
        base_data = construir_base_data(pase, "SICO")
        completar_campos_base(page, base_data)

        # 3. Input 9 — Método pase: seleccionar "Manual" y esperar inputs 10-11
        page.click('div[aria-labelledby^="QuestionId_r1fd586e16e944bf4924ce92e32790e87"]')
        page.wait_for_selector('[role="listbox"]', state="visible")
        page.click('[role="option"]:has-text("Manual")')

        # Esperar visibilidad de inputs 10-11
        page.wait_for_selector(
            '#QuestionId_rc646c2d2197149c3ab80d8d4e950bf92',
            state="visible",
        )
        page.wait_for_selector(
            'input[name="r491dc438942441a396ae7bc7174341aa"][value="No"]',
            state="visible",
        )

        # 4. Construir datos Manual y completar inputs 10-11
        manual_data = construir_manual_data()

        # Input 10 — BD (dropdown → "FOHXG04 - SICO")
        page.click('div[aria-labelledby^="QuestionId_rc646c2d2197149c3ab80d8d4e950bf92"]')
        page.wait_for_selector('[role="listbox"]', state="visible")
        page.click(f'[role="option"]:has-text("{manual_data.bd}")')

        # Input 11 — Nuevas tablas (radio button → "No") y esperar inputs 12-13
        page.click(f'input[name="r491dc438942441a396ae7bc7174341aa"][value="{manual_data.nuevas_tablas}"]')

        # Input 12 — Ruta scripts BD (si aplica)
        if pase.ruta_scripts:
            page.wait_for_selector(
                'input[aria-labelledby*="QuestionId_rcf18a944445b43f8a2910e53e0a6d10a"]',
                state="visible",
                timeout=10_000,
            )
            page.fill(
                'input[aria-labelledby*="QuestionId_rcf18a944445b43f8a2910e53e0a6d10a"]',
                pase.ruta_scripts,
            )

        # 5. Esperar envío manual — el usuario revisa y hace clic en Enviar
        esperar_envio_manual(page)

    except Exception as e:
        raise FormsError(f"Error en formulario Manual: {e}") from e
