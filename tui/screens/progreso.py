from __future__ import annotations

from datetime import datetime

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Label, LoadingIndicator, RichLog
from textual.worker import Worker, WorkerState

from models import PaseData
from tui.worker import ejecutar_pase_worker


class PantallaProgreso(Screen):
    """Pantalla de progreso que ejecuta la automatización en un worker thread."""

    BINDINGS = [
        ("escape", "ir_bienvenida", "Volver"),
    ]

    def __init__(
        self,
        pase: PaseData,
        artefactos_idx: dict,
        destinatarios: dict,
    ) -> None:
        super().__init__()
        self._pase = pase
        self._artefactos_idx = artefactos_idx
        self._destinatarios = destinatarios
        self._resultado: tuple[list[str], str] | None = None
        self._worker_activo: bool = True

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="progreso_container"):
            yield Label("", id="lbl_paso_actual")
            yield RichLog(id="log_progreso", highlight=True, markup=True)
            yield LoadingIndicator(id="spinner")
            yield Button("Ver Resumen", id="btn_ver_resumen", variant="success")
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#btn_ver_resumen", Button).display = False
        self.run_worker(self._run_worker_fn, thread=True)

    def _run_worker_fn(self) -> tuple[list[str], str]:
        """Función ejecutada en el worker thread."""
        callback = lambda msg: self.app.call_from_thread(self.agregar_log, msg)
        return ejecutar_pase_worker(
            self._pase,
            self._artefactos_idx,
            self._destinatarios,
            callback,
        )

    def agregar_log(self, mensaje: str) -> None:
        """Escribe un mensaje en el RichLog con timestamp y markup de color."""
        ts = datetime.now().strftime("%H:%M:%S")
        log = self.query_one("#log_progreso", RichLog)
        lbl = self.query_one("#lbl_paso_actual", Label)

        if "✓" in mensaje:
            linea = f"[{ts}] [green]{mensaje}[/green]"
        elif "✗" in mensaje:
            linea = f"[{ts}] [red]{mensaje}[/red]"
        else:
            linea = f"[{ts}] {mensaje}"

        log.write(linea)
        lbl.update(mensaje)

    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        if event.state == WorkerState.SUCCESS:
            self._resultado = event.worker.result
            self._on_worker_done()

    def _on_worker_done(self) -> None:
        """Llamado cuando el worker finaliza exitosamente."""
        self.query_one("#spinner", LoadingIndicator).display = False
        self.query_one("#btn_ver_resumen", Button).display = True
        self._worker_activo = False

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_ver_resumen":
            self._ir_resumen()

    def _ir_resumen(self) -> None:
        from tui.screens.resumen import PantallaResumen  # noqa: PLC0415

        if self._resultado is not None:
            errores, ruta_log = self._resultado
            self.app.push_screen(PantallaResumen(errores, ruta_log))

    def action_ir_bienvenida(self) -> None:
        if self._worker_activo:
            return
        from tui.screens.bienvenida import PantallaBienvenida  # noqa: PLC0415

        self.app.push_screen(PantallaBienvenida())
