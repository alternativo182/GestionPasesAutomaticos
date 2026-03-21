from textual.app import App, ComposeResult

from tui import APP_TITLE
from tui.screens.bienvenida import PantallaBienvenida
from utils.config_loader import cargar_artefactos, cargar_destinatarios


class TUIApp(App):
    """Aplicación TUI principal para pases a producción SICO."""

    CSS_PATH = "tui/tui_app.tcss"
    TITLE = APP_TITLE
    BINDINGS = [("q", "quit", "Salir")]

    async def on_mount(self) -> None:
        self.artefactos_idx = cargar_artefactos()
        self.destinatarios = cargar_destinatarios()
        await self.push_screen(PantallaBienvenida())


if __name__ == "__main__":
    TUIApp().run()
