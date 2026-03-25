from __future__ import annotations

from datetime import datetime

from textual.app import ComposeResult
from textual.containers import Horizontal, ScrollableContainer, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Input, Label, Select

from exceptions import ValidationError
from main import FORMS_URL, determinar_caso
from models import ArtefactoInput, PaseData
from tui.widgets.artefactos_widget import WidgetArtefactos
from utils.config_loader import cargar_destinatarios


_OPCIONES_EJECUCION = [("Inmediata", "Inmediata"), ("Programada", "Programada")]


_FORMATOS_FECHA = ["%d/%m/%Y", "%-d/%m/%Y", "%d/%-m/%Y", "%-d/%-m/%Y"]


def _validar_fecha(fecha: str) -> bool:
    """Retorna True si la fecha tiene alguno de los 4 formatos válidos:
    d/M/yyyy, dd/MM/yyyy, d/MM/yyyy, dd/M/yyyy.
    """
    # Normalizar: parsear con strptime usando %d/%m/%Y que acepta 1 o 2 dígitos
    # en Python, %d y %m aceptan valores sin cero inicial (1 o 2 dígitos)
    try:
        datetime.strptime(fecha, "%d/%m/%Y")
        return True
    except ValueError:
        pass
    # Intentar con día/mes de 1 dígito explícitamente
    partes = fecha.split("/")
    if len(partes) != 3:
        return False
    dia, mes, anio = partes
    if not (dia.isdigit() and mes.isdigit() and anio.isdigit()):
        return False
    if len(anio) != 4:
        return False
    try:
        datetime(int(anio), int(mes), int(dia))
        return True
    except ValueError:
        return False


