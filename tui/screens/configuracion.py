"""Pantalla de configuración para editar artefactos y destinatarios."""

from textual.message import Message
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import (
    Button,
    DataTable,
    Footer,
    Header,
    Input,
    Label,
    Static,
)


from utils.config_loader import (
    cargar_artefactos,
    cargar_destinatarios,
    guardar_artefacto,
    guardar_caso,
    eliminar_artefacto,
    eliminar_caso,
    inicializar_db,
)


class DialogoAgregarEditarArtefacto(Screen):
    """Diálogo modal para agregar o editar un artefacto."""

    def __init__(
        self, artefacto: dict | None = None, codigo: str | None = None
    ) -> None:
        super().__init__()
        self._artefacto = artefacto or {}
        self._codigo_original = codigo
        self._modo = "Editar" if artefacto else "Agregar"

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="dialog_container"):
            yield Static(f"{self._modo} Artefacto", id="dialog_title")
            yield Label("Artefacto *")
            # En modo edición, usar el código original
            valor_codigo = self._codigo_original or self._artefacto.get("codigo", "")
            yield Input(
                value=valor_codigo,
                id="inp_codigo",
                placeholder="ej: cosicocomun",
            )
            yield Label("", id="lbl_error_codigo", classes="error-label")

            yield Label("Repositorio *")
            yield Input(
                value=self._artefacto.get("repo", ""),
                id="inp_repo",
                placeholder="ej: msc-sicocomun",
            )
            yield Label("", id="lbl_error_repo", classes="error-label")

            yield Label("Nombre *")
            yield Input(
                value=self._artefacto.get("nombre", ""),
                id="inp_nombre",
                placeholder="ej: CORE - SICO Común",
            )
            yield Label("", id="lbl_error_nombre", classes="error-label")

            yield Label("Descripción")
            yield Input(
                value=self._artefacto.get("descripcion", ""),
                id="inp_descripcion",
                placeholder="Descripción del sistema",
            )

            with Horizontal(id="dialog_botones"):
                yield Button("Guardar", id="btn_guardar", variant="success")
                yield Button("Cancelar", id="btn_cancelar", variant="default")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_guardar":
            self._guardar()
        elif event.button.id == "btn_cancelar":
            self.app.pop_screen()

    def _guardar(self) -> None:
        """Valida y retorna los datos del artefacto."""
        # Limpiar errores previos
        self.query_one("#lbl_error_codigo", Label).update("")
        self.query_one("#lbl_error_repo", Label).update("")
        self.query_one("#lbl_error_nombre", Label).update("")

        codigo = self.query_one("#inp_codigo", Input).value.strip()
        repo = self.query_one("#inp_repo", Input).value.strip()
        nombre = self.query_one("#inp_nombre", Input).value.strip()
        descripcion = self.query_one("#inp_descripcion", Input).value.strip()

        hay_error = False

        if not codigo:
            self.query_one("#lbl_error_codigo", Label).update(
                "El código es obligatorio"
            )
            hay_error = True
        if not repo:
            self.query_one("#lbl_error_repo", Label).update(
                "El repositorio es obligatorio"
            )
            hay_error = True
        if not nombre:
            self.query_one("#lbl_error_nombre", Label).update(
                "El nombre es obligatorio"
            )
            hay_error = True

        if hay_error:
            return

        # Guardar en el app y cerrar (incluir ID si existe)
        self.app._temp_artefacto_data = {
            "id": self._artefacto.get("id"),  # ID interno para actualizaciones
            "codigo": codigo,
            "repo": repo,
            "nombre": nombre,
            "descripcion": descripcion,
        }

        # Buscar la pantalla padre y notificar
        if len(self.app._screen_stack) > 1:
            parent = self.app._screen_stack[-2]
            if hasattr(parent, "_on_dialog_closed"):
                parent._on_dialog_closed()

        self.app.pop_screen()


