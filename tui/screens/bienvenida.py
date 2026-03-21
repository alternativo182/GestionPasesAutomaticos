from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Label
from textual.containers import Center, Middle

from tui import APP_TITLE


class PantallaBienvenida(Screen):
    """Pantalla de bienvenida del sistema de pases a producción."""

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
                    "Automatización de pases a producción SICO.\n"
                    "Completá el formulario y el sistema enviará el correo\n"
                    "y completará los formularios DevOps y Manual automáticamente.",
                    id="descripcion",
                ),
                Button("Nuevo Pase", id="btn_nuevo_pase", variant="primary"),
                Button("Salir", id="btn_salir", variant="default"),
            )
        )
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_nuevo_pase":
            from tui.screens.formulario import PantallaFormulario  # noqa: PLC0415

            codigos = list(getattr(self.app, "artefactos_idx", {}).keys())
            self.app.push_screen(PantallaFormulario(codigos))
        elif event.button.id == "btn_salir":
            self.app.exit()

    def action_quit(self) -> None:
        self.app.exit()
