import json
import os

from exceptions import ConfigError


def cargar_artefactos(ruta: str = "config/artefactos.json") -> dict[str, dict]:
    """Lee artefactos.json y retorna índice {codigo: {repo, nombre, descripcion}}.
    Lanza ConfigError si el archivo no existe o el JSON es inválido."""
    if not os.path.exists(ruta):
        raise ConfigError(f"Archivo no encontrado: {ruta}")
    try:
        with open(ruta, encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise ConfigError(f"JSON inválido en {ruta}: {e}") from e

    return {item["codigo"]: {"repo": item["repo"], "nombre": item["nombre"], "descripcion": item["descripcion"]}
            for item in data["artefactos"]}


def cargar_destinatarios(ruta: str = "config/destinatarios.json") -> dict:
    """Lee destinatarios.json y retorna el dict de casos.
    Lanza ConfigError si el archivo no existe o el JSON es inválido."""
    if not os.path.exists(ruta):
        raise ConfigError(f"Archivo no encontrado: {ruta}")
    try:
        with open(ruta, encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise ConfigError(f"JSON inválido en {ruta}: {e}") from e
