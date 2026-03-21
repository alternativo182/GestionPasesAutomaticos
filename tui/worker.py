"""Worker para ejecutar el núcleo de automatización en un hilo separado."""
from __future__ import annotations

import os
from datetime import datetime
from typing import Callable, TextIO

from playwright.sync_api import sync_playwright

from exceptions import FormsError, OutlookError
from forms.formulario_base import esperar_login_forms
from forms.formulario_devops import completar_formulario_devops
from forms.formulario_manual import completar_formulario_manual
from models import Caso, PaseData
from outlook.correo import construir_correo, enviar_correo, esperar_login


def _crear_log() -> tuple[TextIO, str]:
    os.makedirs("logs", exist_ok=True)
    nombre = datetime.now().strftime("pase_%Y%m%d_%H%M%S.log")
    ruta = os.path.join("logs", nombre)
    fh = open(ruta, "w", encoding="utf-8")
    return fh, ruta


def _escribir_log(fh: TextIO, mensaje: str) -> None:
    ts = datetime.now().strftime("%H:%M:%S")
    linea = f"[{ts}] {mensaje}"
    fh.write(linea + "\n")
    fh.flush()


def ejecutar_pase_worker(
    pase: PaseData,
    artefactos_idx: dict[str, dict],
    destinatarios: dict,
    callback_progreso: Callable[[str], None],
) -> tuple[list[str], str]:
    """Ejecuta el núcleo de automatización notificando cada paso al callback."""
    log_fh, ruta_log = _crear_log()

    def _progreso(mensaje: str) -> None:
        _escribir_log(log_fh, mensaje)
        callback_progreso(mensaje)

    errores: list[str] = []
    user_data_dir = os.path.join(os.path.expanduser("~"), ".automatizacion_pases_profile")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch_persistent_context(user_data_dir, headless=False)
            page = browser.new_page()
            try:
                # Paso 1 — Login en Forms
                _progreso("Abriendo Microsoft Forms... Si pide login, complete el MFA (tiene hasta 5 minutos).")
                esperar_login_forms(page, pase.forms_url)
                _progreso("✓ Login en Forms completado")

                # Paso 2 — Login en Outlook
                page.goto("https://outlook.office.com/mail")
                _progreso("Por favor complete el login en Outlook Web...")
                esperar_login(page)
                _progreso("✓ Login en Outlook completado")

                # Paso 3 — Correo
                correo = construir_correo(pase, destinatarios)
                enviar_correo(page, correo)
                _progreso("✓ Correo enviado")

                # Paso 4 — Formularios DevOps
                if pase.caso in (Caso.UNO, Caso.TRES):
                    total = len(pase.artefactos)
                    for i, artefacto in enumerate(pase.artefactos, 1):
                        try:
                            _progreso(f"⏳ Formulario DevOps {i}/{total} ({artefacto.codigo}) — revisá y hacé clic en Enviar")
                            completar_formulario_devops(page, pase.forms_url, pase, artefacto, artefactos_idx)
                            _progreso(f"✓ Formulario DevOps {i}/{total} enviado ({artefacto.codigo})")
                        except FormsError as e:
                            _progreso(f"✗ Error en formulario DevOps ({artefacto.codigo}): {e}")
                            errores.append(str(e))

                # Paso 5 — Formulario Manual
                if pase.caso in (Caso.DOS, Caso.TRES):
                    try:
                        _progreso("⏳ Formulario Manual — revisá y hacé clic en Enviar")
                        completar_formulario_manual(page, pase.forms_url, pase)
                        _progreso("✓ Formulario Manual enviado")
                    except FormsError as e:
                        _progreso(f"✗ Error en formulario Manual: {e}")
                        errores.append(str(e))

                _progreso("=== Automatización finalizada ===")
                if errores:
                    _progreso(f"Completado con {len(errores)} error(es).")
                else:
                    _progreso("✓ Todos los formularios enviados exitosamente.")

            except OutlookError as e:
                _progreso(f"✗ Error fatal en Outlook: {e}")
                errores.append(str(e))
            finally:
                browser.close()

    except Exception as e:
        _progreso(f"✗ Error inesperado: {e}")
        errores.append(str(e))
    finally:
        log_fh.close()

    return errores, ruta_log
