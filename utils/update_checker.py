"""Módulo para verificar actualizaciones desde GitHub Releases."""

from __future__ import annotations

import re
import urllib.request
import json
from dataclasses import dataclass

# Versión actual de la aplicación
__version__ = "1.2.5"

# Repo de GitHub
GITHUB_REPO = "alternativo182/GestionPasesAutomaticos"
RELEASES_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
INSTALL_CMD = "irm https://raw.githubusercontent.com/alternativo182/GestionPasesAutomaticos/main/install.ps1 | iex"


@dataclass
class UpdateInfo:
    """Información sobre una actualización disponible."""

    current_version: str
    latest_version: str
    download_url: str
    release_url: str
    release_notes: str

    @property
    def is_update_available(self) -> bool:
        """Compara versiones semver simple."""
        return self._parse_version(self.latest_version) > self._parse_version(
            self.current_version
        )

    @staticmethod
    def _parse_version(version: str) -> tuple[int, ...]:
        """Parsea una versión semver simple a tuple para comparación."""
        # Quitar 'v' del inicio si existe
        version = version.lstrip("v")
        # Extraer solo números
        parts = re.findall(r"\d+", version)
        return tuple(int(p) for p in parts) if parts else (0,)


def check_for_updates(timeout: float = 5.0) -> UpdateInfo | None:
    """Consulta GitHub si hay una nueva versión disponible.

    Args:
        timeout: Tiempo máximo de espera en segundos.

    Returns:
        UpdateInfo si hay información disponible, None si falla.
    """
    try:
        req = urllib.request.Request(
            RELEASES_URL,
            headers={
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "GestionPases",
            },
        )
        with urllib.request.urlopen(req, timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8"))

        latest_version = data.get("tag_name", "unknown")
        download_url = ""
        for asset in data.get("assets", []):
            if "GestionPases.zip" in asset.get("name", ""):
                download_url = asset.get("browser_download_url", "")
                break

        return UpdateInfo(
            current_version=__version__,
            latest_version=latest_version,
            download_url=download_url,
            release_url=data.get("html_url", ""),
            release_notes=data.get("body", "Sin notas de versión"),
        )
    except Exception:
        # Silenciar errores - la app debe funcionar sin conexión
        return None


def get_update_message(info: UpdateInfo) -> str:
    """Retorna un mensaje formateado para mostrar al usuario."""
    return (
        f"📦 Nueva versión disponible: {info.latest_version}\n"
        f"   Tu versión: {info.current_version}\n\n"
        f"📝 Cambios:\n"
        f"{info.release_notes[:200]}...\n\n"
        f"Para actualizar, ejecutá:\n"
        f"  {INSTALL_CMD}"
    )
