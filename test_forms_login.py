# -*- coding: utf-8 -*-
"""Script de diagnostico: prueba el flujo completo de completar_campos_base (inputs 1-9)."""
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

from playwright.sync_api import sync_playwright

FORMS_URL = "https://forms.office.com/Pages/ResponsePage.aspx?id=eQz1rjw3-UeC7n-CSipNUZcRcu5aCiJBgzQxPKcgO7xUQkJSR1lNUVlUNDJYNkpUVUhRSjVBOEJTMyQlQCN0PWcu"
USER_DATA_DIR = os.path.join(os.path.expanduser("~"), ".automatizacion_pases_profile")

with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context(USER_DATA_DIR, headless=False)
    page = ctx.new_page()
    page.goto(FORMS_URL)

    print("Esperando formulario...")
    page.wait_for_selector('input#DatePicker0-label', state="visible", timeout=30_000)
    print("OK cargado")
    page.wait_for_timeout(500)

    print("\n[1] Fecha")
    try:
        page.fill('input#DatePicker0-label', '20/3/2026')
        print("  OK")
    except Exception as e:
        print(f"  FAIL: {e}")

    print("\n[2] Ejecucion = Inmediata")
    try:
        page.click('input[name="rf62c7c231241404fb3c72296c6e372b1"][value="Inmediata"]')
        print("  OK")
    except Exception as e:
        print(f"  FAIL: {e}")

    print("\n[3] HU")
    try:
        page.fill('input[aria-labelledby*="QuestionId_re8a9340464d1401897c22d9dc3a9399f"]', 'HU-TEST-123')
        print("  OK")
    except Exception as e:
        print(f"  FAIL: {e}")

    print("\n[4] Agora = No")
    try:
        page.click('input[name="r04057fb07c984f109a1c2a6d67114e5e"][value="No"]')
        print("  OK")
    except Exception as e:
        print(f"  FAIL: {e}")

    print("\n[5] Endpoint")
    try:
        page.fill('input[aria-labelledby*="QuestionId_reb7dee5f8d714426afe0d2de2c50e43c"]', 'cosicocomunicaciones')
        print("  OK")
    except Exception as e:
        print(f"  FAIL: {e}")

    print("\n[6] Responsable")
    try:
        page.click('div[aria-labelledby^="QuestionId_r5739e22cfbc641829dde6e4cc23f83bb"]')
        page.wait_for_selector('[role="listbox"]', state="visible", timeout=5000)
        page.click('[role="option"]:has-text("Marco Mosqueira")')
        print("  OK")
    except Exception as e:
        print(f"  FAIL: {e}")

    print("\n[7] Donde cambio = Aplicacion/BD")
    try:
        page.click('input[name="r112deb4a9605429e824664e088c3ad1e"][value="Aplicaci\u00f3n/BD"]')
        page.wait_for_selector('input[name="r0409ad20e573453fbe6834322be198a1"][value="SICO"]', state="visible", timeout=5000)
        page.wait_for_selector('div[aria-labelledby^="QuestionId_r1fd586e16e944bf4924ce92e32790e87"]', state="visible", timeout=5000)
        print("  OK (inputs 8 y 9 visibles)")
    except Exception as e:
        print(f"  FAIL: {e}")

    print("\n[8] Sistema = SICO")
    try:
        page.click('input[name="r0409ad20e573453fbe6834322be198a1"][value="SICO"]')
        print("  OK")
    except Exception as e:
        print(f"  FAIL: {e}")

    print("\n[9] Metodo pase = DevOps")
    try:
        page.click('div[aria-labelledby^="QuestionId_r1fd586e16e944bf4924ce92e32790e87"]')
        page.wait_for_selector('[role="listbox"]', state="visible", timeout=5000)
        page.click('[role="option"]:has-text("DevOps")')
        print("  OK")
    except Exception as e:
        print(f"  FAIL: {e}")

    print("\n=== RESULTADO: todos los inputs 1-9 probados ===")
    page.wait_for_timeout(1000)
    ctx.close()
