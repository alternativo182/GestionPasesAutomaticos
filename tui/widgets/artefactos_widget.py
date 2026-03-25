from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Button, Input, Select

from models import ArtefactoInput


class FilaArtefacto(Widget):
    """Una fila con Select de código y Input de URL Release."""

    DEFAULT_CSS = """
    FilaArtefacto {
        height: auto;
        width: 100%;
        border-bottom: solid #45475a;
        padding: 0 0 1 0;
        margin-bottom: 1;
    }
    FilaArtefacto Horizontal {
        height: auto;
        width: 100%;
    }
    FilaArtefacto .select-codigo {
        width: 40%;
        max-width: 40%;
    }
    FilaArtefacto .input-url {
        width: 1fr;
    }
    FilaArtefacto .btn-eliminar {
        width: 14;
    }
    """

    class Eliminada(Message):
        def __init__(self, fila: "FilaArtefacto") -> None:
            super().__init__()
            self.fila = fila

    def __init__(self, codigos: list[str], index: int) -> None:
        super().__init__()
        self._codigos = codigos
        self._index = index

    def compose(self) -> ComposeResult:
        opciones = [(codigo, codigo) for codigo in self._codigos]
        select = Select(
            opciones,
            prompt="Seleccionar artefacto",
            allow_blank=True,
            classes="select-codigo",
        )
        inp = Input(placeholder="URL Release", classes="input-url")
        btn = Button(
            "Eliminar",
            id=f"btn_eliminar_{self._index}",
            variant="error",
            classes="btn-eliminar",
        )
        with Horizontal():
            yield select
            yield inp
            yield btn

    def on_mount(self) -> None:
        self.query_one(".select-codigo").styles.width = "40%"
        self.query_one(".input-url").styles.width = "1fr"
        self.query_one(".btn-eliminar").styles.width = 14

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == f"btn_eliminar_{self._index}":
            event.stop()
            self.post_message(self.Eliminada(self))


class WidgetArtefactos(Widget):
    """Gestiona la lista dinámica de FilaArtefacto."""

    class Cambio(Message):
        """Se dispara cuando se agrega o elimina una fila de artefactos."""

        pass

    DEFAULT_CSS = """
    WidgetArtefactos {
        height: auto;
        min-height: 5;
        width: 100%;
        border: round #45475a;
        padding: 1;
        margin-top: 1;
    }
    WidgetArtefactos #contenedor_filas {
        height: auto;
        width: 100%;
    }
    """

    def __init__(self, codigos: list[str], **kwargs) -> None:
        super().__init__(**kwargs)
        self._codigos = codigos
        self._filas: list[FilaArtefacto] = []
        self._contador = 0

    def compose(self) -> ComposeResult:
        yield Vertical(id="contenedor_filas")
        yield Button("Agregar artefacto", id="btn_agregar", variant="primary")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_agregar":
            event.stop()
            fila = FilaArtefacto(self._codigos, self._contador)
            self._contador += 1
            self._filas.append(fila)
            self.query_one("#contenedor_filas", Vertical).mount(fila)
            self.post_message(self.Cambio())

    def on_fila_artefacto_eliminada(self, event: FilaArtefacto.Eliminada) -> None:
        fila = event.fila
        if fila in self._filas:
            self._filas.remove(fila)
        fila.remove()
        self.post_message(self.Cambio())

    def obtener_artefactos(self) -> list[ArtefactoInput]:
        resultado = []
        for fila in self._filas:
            codigo = fila.query_one(".select-codigo", Select).value
            url = fila.query_one(".input-url", Input).value
            if codigo is Select.BLANK or not codigo:
                continue
            resultado.append(ArtefactoInput(codigo=str(codigo), url_release=url))
        return resultado