class PantallaFormulario(Screen):
    """Pantalla de formulario para ingresar los datos del pase a producción."""

    BINDINGS = [
        ("escape", "volver", "Volver"),
    ]

    def __init__(self, nombre_a_codigo: dict[str, str] | None = None) -> None:
        super().__init__()
        self._nombre_a_codigo: dict[str, str] = nombre_a_codigo or {}

    def compose(self) -> ComposeResult:
        yield Header()
        with ScrollableContainer():
            with Vertical(id="form_container"):
                yield Label("Nuevo Pase a Producción", id="form_titulo")

                yield Label("Asunto *")
                yield Input(placeholder="Asunto del pase", id="inp_asunto")
                yield Label("", id="lbl_error_asunto", classes="error-label")

                yield Label("HU *")
                yield Input(placeholder="Historia de usuario", id="inp_hu")
                yield Label("", id="lbl_error_hu", classes="error-label")

                yield Label("Fecha * (d/M/yyyy)")
                yield Input(placeholder="ej: 15/3/2025", id="inp_fecha")
                yield Label("", id="lbl_error_fecha", classes="error-label")

                yield Label("Opción de Ejecución *")
                yield Select(
                    _OPCIONES_EJECUCION, prompt="Seleccionar opción", id="sel_ejecucion"
                )

                yield Label("Artefactos")
                yield WidgetArtefactos(
                    list(self._nombre_a_codigo.keys()),
                    self._nombre_a_codigo,
                    id="widget_artefactos",
                )
                yield Label("", id="lbl_error_artefactos", classes="error-label")

                yield Label("Ruta Scripts BD (opcional)")
                yield Input(
                    placeholder="Ruta a los scripts de base de datos", id="inp_scripts"
                )

                yield Label("Tipo pase: ", id="lbl_caso")

                with Horizontal(id="botones"):
                    yield Button("Iniciar Pase", id="btn_iniciar", variant="success")
                    yield Button("Volver", id="btn_volver", variant="default")
        yield Footer()

    def on_mount(self) -> None:
        pass  # codigos ya vienen por constructor desde PantallaBienvenida

    def on_input_changed(self, event: Input.Changed) -> None:
        self._actualizar_caso()

    def on_select_changed(self, event: Select.Changed) -> None:
        self._actualizar_caso()

    def on_widget_artefactos_cambio(self, event: WidgetArtefactos.Cambio) -> None:
        """Se dispara cuando se agrega o elimina un artefacto."""
        self._actualizar_caso()

    def _actualizar_caso(self) -> None:
        """Actualiza el label lbl_caso con el caso determinado en tiempo real."""
        try:
            artefactos = self.query_one(
                "#widget_artefactos", WidgetArtefactos
            ).obtener_artefactos()
            ruta_scripts = self.query_one("#inp_scripts", Input).value.strip() or None
            caso = determinar_caso(artefactos, ruta_scripts)

            # Mapear Caso enum a key de BD
            caso_key_map = {
                1: "artefactos",  # Caso.UNO
                2: "scripts",  # Caso.DOS
                3: "mixto",  # Caso.TRES
            }

            # Obtener el nombre del caso desde la BD
            destinatarios = cargar_destinatarios()
            casos = destinatarios.get("casos", {})
            caso_key = caso_key_map.get(caso.value, "")
            caso_nombre = casos.get(caso_key, {}).get("nombre", f"Caso {caso.value}")

            self.query_one("#lbl_caso", Label).update(f"Tipo pase: {caso_nombre}")
        except ValidationError:
            self.query_one("#lbl_caso", Label).update("Tipo pase: ")
        except Exception:
            self.query_one("#lbl_caso", Label).update("Tipo pase: ")
        except Exception:
            self.query_one("#lbl_caso", Label).update("Tipo pase: ")
        except Exception:
            self.query_one("#lbl_caso", Label).update("Tipo pase: ")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_iniciar":
            self._iniciar_pase()
        elif event.button.id == "btn_volver":
            self.action_volver()

    def _iniciar_pase(self) -> None:
        """Valida el formulario y navega a PantallaProgreso si todo es correcto."""
        valido = True

        # Limpiar errores previos
        self.query_one("#lbl_error_asunto", Label).update("")
        self.query_one("#lbl_error_hu", Label).update("")
        self.query_one("#lbl_error_fecha", Label).update("")
        self.query_one("#lbl_error_artefactos", Label).update("")

        asunto = self.query_one("#inp_asunto", Input).value.strip()
        if not asunto:
            self.query_one("#lbl_error_asunto", Label).update(
                "El asunto es obligatorio"
            )
            valido = False

        hu = self.query_one("#inp_hu", Input).value.strip()
        if not hu:
            self.query_one("#lbl_error_hu", Label).update("La HU es obligatoria")
            valido = False

        fecha = self.query_one("#inp_fecha", Input).value.strip()
        if not _validar_fecha(fecha):
            self.query_one("#lbl_error_fecha", Label).update(
                "Formato de fecha inválido (use d/M/yyyy o dd/MM/yyyy)"
            )
            valido = False

        artefactos = self.query_one(
            "#widget_artefactos", WidgetArtefactos
        ).obtener_artefactos()
        ruta_scripts = self.query_one("#inp_scripts", Input).value.strip() or None

        try:
            caso = determinar_caso(artefactos, ruta_scripts)
        except ValidationError:
            self.query_one("#lbl_error_artefactos", Label).update(
                "Debe ingresar al menos un artefacto o una ruta de scripts BD"
            )
            valido = False
            caso = None

        if not valido:
            return

        sel_ejecucion = self.query_one("#sel_ejecucion", Select)
        opcion_ejecucion = (
            str(sel_ejecucion.value)
            if sel_ejecucion.value is not Select.BLANK
            else "Inmediata"
        )

        pase = PaseData(
            texto_asunto=asunto,
            texto_hu=hu,
            fecha=fecha,
            opcion_ejecucion=opcion_ejecucion,
            artefactos=artefactos,
            ruta_scripts=ruta_scripts,
            forms_url=FORMS_URL,
            caso=caso,
        )

        # Importación local para evitar circular import
        from tui.screens.progreso import PantallaProgreso  # noqa: PLC0415

        artefactos_idx = getattr(self.app, "artefactos_idx", {})
        destinatarios = getattr(self.app, "destinatarios", {})
        self.app.push_screen(PantallaProgreso(pase, artefactos_idx, destinatarios))

    def action_volver(self) -> None:
        from tui.screens.bienvenida import PantallaBienvenida  # noqa: PLC0415

        self.app.push_screen(PantallaBienvenida())
