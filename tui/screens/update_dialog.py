"""Diálogo para mostrar actualizaciones disponibles."""

from __future__ import annotations

import subprocess
import sys

from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Button, Label, Static
from textual.containers import Center, Vertical

from utils.update_checker import UpdateInfo

INSTALL_CMD = "irm https://raw.githubusercontent.com/alternativo182/GestionPasesAutomaticos/main/install.ps1 | iex"


class UpdateDialog(ModalScreen):
    """Diálogo modal para notificar actualizaciones."""

    CSS = """
    UpdateDialog {
        align: center middle;
    }

    #update-container {
        width: 60;
        height: auto;
        padding: 1 2;
        background: $surface;
        border: thick $warning;
    }

    #update-title {
        text-style: bold;
        color: $warning;
        text-align: center;
        margin-bottom: 1;
    }

    #update-info {
        text-align: center;
        margin-bottom: 2;
    }

    #update-buttons {
        width: 100%;
        height: auto;
        align: center middle;
    }

    Button {
        margin: 0 1;
    }
    """

    BINDINGS = [
        ("escape", "dismiss", "Ignorar"),
        ("i", "dismiss", "Ignorar"),
        ("r", "do_update", "Actualizar"),
    ]

    def __init__(self, update_info: UpdateInfo) -> None:
        super().__init__()
        self.update_info = update_info

    def compose(self) -> ComposeResult:
        with Vertical(id="update-container"):
            yield Label(
                f"⚠️  Nueva versión disponible: {self.update_info.latest_version}",
                id="update-title",
            )
            yield Label(
                f"Tu versión: {self.update_info.current_version}",
                id="update-info",
            )
            with Center(id="update-buttons"):
                yield Button("Actualizar", id="btn-update", variant="success")
                yield Button("Ignorar", id="btn-ignore", variant="default")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-update":
            self.action_do_update()
        elif event.button.id == "btn-ignore":
            self.dismiss(False)

    def action_do_update(self) -> None:
        """Ejecuta la actualización y cierra la app."""
        self.app.exit()

        # Ejecutar PowerShell con el comando de instalación
        # Esto reemplazará el exe actual con la nueva versión
        subprocess.Popen(
            [
                "powershell.exe",
                "-NoExit",
                "-Command",
                INSTALL_CMD,
            ],
            creationflags=subprocess.CREATE_NEW_CONSOLE,  # Windows only
        )
        sys.exit(0)

    def action_dismiss(self) -> None:
        self.dismiss(False)
