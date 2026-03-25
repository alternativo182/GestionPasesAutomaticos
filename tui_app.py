from textual.app import App, ComposeResult

from tui import APP_TITLE
from tui.screens.bienvenida import PantallaBienvenida
from tui.screens.update_dialog import UpdateDialog
from utils.config_loader import cargar_artefactos, cargar_destinatarios, inicializar_db
from utils.update_checker import check_for_updates


class TUIApp(App):
    """Aplicación TUI principal para pases a producción SICO."""

    CSS_PATH = "tui/tui_app.tcss"
    TITLE = APP_TITLE
    BINDINGS = [("q", "quit", "Salir")]

    async def on_mount(self) -> None:
        # Inicializar base de datos SQLite
        inicializar_db()

        self.artefactos_idx = cargar_artefactos()
        self.destinatarios = cargar_destinatarios()

        # Verificar actualizaciones en segundo plano
        self.check_updates_background()

        await self.push_screen(PantallaBienvenida())

    def check_updates_background(self) -> None:
        """Verifica actualizaciones y muestra diálogo si hay una nueva versión."""
        try:
            update_info = check_for_updates()
            if update_info and update_info.is_update_available:
                # Mostrar diálogo con un pequeño delay para que la UI se renderice primero
                self.set_timer(0.5, lambda: self.push_screen(UpdateDialog(update_info)))
        except Exception:
            # Silenciar errores de actualización
            pass


if __name__ == "__main__":
    TUIApp().run()
