from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Label
from textual.containers import Center, Middle

from tui import APP_TITLE
from utils.update_checker import __version__


class PantallaBienvenida(Screen):
    """Pantalla de bienvenida del sistema de pases a producción."""

    CSS = """
    #version-label {
        color: $text-muted;
        margin-top: 1;
    }
    """

    BINDINGS = [
        ("q", "quit", "Salir"),
        ("escape", "quit", "Salir"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Middle(
            Center(
                Label(APP_TITLE, id="titulo"),
                Label(
                    "Completa el formulario y el sistema enviará el correo y completará los formularios automáticamente.",
                    id="descripcion",
                ),
                Button("Nuevo Pase", id="btn_nuevo_pase", variant="success"),
                Button("Configuración", id="btn_configuracion", variant="primary"),
                Button("Salir", id="btn_salir", variant="default"),
                Label(f"v{__version__}", id="version-label"),
            )
        )
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_nuevo_pase":
            from tui.screens.formulario import PantallaFormulario  # noqa: PLC0415

            # Obtener mapeo nombre -> código para el dropdown
            artefactos_idx = getattr(self.app, "artefactos_idx", {})
            nombre_a_codigo = {
                artefactos.get("nombre", codigo): codigo
                for codigo, artefactos in artefactos_idx.items()
            }
            self.app.push_screen(PantallaFormulario(nombre_a_codigo))
        elif event.button.id == "btn_configuracion":
            from tui.screens.configuracion import PantallaConfiguracion  # noqa: PLC0415

            self.app.push_screen(PantallaConfiguracion())
        elif event.button.id == "btn_salir":
            self.app.exit()

    def action_quit(self) -> None:
        self.app.exit()
