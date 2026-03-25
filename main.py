from __future__ import annotations

import os
import sys
from datetime import datetime
from typing import TextIO

from playwright.sync_api import sync_playwright

from exceptions import FormsError, OutlookError, ValidationError
from forms.formulario_base import esperar_login_forms
from forms.formulario_devops import completar_formulario_devops
from forms.formulario_manual import completar_formulario_manual
from models import ArtefactoInput, Caso, PaseData
from outlook.correo import construir_correo, enviar_correo, esperar_login
from utils.browser_resolver import get_browser_path
from utils.config_loader import cargar_artefactos, cargar_destinatarios

# URL fija del formulario de Microsoft Forms para pases SICO
FORMS_URL = "https://forms.office.com/Pages/ResponsePage.aspx?id=eQz1rjw3-UeC7n-CSipNUZcRcu5aCiJBgzQxPKcgO7xUQkJSR1lNUVlUNDJYNkpUVUhRSjVBOEJTMyQlQCN0PWcu"


# ---------------------------------------------------------------------------
# 9.1 — Determinación de caso
# ---------------------------------------------------------------------------


def determinar_caso(artefactos: list[ArtefactoInput], ruta_scripts: str | None) -> Caso:
    """Retorna Caso.UNO, Caso.DOS o Caso.TRES según las reglas de negocio.

    | artefactos | ruta_scripts | Caso                 |
    | ---------- | ------------ | -------------------- |
    | len > 0    | None         | Caso_1               |
    | len == 0   | str no vacío | Caso_2               |
    | len > 0    | str no vacío | Caso_3               |
    | len == 0   | None         | Error — no continuar |

    Raises:
        ValidationError: Si no hay artefactos ni ruta_scripts.
    """
    tiene_artefactos = len(artefactos) > 0
    tiene_scripts = ruta_scripts is not None and ruta_scripts.strip() != ""

    if tiene_artefactos and not tiene_scripts:
        return Caso.UNO
    if not tiene_artefactos and tiene_scripts:
        return Caso.DOS
    if tiene_artefactos and tiene_scripts:
        return Caso.TRES
    # len == 0 y ruta_scripts is None
    raise ValidationError(
        "Debe proporcionar al menos un artefacto o una ruta de scripts BD."
    )


# ---------------------------------------------------------------------------
# 9.3 — Recolección de inputs
# ---------------------------------------------------------------------------


def recolectar_inputs(artefactos_idx: dict[str, dict]) -> PaseData:
    """Solicita todos los inputs al usuario por consola y retorna PaseData validado.

    Raises:
        ValidationError: Si algún input es inválido.
    """
    texto_asunto = input("Asunto del pase: ")
    texto_hu = input("HU: ")
    fecha = input("Fecha (d/M/yyyy): ")

    opcion_ejecucion = input("Opción de ejecución (Inmediata/Programada): ")
    if opcion_ejecucion not in {"Inmediata", "Programada"}:
        raise ValidationError(
            f"Opción de ejecución inválida: '{opcion_ejecucion}'. "
            "Debe ser 'Inmediata' o 'Programada'."
        )

    n = int(input("Número de artefactos (0 si solo scripts BD): ") or "0")
    artefactos: list[ArtefactoInput] = []
    for i in range(n):
        codigo = input(f"Código artefacto {i + 1}: ")
        if codigo not in artefactos_idx:
            raise ValidationError(
                f"Código de artefacto desconocido: '{codigo}'. "
                "Verifique la configuración."
            )
        url = input(f"URL release {i + 1}: ")
        artefactos.append(ArtefactoInput(codigo=codigo, url_release=url))

    ruta_scripts = input("Ruta scripts BD (Enter para omitir): ") or None

    # Validar que hay al menos un artefacto o ruta_scripts (delega a determinar_caso)
    caso = determinar_caso(artefactos, ruta_scripts)

    return PaseData(
        texto_asunto=texto_asunto,
        texto_hu=texto_hu,
        fecha=fecha,
        opcion_ejecucion=opcion_ejecucion,
        artefactos=artefactos,
        ruta_scripts=ruta_scripts,
        forms_url=FORMS_URL,
        caso=caso,
    )


# ---------------------------------------------------------------------------
# 9.5 — Progreso y main
# ---------------------------------------------------------------------------

_log_file: TextIO | None = None


def _init_log() -> None:
    """Crea el archivo de log para esta ejecución en la carpeta logs/."""
    global _log_file
    os.makedirs("logs", exist_ok=True)
    nombre = datetime.now().strftime("pase_%Y%m%d_%H%M%S.log")
    ruta = os.path.join("logs", nombre)
    _log_file = open(ruta, "w", encoding="utf-8")
    mostrar_progreso(f"Log de ejecución: {ruta}")


