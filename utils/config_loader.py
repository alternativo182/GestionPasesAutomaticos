"""Módulo de carga de configuración usando SQLite."""

import os
import sqlite3
import sys
import shutil
from pathlib import Path

from exceptions import ConfigError


def _get_base_dir() -> Path:
    """Obtiene el directorio base del proyecto.

    Si está ejecutando como exe empaquetado (PyInstaller),
    busca la base en el directorio del ejecutable.
    """
    if getattr(sys, "frozen", False):
        # Ejecutando como exe empaquetado por PyInstaller
        return Path(sys.executable).parent
    else:
        # Ejecutando como script Python normal
        return Path(__file__).parent.parent


def _get_data_dir() -> Path:
    """Obtiene el directorio de datos persistente del usuario.

    Los datos se guardan en %LOCALAPPDATA%\GestionPases\data\
    para persistir entre actualizaciones del programa.
    """
    if getattr(sys, "frozen", False):
        # En modo exe: usar carpeta de datos persistente
        return Path(os.environ.get("LOCALAPPDATA", "")) / "GestionPases" / "data"
    else:
        # En modo desarrollo: usar config/ local
        return _get_base_dir() / "config"


def _migrate_db_if_needed(data_dir: Path, base_dir: Path) -> None:
    """Migra la base de datos desde la ubicación vieja si existe.

    Antes, la DB estaba en {base_dir}/config/config.db
    Ahora, la DB está en {data_dir}/config.db

    Si la DB vieja existe y la nueva no, la migra.
    """
    old_db = base_dir / "config" / "config.db"
    new_db = data_dir / "config.db"

    # Si la nueva ya existe, no hacer nada
    if new_db.exists():
        return

    # Si la vieja existe y la nueva no, migrar
    if old_db.exists():
        data_dir.mkdir(parents=True, exist_ok=True)
        try:
            shutil.copy2(old_db, new_db)
            print(f"[INFO] Base de datos migrada a: {new_db}")
        except Exception as e:
            print(f"[WARN] No se pudo migrar la DB: {e}")


# Directorio base del programa (donde está el exe)
BASE_DIR = _get_base_dir()

# Directorio de datos persistente del usuario
DATA_DIR = _get_data_dir()

# Migrar DB si es necesario (antes de cualquier otra cosa)
_migrate_db_if_needed(DATA_DIR, BASE_DIR)

# Ruta de la base de datos (en carpeta de datos persistente)
DB_PATH = DATA_DIR / "config.db"


