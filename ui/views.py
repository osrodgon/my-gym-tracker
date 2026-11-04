import flet as ft
import sqlite3
from datetime import date
import re
import unicodedata
from pathlib import Path

from xlsx_export import build_usage_history_workbook
from xlsx_import import parse_usage_workbook
from ui.texts import COMMON, EXPORT, HISTORY, IMPORT, MACHINES, NAVIGATION, USAGE, ERRORS, DATE

class GymAppView(ft.Column):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.expand = True
        self.horizontal_alignment = ft.CrossAxisAlignment.STRETCH
        self.file_picker = ft.FilePicker()

        # UI components
        self.summary_list = ft.ListView(
            expand=True, 
            spacing=10,
            padding=ft.Padding.only(top=4, bottom=4),
        )
        self.machine_dropdown = ft.Dropdown(
            label=USAGE["machine_label"],
            border=ft.OutlineInputBorder(border_radius=20),
            on_select=self._on_machine_selected,
            expand=True,
        )
        self.latest_usage_text = ft.Text(
            USAGE["select_machine"],
            italic=True,
        )
        self.weight_input = ft.TextField(
            label=USAGE["weight_label"], 
            width=150, 
            keyboard_type=ft.KeyboardType.NUMBER,
            border=ft.OutlineInputBorder(border_radius=20),
            on_change=self._clear_field_error,
        )
        self.machine_list = ft.ListView(
            expand=True,
            spacing=8,
            padding=ft.Padding.only(top=4, bottom=4),
        )
        self.machine_dropdown.col = {"xs": 12}
        self.latest_usage_text.col = {"xs": 12}
        self.machine_image = ft.Image(
            fit=ft.BoxFit.CONTAIN,
            visible=False,
            src="",
            expand=True,
        )

        self._build_ui()

    @staticmethod
    def _format_date(iso_date: str) -> str:
            parsed_date = date.fromisoformat(iso_date)
            month_names = DATE["months_short"]
            return f"{parsed_date.day} {month_names[parsed_date.month - 1]}. {parsed_date.year}"

    def _build_ui(self):
        self.button_style = ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=24),
            padding=24,
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
            expand=True,
            padding=0,
            content=ft.Stack(
                expand=True,
                controls=[
                    self.summary_list,
                    ft.Container(
                        content=ft.FloatingActionButton(
                            icon=ft.Icons.MORE_VERT,
                            tooltip="Opciones del histórico",
                            on_click=self._show_history_actions,
                            mini=True,
                            shape=ft.CircleBorder(),
                        ),
                        right=10,
                        bottom=10,
                    ),
                ],
            ),
        )

    def _build_usage_panel(self):
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.ResponsiveRow(
                        run_spacing=15,
                        controls=[
                            self.machine_dropdown,
                            self.latest_usage_text,
                            ft.Container(
                                content=self.weight_input,
                                width=150,
                                col={"xs": 12},
                            ),
                            ft.FilledButton(
                                USAGE["save"],
                                icon=ft.Icons.CHECK,
                                on_click=self._on_log_usage_click,
                                style=self.button_style,
                                col={"xs": 12, "sm": 6},
                            ),
                            ft.Container(
                                content=self.machine_image,
                                height=400,
                                alignment=ft.Alignment.CENTER,
                                col={"xs": 12},
                            ),
                        ],
                    )
                ],
                scroll=ft.ScrollMode.AUTO,
            ),
            padding=0,
        )

    def _show_history_actions(self, e):
        def close_sheet_then(handler):
            def on_click(event):
                self.page.pop_dialog()
                handler(event)

            return on_click

        self.page.show_dialog(
            ft.BottomSheet(
                show_drag_handle=True,
                content=ft.Container(
                    padding=16,
                    content=ft.Column(
                        tight=True,
                        controls=[
                            ft.ResponsiveRow(
                                controls=[
                                    ft.OutlinedButton(
                                        HISTORY["export"],
                                        icon=ft.Icons.FILE_DOWNLOAD,
                                        on_click=close_sheet_then(
                                            self._on_export_history_click
                                        ),
                                        style=self.button_style,
                                    ),
                                    ft.OutlinedButton(
                                        HISTORY["import"],
                                        icon=ft.Icons.FILE_UPLOAD,
                                        on_click=close_sheet_then(
                                            self._on_import_history_click
                                        ),
                                        style=self.button_style,
                                    ),
                                ],
                                run_spacing=12,
                            ),
                        ],
                    ),
                ),
            )
        )

    def _build_management_panel(self):
        return ft.Container(
            expand=True,
            padding=0,
            content=ft.Column(
                expand=True,
                spacing=12,
                controls=[
                    self.machine_list,
                    ft.ResponsiveRow(
                        controls=[
                            ft.FilledButton(
                                MACHINES["add_button"],
                                icon=ft.Icons.ADD,
                                on_click=self._on_add_machine_click,
                                style=self.button_style,
                                col={"xs": 12},
                            ),
                        ],
                    ),
                ],
            ),
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
                padding=ft.Padding.only(top=16),
                expand=True,
            )
        ]

    def _update_machine_image(self, machine_name):
        normalized = unicodedata.normalize("NFKD", machine_name)
        slug = re.sub(
            r"[^a-z0-9]+",
            "-",
            normalized.encode("ascii", "ignore").decode().lower(),
        ).strip("-")

        filename = f"{slug}.svg"
        file_path = (
            Path(__file__).resolve().parent.parent
            / "assets"
            / "machines"
            / filename
        )

        self.machine_image.visible = file_path.is_file()
        if self.machine_image.visible:
            self.machine_image.src = f"machines/{filename}"
            is_dark = (
                self.page.theme_mode == ft.ThemeMode.DARK
                or (
                    self.page.theme_mode == ft.ThemeMode.SYSTEM
                    and self.page.platform_brightness == ft.Brightness.DARK
                )
            )
            self.machine_image.color = (
                ft.Colors.WHITE if is_dark else ft.Colors.BLACK
            )

    def _on_platform_brightness_change(self, e):
        selected_key = self.machine_dropdown.value
        if not selected_key:
            return

        option = next(
            (
                option
                for option in self.machine_dropdown.options
                if option.key == selected_key
            ),
            None,
        )
        if option is not None:
            self._update_machine_image(option.text)
            self.update()

    def update_data(self):
        results = self.db.get_summary()
        machines = self.db.get_machines()

        self._render_summary(results, machines)
        self._render_machine_list(machines)
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
                    margin=0,
                    shape=ft.RoundedRectangleBorder(radius=20),
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

    def _render_machine_list(self, machines):
        if not machines:
            self.machine_list.controls = [
                ft.Container(
                    padding=12,
                    content=ft.Text(
                        MACHINES["empty_list"],
                        italic=True,
                        text_align=ft.TextAlign.CENTER,
                    ),
                )
            ]
            return

        self.machine_list.controls = [
            ft.Card(
                margin=0,
                shape=ft.RoundedRectangleBorder(radius=20),
                content=ft.ListTile(
                    leading=ft.Icon(
                        ft.Icons.FITNESS_CENTER,
                        color=ft.Colors.PRIMARY,
                    ),
                    title=ft.Text(machine_name),
                    trailing=ft.Row(
                        tight=True,
                        controls=[
                            ft.IconButton(
                                icon=ft.Icons.EDIT,
                                tooltip=MACHINES["edit_tooltip"],
                                on_click=lambda e, mid=machine_id, name=machine_name: (
                                    self._show_machine_dialog(mid, name)
                                ),
                            ),
                            ft.IconButton(
                                icon=ft.Icons.DELETE,
                                tooltip=MACHINES["delete_tooltip"],
                                icon_color=ft.Colors.ERROR,
                                on_click=lambda e, mid=machine_id: (
                                    self._on_delete_machine_click(mid)
                                ),
                            ),
                        ],
                    ),
                ),
            )
            for machine_id, machine_name in machines
        ]

    def _update_machine_options(self, machines):
        self.machine_dropdown.options = [
            ft.DropdownOption(text=name, key=str(machine_id))
            for machine_id, name in machines
        ]

    def _reset_inputs(self):
        self.machine_dropdown.value = None
        self.latest_usage_text.value = USAGE["select_machine"]
        self.weight_input.value = ""
        self.weight_input.error = None

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
            machine_name = self.machine_dropdown.options[
                next(
                    i for i, option in enumerate(self.machine_dropdown.options)
                    if option.key == self.machine_dropdown.value
                )
            ].text
            self._update_machine_image(machine_name)
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
                        style=self.destructive_filled_button_style,
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

        self.update()

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

    def _show_snackbar(self, message):
        self.page.show_dialog(
            ft.SnackBar(
                ft.Text(message),
                duration=2000,
                dismiss_direction=ft.DismissDirection.HORIZONTAL,
            )
        )

    def _show_error(self, message):
        self._show_message_dialog(ERRORS["title"], message)

    def _show_import_result(self, message):
        self._show_message_dialog(IMPORT["result_title"], message)

    # --- EVENT HANDLERS ---
    def _on_log_usage_click(self, e):
        if not self.machine_dropdown.value:
            self._show_snackbar(ERRORS["select_machine"])
            return

        if not self.weight_input.value:
            self._show_snackbar(ERRORS["enter_weight"])
            return

        try:
            weight = float(self.weight_input.value)
        except ValueError:
            self._show_snackbar(ERRORS["invalid_weight"])
            return

        machine_id = int(self.machine_dropdown.value)

        try:
            self.db.log_use(machine_id, weight)
        except sqlite3.Error as exc:
            self._show_snackbar(ERRORS["log_usage"].format(error=exc))
            return

        self.update_data()


    def _on_add_machine_click(self, e):
        self._show_machine_dialog()

    def _show_machine_dialog(self, machine_id=None, machine_name=""):
        is_new = machine_id is None

        name_input = ft.TextField(
            label=(
                MACHINES["new_name_label"]
                if is_new
                else MACHINES["new_name"]
            ),
            value=machine_name,
            border=ft.OutlineInputBorder(border_radius=20),
            on_change=self._clear_field_error,
        )

        def save_machine(e):
            name = (name_input.value or "").strip()
            if not name:
                error_key = (
                    ERRORS["enter_machine_name"]
                    if is_new
                    else ERRORS["enter_new_name"]
                )
                name_input.error = error_key
                name_input.update()
                return

            try:
                if is_new:
                    self.db.add_machine(name)
                else:
                    self.db.rename_machine(machine_id, name)
            except sqlite3.IntegrityError:
                name_input.error = ERRORS["duplicate_machine"]
                name_input.update()
                return
            except sqlite3.Error as exc:
                self.page.pop_dialog()
                error_key = (
                    ERRORS["add_machine"]
                    if is_new
                    else ERRORS["rename_machine"]
                )
                self._show_error(error_key.format(error=exc))
                return

            self.page.pop_dialog()
            self.update_data()

        self.page.show_dialog(
            ft.AlertDialog(
                modal=True,
                title=ft.Text(
                    MACHINES["create_heading"]
                    if is_new
                    else MACHINES["rename_heading"]
                ),
                content=name_input,
                actions=[
                    ft.OutlinedButton(
                        COMMON["cancel"],
                        on_click=lambda e: self.page.pop_dialog(),
                        style=self.button_style,
                    ),
                    ft.FilledButton(
                        MACHINES["create"]
                        if is_new
                        else MACHINES["rename"],
                        on_click=save_machine,
                        style=self.button_style,
                    ),
                ],
            )
        )

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

    def _on_delete_machine_click(self, machine_id):
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
                        style=self.button_style,
                    ),
                    ft.OutlinedButton(
                        MACHINES["delete"],
                        on_click=confirm_delete,
                        style=self.destructive_button_style,
                    ),
                ],
            )
        )
                