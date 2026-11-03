import flet as ft
import sqlite3

from xlsx_export import build_usage_history_workbook
from xlsx_import import parse_usage_workbook

class GymAppView(ft.Column):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.expand = True
        self.file_picker = ft.FilePicker()

        # UI components
        self.summary_list = ft.ListView(expand=True, spacing=10, padding=10)
        self.machine_dropdown = ft.Dropdown(
            label="Selecciona máquina", 
            width=450,
            on_select=self._on_machine_selected,
        )
        self.latest_usage_text = ft.Text(
            "Selecciona una máquina para consultar su último registro.",
            italic=True,
        )
        self.weight_input = ft.TextField(label="Peso (kg)", width=150, keyboard_type=ft.KeyboardType.NUMBER)
        
        self.new_machine_input = ft.TextField(label="Nombre nueva máquina", width=450)
        self.machine_mod_dropdown = ft.Dropdown(label="Máquina a modificar", width=450)
        self.new_name_input = ft.TextField(label="Nuevo nombre", width=450)
        self.machine_del_dropdown = ft.Dropdown(label="Máquina a eliminar", width=450)

        self._build_ui()

    def _build_ui(self):
        self.button_style = ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=12),
            padding=20,
            text_style=ft.TextStyle(size=18, weight=ft.FontWeight.W_500),
        )

        summary_panel = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        "Último peso registrado por máquina",
                        theme_style=ft.TextThemeStyle.TITLE_LARGE,
                        weight=ft.FontWeight.BOLD,
                    ),
                    self.summary_list,
                    ft.OutlinedButton(
                        "Exportar historial a Excel",
                        icon=ft.Icons.FILE_DOWNLOAD,
                        on_click=self._on_export_history_click,
                        style=self.button_style,
                        width=280
                    ),
                    ft.OutlinedButton(
                        "Importar desde Excel",
                        icon=ft.Icons.FILE_UPLOAD,
                        on_click=self._on_import_history_click,
                        style=self.button_style,
                        width=280
                    ),
                ]
            ),
            padding=10,
        )

        new_usage_panel = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        "Registrar entrenamiento",
                        theme_style=ft.TextThemeStyle.TITLE_LARGE,
                        weight=ft.FontWeight.BOLD,
                    ),
                    self.machine_dropdown,
                    self.latest_usage_text,
                    self.weight_input,
                    ft.FilledButton(
                        "Guardar Uso",
                        icon=ft.Icons.SAVE,
                        on_click=self._on_log_usage_click,
                        style=self.button_style,
                    ),
                ],
                spacing=15,
            ),
            padding=20,
        )

        management_panel = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        "Añadir Máquina Nueva", 
                        theme_style=ft.TextThemeStyle.TITLE_LARGE,
                        weight=ft.FontWeight.BOLD
                    ),
                    self.new_machine_input,
                    ft.FilledButton(
                        "Crear Máquina",
                        icon=ft.Icons.ADD,
                        on_click=self._on_add_machine_click,
                        style=self.button_style,
                    ),
                    ft.Divider(),
                    ft.Text(
                        "Modificar Nombre",
                        theme_style=ft.TextThemeStyle.TITLE_MEDIUM, 
                        weight=ft.FontWeight.BOLD
                    ),
                    self.machine_mod_dropdown,
                    self.new_name_input,
                    ft.FilledButton(
                        "Actualizar Nombre",
                        icon=ft.Icons.EDIT,
                        on_click=self._on_rename_machine_click,
                        style=self.button_style,
                    ),
                    ft.Divider(),
                    ft.Text(
                        "Eliminar Máquina",
                        theme_style=ft.TextThemeStyle.TITLE_MEDIUM,
                        weight=ft.FontWeight.BOLD
                    ),
                    self.machine_del_dropdown,
                    ft.FilledButton(
                        "Eliminar",
                        icon=ft.Icons.DELETE,
                        on_click=self._on_delete_machine_click,
                        style=self.button_style,
                    ),
                ],
                spacing=10,
                scroll=ft.ScrollMode.AUTO,
            ),
            padding=20,
        )

        tab_label_style = ft.TextStyle(
            size=18,
            weight=ft.FontWeight.W_500,
        )

        tab_bar = ft.TabBar(
            tabs=[
                ft.Tab(label="Añadir Uso"),
                ft.Tab(label="Historial"),
                ft.Tab(label="Gestionar Máquinas"),
            ],
            label_text_style=tab_label_style,
            unselected_label_text_style=tab_label_style,
        )

        tab_view = ft.TabBarView(
            controls=[
                new_usage_panel,
                summary_panel,
                management_panel,
            ],
            expand=True,
        )

        tabs = ft.Tabs(
            content=ft.Column(
                controls=[tab_bar, tab_view],
                expand=True,
            ),
            length=3,
            selected_index=0,
            animation_duration=300,
            expand=1,
        )

        self.controls = [
            ft.Container(
                content=tabs,
                padding=ft.Padding.only(top=24),
                expand=True,
            )
        ]

    def update_data(self):
        results = self.db.get_summary()
        self.summary_list.controls.clear()
        
        if not results:
            self.summary_list.controls.append(ft.Text("No hay máquinas registradas aún.", italic=True))
        else:
            for machine_id, machine_name, weight, date in results:
                self.summary_list.controls.append(
                    ft.Card(
                        content=ft.Container(
                            content=ft.Row(
                                controls=[
                                    ft.Container(
                                        content=ft.Text(
                                            machine_name,
                                            theme_style=ft.TextThemeStyle.TITLE_MEDIUM,
                                            weight=ft.FontWeight.BOLD,
                                            max_lines=1,
                                            overflow=ft.TextOverflow.ELLIPSIS,
                                        ),
                                        width=200,
                                    ),
                                    ft.Container(
                                        content=ft.Text(
                                            f"{weight} kg",
                                            theme_style=ft.TextThemeStyle.BODY_MEDIUM,
                                            color=ft.Colors.BLUE_700,
                                            text_align=ft.TextAlign.CENTER,
                                        ),
                                        width=90,
                                    ),
                                    ft.Container(
                                        content=ft.Text(
                                            date,
                                            theme_style=ft.TextThemeStyle.BODY_MEDIUM,
                                            color=ft.Colors.GREY_700,
                                            text_align=ft.TextAlign.RIGHT,
                                        ),
                                        width=100,
                                    ),
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            ),
                            padding=10,
                        )
                    )
                )

        machines = self.db.get_machines()
        options = [ft.DropdownOption(text=m[1], key=str(m[0])) for m in machines]
        
        self.machine_dropdown.options = options
        self.machine_mod_dropdown.options = options
        self.machine_del_dropdown.options = options

        self.machine_dropdown.value = None
        self.latest_usage_text.value = (
            "Selecciona una máquina para consultar su último registro."
        )
        self.weight_input.value = ""
        self.new_machine_input.value = ""
        self.new_name_input.value = ""
        
        if self.page is not None:
            self.update()

    def _on_machine_selected(self, e):
        if not self.machine_dropdown.value:
            self.latest_usage_text.value = (
                "Selecciona una máquina para consultar su último registro."
            )
        else:
            latest_usage = self.db.get_latest_usage(
                int(self.machine_dropdown.value)
            )

            if latest_usage is None:
                self.latest_usage_text.value = (
                    "Esta máquina todavía no tiene registros."
                )
            else:
                weight, usage_date = latest_usage
                self.latest_usage_text.value = (
                    f"Último peso registrado: {weight} kg ({usage_date})"
                )

        if self.page is not None:
            self.update()

    async def _on_export_history_click(self, e):
        history = self.db.get_usage_history()
        workbook = build_usage_history_workbook(history)
        await self.file_picker.save_file(
            dialog_title="Exportar historial a Excel",
            file_name="historial_gimnasio.xlsx",
            file_type=ft.FilePickerFileType.CUSTOM,
            allowed_extensions=["xlsx"],
            src_bytes=workbook,
        )

    def _on_import_history_click(self, e):
        self.page.show_dialog(
            ft.AlertDialog(
                modal=True,
                title=ft.Text("Confirmar importación"),
                content=ft.Text(
                    "La importación reemplazará todas las máquinas "
                    "y registros actuales."
                ),
                actions=[
                    ft.OutlinedButton(
                        "Cancelar",
                        on_click=lambda e: self.page.pop_dialog(),
                        style=self.button_style,
                    ),
                    ft.FilledButton(
                        "Continuar",
                        on_click=self._on_confirm_import_history_click,
                        style=self.button_style,
                    ),
                ],
            )
        )

    async def _on_confirm_import_history_click(self, e):
        self.page.pop_dialog()

        files = await self.file_picker.pick_files(
            dialog_title="Importar historial desde Excel",
            file_type=ft.FilePickerFileType.CUSTOM,
            allowed_extensions=["xlsx"],
            allow_multiple=False,
            with_data=True,
        )

        # Cancelar el selector de archivos no inicia la importación.
        if not files:
            return

        try:
            workbook_bytes = files[0].bytes
            if workbook_bytes is None:
                raise ValueError("No se pudieron leer los datos del archivo.")

            machines, usages = parse_usage_workbook(workbook_bytes)
            self.db.replace_data(machines, usages)
        except (ValueError, sqlite3.Error) as exc:
            result = f"No se pudo importar: {exc}"
        else:
            self.update_data()
            result = (
                f"Importación completada: {len(machines)} máquinas y "
                f"{len(usages)} registros."
            )

        self._show_import_result(result)

    def _show_import_result(self, message):
        self.page.show_dialog(
            ft.AlertDialog(
                modal=True,
                title=ft.Text("Resultado de la importación"),
                content=ft.Text(message),
                actions=[
                    ft.FilledButton(
                        "Aceptar",
                        on_click=lambda e: self.page.pop_dialog(),
                        style=self.button_style,
                    ),
                ],
            )
        )

    # --- EVENT HANDLERS ---
    def _on_log_usage_click(self, e):
        if not self.machine_dropdown.value or not self.weight_input.value:
            return
        try:
            weight = float(self.weight_input.value)
            machine_id = int(self.machine_dropdown.value)
            self.db.log_use(machine_id, weight)
            self.update_data()
        except ValueError:
            pass

    def _on_add_machine_click(self, e):
        name = self.new_machine_input.value.strip()
        if name:
            try:
                self.db.add_machine(name)
                self.update_data()
            except Exception:
                pass

    def _on_rename_machine_click(self, e):
        if self.machine_mod_dropdown.value and self.new_name_input.value.strip():
            machine_id = int(self.machine_mod_dropdown.value)
            new_name = self.new_name_input.value.strip()
            try:
                self.db.rename_machine(machine_id, new_name)
                self.update_data()
            except Exception:
                pass

    def _on_delete_machine_click(self, e):
        if not self.machine_del_dropdown.value:
            return

        machine_id = int(self.machine_del_dropdown.value)

        def confirm_delete(e):
            self.page.pop_dialog()
            self.db.delete_machine(machine_id)
            self.update_data()

        self.page.show_dialog(
            ft.AlertDialog(
                modal=True,
                title=ft.Text("Confirmar eliminación"),
                content=ft.Text(
                    "¿Seguro que quieres eliminar esta máquina? "
                    "También se borrarán sus registros de uso."
                ),
                actions=[
                    ft.OutlinedButton(
                        "Cancelar",
                        on_click=lambda e: self.page.pop_dialog(),
                        style=self.button_style,
                    ),
                    ft.FilledButton(
                        "Eliminar",
                        on_click=confirm_delete,
                        style=self.button_style,
                    ),
                ],
            )
        )
            