def _get_connection() -> sqlite3.Connection:
    """Obtiene una conexión a la base de datos."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def inicializar_db() -> None:
    """Inicializa la base de datos con las tablas necesarias."""
    conn = _get_connection()
    try:
        cursor = conn.cursor()

        # Tabla de artefactos - ahora con ID auto increment
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS artefactos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo TEXT NOT NULL,
                repo TEXT NOT NULL,
                nombre TEXT NOT NULL,
                descripcion TEXT DEFAULT '',
                UNIQUE(codigo)
            )
        """)

        # Tabla de destinatarios - ahora con ID auto increment
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS destinatarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                caso_id TEXT NOT NULL,
                nombre TEXT NOT NULL,
                descripcion TEXT DEFAULT '',
                para TEXT NOT NULL,
                cc TEXT DEFAULT '',
                UNIQUE(caso_id)
            )
        """)

        # Si no hay datos, cargar desde seed data o JSON legacy
        cursor.execute("SELECT COUNT(*) as count FROM artefactos")
        if cursor.fetchone()["count"] == 0:
            # Primero intentar con seed data (datos incluidos en el código)
            from utils.seed_data import seed_database

            inserted = seed_database(cursor)

            # Si no hay seed data, intentar con JSON legacy (compatibilidad)
            if inserted == 0:
                _cargar_desde_json_legacy(cursor)

        conn.commit()
    finally:
        conn.close()


def _cargar_desde_json_legacy(cursor: sqlite3.Cursor) -> None:
    """Carga datos iniciales desde los archivos JSON legacy."""
    import json

    # Cargar artefactos
    json_path = BASE_DIR / "config" / "artefactos.json"
    if json_path.exists():
        try:
            with open(json_path, encoding="utf-8") as f:
                data = json.load(f)
            for item in data.get("artefactos", []):
                cursor.execute(
                    "INSERT OR IGNORE INTO artefactos (codigo, repo, nombre, descripcion) VALUES (?, ?, ?, ?)",
                    (
                        item["codigo"],
                        item["repo"],
                        item["nombre"],
                        item.get("descripcion", ""),
                    ),
                )
        except Exception:
            pass

    # Cargar destinatarios
    json_path = BASE_DIR / "config" / "destinatarios.json"
    if json_path.exists():
        try:
            with open(json_path, encoding="utf-8") as f:
                data = json.load(f)
            for caso_id, item in data.get("casos", {}).items():
                cursor.execute(
                    "INSERT OR IGNORE INTO destinatarios (caso_id, nombre, descripcion, para, cc) VALUES (?, ?, ?, ?, ?)",
                    (
                        caso_id,
                        item.get("nombre", ""),
                        item.get("descripcion", ""),
                        ",".join(item.get("para", [])),
                        ",".join(item.get("cc", [])),
                    ),
                )
        except Exception:
            pass


def cargar_artefactos() -> dict[str, dict]:
    """Carga todos los artefactos de la base de datos.

    Returns:
        Dict {codigo: {id, repo, nombre, descripcion}}
    Raises:
        ConfigError si hay error de base de datos
    """
    try:
        conn = _get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, codigo, repo, nombre, descripcion FROM artefactos ORDER BY codigo"
            )
            rows = cursor.fetchall()
            return {
                row["codigo"]: {
                    "id": row["id"],
                    "repo": row["repo"],
                    "nombre": row["nombre"],
                    "descripcion": row["descripcion"] or "",
                }
                for row in rows
            }
        finally:
            conn.close()
    except sqlite3.Error as e:
        raise ConfigError(f"Error al cargar artefactos: {e}") from e


def cargar_destinatarios() -> dict:
    """Carga todos los destinatarios de la base de datos.

    Returns:
        Dict con estructura {'casos': {caso_id: {id, nombre, descripcion, para: [], cc: []}}}
    Raises:
        ConfigError si hay error de base de datos
    """
    try:
        conn = _get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, caso_id, nombre, descripcion, para, cc FROM destinatarios ORDER BY caso_id"
            )
            rows = cursor.fetchall()

            casos = {}
            for row in rows:
                casos[row["caso_id"]] = {
                    "id": row["id"],
                    "nombre": row["nombre"] or "",
                    "descripcion": row["descripcion"] or "",
                    "para": row["para"].split(",") if row["para"] else [],
                    "cc": row["cc"].split(",") if row["cc"] else [],
                }

            return {"casos": casos}
        finally:
            conn.close()
    except sqlite3.Error as e:
        raise ConfigError(f"Error al cargar destinatarios: {e}") from e


def guardar_artefacto(
    id: int | None, codigo: str, repo: str, nombre: str, descripcion: str = ""
) -> bool:
    """Guarda o actualiza un artefacto.

    Args:
        id: ID interno (None para nuevo registro)
        codigo: Código único del artefacto
        repo: Nombre del repositorio
        nombre: Nombre descriptivo
        descripcion: Descripción (opcional)
    Returns:
        True si fue exitoso
    Raises:
        ConfigError si hay error de base de datos
    """
    try:
        conn = _get_connection()
        try:
            cursor = conn.cursor()
            if id is None:
                # Nuevo registro
                cursor.execute(
                    "INSERT INTO artefactos (codigo, repo, nombre, descripcion) VALUES (?, ?, ?, ?)",
                    (codigo, repo, nombre, descripcion or ""),
                )
            else:
                # Actualizar por ID
                cursor.execute(
                    "UPDATE artefactos SET codigo = ?, repo = ?, nombre = ?, descripcion = ? WHERE id = ?",
                    (codigo, repo, nombre, descripcion or "", id),
                )
            conn.commit()
            return True
        finally:
            conn.close()
    except sqlite3.Error as e:
        raise ConfigError(f"Error al guardar artefacto: {e}") from e


def eliminar_artefacto(id: int) -> bool:
    """Elimina un artefacto.

    Args:
        id: ID interno del artefacto a eliminar
    Returns:
        True si fue exitoso
    Raises:
        ConfigError si hay error de base de datos
    """
    try:
        conn = _get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM artefactos WHERE id = ?", (id,))
            conn.commit()
            return True
        finally:
            conn.close()
    except sqlite3.Error as e:
        raise ConfigError(f"Error al eliminar artefacto: {e}") from e


def guardar_caso(
    id: int | None,
    caso_id: str,
    nombre: str,
    descripcion: str,
    para: list,
    cc: list = None,
) -> bool:
    """Guarda o actualiza un caso de destinatarios.

    Args:
        id: ID interno (None para nuevo registro)
        caso_id: ID único del caso
        nombre: Nombre del caso
        descripcion: Descripción (opcional)
        para: Lista de destinatarios principales
        cc: Lista de destinatarios en copia
    Returns:
        True si fue exitoso
    Raises:
        ConfigError si hay error de base de datos
    """
    if cc is None:
        cc = []

    try:
        conn = _get_connection()
        try:
            cursor = conn.cursor()
            if id is None:
                # Nuevo registro
                cursor.execute(
                    "INSERT INTO destinatarios (caso_id, nombre, descripcion, para, cc) VALUES (?, ?, ?, ?, ?)",
                    (caso_id, nombre, descripcion or "", ",".join(para), ",".join(cc)),
                )
            else:
                # Actualizar por ID
                cursor.execute(
                    "UPDATE destinatarios SET caso_id = ?, nombre = ?, descripcion = ?, para = ?, cc = ? WHERE id = ?",
                    (
                        caso_id,
                        nombre,
                        descripcion or "",
                        ",".join(para),
                        ",".join(cc),
                        id,
                    ),
                )
            conn.commit()
            return True
        finally:
            conn.close()
    except sqlite3.Error as e:
        raise ConfigError(f"Error al guardar caso: {e}") from e


def eliminar_caso(id: int) -> bool:
    """Elimina un caso de destinatarios.

    Args:
        id: ID interno del caso a eliminar
    Returns:
        True si fue exitoso
    Raises:
        ConfigError si hay error de base de datos
    """
    try:
        conn = _get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM destinatarios WHERE id = ?", (id,))
            conn.commit()
            return True
        finally:
            conn.close()
    except sqlite3.Error as e:
        raise ConfigError(f"Error al eliminar caso: {e}") from e
