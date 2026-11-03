import flet as ft
import sqlite3
from datetime import date

from xlsx_export import build_usage_history_workbook
from xlsx_import import parse_usage_workbook
from ui.texts import COMMON, EXPORT, HISTORY, IMPORT, MACHINES, NAVIGATION, USAGE, ERRORS

class GymAppView(ft.Column):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.expand = True
        self.file_picker = ft.FilePicker()

        # UI components
        self.summary_list = ft.ListView(expand=True, spacing=10, padding=10)
        self.machine_dropdown = ft.Dropdown(
            label=USAGE["machine_label"],
            border=ft.OutlineInputBorder(border_radius=12),
        )
        self.latest_usage_text = ft.Text(
            USAGE["select_machine"],
            italic=True,
        )
        self.weight_input = ft.TextField(
            label=USAGE["weight_label"], 
            width=150, 
            keyboard_type=ft.KeyboardType.NUMBER,
            border=ft.OutlineInputBorder(border_radius=12),
            on_change=self._clear_field_error,
        )
        self.new_machine_input = ft.TextField(
            label=MACHINES["new_name_label"],
            border=ft.OutlineInputBorder(border_radius=12),
            on_change=self._clear_field_error,
        )
        self.machine_mod_dropdown = ft.Dropdown(
            label=MACHINES["select_to_rename"],
            border=ft.OutlineInputBorder(border_radius=12),
        )
        self.new_name_input = ft.TextField(
            label=MACHINES["new_name"],
            border=ft.OutlineInputBorder(border_radius=12),
            on_change=self._clear_field_error,
        )
        self.machine_del_dropdown = ft.Dropdown(
            label=MACHINES["select_to_delete"],
            border=ft.OutlineInputBorder(border_radius=12),
        )

        self.machine_dropdown.col = {"xs": 12, "md": 8}
        self.latest_usage_text.col = {"xs": 12}

        self._build_ui()

    @staticmethod
    def _format_date(iso_date: str) -> str:
            parsed_date = date.fromisoformat(iso_date)
            month_names = (
                "ene", "feb", "mar", "abr", "may", "jun",
                "jul", "ago", "sep", "oct", "nov", "dic",
            )
            return f"{parsed_date.day} {month_names[parsed_date.month - 1]}. {parsed_date.year}"

    def _build_ui(self):
        self.button_style = ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=12),
            padding=20,
            text_style=ft.TextStyle(size=18, weight=ft.FontWeight.W_500),
        )

        self.destructive_button_style = self.button_style.copy(
            color=ft.Colors.ERROR,
            side=ft.BorderSide(color=ft.Colors.ERROR),
        )

        self.destructive_filled_button_style = self.button_style.copy(
            bgcolor=ft.Colors.ERROR,
            color=ft.Colors.ON_ERROR,
        )

        usage_panel = self._build_usage_panel()
        summary_panel = self._build_summary_panel()
        management_panel = self._build_management_panel()

        self._build_navigation(
            usage_panel,
            summary_panel,
            management_panel,
        )

    def _build_summary_panel(self):
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        HISTORY["heading"],
                        theme_style=ft.TextThemeStyle.TITLE_LARGE,
                        weight=ft.FontWeight.BOLD,
                    ),
                    self.summary_list,
                    ft.OutlinedButton(
                        HISTORY["export"],
                        icon=ft.Icons.FILE_DOWNLOAD,
                        on_click=self._on_export_history_click,
                        style=self.button_style,
                        width=280,
                    ),
                    ft.OutlinedButton(
                        HISTORY["import"],
                        icon=ft.Icons.FILE_UPLOAD,
                        on_click=self._on_import_history_click,
                        style=self.button_style,
                        width=280,
                    ),
                ]
            ),
            padding=10,
        )

    def _build_usage_panel(self):
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.ResponsiveRow(
                        run_spacing=15,
                        controls=[
                            ft.Text(
                                USAGE["heading"],
                                theme_style=ft.TextThemeStyle.TITLE_LARGE,
                                weight=ft.FontWeight.BOLD,
                                col={"xs": 12},
                            ),
                            self.machine_dropdown,
                            self.latest_usage_text,
                            ft.Container(
                                content=self.weight_input,
                                width=150,
                                col={"xs": 12},
                            ),
                            ft.FilledButton(
                                USAGE["save"],
                                icon=ft.Icons.SAVE,
                                on_click=self._on_log_usage_click,
                                style=self.button_style,
                                col={"xs": 12, "sm": 6},
                            ),
                        ],
                    )
                ],
                scroll=ft.ScrollMode.AUTO,
            ),
            padding=20,
        )

    def _build_management_panel(self):
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        MACHINES["create_heading"],
                        theme_style=ft.TextThemeStyle.TITLE_LARGE,
                        weight=ft.FontWeight.BOLD,
                    ),
                    self.new_machine_input,
                    ft.FilledButton(
                        MACHINES["create"],
                        icon=ft.Icons.ADD,
                        on_click=self._on_add_machine_click,
                        style=self.button_style,
                    ),
                    ft.Divider(),
                    ft.Text(
                        MACHINES["rename_heading"],
                        theme_style=ft.TextThemeStyle.TITLE_MEDIUM,
                        weight=ft.FontWeight.BOLD,
                    ),
                    self.machine_mod_dropdown,
                    self.new_name_input,
                    ft.FilledButton(
                        MACHINES["rename"],
                        icon=ft.Icons.EDIT,
                        on_click=self._on_rename_machine_click,
                        style=self.button_style,
                    ),
                    ft.Divider(),
                    ft.Text(
                        MACHINES["delete_heading"],
                        theme_style=ft.TextThemeStyle.TITLE_MEDIUM,
                        weight=ft.FontWeight.BOLD,
                    ),
                    self.machine_del_dropdown,
                    ft.OutlinedButton(
                        MACHINES["delete"],
                        icon=ft.Icons.DELETE,
                        on_click=self._on_delete_machine_click,
                        style=self.destructive_button_style,
                    ),
                ],
                spacing=10,
                scroll=ft.ScrollMode.AUTO,
            ),
            padding=20,
        )

    def _build_navigation(
        self,
        usage_panel,
        summary_panel,
        management_panel,
    ):
        self.sections = [
            (NAVIGATION["usage"], usage_panel, ft.Icons.FITNESS_CENTER),
            (NAVIGATION["history"], summary_panel, ft.Icons.HISTORY),
            (NAVIGATION["machines"], management_panel, ft.Icons.SETTINGS),
        ]
        self.selected_section = 0

        self.content_container = ft.Container(
            content=self.sections[self.selected_section][1],
            expand=True,
        )

        self.app_bar = ft.AppBar(
            title=ft.Text(self.sections[self.selected_section][0]),
        )

        self.navigation_bar = ft.NavigationBar(
            selected_index=self.selected_section,
            on_change=self._on_navigation_change,
            destinations=[
                ft.NavigationBarDestination(
                    label=label,
                    icon=icon,
                )
                for label, _, icon in self.sections
            ],
        )

        self.controls = [
            ft.Container(
                content=self.content_container,
                padding=ft.Padding.only(top=24),
                expand=True,
            )
        ]

    def update_data(self):
        results = self.db.get_summary()
        machines = self.db.get_machines()

        self._render_summary(results, machines)
        self._update_machine_options(machines)
        self._reset_inputs()

        if self.page is not None:
            self.update()

    def _render_summary(self, results, machines):
        self.summary_list.controls.clear()

        if not results:
            message = (
                HISTORY["empty_no_machines"]
                if not machines
                else HISTORY["empty_no_usages"]
            )
            self.summary_list.controls.append(
                ft.Container(
                    alignment=ft.Alignment.CENTER,
                    padding=24,
                    content=ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Icon(
                                ft.Icons.HISTORY,
                                color=ft.Colors.PRIMARY,
                            ),
                            ft.Text(
                                message,
                                italic=True,
                                text_align=ft.TextAlign.CENTER,
                            ),
                        ],
                    ),
                )
            )
            return

        grouped_results = {}

        for machine_id, machine_name, weight, usage_date in results:
            if machine_id not in grouped_results:
                grouped_results[machine_id] = {
                    "name": machine_name,
                    "entries": [],
                }

            grouped_results[machine_id]["entries"].append(
                (weight, usage_date)
            )

        for machine in grouped_results.values():
            entries = machine["entries"]
            latest_weight, latest_date = entries[0]

            self.summary_list.controls.append(
                ft.Card(
                    content=ft.ExpansionTile(
                        title=ft.Text(
                            machine["name"],
                            weight=ft.FontWeight.BOLD,
                        ),
                        subtitle=ft.Text(
                            HISTORY["latest"].format(
                                weight=latest_weight,
                                date=self._format_date(latest_date),
                            ),
                            italic=True,
                        ),
                        controls=[
                            ft.ListTile(
                                title=ft.Text(self._format_date(entry_date)),
                                trailing=ft.Text(
                                    HISTORY["weight"].format(
                                        weight=entry_weight
                                    ),
                                    theme_style=ft.TextThemeStyle.TITLE_MEDIUM,
                                    color=ft.Colors.PRIMARY,
                                ),
                            )
                            for entry_weight, entry_date in entries
                        ],
                    ),
                )
            )

    def _update_machine_options(self, machines):
        options = [
            ft.DropdownOption(text=name, key=str(machine_id))
            for machine_id, name in machines
        ]

        self.machine_dropdown.options = options
        self.machine_mod_dropdown.options = options
        self.machine_del_dropdown.options = options

    def _reset_inputs(self):
        self.machine_dropdown.value = None
        self.latest_usage_text.value = USAGE["select_machine"]
        self.weight_input.value = ""
        self.new_machine_input.value = ""
        self.new_name_input.value = ""

    def _clear_field_error(self, e):
        if e.control.error is not None:
            e.control.error = None
            e.control.update()
    
    def _on_machine_selected(self, e):
        if not self.machine_dropdown.value:
            self.latest_usage_text.value = (
                USAGE["select_machine"]
            )
        else:
            latest_usage = self.db.get_latest_usage(
                int(self.machine_dropdown.value)
            )

            if latest_usage is None:
                self.latest_usage_text.value = (
                    USAGE["no_records"]
                )
            else:
                weight, usage_date = latest_usage
                self.latest_usage_text.value = USAGE["latest_weight"].format(
                    weight=weight,
                    date=self._format_date(usage_date),
                )

        if self.page is not None:
            self.update()

    async def _on_export_history_click(self, e):
        history = self.db.get_usage_history()
        workbook = build_usage_history_workbook(history)
        await self.file_picker.save_file(
            dialog_title=EXPORT["dialog_title"],
            file_name=EXPORT["file_name"],
            file_type=ft.FilePickerFileType.CUSTOM,
            allowed_extensions=["xlsx"],
            src_bytes=workbook,
        )

    def _on_import_history_click(self, e):
        self.page.show_dialog(
            ft.AlertDialog(
                modal=True,
                title=ft.Text(IMPORT["confirm_title"]),
                content=ft.Text(
                    IMPORT["confirm_message"]
                ),
                actions=[
                    ft.OutlinedButton(
                        COMMON["cancel"],
                        on_click=lambda e: self.page.pop_dialog(),
                        style=self.button_style,
                    ),
                    ft.FilledButton(
                        IMPORT["continue"],
                        on_click=self._on_confirm_import_history_click,
                        style=self.button_style,
                    ),
                ],
            )
        )

    async def _on_confirm_import_history_click(self, e):
        self.page.pop_dialog()

        files = await self.file_picker.pick_files(
            dialog_title=IMPORT["dialog_title"],
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
                raise ValueError(IMPORT["missing_file_data"])

            machines, usages = parse_usage_workbook(workbook_bytes)
            self.db.replace_data(machines, usages)
        except (ValueError, sqlite3.Error) as exc:
            result = IMPORT["failed"].format(error=exc)
        else:
            self.update_data()
            result = IMPORT["completed"].format(machines=len(machines), usages=len(usages))
        self._show_import_result(result)

    def _show_import_result(self, message):
        self.page.show_dialog(
            ft.AlertDialog(
                modal=True,
                title=ft.Text(IMPORT["result_title"]),
                content=ft.Text(message),
                actions=[
                    ft.FilledButton(
                        COMMON["accept"],
                        on_click=lambda e: self.page.pop_dialog(),
                        style=self.button_style,
                    ),
                ],
            )
        )

    def _on_navigation_change(self, e):
        index = e.control.selected_index
        if index is None or not 0 <= index < len(self.sections):
            return

        self.selected_section = index
        self.content_container.content = self.sections[index][1]
        self.app_bar.title = ft.Text(self.sections[index][0])

        self.update()
        self.app_bar.update()

    def _show_message_dialog(self, title, message):
        self.page.show_dialog(
            ft.AlertDialog(
                modal=True,
                title=ft.Text(title),
                content=ft.Text(message),
                actions=[
                    ft.TextButton(
                        COMMON["accept"],
                        on_click=lambda e: self.page.pop_dialog(),
                    ),
                ],
            )
        )

    def _show_error(self, message):
        self._show_message_dialog(ERRORS["title"], message)

    def _show_import_result(self, message):
        self._show_message_dialog(IMPORT["result_title"], message)

    # --- EVENT HANDLERS ---
    def _on_log_usage_click(self, e):
        if not self.machine_dropdown.value:
            self._show_error(ERRORS["select_machine"])
            return

        if not self.weight_input.value:
            self._show_error(ERRORS["enter_weight"])
            return

        try:
            weight = float(self.weight_input.value)
        except ValueError:
            self._show_error(ERRORS["invalid_weight"])
            return

        machine_id = int(self.machine_dropdown.value)

        try:
            self.db.log_use(machine_id, weight)
        except sqlite3.Error as exc:
            self._show_error(ERRORS["log_usage"].format(error=exc))
            return

        self.update_data()


    def _on_add_machine_click(self, e):
        name = self.new_machine_input.value.strip()
        if not name:
            self.new_machine_input.error = ERRORS["enter_machine_name"]
            self.update()
            return

        try:
            self.db.add_machine(name)
        except sqlite3.IntegrityError:
            self.new_machine_input.error = ERRORS["duplicate_machine"]
            self.update()
            return
        except sqlite3.Error as exc:
            self._show_error(ERRORS["add_machine"].format(error=exc))
            return

        self.update_data()

    def _on_rename_machine_click(self, e):
        if not self.machine_mod_dropdown.value:
           self._show_error(ERRORS["select_machine_to_rename"])
           return

        new_name = self.new_name_input.value.strip()
        if not new_name:
            self._show_error(ERRORS["enter_new_name"])
            return

        machine_id = int(self.machine_mod_dropdown.value)

        try:
            self.db.rename_machine(machine_id, new_name)
        except sqlite3.IntegrityError:
            self._show_error(ERRORS["duplicate_machine"])
            self.update()
            return
        except sqlite3.Error as exc:
            self._show_error(ERRORS["rename_machine"].format(error=exc))
            return

        self.update_data()

    def _on_delete_machine_click(self, e):
        if not self.machine_del_dropdown.value:
            self._show_error(ERRORS["select_machine_to_delete"])
            return

        machine_id = int(self.machine_del_dropdown.value)

        def confirm_delete(e):
            try:
                self.db.delete_machine(machine_id)
            except sqlite3.Error as exc:
                self.page.pop_dialog()
                self._show_error(
                    ERRORS["delete_machine"].format(error=exc)
                )
                return

            self.page.pop_dialog()
            self.update_data()

        self.page.show_dialog(
            ft.AlertDialog(
                modal=True,
                title=ft.Text(MACHINES["confirm_title"]),
                content=ft.Text(MACHINES["confirm_message"]),
                actions=[
                    ft.OutlinedButton(
                        COMMON["cancel"],
                        on_click=lambda e: self.page.pop_dialog(),
                        style=self.button_style
                    ),
                    ft.OutlinedButton(
                        MACHINES["delete"],
                        on_click=confirm_delete,
                        style=self.destructive_button_style,
                    ),
                ],
            )
        )
            