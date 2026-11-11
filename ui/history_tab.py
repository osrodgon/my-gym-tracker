import flet as ft
import inspect
import sqlite3

from xlsx_export import build_usage_history_workbook
from xlsx_import import parse_usage_workbook
from ui import design
from ui.texts import COMMON, EXPORT, HISTORY, IMPORT, MACHINES
from ui.utils import ButtonStyles, _DialogsMixin, format_date, format_weight


class HistoryTab(_DialogsMixin):
    """
    Manages the 'Historial' (history) tab, including export and import.

    Exposes:
      panel  – ft.Container to embed in the navigation scaffold.
      render – call with fresh DB results to redraw the list.
    """

    def __init__(self, db, file_picker: ft.FilePicker, styles: ButtonStyles, on_refresh):
        self._db = db
        self._file_picker = file_picker
        self._styles = styles
        self._on_refresh = on_refresh

        self._summary_list = ft.ListView(
            expand=True,
            spacing=10,
            padding=ft.Padding.only(top=4, bottom=72),
        )

        # Lives in page.floating_action_button, managed by GymAppView.
        self.fab = ft.FloatingActionButton(
            icon=ft.Icons.MORE_VERT,
            tooltip=HISTORY["options_tooltip"],
            on_click=self._show_history_actions,
            shape=ft.RoundedRectangleBorder(radius=design.FAB_RADIUS),
        )

        self.panel = self._build_panel()

    @property
    def _page(self) -> ft.Page:
        return self.panel.page

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def render(self, results, machines) -> None:
        self._summary_list.controls.clear()

        if not results:
            message = (
                HISTORY["empty_no_machines"] if not machines
                else HISTORY["empty_no_usages"]
            )
            self._summary_list.controls.append(
                ft.Container(
                    alignment=ft.Alignment.CENTER,
                    padding=24,
                    content=ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Icon(ft.Icons.HISTORY, color=ft.Colors.PRIMARY),
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

        grouped: dict = {}
        for machine_id, machine_name, weight, usage_date in results:
            if machine_id not in grouped:
                grouped[machine_id] = {"name": machine_name, "entries": [], "id": machine_id}
            grouped[machine_id]["entries"].append((weight, usage_date))

        for machine in grouped.values():
            entries = machine["entries"]
            latest_weight, latest_date = entries[0]
            self._summary_list.controls.append(
                ft.Card(
                    margin=0,
                    shape=ft.RoundedRectangleBorder(radius=design.CARD_RADIUS),
                    content=ft.ExpansionTile(
                        title=ft.Text(machine["name"], weight=ft.FontWeight.BOLD),
                        subtitle=ft.Text(
                            HISTORY["latest"].format(
                                weight=format_weight(latest_weight),
                                date=format_date(latest_date),
                            ),
                            italic=True,
                        ),
                        controls=[
                            ft.ListTile(
                                title=ft.Text(format_date(entry_date)),
                                trailing=ft.Row(
                                    tight=True,
                                    spacing=10,
                                    controls=[
                                        ft.Text(
                                            HISTORY["weight"].format(
                                                weight=format_weight(entry_weight)
                                            ),
                                            theme_style=ft.TextThemeStyle.TITLE_MEDIUM,
                                            color=ft.Colors.PRIMARY,
                                        ),
                                        ft.IconButton(
                                            icon=ft.Icons.DELETE,
                                            icon_color=ft.Colors.ERROR,
                                            tooltip=HISTORY["delete"],
                                            on_click=lambda e, mid=machine["id"], w=entry_weight, d=entry_date: (
                                                self._show_delete_confirmation(mid, w, d)
                                            ),
                                        ),
                                    ],
                                ),
                            )
                            for entry_weight, entry_date in entries
                        ],
                    ),
                )
            )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_panel(self) -> ft.Container:
        return ft.Container(
            expand=True,
            padding=0,
            content=self._summary_list,
        )

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def _show_history_actions(self, e) -> None:
        def close_sheet_then(handler):
            async def on_click(event):
                self._page.pop_dialog()
                result = handler(event)
                if inspect.isawaitable(result):
                    await result
            return on_click

        self._page.show_dialog(
            ft.BottomSheet(
                show_drag_handle=True,
                content=ft.Container(
                    padding=design.SHEET_PADDING,
                    content=ft.Column(
                        tight=True,
                        controls=[
                            ft.ResponsiveRow(
                                run_spacing=12,
                                controls=[
                                    ft.OutlinedButton(
                                        HISTORY["export"],
                                        icon=ft.Icons.FILE_DOWNLOAD,
                                        on_click=close_sheet_then(
                                            self._on_export_history_click
                                        ),
                                        style=self._styles.default,
                                    ),
                                    ft.OutlinedButton(
                                        HISTORY["import"],
                                        icon=ft.Icons.FILE_UPLOAD,
                                        on_click=close_sheet_then(
                                            self._on_import_history_click
                                        ),
                                        style=self._styles.default,
                                    ),
                                ],
                            ),
                        ],
                    ),
                ),
            )
        )



    def _show_delete_confirmation(self, machine_id: int, weight: float, date: str) -> None:
        """Show confirmation dialog and delete the specific usage record."""
        def _confirm_delete(e) -> None:
            self._db.delete_usage_by_machine_weight_date(machine_id, weight, date)
            # Refresh the data after deletion
            self._on_refresh()
            self._page.pop_dialog()

        self._page.show_dialog(
            ft.AlertDialog(
                modal=True,
                title=ft.Text(HISTORY["delete_title"]),
                content=ft.Text(HISTORY["delete_record"]),
                actions=[
                    ft.TextButton(
                        COMMON["cancel"],
                        on_click=lambda e: self._page.pop_dialog(),
                        style=self._styles.dialog,
                    ),
                    ft.TextButton(
                        MACHINES["delete"],
                        on_click=_confirm_delete,
                        style=self._styles.dialog_destructive,
                    ),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )
        )


    async def _on_export_history_click(self, e) -> None:
        history = self._db.get_usage_history()
        workbook = build_usage_history_workbook(history)
        await self._file_picker.save_file(
            dialog_title=EXPORT["dialog_title"],
            file_name=EXPORT["file_name"],
            file_type=ft.FilePickerFileType.CUSTOM,
            allowed_extensions=["xlsx"],
            src_bytes=workbook,
        )

    def _on_import_history_click(self, e) -> None:
        self._page.show_dialog(
            ft.AlertDialog(
                modal=True,
                title=ft.Text(IMPORT["confirm_title"]),
                content=ft.Text(IMPORT["confirm_message"]),
                actions=[
                    ft.TextButton(
                        COMMON["cancel"],
                        on_click=lambda e: self._page.pop_dialog(),
                        style=self._styles.dialog,
                    ),
                    ft.TextButton(
                        IMPORT["continue"],
                        on_click=self._on_confirm_import_history_click,
                        style=self._styles.dialog_destructive,
                    ),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )
        )

    async def _on_confirm_import_history_click(self, e) -> None:
        self._page.pop_dialog()

        files = await self._file_picker.pick_files(
            dialog_title=IMPORT["dialog_title"],
            file_type=ft.FilePickerFileType.CUSTOM,
            allowed_extensions=["xlsx"],
            allow_multiple=False,
            with_data=True,
        )

        # Cancelling the file picker aborts the import.
        if not files:
            return

        try:
            workbook_bytes = files[0].bytes
            if workbook_bytes is None:
                raise ValueError(IMPORT["missing_file_data"])
            machines, usages = parse_usage_workbook(workbook_bytes)
            self._db.replace_data(machines, usages)
        except (ValueError, sqlite3.Error) as exc:
            result = IMPORT["failed"].format(error=exc)
        else:
            self._on_refresh()
            result = IMPORT["completed"].format(
                machines=len(machines), usages=len(usages)
            )

        self._show_message_dialog(IMPORT["result_title"], result)
