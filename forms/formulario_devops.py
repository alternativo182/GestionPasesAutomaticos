from playwright.sync_api import Page

from exceptions import FormsError
from forms.formulario_base import (
    construir_base_data,
    completar_campos_base,
    esperar_formulario_listo,
    esperar_envio_manual,
)
from models import PaseData, ArtefactoInput, DevOpsFormData


def construir_devops_data(
    pase: PaseData,
    artefacto: ArtefactoInput,
    artefactos_idx: dict,
) -> DevOpsFormData:
    """Función pura. Construye los datos para los campos específicos DevOps.

    Mapeos:
    - opcion_ejecucion "Inmediata" → tipo_pase "Hotfix"
    - opcion_ejecucion "Programada" → tipo_pase "Release"
    - codigo "websico" → proyecto_devops "APL-SICO"
    - cualquier otro codigo → proyecto_devops "SCO-SICO"
    - artefacto (Input 16) = codigo del artefacto = codigo_artefacto de BaseFormData (Input 5)
    - repo_azure = valor de repo en artefactos_idx para el codigo del artefacto

    Args:
        pase: Datos del pase a producción.
        artefacto: Artefacto a desplegar.
        artefactos_idx: Índice {codigo: {repo, nombre, descripcion}} cargado desde la base de datos.

    Returns:
        DevOpsFormData con todos los campos mapeados.
    """
    tipo_pase = "Hotfix" if pase.opcion_ejecucion == "Inmediata" else "Release"
    proyecto_devops = "APL-SICO" if artefacto.codigo == "websico" else "SCO-SICO"
    repo_azure = artefactos_idx[artefacto.codigo]["repo"]

    return DevOpsFormData(
        tipo_pase=tipo_pase,
        url_release=artefacto.url_release,
        proyecto_devops=proyecto_devops,
        artefacto=artefacto.codigo,
        repo_azure=repo_azure,
    )


def completar_formulario_devops(
    page: Page,
    forms_url: str,
    pase: PaseData,
    artefacto: ArtefactoInput,
    artefactos_idx: dict,
) -> None:
    """Navega a forms_url, completa campos base + DevOps y envía el formulario.

    Secuencia:
    1. Navegar a forms_url
    2. Construir base_data y completar inputs 1-8 (completar_campos_base)
    3. Seleccionar "DevOps" en Input 9 y esperar visibilidad de inputs 10-18
    4. Construir devops_data y completar inputs 10-18
    5. Clic en submit

    Args:
        page: Objeto Page de Playwright.
        forms_url: URL del formulario de Microsoft Forms.
        pase: Datos del pase a producción.
        artefacto: Artefacto a desplegar.
        artefactos_idx: Índice de artefactos cargado desde la base de datos.

    Raises:
        FormsError: Si ocurre cualquier error durante la automatización.
    """
    try:
        # 1. Navegar al formulario y esperar que cargue
        esperar_formulario_listo(page, forms_url)

        # 2. Completar campos base (inputs 1-8)
        base_data = construir_base_data(pase, artefacto.codigo)
        completar_campos_base(page, base_data)

        # 3. Input 9 — Método pase: seleccionar "DevOps" y esperar inputs 10-18
        page.click(
            'div[aria-labelledby^="QuestionId_r1fd586e16e944bf4924ce92e32790e87"]'
        )
        page.wait_for_selector('[role="listbox"]', state="visible")
        page.click('[role="option"]:has-text("DevOps")')

        # Esperar visibilidad de inputs 10-18
        page.wait_for_selector(
            f'input[name="rc3b03cba41d9417088fb3392d277a07f"]',
            state="visible",
        )

        # 4. Construir datos DevOps y completar inputs 10-18
        devops_data = construir_devops_data(pase, artefacto, artefactos_idx)

        # Input 10 — Tipo PASE (radio button)
        page.click(
            f'input[name="rc3b03cba41d9417088fb3392d277a07f"][value="{devops_data.tipo_pase}"]'
        )

        # Input 11 — Servidor (dropdown → "Anthos")
        page.click(
            'div[aria-labelledby^="QuestionId_rf9b9c647dd8c4d0a811e899da88ea094"]'
        )
        page.wait_for_selector('[role="listbox"]', state="visible")
        page.click('[role="option"]:has-text("Anthos")')

        # Input 12 — URL release
        page.fill(
            'input[aria-labelledby*="QuestionId_r5723d9e923af4eb3aef75e1e7971df6d"]',
            devops_data.url_release,
        )

        # Input 13 — Config (radio button → "NO")
        page.click('input[name="r1e89ec0af3e648b19a75d370e574000c"][value="NO"]')

        # Input 14 — Web.conf (vacío)
        page.fill(
            'input[aria-labelledby*="QuestionId_ra9d8e091630c4da198cc88862b94c124"]',
            "",
        )

        # Input 15 — Proyecto DEVOPS (dropdown)
        page.click(
            'div[aria-labelledby^="QuestionId_r5ac855f36819495a8f684b8c69667c0b"]'
        )
        page.wait_for_selector('[role="listbox"]', state="visible")
        page.click(f'[role="option"]:has-text("{devops_data.proyecto_devops}")')

        # Input 16 — Artefacto
        page.fill(
            'input[aria-labelledby*="QuestionId_r989ec56aa8f3491ca04e5c56f5db002b"]',
            devops_data.artefacto,
        )

        # Input 17 — Repo Azure
        page.fill(
            'input[aria-labelledby*="QuestionId_rca2faa97c69b4a808f5b2f82e3b3c5af"]',
            devops_data.repo_azure,
        )

        # Input 18 — Cambios BD (radio button → "No")
        page.click('input[name="rab53491496864b1487df1c2ad32ed5aa"][value="No"]')

        # 5. Esperar envío manual — el usuario revisa y hace clic en Enviar
        esperar_envio_manual(page)

    except Exception as e:
        raise FormsError(f"Error en formulario DevOps ({artefacto.codigo}): {e}") from e
