"""Datos iniciales para nuevas instalaciones.

Este módulo contiene los datos semilla que se cargan cuando
la base de datos está vacía (primera instalación).
"""

from __future__ import annotations

import sqlite3


# ============================================
# DATOS INICIALES - Editar aquí para agregar
# nuevos artefactos o destinatarios
# ============================================

SEED_ARTEFACTOS = [
    # (codigo, repo, nombre, descripcion)
    # Ejemplo:
    # ("SICO-BE", "org/repo-backend", "SICO Backend", "API principal"),
    # ("SICO-FE", "org/repo-frontend", "SICO Frontend", "Interfaz web"),
]

SEED_DESTINATARIOS = [
    # (caso_id, nombre, descripcion, para, cc)
    # Ejemplo:
    # ("UNO", "DevOps Team", "Solo artefactos", "devops@empresa.com", "gerente@empresa.com"),
    # ("DOS", "DBA Team", "Solo scripts BD", "dba@empresa.com", ""),
    # ("TRES", "Completo", "Artefactos + BD", "devops@empresa.com,dba@empresa.com", ""),
]


def seed_database(cursor: sqlite3.Cursor) -> int:
    """Carga datos iniciales si la base de datos está vacía.

    Returns:
        Número de registros insertados.
    """
    inserted = 0

    # Verificar si hay artefactos
    cursor.execute("SELECT COUNT(*) as count FROM artefactos")
    has_artefactos = cursor.fetchone()["count"] > 0

    # Verificar si hay destinatarios
    cursor.execute("SELECT COUNT(*) as count FROM destinatarios")
    has_destinatarios = cursor.fetchone()["count"] > 0

    # Cargar artefactos si no hay ninguno
    if not has_artefactos and SEED_ARTEFACTOS:
        for codigo, repo, nombre, descripcion in SEED_ARTEFACTOS:
            cursor.execute(
                "INSERT OR IGNORE INTO artefactos (codigo, repo, nombre, descripcion) VALUES (?, ?, ?, ?)",
                (codigo, repo, nombre, descripcion),
            )
            inserted += 1

    # Cargar destinatarios si no hay ninguno
    if not has_destinatarios and SEED_DESTINATARIOS:
        for caso_id, nombre, descripcion, para, cc in SEED_DESTINATARIOS:
            cursor.execute(
                "INSERT OR IGNORE INTO destinatarios (caso_id, nombre, descripcion, para, cc) VALUES (?, ?, ?, ?, ?)",
                (caso_id, nombre, descripcion, para, cc),
            )
            inserted += 1

    return inserted
