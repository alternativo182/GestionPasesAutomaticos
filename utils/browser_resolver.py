"""Módulo para resolver la ruta del browser Chromium de Playwright.

Busca el browser en la instalación de Playwright:
- %LOCALAPPDATA%\ms-playwright\ (Windows)
- ~/.cache/ms-playwright/ (Linux/Mac)
"""

from __future__ import annotations

import os
from pathlib import Path


def get_browser_path() -> Path | None:
    """Obtiene la ruta al ejecutable de Chrome.

    Busca en la instalación de Playwright:
    - %LOCALAPPDATA%\ms-playwright\ (Windows)
    - ~/.cache/ms-playwright/ (Linux/Mac)

    Returns:
        Path a chrome.exe, o None si no se encuentra.
    """
    # Rutas de instalación de Playwright
    playwright_paths = [
        Path(os.environ.get("LOCALAPPDATA", "")) / "ms-playwright",
        Path.home() / ".cache" / "ms-playwright",
    ]

    for base_path in playwright_paths:
        if not base_path.exists():
            continue

        # Buscar cualquier carpeta chromium-*
        for item in base_path.iterdir():
            if item.is_dir() and item.name.startswith("chromium"):
                chrome_path = item / "chrome-win64"
                if chrome_path.exists() and (chrome_path / "chrome.exe").exists():
                    return chrome_path / "chrome.exe"

                # También buscar chrome-win (versión vieja)
                chrome_path = item / "chrome-win"
                if chrome_path.exists() and (chrome_path / "chrome.exe").exists():
                    return chrome_path / "chrome.exe"

    return None


def is_browser_installed() -> bool:
    """Verifica si el browser está instalado."""
    return get_browser_path() is not None


def get_cache_info() -> dict:
    """Retorna información sobre el estado del browser."""
    chrome_path = get_browser_path()
    browser_dir = chrome_path.parent if chrome_path else None

    info = {
        "browser_found": chrome_path is not None,
        "browser_path": str(chrome_path) if chrome_path else None,
    }

    if browser_dir and browser_dir.exists():
        try:
            total_size = sum(
                f.stat().st_size for f in browser_dir.rglob("*") if f.is_file()
            )
            info["size_mb"] = round(total_size / (1024 * 1024), 1)
        except OSError:
            info["size_mb"] = None
    else:
        info["size_mb"] = None

    return info