class DialogoConfirmacion(Screen):
    """Diálogo de confirmación genérico."""

    BINDINGS = [
        ("escape", "cancelar", "Cancelar"),
    ]

    def __init__(self, titulo: str, mensaje: str, callback=None) -> None:
        super().__init__()
        self._titulo = titulo
        self._mensaje = mensaje
        self._callback = callback

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="dialog_container"):
            yield Static(self._titulo, id="dialog_title")
            yield Static(self._mensaje, id="dialog_mensaje")
            with Horizontal(id="dialog_botones"):
                yield Button("Confirmar", id="btn_confirmar", variant="error")
                yield Button("Cancelar", id="btn_cancelar", variant="default")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_confirmar":
            # Llamar al callback si existe
            if self._callback:
                self._callback()
            self.app.pop_screen()
        elif event.button.id == "btn_cancelar":
            self.app.pop_screen()

    def action_cancelar(self) -> None:
        """Acción para cancelar."""
        self.app.pop_screen()


class DialogoAgregarEditarCaso(Screen):
    """Diálogo modal para agregar o editar un caso de destinatarios."""

    def __init__(
        self, caso_id: str | None = None, caso_data: dict | None = None
    ) -> None:
        super().__init__()
        self._caso_id = caso_id
        self._caso_data = caso_data or {}
        self._modo = "Editar" if caso_id else "Agregar"

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="dialog_container"):
            yield Static(f"{self._modo} Caso de Destinatarios", id="dialog_title")

            # Solo lectura - Nombre
            yield Label("Caso")
            yield Static(self._caso_data.get("nombre", ""), id="static_nombre")

            # Solo lectura - Descripción
            yield Label("Descripción")
            yield Static(
                self._caso_data.get("descripcion", ""), id="static_descripcion"
            )

            # Editables - Destinatarios Para
            yield Label("PARA * (separados por coma)")
            para_str = ", ".join(self._caso_data.get("para", []))
            yield Input(
                value=para_str,
                id="inp_para",
                placeholder="email1@ejemplo.com, email2@ejemplo.com",
            )
            yield Label("", id="lbl_error_para", classes="error-label")

            # Editables - Destinatarios CC
            yield Label("CC (separados por coma)")
            cc_str = ", ".join(self._caso_data.get("cc", []))
            yield Input(
                value=cc_str,
                id="inp_cc",
                placeholder="email1@ejemplo.com, email2@ejemplo.com",
            )

            with Horizontal(id="dialog_botones"):
                yield Button("Guardar", id="btn_guardar", variant="success")
                yield Button("Cancelar", id="btn_cancelar", variant="default")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_guardar":
            self._guardar()
        elif event.button.id == "btn_cancelar":
            self.app.pop_screen()

    def _guardar(self) -> None:
        """Valida y retorna los datos del caso."""
        # Limpiar errores previos
        self.query_one("#lbl_error_para", Label).update("")

        # Solo obtener Para y CC (los editables)
        para_str = self.query_one("#inp_para", Input).value.strip()
        cc_str = self.query_one("#inp_cc", Input).value.strip()

        hay_error = False

        if not para_str:
            self.query_one("#lbl_error_para", Label).update(
                "Los destinatarios son obligatorios"
            )
            hay_error = True

        if hay_error:
            return

        # Parsear listas de emails
        para = [e.strip() for e in para_str.split(",") if e.strip()]
        cc = [e.strip() for e in cc_str.split(",") if e.strip()]

        # Guardar en el app y cerrar (incluir ID si existe)
        # Usar los valores originales de los campos de solo lectura
        self.app._temp_caso_data = {
            "id": self._caso_data.get("id"),  # ID interno para actualizaciones
            "caso_id": self._caso_id,  # Valor original
            "nombre": self._caso_data.get("nombre", ""),  # Valor original
            "descripcion": self._caso_data.get("descripcion", ""),  # Valor original
            "para": para,
            "cc": cc,
        }

        # Buscar la pantalla padre y notificar
        if len(self.app._screen_stack) > 1:
            parent = self.app._screen_stack[-2]
            if hasattr(parent, "_on_dialog_closed"):
                parent._on_dialog_closed()

        self.app.pop_screen()


