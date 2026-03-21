from dataclasses import dataclass, field
from enum import Enum


class Caso(Enum):
    UNO = 1    # Solo artefactos
    DOS = 2    # Solo scripts BD
    TRES = 3   # Artefactos + scripts BD


@dataclass
class ArtefactoInput:
    codigo: str
    url_release: str


@dataclass
class PaseData:
    texto_asunto: str
    texto_hu: str
    fecha: str                          # formato d/M/yyyy
    opcion_ejecucion: str               # "Inmediata" | "Programada"
    artefactos: list[ArtefactoInput]    # vacío si Caso_2
    ruta_scripts: str | None            # None si Caso_1
    forms_url: str
    caso: Caso


@dataclass
class CorreoData:
    asunto: str
    para: list[str]
    cc: list[str]
    cuerpo: str


@dataclass
class BaseFormData:
    fecha: str
    opcion_ejecucion: str
    texto_hu: str
    codigo_artefacto: str   # vacío "" para formulario Manual


@dataclass
class DevOpsFormData:
    tipo_pase: str          # "Hotfix" | "Release"
    url_release: str
    proyecto_devops: str    # "APL-SICO" | "SCO-SICO"
    artefacto: str          # = codigo_artefacto (mismo que Input 5)
    repo_azure: str


@dataclass
class ManualFormData:
    bd: str = "FOHXG04 - SICO"
    nuevas_tablas: str = "No"
