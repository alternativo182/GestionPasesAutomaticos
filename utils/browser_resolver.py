"""Módulo para resolver la ruta del browser Chromium de Playwright.

Busca el browser en orden de prioridad:
1. Cache local de GestionPases (%LOCALAPPDATA%\GestionPases\cache\)
2. Instalación global de Playwright
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


# Ruta de cache local
CACHE_BASE = Path(os.environ.get("LOCALAPPDATA", "")) / "GestionPases" / "cache"
PLAYWRIGHT_CACHE = CACHE_BASE / "ms-playwright"

# Nombres de carpetas de Chromium conocidos
CHROMIUM_FOLDERS = [
    "chromium-1208",
    "chromium-1155",
    "chromium-1161",
    "chromium-1169",
]


def get_local_cache_path() -> Path:
    """Retorna la ruta base del cache local."""
    return CACHE_BASE


def find_chromium_in_cache() -> Path | None:
    """Busca Chromium en el cache local de GestionPases.

    Returns:
        Path al directorio de Chrome, o None si no se encuentra.
    """
    if not PLAYWRIGHT_CACHE.exists():
        return None

    # Buscar por versiones conocidas (más reciente primero)
    for folder in CHROMIUM_FOLDERS:
        chrome_path = PLAYWRIGHT_CACHE / folder / "chrome-win64"
        if chrome_path.exists() and (chrome_path / "chrome.exe").exists():
            return chrome_path

    # Si no encuentra por nombre conocido, buscar cualquier chromium-*
    for item in PLAYWRIGHT_CACHE.iterdir():
        if item.is_dir() and item.name.startswith("chromium-"):
            chrome_path = item / "chrome-win64"
            if chrome_path.exists() and (chrome_path / "chrome.exe").exists():
                return chrome_path

    return None


def find_chromium_global() -> Path | None:
    """Busca Chromium en la instalación global de Playwright.

    Returns:
        Path al directorio de Chrome, o None si no se encuentra.
    """
    # Instalación global típica de Playwright
    global_paths = [
        Path(os.environ.get("LOCALAPPDATA", "")) / "ms-playwright",
        Path.home() / ".cache" / "ms-playwright",
    ]

    for global_base in global_paths:
        if not global_base.exists():
            continue

        for folder in CHROMIUM_FOLDERS:
            chrome_path = global_base / folder / "chrome-win64"
            if chrome_path.exists() and (chrome_path / "chrome.exe").exists():
                return chrome_path

        # Buscar cualquier chromium-*
        for item in global_base.iterdir():
            if item.is_dir() and item.name.startswith("chromium-"):
                chrome_path = item / "chrome-win64"
                if chrome_path.exists() and (chrome_path / "chrome.exe").exists():
                    return chrome_path

    return None


def get_browser_path() -> Path | None:
    """Obtiene la ruta al ejecutable de Chrome.

    Busca en orden de prioridad:
    1. Cache local de GestionPases (recomendado)
    2. Instalación global de Playwright

    Returns:
        Path a chrome.exe, o None si no se encuentra.
    """
    # 1. Buscar en cache local
    local_path = find_chromium_in_cache()
    if local_path:
        return local_path / "chrome.exe"

    # 2. Buscar en instalación global
    global_path = find_chromium_global()
    if global_path:
        return global_path / "chrome.exe"

    return None


def is_browser_installed() -> bool:
    """Verifica si el browser está instalado en alguna ubicación."""
    return get_browser_path() is not None


def get_cache_info() -> dict:
    """Retorna información sobre el estado del cache."""
    chrome_path = find_chromium_in_cache()
    cache_exists = PLAYWRIGHT_CACHE.exists()

    info = {
        "cache_dir": str(PLAYWRIGHT_CACHE),
        "cache_exists": cache_exists,
        "browser_found": chrome_path is not None,
        "browser_path": str(chrome_path) if chrome_path else None,
    }

    if chrome_path:
        # Calcular tamaño aproximado
        try:
            total_size = sum(
                f.stat().st_size for f in chrome_path.rglob("*") if f.is_file()
            )
            info["size_mb"] = round(total_size / (1024 * 1024), 1)
        except OSError:
            info["size_mb"] = None

    return info