class PantallaConfiguracion(Screen):
    """Pantalla de configuración para editar artefactos y destinatarios."""

    BINDINGS = [
        ("escape", "volver", "Volver"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._artefactos: dict[str, dict] = {}
        self._destinatarios: dict = {}
        self._tab_seleccionada = "artefactos"

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="config_container"):
            # Botones de navegación entre secciones
            with Horizontal(id="nav_botones"):
                yield Button("Artefactos", id="btn_ver_artefactos", variant="primary")
                yield Button(
                    "Destinatarios", id="btn_ver_destinatarios", variant="default"
                )

            # Sección de Artefactos
            with Vertical(id="seccion_artefactos"):
                yield Label("Gestión de Artefactos", id="lbl_artefactos_titulo")
                yield DataTable(id="tabla_artefactos")
                with Horizontal(id="botones_artefactos"):
                    yield Button(
                        "Agregar", id="btn_agregar_artefacto", variant="success"
                    )
                    yield Button("Editar", id="btn_editar_artefacto", variant="warning")
                    yield Button(
                        "Eliminar", id="btn_eliminar_artefacto", variant="error"
                    )

            # Sección de Destinatarios
            with Vertical(id="seccion_destinatarios"):
                yield Label(
                    "Gestión de Destinatarios por Caso", id="lbl_destinatarios_titulo"
                )
                yield DataTable(id="tabla_destinatarios")
                with Horizontal(id="botones_destinatarios"):
                    yield Button("Editar", id="btn_editar_caso", variant="warning")

            # Botón Volver
            with Horizontal(id="botones_volver"):
                yield Button("Volver", id="btn_volver", variant="default")

            yield Label("", id="lbl_mensaje")
        yield Footer()

    def _on_dialog_closed(self) -> None:
        """Se llama cuando un diálogo se cierra."""
        # Verificar artefactos
        data = getattr(self.app, "_temp_artefacto_data", None)
        if data:
            delattr(self.app, "_temp_artefacto_data")

            # Obtener ID si existe
            artefacto_id = data.get("id")

            try:
                guardar_artefacto(
                    artefacto_id,
                    data["codigo"],
                    data["repo"],
                    data["nombre"],
                    data.get("descripcion", ""),
                )
                self._artefactos = cargar_artefactos()
            except Exception as e:
                self._mostrar_mensaje(f"ERROR: {e}", "error")
            self._actualizar_tabla_artefactos()
            self._mostrar_mensaje(f"Artefacto '{data['codigo']}' guardado")
            return

        # Verificar casos
        caso_data = getattr(self.app, "_temp_caso_data", None)
        if caso_data:
            delattr(self.app, "_temp_caso_data")

            # Obtener ID si existe
            caso_id_db = caso_data.get("id")

            try:
                guardar_caso(
                    caso_id_db,
                    caso_data["caso_id"],
                    caso_data["nombre"],
                    caso_data.get("descripcion", ""),
                    caso_data["para"],
                    caso_data.get("cc", []),
                )
                self._destinatarios = cargar_destinatarios()
            except Exception as e:
                self._mostrar_mensaje(f"ERROR: {e}", "error")
            self._actualizar_tabla_destinatarios()
            self._mostrar_mensaje(f"Caso '{caso_data['caso_id']}' guardado")
            return

    def _cargar_datos(self) -> None:
        """Carga los datos desde la base de datos."""
        self._artefactos = cargar_artefactos()
        self._destinatarios = cargar_destinatarios()

    def _actualizar_tabla_artefactos(self) -> None:
        """Actualiza la tabla de artefactos."""
        tabla = self.query_one("#tabla_artefactos", DataTable)
        tabla.clear()

        # Agregar columnas si no existen
        if not tabla.columns:
            tabla.add_columns("Artefacto", "Repositorio", "Nombre", "Descripción")

        # Agregar filas
        for codigo, data in sorted(self._artefactos.items()):
            tabla.add_row(
                codigo,
                data.get("repo", ""),
                data.get("nombre", ""),
                data.get("descripcion", ""),
            )

    def _actualizar_tabla_destinatarios(self) -> None:
        """Actualiza la tabla de destinatarios."""
        tabla = self.query_one("#tabla_destinatarios", DataTable)
        tabla.clear()

        # Agregar columnas si no existen
        if not tabla.columns:
            tabla.add_columns("Caso", "Para", "CC")

        casos = self._destinatarios.get("casos", {})
        for caso_id, data in sorted(casos.items()):
            para = ", ".join(data.get("para", []))
            cc = ", ".join(data.get("cc", []))
            tabla.add_row(
                data.get("nombre", ""),
                para,
                cc,
            )

    def on_mount(self) -> None:
        """Carga los datos al iniciar."""
        self._cargar_datos()
        self._actualizar_tabla_artefactos()
        self._actualizar_tabla_destinatarios()
        self._tab_seleccionada = "artefactos"
        # Mostrar sección de artefactos por defecto
        self.query_one("#seccion_artefactos").display = True
        self.query_one("#seccion_destinatarios").display = False

    def _mostrar_artefactos(self) -> None:
        """Muestra la sección de artefactos."""
        self.query_one("#seccion_artefactos").display = True
        self.query_one("#seccion_destinatarios").display = False
        self.query_one("#btn_ver_artefactos", Button).variant = "primary"
        self.query_one("#btn_ver_destinatarios", Button).variant = "default"
        self._tab_seleccionada = "artefactos"

    def _mostrar_destinatarios(self) -> None:
        """Muestra la sección de destinatarios."""
        self.query_one("#seccion_artefactos").display = False
        self.query_one("#seccion_destinatarios").display = True
        self.query_one("#btn_ver_artefactos", Button).variant = "default"
        self.query_one("#btn_ver_destinatarios", Button).variant = "primary"
        self._tab_seleccionada = "destinatarios"

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Maneja los botones de acción."""
        button_id = event.button.id

        # Botón Volver
        if button_id == "btn_volver":
            self.action_volver()
            return

        # Botones de navegación
        if button_id == "btn_ver_artefactos":
            self._mostrar_artefactos()
            return
        elif button_id == "btn_ver_destinatarios":
            self._mostrar_destinatarios()
            return

        # Botones de artefactos
        if button_id == "btn_agregar_artefacto":
            self._agregar_artefacto()
        elif button_id == "btn_editar_artefacto":
            self._editar_artefacto()
        elif button_id == "btn_eliminar_artefacto":
            self._eliminar_artefacto()
        # Botones de destinatarios
        elif button_id == "btn_editar_caso":
            self._editar_caso()

    def _agregar_artefacto(self) -> None:
        """Abre el diálogo para agregar un artefacto."""

        self.app.push_screen(DialogoAgregarEditarArtefacto())

    def _editar_artefacto(self) -> None:
        """Abre el diálogo para editar el artefacto seleccionado."""
        tabla = self.query_one("#tabla_artefactos", DataTable)
        fila_seleccionada = tabla.cursor_row

        if fila_seleccionada is None:
            self._mostrar_mensaje("Seleccione un artefacto para editar", "error")
            return

        # Obtener el código del artefacto seleccionado
        codigos = sorted(self._artefactos.keys())
        if fila_seleccionada < len(codigos):
            codigo = codigos[fila_seleccionada]
            artefacto = self._artefactos[codigo]
            self.app.push_screen(
                DialogoAgregarEditarArtefacto(artefacto, codigo),
                self._on_artefacto_editado,
            )

    def _on_artefacto_editado(self, screen: DialogoAgregarEditarArtefacto) -> None:
        """Callback cuando se edita el artefacto."""
        data = getattr(self.app, "_temp_artefacto_data", None)
        if data:
            delattr(self.app, "_temp_artefacto_data")

            # Obtener el código original (del que estábamos editando)
            tabla = self.query_one("#tabla_artefactos", DataTable)
            fila_seleccionada = tabla.cursor_row
            codigos = sorted(self._artefactos.keys())
            codigo_original = (
                codigos[fila_seleccionada] if fila_seleccionada is not None else None
            )

            # Obtener el ID original
            id_original = None
            if codigo_original and codigo_original in self._artefactos:
                id_original = self._artefactos[codigo_original].get("id")

            # Verificar si cambió el código y si el nuevo código ya existe
            if codigo_original and codigo_original != data["codigo"]:
                if data["codigo"] in self._artefactos:
                    self._mostrar_mensaje(
                        f"Error: El código '{data['codigo']}' ya existe", "error"
                    )
                    return

            # Eliminar el original de la BD si cambió el código
            if id_original and codigo_original and codigo_original != data["codigo"]:
                try:
                    eliminar_artefacto(id_original)
                except Exception as e:
                    self._mostrar_mensaje(f"ERROR: {e}", "error")
                    return

            try:
                guardar_artefacto(
                    id_original,
                    data["codigo"],
                    data["repo"],
                    data["nombre"],
                    data.get("descripcion", ""),
                )
                self._artefactos = cargar_artefactos()
            except Exception as e:
                self._mostrar_mensaje(f"ERROR: {e}", "error")
            self._actualizar_tabla_artefactos()
            self._mostrar_mensaje(
                f"Artefacto '{data['codigo']}' actualizado correctamente"
            )

    def _eliminar_artefacto(self) -> None:
        """Elimina el artefacto seleccionado."""
        tabla = self.query_one("#tabla_artefactos", DataTable)
        fila_seleccionada = tabla.cursor_row

        if fila_seleccionada is None:
            self._mostrar_mensaje("Seleccione un artefacto para eliminar", "error")
            return

        codigos = sorted(self._artefactos.keys())
        if fila_seleccionada < len(codigos):
            codigo = codigos[fila_seleccionada]

            # Mostrar diálogo de confirmación con callback directo
            self.app.push_screen(
                DialogoConfirmacion(
                    "Confirmar Eliminación",
                    f"¿Está seguro de eliminar el artefacto '{codigo}'?",
                    callback=self._on_confirmar_eliminar_artefacto,
                )
            )

    def _on_confirmar_eliminar_artefacto(self) -> None:
        """Callback de confirmación de eliminación de artefacto."""
        # El callback se llama solo cuando se confirma
        try:
            tabla = self.query_one("#tabla_artefactos", DataTable)
            fila_seleccionada = tabla.cursor_row
            codigos = sorted(self._artefactos.keys())
            if fila_seleccionada is not None and fila_seleccionada < len(codigos):
                codigo = codigos[fila_seleccionada]
                artefacto_id = self._artefactos[codigo]["id"]
                eliminar_artefacto(artefacto_id)
                self._artefactos = cargar_artefactos()
                self._actualizar_tabla_artefactos()
                self._mostrar_mensaje(f"Artefacto '{codigo}' eliminado")
        except Exception as e:
            self._mostrar_mensaje(f"ERROR: {e}", "error")

    def _editar_caso(self) -> None:
        """Abre el diálogo para editar el caso seleccionado."""
        tabla = self.query_one("#tabla_destinatarios", DataTable)
        fila_seleccionada = tabla.cursor_row

        if fila_seleccionada is None:
            self._mostrar_mensaje("Seleccione un caso para editar", "error")
            return

        casos = self._destinatarios.get("casos", {})
        caso_ids = sorted(casos.keys())
        if fila_seleccionada < len(caso_ids):
            caso_id = caso_ids[fila_seleccionada]
            caso_data = casos[caso_id]
            self.app.push_screen(
                DialogoAgregarEditarCaso(caso_id, caso_data), self._on_caso_editado
            )

    def _on_caso_editado(self, screen: DialogoAgregarEditarCaso) -> None:
        """Callback cuando se edita el caso."""
        data = getattr(self.app, "_temp_caso_data", None)
        if data:
            delattr(self.app, "_temp_caso_data")

            # Obtener el caso original
            tabla = self.query_one("#tabla_destinatarios", DataTable)
            fila_seleccionada = tabla.cursor_row
            casos = self._destinatarios.get("casos", {})
            caso_ids = sorted(casos.keys())
            caso_original = (
                caso_ids[fila_seleccionada] if fila_seleccionada is not None else None
            )

            # Obtener el ID original
            id_original = None
            if caso_original and caso_original in casos:
                id_original = casos[caso_original].get("id")

            # Verificar si cambió el ID y si el nuevo ID ya existe
            if caso_original and caso_original != data["caso_id"]:
                if data["caso_id"] in casos:
                    self._mostrar_mensaje(
                        f"Error: El caso '{data['caso_id']}' ya existe", "error"
                    )
                    return

            # Eliminar el original de la BD si cambió el código
            if id_original and caso_original and caso_original != data["caso_id"]:
                try:
                    eliminar_caso(id_original)
                except Exception as e:
                    self._mostrar_mensaje(f"ERROR: {e}", "error")
                    return

            try:
                guardar_caso(
                    id_original,
                    data["caso_id"],
                    data["nombre"],
                    data.get("descripcion", ""),
                    data["para"],
                    data.get("cc", []),
                )
                self._destinatarios = cargar_destinatarios()
            except Exception as e:
                self._mostrar_mensaje(f"ERROR: {e}", "error")
            self._actualizar_tabla_destinatarios()
            self._mostrar_mensaje(f"Caso '{data['caso_id']}' actualizado correctamente")

    def _guardar_artefacto_individual(
        self, id: int | None, codigo: str, repo: str, nombre: str, descripcion: str
    ) -> None:
        """Guarda un artefacto en la base de datos."""
        try:
            guardar_artefacto(id, codigo, repo, nombre, descripcion)
            self._mostrar_mensaje(f"Artefacto '{codigo}' guardado")
        except Exception as e:
            self._mostrar_mensaje(f"ERROR: {e}", "error")

    def _eliminar_artefacto_db(self, id: int) -> None:
        """Elimina un artefacto de la base de datos."""
        try:
            eliminar_artefacto(id)
            self._mostrar_mensaje(f"Artefacto eliminado")
        except Exception as e:
            self._mostrar_mensaje(f"ERROR: {e}", "error")

    def _guardar_caso_individual(
        self,
        id: int | None,
        caso_id: str,
        nombre: str,
        descripcion: str,
        para: list,
        cc: list,
    ) -> None:
        """Guarda un caso en la base de datos."""
        try:
            guardar_caso(id, caso_id, nombre, descripcion, para, cc)
            self._mostrar_mensaje(f"Caso '{caso_id}' guardado")
        except Exception as e:
            self._mostrar_mensaje(f"ERROR: {e}", "error")

    def _recargar_datos(self) -> None:
        """Recarga los datos desde la base de datos."""
        try:
            self._artefactos = cargar_artefactos()
            self._destinatarios = cargar_destinatarios()
            self._actualizar_tabla_artefactos()
            self._actualizar_tabla_destinatarios()
        except Exception as e:
            self._mostrar_mensaje(f"ERROR al recargar: {e}", "error")

    def _guardar_artefactos(self) -> None:
        """Guarda los artefactos (legacy, ya no se usa)."""
        pass

    def _guardar_destinatarios(self) -> None:
        """Guarda los destinatarios (legacy, ya no se usa)."""
        pass

    def _mostrar_mensaje(self, mensaje: str, tipo: str = "success") -> None:
        """Muestra un mensaje en la pantalla."""
        try:
            label = self.query_one("#lbl_mensaje", Label)
            if tipo == "error":
                label.update(f"[red]{mensaje}[/red]")
            else:
                label.update(f"[green]{mensaje}[/green]")
        except Exception:
            pass  # Si no existe el label, ignorar

    def action_volver(self) -> None:
        """Regresa a la pantalla anterior."""
        self.app.pop_screen()
