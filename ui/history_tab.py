import flet as ft
import inspect
import sqlite3

from xlsx_export import build_usage_history_workbook
from xlsx_import import parse_usage_workbook
from ui import design
from ui.texts import COMMON, ERRORS, EXPORT, HISTORY, IMPORT, MACHINES
from ui.utils import (
    ButtonStyles,
    _DialogsMixin,
    format_date,
    format_series,
    format_weight,
)


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

        # Machine ids whose ExpansionTile stays open across a re-render. Flet
        # recreates the tiles from scratch on every refresh, so the expansion
        # state has to be kept here.
        self._expanded_machines: set[int] = set()

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
            self._expanded_machines.clear()
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
        for (
            usage_id,
            machine_id,
            machine_name,
            weight,
            reps,
            rpe,
            usage_date,
        ) in results:
            if machine_id not in grouped:
                grouped[machine_id] = {
                    "name": machine_name,
                    "entries": [],
                    "id": machine_id,
                }
            grouped[machine_id]["entries"].append(
                (usage_id, weight, reps, rpe, usage_date)
            )

        # A deleted machine cannot stay expanded, so ids that are no longer in
        # the list are dropped instead of piling up.
        self._expanded_machines &= set(grouped)

        for machine_id, machine in grouped.items():
            entries = machine["entries"]
            _latest_id, latest_weight, latest_reps, _latest_rpe, latest_date = (
                entries[0]
            )
            # Heaviest set, more reps breaking a tie. Computed from the rows
            # already loaded, so the badge costs no extra query.
            record = max(entries, key=lambda entry: (entry[1], entry[2]))
            self._summary_list.controls.append(
                ft.Card(
                    margin=0,
                    shape=ft.RoundedRectangleBorder(radius=design.CARD_RADIUS),
                    content=ft.ExpansionTile(
                        title=ft.Row(
                            spacing=design.dp(8),
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            controls=[
                                # The name takes the free width and truncates
                                # instead of pushing the badge off the row.
                                ft.Text(
                                    machine["name"],
                                    weight=ft.FontWeight.BOLD,
                                    max_lines=1,
                                    no_wrap=True,
                                    overflow=ft.TextOverflow.ELLIPSIS,
                                    expand=True,
                                ),
                                self._build_pr_badge(record[1]),
                            ],
                        ),
                        expanded=machine_id in self._expanded_machines,
                        on_change=lambda e, mid=machine_id: (
                            self._on_tile_change(mid, e)
                        ),
                        subtitle=ft.Text(
                            HISTORY["latest"].format(
                                value=format_series(latest_weight, latest_reps),
                                date=format_date(latest_date),
                            ),
                            italic=True,
                        ),
                        controls=[
                            ft.ListTile(
                                title=ft.Text(format_date(entry_date)),
                                subtitle=(
                                    ft.Text(
                                        HISTORY["rpe"].format(value=entry_rpe),
                                        italic=True,
                                    )
                                    if entry_rpe is not None
                                    else None
                                ),
                                trailing=ft.Row(
                                    tight=True,
                                    spacing=10,
                                    controls=[
                                        ft.Text(
                                            format_series(entry_weight, entry_reps),
                                            theme_style=ft.TextThemeStyle.TITLE_MEDIUM,
                                            color=ft.Colors.PRIMARY,
                                        ),
                                        ft.IconButton(
                                            icon=ft.Icons.DELETE,
                                            icon_color=ft.Colors.ERROR,
                                            tooltip=HISTORY["delete"],
                                            on_click=lambda e, uid=entry_id: (
                                                self._show_delete_confirmation(uid)
                                            ),
                                        ),
                                    ],
                                ),
                            )
                            for entry_id, entry_weight, entry_reps, entry_rpe, entry_date
                            in entries
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

    def _build_pr_badge(self, weight: float) -> ft.Container:
        """Badge next to the machine name marking its heaviest set."""
        return ft.Container(
            bgcolor=ft.Colors.PRIMARY_CONTAINER,
            border_radius=design.BADGE_RADIUS,
            padding=design.BADGE_PADDING,
            content=ft.Text(
                HISTORY["personal_record"].format(
                    value=f"{format_weight(weight)} kg"
                ),
                color=ft.Colors.ON_PRIMARY_CONTAINER,
                size=design.FONT_BODY_SMALL,
            ),
        )

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def _on_tile_change(self, machine_id: int, e) -> None:
        """Remember a tile's state so the next render can restore it."""
        expanded = e.data if isinstance(e.data, bool) else str(e.data) == "true"
        if expanded:
            self._expanded_machines.add(machine_id)
        else:
            self._expanded_machines.discard(machine_id)

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



    def _show_delete_confirmation(self, usage_id: int) -> None:
        """Show confirmation dialog and delete the specific usage record."""
        def _confirm_delete(e) -> None:
            try:
                self._db.delete_usage(usage_id)
            except sqlite3.Error as exc:
                self._page.pop_dialog()
                self._show_error(ERRORS["delete_usage"].format(error=exc))
                return

            self._page.pop_dialog()
            # Refresh the data after deletion
            self._on_refresh()

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
        # `save_file()` returns the chosen path, or None when the user closes
        # the dialog without saving.
        path = await self._file_picker.save_file(
            dialog_title=EXPORT["dialog_title"],
            file_name=EXPORT["file_name"],
            file_type=ft.FilePickerFileType.CUSTOM,
            allowed_extensions=["xlsx"],
            src_bytes=workbook,
        )
        self._show_snackbar(EXPORT["saved"] if path else EXPORT["cancelled"])

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
