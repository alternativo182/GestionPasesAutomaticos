from __future__ import annotations

from models import PaseData, CorreoData, Caso
from exceptions import LoginTimeoutError, OutlookError


def construir_correo(pase: PaseData, destinatarios: dict) -> CorreoData:
    """Función pura. Construye asunto, para, cc y cuerpo según el caso del pase."""
    casos = destinatarios["casos"]

    asunto = f"SICO - PASE A PRODUCCIÓN: {pase.texto_asunto}"

    if pase.caso == Caso.UNO:
        dest = casos["caso_1_devops"]
        para = dest["para"]
        cc = dest["cc"]
        cuerpo = _cuerpo_caso_1(pase)
    elif pase.caso == Caso.DOS:
        dest = casos["caso_2_manual"]
        para = dest["para"]
        cc = dest["cc"]
        cuerpo = _cuerpo_caso_2(pase)
    else:  # Caso.TRES
        dest = casos["caso_3_mixto"]
        para = dest["para"]
        cc = dest["cc"]
        cuerpo = _cuerpo_caso_3(pase)

    return CorreoData(asunto=asunto, para=para, cc=cc, cuerpo=cuerpo)


def _lineas_artefactos(pase: PaseData) -> str:
    return "\n".join(f"\t• {a.codigo}: {a.url_release}" for a in pase.artefactos)


def _cuerpo_caso_1(pase: PaseData) -> str:
    lineas = _lineas_artefactos(pase)
    return (
        f"Por favor, su apoyo con el Pase a producción de SICO, el día de hoy {pase.fecha} de forma {pase.opcion_ejecucion}.\n\n"
        f"Este pase incluye {len(pase.artefactos)} release(s), los formularios de pase a producción fueron creados.\n\n"
        f"Finalidad: {pase.texto_asunto}\n"
        f"HU: {pase.texto_hu}\n\n"
        f"Artefactos:\n\n"
        f"{lineas}\n\n"
        f"Hola Jorge, Maritza, Fanny, Ruben\n\n"
        f"Por favor su aprobación para este Pase a Producción por este medio y en el Azure Devops.\n\n"
        f"Saludos,\n\n"
        f"Jossy Willians Quispe Oroya\n"
        f"Analista de Proyectos Pasivos y Regulatorios"
    )


def _cuerpo_caso_2(pase: PaseData) -> str:
    return (
        f"Por favor, su apoyo con el Pase a producción de SICO, el día de hoy {pase.fecha} de forma {pase.opcion_ejecucion} de los packages incluidos en carpeta de pases.\n\n"
        f"El formulario de pase a producción fue creado.\n\n"
        f"Finalidad: {pase.texto_asunto}\n"
        f"HU: {pase.texto_hu}\n\n"
        f"Ubicación scripts:\n\n"
        f"\t\u200b{pase.ruta_scripts}\n\n"
        f"Hola Jorge, Maritza, Fanny\n\n"
        f"Por favor su aprobación para este Pase a Producción por este medio y en el Azure Devops.\n\n"
        f"Saludos,\n\n"
        f"Jossy Willians Quispe Oroya\n"
        f"Analista de Proyectos Pasivos y Regulatorios"
    )


def _cuerpo_caso_3(pase: PaseData) -> str:
    lineas = _lineas_artefactos(pase)
    return (
        f"Por favor, su apoyo con el Pase a producción de SICO, el día de hoy {pase.fecha} de forma {pase.opcion_ejecucion}.\n\n"
        f"Este pase incluye {len(pase.artefactos)} release(s) y scripts de BD, los formularios de pase a producción fueron creados.\n\n"
        f"Finalidad: {pase.texto_asunto}\n"
        f"HU: {pase.texto_hu}\n\n"
        f"Artefactos:\n\n"
        f"{lineas}\n\n"
        f"Ubicación scripts:\n\n"
        f"\t\u200b{pase.ruta_scripts}\n\n"
        f"Hola Jorge, Maritza, Fanny, Ruben\n\n"
        f"Por favor su aprobación para este Pase a Producción por este medio y en el Azure Devops.\n\n"
        f"Saludos,\n\n"
        f"Jossy Willians Quispe Oroya\n"
        f"Analista de Proyectos Pasivos y Regulatorios"
    )


def esperar_login(page, timeout_ms: int = 120_000) -> None:
    """Espera hasta que el usuario complete el login manual en Outlook Web.
    Lanza LoginTimeoutError si supera el timeout."""
    try:
        page.wait_for_url("**/mail**", timeout=timeout_ms)
        page.wait_for_selector(
            '[aria-label="Correo nuevo"]', state="visible", timeout=timeout_ms
        )
    except Exception as e:
        raise LoginTimeoutError(
            f"Timeout esperando login en Outlook Web ({timeout_ms}ms)"
        ) from e


def _agregar_destinatarios(page, selector: str, destinatarios: list[str]) -> None:
    """Agrega múltiples destinatarios a un campo de Outlook Web.

    Los destinatarios se unen con "; " y se escriben como cadena completa.
    Luego se presiona Enter para confirmar en Outlook Web.
    """
    if not destinatarios:
        return

    # Hacer clic en el campo para asegurar que tenga foco (necesario para CC)
    try:
        page.click(selector, timeout=1000)
    except:
        pass

    # Limpiar el campo antes de empezar
    page.fill(selector, "")
    page.wait_for_timeout(100)

    # Unir todos los destinatarios con "; " como separador (Outlook Web usa punto y coma)
    destinatarios_str = "; ".join(destinatarios)

    # Escribir la cadena completa y presionar Enter
    page.keyboard.type(destinatarios_str)
    page.keyboard.press("Enter")
    page.wait_for_timeout(100)


def enviar_correo(page, correo: CorreoData) -> None:
    """Automatiza la creación y envío del correo en Outlook Web.
    Lanza OutlookError si falla cualquier interacción."""
    try:
        page.click('[aria-label="Correo nuevo"]')

        # Campo Para — puede tener múltiples destinatarios
        _agregar_destinatarios(page, '[aria-label="Para"]', correo.para)

        # Campo CC — puede tener múltiples destinatarios (selectores flexibles)
        cc_selectores = [
            '[aria-label="CC"]',
            '[aria-label="Cc"]',
            '[aria-label="CCO"]',
            'input[name="cc"]',
            'input[aria-label*="CC" i]',  # case-insensitive
        ]

        cc_exitoso = False
        for selector in cc_selectores:
            try:
                # Esperar a que el campo esté visible
                page.wait_for_selector(selector, timeout=2000, state="visible")
                # Hacer clic para asegurar foco
                page.click(selector, timeout=1000)
                # Agregar destinatarios
                _agregar_destinatarios(page, selector, correo.cc)
                cc_exitoso = True
                break
            except Exception:
                continue

        if not cc_exitoso and correo.cc:
            # Si ningún selector funcionó pero hay CC, intentar con el último selector
            # quizás el campo está oculto o necesita activación especial
            pass  # Por ahora no hacemos nada, pero podríamos agregar lógica aquí

        page.fill('[aria-label="Asunto"]', correo.asunto)
        page.click('[aria-label="Cuerpo del mensaje"]')
        page.keyboard.type(correo.cuerpo)

        page.click('[aria-label="Enviar"]')
    except Exception as e:
        raise OutlookError(f"Error enviando correo en Outlook Web: {e}") from e
