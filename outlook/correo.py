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
    return "\n".join(
        f"{a.codigo}: {a.url_release}" for a in pase.artefactos
    )


def _cuerpo_caso_1(pase: PaseData) -> str:
    lineas = _lineas_artefactos(pase)
    return (
        f"Por favor, su apoyo con el Pase a producción de SICO, el día de hoy {pase.fecha} de forma {pase.opcion_ejecucion}.\n"
        f"Este pase incluye {len(pase.artefactos)} release(s), los formularios de pase a producción fueron creados.\n"
        f"El pase tiene como finalidad: {pase.texto_asunto}\n"
        f"HU: {pase.texto_hu}\n"
        f"{lineas}\n"
        f"Hola Jorge, Maritza, Fanny, Ruben\n"
        f"Por favor su aprobación para este Pase a Producción por este medio y en el Azure Devops.\n"
        f"Saludos\n"
        f"Jossy Willians Quispe Oroya\n"
        f"Analista de Proyectos Pasivos y Regulatorios"
    )


def _cuerpo_caso_2(pase: PaseData) -> str:
    return (
        f"Por favor, su apoyo con el Pase a producción de SICO, el día de hoy {pase.fecha} de forma {pase.opcion_ejecucion} de los packages incluidos en carpeta de pases.\n"
        f"El formulario de pase a producción fue creado.\n"
        f"El pase tiene como finalidad: {pase.texto_asunto}\n"
        f"HU: {pase.texto_hu}\n"
        f"Se ha generado el formulario y subido el archivo en la siguiente carpeta:\n"
        f"{pase.ruta_scripts}\n"
        f"Hola Jorge, Maritza, Fanny\n"
        f"Por favor su aprobación para este Pase a Producción por este medio y en el Azure Devops.\n"
        f"Saludos\n"
        f"Jossy Willians Quispe Oroya\n"
        f"Analista de Proyectos Pasivos y Regulatorios"
    )


def _cuerpo_caso_3(pase: PaseData) -> str:
    lineas = _lineas_artefactos(pase)
    return (
        f"Por favor, su apoyo con el Pase a producción de SICO, el día de hoy {pase.fecha} de forma {pase.opcion_ejecucion}.\n"
        f"Este pase incluye {len(pase.artefactos)} release(s) y scripts de BD, los formularios de pase a producción fueron creados.\n"
        f"El pase tiene como finalidad: {pase.texto_asunto}\n"
        f"HU: {pase.texto_hu}\n"
        f"{lineas}\n"
        f"Se ha generado el formulario y subido el archivo en la siguiente carpeta:\n"
        f"{pase.ruta_scripts}\n"
        f"Hola Jorge, Maritza, Fanny, Ruben\n"
        f"Por favor su aprobación para este Pase a Producción por este medio y en el Azure Devops.\n"
        f"Saludos\n"
        f"Jossy Willians Quispe Oroya\n"
        f"Analista de Proyectos Pasivos y Regulatorios"
    )


def esperar_login(page, timeout_ms: int = 120_000) -> None:
    """Espera hasta que el usuario complete el login manual en Outlook Web.
    Lanza LoginTimeoutError si supera el timeout."""
    try:
        page.wait_for_url("**/mail**", timeout=timeout_ms)
        page.wait_for_selector('[aria-label="Correo nuevo"]', state="visible", timeout=timeout_ms)
    except Exception as e:
        raise LoginTimeoutError(
            f"Timeout esperando login en Outlook Web ({timeout_ms}ms)"
        ) from e


def enviar_correo(page, correo: CorreoData) -> None:
    """Automatiza la creación y envío del correo en Outlook Web.
    Lanza OutlookError si falla cualquier interacción."""
    try:
        page.click('[aria-label="Correo nuevo"]')

        # Campo Para — un destinatario por Enter
        for destinatario in correo.para:
            page.fill('[aria-label="Para"]', destinatario)
            page.keyboard.press("Enter")

        # Campo CC — puede haber múltiples destinatarios
        for destinatario in correo.cc:
            page.fill('[aria-label="CC"]', destinatario)
            page.keyboard.press("Enter")

        page.fill('[aria-label="Asunto"]', correo.asunto)
        page.click('[aria-label="Cuerpo del mensaje"]')
        page.keyboard.type(correo.cuerpo)

        page.click('[aria-label="Enviar"]')
    except Exception as e:
        raise OutlookError(f"Error enviando correo en Outlook Web: {e}") from e
