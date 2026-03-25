"""Datos iniciales para nuevas instalaciones.

Este módulo contiene los datos semilla que se cargan cuando
la base de datos está vacía (primera instalación).

Editá SEED_ARTEFACTOS y SEED_DESTINATARIOS para agregar
datos iniciales que se distribuirán con cada release.
"""

from __future__ import annotations

import sqlite3


# ============================================
# DATOS INICIALES - Editar aquí para agregar
# nuevos artefactos o destinatarios
# ============================================

SEED_ARTEFACTOS = [
    ("cotest", "msc-test", "CORE - Test", "Microservicio core test"),
    ("bstest", "msn-test", "BS - Test", "Microservicio business test"),
    ("webtest", "web-test", "APP - Test", "Aplicación web test")
]

SEED_DESTINATARIOS = [
    ("artefactos", "Caso 1 - Microservicios/Web", "Despliegue de artefactos", "test@test.com", ""),
    ("scripts", "Caso 2 - Base de Datos", "Despliegue de scripts", "test@test.com", ""),
    ("mixto", "Caso 3 - Microservicios/Web + BD", "Despliegue de artefactos y scripts", "test@test.com", "")

]


def seed_database(cursor: sqlite3.Cursor) -> int:
    """Carga datos iniciales si la base de datos está vacía.

    Args:
        cursor: Cursor de SQLite activo.

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
