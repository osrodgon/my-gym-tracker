import flet as ft
import sqlite3

from machine_images import MACHINE_IMAGES, get_machine_image_key, get_machine_image_svg
from ui.texts import COMMON, MACHINES, ERRORS
from ui.utils import ButtonStyles, _DialogsMixin, is_dark_theme


class MachinesTab(_DialogsMixin):
    """
    Manages the 'Máquinas' (machine management) tab.

    Exposes:
      panel  – ft.Container to embed in the navigation scaffold.
      render – call with fresh machine list to redraw.
    """

    def __init__(self, db, styles: ButtonStyles, on_refresh):
        self._db = db
        self._styles = styles
        self._on_refresh = on_refresh

        self._machine_list = ft.ListView(
            expand=True,
            spacing=8,
            padding=ft.Padding.only(top=4, bottom=56),
        )

        # Lives in page.floating_action_button, managed by GymAppView.
        self.fab = ft.FloatingActionButton(
            icon=ft.Icons.ADD,
            tooltip=MACHINES["add_button"],
            on_click=self._on_add_machine_click,
            mini=True,
            shape=ft.CircleBorder(),
        )

        self.panel = self._build_panel()

    @property
    def _page(self) -> ft.Page:
        return self.panel.page

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def render(self, machines) -> None:
        if not machines:
            self._machine_list.controls = [
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

        self._machine_list.controls = [
            ft.Card(
                margin=0,
                shape=ft.RoundedRectangleBorder(radius=20),
                content=ft.ListTile(
                    horizontal_spacing=8,
                    content_padding=ft.Padding.only(left=16, right=4),
                    leading=ft.Icon(ft.Icons.FITNESS_CENTER, color=ft.Colors.PRIMARY),
                    title=ft.Text(machine_name),
                    trailing=ft.Row(
                        tight=True,
                        spacing=0,
                        controls=[
                            ft.IconButton(
                                icon=ft.Icons.EDIT,
                                tooltip=MACHINES["edit_tooltip"],
                                on_click=lambda e, mid=machine_id, name=machine_name, key=image_key: (
                                    self._show_machine_dialog(mid, name, key)
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
            for machine_id, machine_name, image_key in machines
        ]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_panel(self) -> ft.Container:
        return ft.Container(
            expand=True,
            padding=0,
            content=self._machine_list,
        )

    def _is_dark_theme(self) -> bool:
        return is_dark_theme(self._page)

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def _on_add_machine_click(self, e) -> None:
        self._show_machine_dialog()

    def _show_machine_dialog(
        self,
        machine_id=None,
        machine_name: str = "",
        current_image_key: str | None = None,
    ) -> None:
        is_new = machine_id is None
        automatic_image_key = get_machine_image_key(machine_name)
        initial_image_key = (
            automatic_image_key or current_image_key
            if is_new
            else current_image_key
        )

        name_input = ft.TextField(
            label=MACHINES["new_name_label"] if is_new else MACHINES["new_name"],
            value=machine_name,
            text_style=ft.TextStyle(size=16),
            label_style=ft.TextStyle(size=14),
            border=ft.OutlineInputBorder(border_radius=20),
            expand=True,
        )

        image_dropdown = ft.Dropdown(
            label=MACHINES["image_label"],
            value=initial_image_key or "none",
            border=ft.OutlineInputBorder(border_radius=20),
            text_size=16,
            label_style=ft.TextStyle(size=14),
            options=[
                ft.DropdownOption(key="none", text=MACHINES["no_image"]),
                *[
                    ft.DropdownOption(
                        key=key,
                        text=key.replace("-", " ").title(),
                    )
                    for key in MACHINE_IMAGES
                ],
            ],
            on_select=lambda e: _update_image_preview(),
            expand=True,
        )

        image_preview = ft.Image(
        src=get_machine_image_svg(initial_image_key, dark=self._is_dark_theme()),
        width=160,
        height=120,
        fit=ft.BoxFit.CONTAIN,
    )
        image_preview_container = ft.Container(
            content=image_preview,
            width=200,
            height=140,
            alignment=ft.Alignment.CENTER,
        )
        preview_row = ft.Row(
            alignment=ft.MainAxisAlignment.CENTER,
            controls=[image_preview_container],
            visible=initial_image_key is not None,
        )

        def _update_image_preview() -> None:
            image_preview.color = (
                ft.Colors.WHITE if self._is_dark_theme() else ft.Colors.BLACK
            )
            selected_key = image_dropdown.value
            has_image = selected_key is not None and selected_key != "none"
            image_preview.src = get_machine_image_svg(
                selected_key if has_image else None,
                dark=self._is_dark_theme(),
            )
            preview_row.visible = has_image
            preview_row.update()

        def _handle_name_change(e) -> None:
            nonlocal automatic_image_key
            if e.control.error is not None:
                e.control.error = None
                e.control.update()

            new_key = get_machine_image_key(name_input.value or "")
            if new_key is not None:
                automatic_image_key = new_key
                image_dropdown.value = new_key
                _update_image_preview()
            elif image_dropdown.value == automatic_image_key:
                automatic_image_key = None
                image_dropdown.value = "none"
                _update_image_preview()

        name_input.on_change = _handle_name_change

        def _save_machine(e) -> None:
            name = (name_input.value or "").strip()
            if not name:
                name_input.error = ERRORS["enter_machine_name"]
                name_input.update()
                return

            selected_key = image_dropdown.value
            image_key = None if selected_key == "none" else selected_key

            try:
                if is_new:
                    self._db.add_machine(name, image_key)
                else:
                    self._db.rename_machine(machine_id, name, image_key)
            except sqlite3.IntegrityError:
                name_input.error = ERRORS["duplicate_machine"]
                name_input.update()
                return
            except sqlite3.Error as exc:
                self._page.pop_dialog()
                error_key = (
                    ERRORS["add_machine"] if is_new else ERRORS["rename_machine"]
                )
                self._show_error(error_key.format(error=exc))
                return

            self._page.pop_dialog()
            self._on_refresh()

        self._page.show_dialog(
            ft.AlertDialog(
                modal=True,
                title=ft.Text(
                    MACHINES["create_heading"] if is_new else MACHINES["rename_heading"]
                ),
                content=ft.Column(
                    tight=True,
                    horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                    controls=[
                        ft.Row(controls=[name_input]),
                        ft.Row(controls=[image_dropdown]),
                        preview_row,
                    ],
                ),
                actions=[
                    ft.OutlinedButton(
                        COMMON["cancel"],
                        on_click=lambda e: self._page.pop_dialog(),
                        style=self._styles.dialog,
                    ),
                    ft.FilledButton(
                        MACHINES["create"] if is_new else MACHINES["rename"],
                        on_click=_save_machine,
                        style=self._styles.dialog,
                    ),
                ],
            )
        )

    def _on_delete_machine_click(self, machine_id: int) -> None:
        def _confirm_delete(e) -> None:
            try:
                self._db.delete_machine(machine_id)
            except sqlite3.Error as exc:
                self._page.pop_dialog()
                self._show_error(ERRORS["delete_machine"].format(error=exc))
                return

            self._page.pop_dialog()
            self._on_refresh()

        self._page.show_dialog(
            ft.AlertDialog(
                modal=True,
                title=ft.Text(MACHINES["confirm_title"]),
                content=ft.Text(MACHINES["confirm_message"]),
                actions=[
                    ft.OutlinedButton(
                        COMMON["cancel"],
                        on_click=lambda e: self._page.pop_dialog(),
                        style=self._styles.dialog,
                    ),
                    ft.OutlinedButton(
                        MACHINES["delete"],
                        on_click=_confirm_delete,
                        style=self._styles.dialog_destructive,
                    ),
                ],
            )
        )
