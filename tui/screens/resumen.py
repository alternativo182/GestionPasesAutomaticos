from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import ScrollableContainer, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Label


class PantallaResumen(Screen):
    """Pantalla de resumen que muestra el resultado del pase a producción."""

    BINDINGS = [
        ("escape", "ir_bienvenida", "Volver"),
    ]

    def __init__(self, errores: list[str], ruta_log: str) -> None:
        super().__init__()
        self._errores = errores
        self._ruta_log = ruta_log

    def compose(self) -> ComposeResult:
        yield Header()
        with ScrollableContainer():
            with Vertical(id="resumen_container"):
                yield Label("Resumen del Pase", id="resumen_titulo")

                if self._errores:
                    lbl_estado = Label("Completado con errores", id="lbl_estado")
                    lbl_estado.add_class("estado-error")
                else:
                    lbl_estado = Label("Completado exitosamente", id="lbl_estado")
                    lbl_estado.add_class("estado-ok")
                yield lbl_estado

                yield Label("Errores:", id="lbl_errores_titulo")
                if not self._errores:
                    yield Label("Sin errores", id="lbl_sin_errores")
                else:
                    for error in self._errores:
                        yield Label(f"• {error}", classes="error-item")

                yield Label(f"Log: {self._ruta_log}", id="lbl_ruta_log")

                with Vertical(id="botones_resumen"):
                    yield Button("Nuevo Pase", id="btn_nuevo_pase", variant="primary")
                    yield Button("Salir", id="btn_salir", variant="default")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_nuevo_pase":
            self._nuevo_pase()
        elif event.button.id == "btn_salir":
            self.app.exit()

    def _nuevo_pase(self) -> None:
        from tui.screens.formulario import PantallaFormulario  # noqa: PLC0415

        codigos = list(getattr(self.app, "artefactos_idx", {}).keys())
        self.app.push_screen(PantallaFormulario(codigos))

    def action_ir_bienvenida(self) -> None:
        from tui.screens.bienvenida import PantallaBienvenida  # noqa: PLC0415

        self.app.push_screen(PantallaBienvenida())