def mostrar_progreso(mensaje: str) -> None:
    """Imprime mensaje de progreso con prefijo [HH:MM:SS] y lo escribe al log."""
    ts = datetime.now().strftime("%H:%M:%S")
    linea = f"[{ts}] {mensaje}"
    print(linea)
    if _log_file is not None:
        _log_file.write(linea + "\n")
        _log_file.flush()


def _ejecutar_pase(
    page: object,
    pase: PaseData,
    artefactos_idx: dict[str, dict],
    destinatarios: dict,
) -> list[str]:
    """Orquesta el envío del correo y el llenado de formularios para un pase.

    Retorna la lista de errores no-fatales (FormsError) encontrados.
    Lanza OutlookError si el correo falla (error fatal).
    """
    correo = construir_correo(pase, destinatarios)
    enviar_correo(page, correo)
    mostrar_progreso("✓ Correo enviado")

    errores: list[str] = []

    if pase.caso in (Caso.UNO, Caso.TRES):
        total = len(pase.artefactos)
        for i, artefacto in enumerate(pase.artefactos, 1):
            try:
                mostrar_progreso(
                    f"⏳ Completando formulario DevOps {i}/{total} ({artefacto.codigo})..."
                )
                completar_formulario_devops(
                    page, pase.forms_url, pase, artefacto, artefactos_idx
                )
                mostrar_progreso(
                    f"✓ Formulario DevOps {i}/{total} enviado ({artefacto.codigo})"
                )
            except FormsError as e:
                mostrar_progreso(
                    f"✗ Error en formulario DevOps ({artefacto.codigo}): {e}"
                )
                errores.append(str(e))

    if pase.caso in (Caso.DOS, Caso.TRES):
        try:
            mostrar_progreso("⏳ Completando formulario Manual...")
            completar_formulario_manual(page, pase.forms_url, pase)
            mostrar_progreso("✓ Formulario Manual enviado")
        except FormsError as e:
            mostrar_progreso(f"✗ Error en formulario Manual: {e}")
            errores.append(str(e))

    return errores


def main() -> None:
    """Punto de entrada principal. Orquesta todo el flujo."""
    _init_log()
    artefactos_idx = cargar_artefactos()
    destinatarios = cargar_destinatarios()
    pase = recolectar_inputs(artefactos_idx)

    # Obtener ruta del browser desde cache
    browser_path = get_browser_path()
    if browser_path is None:
        mostrar_progreso("✗ ERROR: No se encontró Chromium.")
        mostrar_progreso("  Ejecute install.ps1 para instalar el browser.")
        mostrar_progreso(
            "  O descargue manualmente: https://playwright.dev/docs/browsers"
        )
        return

    mostrar_progreso(f"✓ Browser encontrado: {browser_path}")

    with sync_playwright() as p:
        # Usar perfil persistente para conservar cookies de sesión entre ejecuciones
        # Esto evita tener que hacer login + MFA en cada ejecución
        user_data_dir = os.path.join(
            os.path.expanduser("~"), ".automatizacion_pases_profile"
        )
        browser = p.chromium.launch_persistent_context(
            user_data_dir,
            headless=False,
            executable_path=str(browser_path),
        )
        browser = p.chromium.launch_persistent_context(
            user_data_dir,
            headless=False,
        )
        page = browser.new_page()
        try:
            # 1. Login en Forms primero (para que la sesión quede autenticada)
            mostrar_progreso(
                "Abriendo Microsoft Forms... Si pide login, complete el MFA (tiene hasta 5 minutos)."
            )
            esperar_login_forms(page, pase.forms_url)
            mostrar_progreso("✓ Login en Forms completado")

            # 2. Login en Outlook
            page.goto("https://outlook.office.com/mail")
            mostrar_progreso("Por favor complete el login en Outlook Web...")
            esperar_login(page)

            errores = _ejecutar_pase(page, pase, artefactos_idx, destinatarios)

            mostrar_progreso("=== Resumen ===")
            if errores:
                mostrar_progreso(f"Completado con {len(errores)} error(es):")
                for err in errores:
                    mostrar_progreso(f"  - {err}")
            else:
                mostrar_progreso("Todos los formularios enviados exitosamente.")

        except OutlookError as e:
            mostrar_progreso(f"✗ Error fatal en Outlook: {e}")
        finally:
            browser.close()
            if _log_file is not None:
                _log_file.close()


if __name__ == "__main__":
    from tui_app import TUIApp

    TUIApp().run()
