import flet as ft
import sqlite3

from machine_images import (
    MACHINE_IMAGES,
    get_machine_image_key,
    get_machine_image,
    get_no_selection_image,
    get_placeholder_image,
)
from ui import design
from ui.texts import COMMON, MACHINES, ERRORS
from ui.utils import (
    ButtonStyles,
    _DialogsMixin,
    create_dropdown,
    create_text_field,
)

_SWIPE_VELOCITY = 400
"""px/s a horizontal drag must reach to count as an image swipe."""


class MachinesTab(_DialogsMixin):
    """
    Manages the 'Máquinas' (machine management) tab.

    Exposes:
      panel  – ft.Container to embed in the navigation scaffold.
      render – call with fresh machine list to redraw.
    """

    def __init__(
        self,
        db,
        styles: ButtonStyles,
        on_refresh,
        on_edit_mode_changed=None,
    ):
        self._db = db
        self._styles = styles
        self._on_refresh = on_refresh
        self._on_edit_mode_changed = on_edit_mode_changed
        self._form_open = False

        self._machine_list = ft.ListView(
            expand=True,
            spacing=8,
            padding=ft.Padding.only(top=4, bottom=72),
        )
        self._list_view = ft.Container(expand=True, content=self._machine_list)

        # Lives in page.floating_action_button, managed by GymAppView.
        self.fab = ft.FloatingActionButton(
            icon=ft.Icons.ADD,
            tooltip=MACHINES["add_button"],
            on_click=self._on_add_machine_click,
            shape=ft.RoundedRectangleBorder(radius=design.FAB_RADIUS),
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
                shape=ft.RoundedRectangleBorder(radius=design.CARD_RADIUS),
                content=ft.ListTile(
                    horizontal_spacing=8,
                    content_padding=ft.Padding.only(left=16, right=4),
                    leading=ft.Image(
                        src=get_placeholder_image(),
                        width=design.LIST_ICON_SIZE,
                        height=design.LIST_ICON_SIZE,
                        fit=ft.BoxFit.CONTAIN,
                        color=ft.Colors.PRIMARY,
                    ),
                    title=ft.Text(machine_name),
                    trailing=ft.Row(
                        tight=True,
                        spacing=0,
                        controls=[
                            ft.IconButton(
                                icon=ft.Icons.EDIT,
                                tooltip=MACHINES["edit_tooltip"],
                                on_click=lambda e, mid=machine_id, name=machine_name, key=image_key: (
                                    self._open_machine_form(mid, name, key)
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
            content=self._list_view,
        )

    def reset(self) -> None:
        """Show the list again, discarding an open machine form."""
        if self._form_open:
            self._close_machine_form()

    @property
    def is_editing(self) -> bool:
        """True while the create/rename form replaces the list."""
        return self._form_open

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def _on_add_machine_click(self, e) -> None:
        self._open_machine_form()

    def _open_machine_form(
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

        name_input = create_text_field(
            label=MACHINES["new_name_label"] if is_new else MACHINES["new_name"],
            value=machine_name,
        )

        image_dropdown = create_dropdown(
            label=MACHINES["image_label"],
            value=initial_image_key or "none",
            options=[
                ft.DropdownOption(
                    key="none",
                    text=MACHINES["no_image"],
                    style=self._styles.menu_item,
                ),
                *[
                    ft.DropdownOption(
                        key=key,
                        text=key.replace("-", " ").title(),
                        style=self._styles.menu_item,
                    )
                    for key in MACHINE_IMAGES
                ],
            ],
            on_select=lambda e: _update_image_preview(),
            expand=True,
        )

        image_preview = ft.Image(
            src="",
            fit=ft.BoxFit.CONTAIN,
            expand=True,
            opacity=design.IMAGE_OPACITY,
        )
        # Same tonal card as the Registrar image: it takes the height the fields
        # and the form actions leave free, and shrinks with them when the Android
        # keyboard opens.
        image_preview_container = ft.Container(
            expand=True,
            alignment=ft.Alignment.CENTER,
            bgcolor=design.SURFACE_PANEL_COLOR,
            border_radius=design.IMAGE_CARD_RADIUS,
            padding=design.IMAGE_CARD_PADDING,
            content=image_preview,
        )

        # --- Card sizing: measure the fixed rows once, then fix the height. ---

        def _apply_preview(selected_key: str | None) -> None:
            # `ft.Image.color` blends every pixel with that colour and would
            # flatten the drawing into a silhouette, so it is never set here.
            if selected_key is None:
                # The generic drawing is tightly framed: scale it down so it
                # matches the weight of the machine illustrations.
                image_preview.scale = design.NO_SELECTION_IMAGE_SCALE
                image_preview.src = get_no_selection_image()
                return

            image_preview.scale = None
            image_preview.src = get_machine_image(selected_key)

        def _update_image_preview() -> None:
            selected_key = image_dropdown.value
            has_image = selected_key is not None and selected_key != "none"
            _apply_preview(selected_key if has_image else None)
            image_preview_container.update()

        def _on_swipe_image(e) -> None:
            """Move to the previous/next image of the catalog, wrapping around."""
            velocity = e.primary_velocity or 0
            if abs(velocity) < _SWIPE_VELOCITY:
                return

            options = ["none", *MACHINE_IMAGES]
            current = image_dropdown.value
            index = options.index(current) if current in options else 0

            if velocity < 0:
                index = (index + 1) % len(options)
            else:
                index = (index - 1) % len(options)

            image_dropdown.value = options[index]
            _update_image_preview()

        _apply_preview(
            initial_image_key if initial_image_key is not None else None
        )

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
                error_key = (
                    ERRORS["add_machine"] if is_new else ERRORS["rename_machine"]
                )
                self._show_error(error_key.format(error=exc))
                return

            self._close_machine_form()
            self._on_refresh()

        heading = (
            MACHINES["create_heading"] if is_new else MACHINES["rename_heading"]
        )
        # No scroll on the field block: the preview card is the flexible child
        # and absorbs the free height, exactly like the Registrar image card.
        fields = ft.Column(
            expand=True,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            spacing=16,
            controls=[
                ft.Text(
                    heading,
                    size=design.FONT_TITLE_LARGE,
                    weight=ft.FontWeight.W_500,
                ),
                name_input,
                ft.Row(controls=[image_dropdown]),
                ft.GestureDetector(
                    expand=True,
                    on_horizontal_drag_end=_on_swipe_image,
                    content=image_preview_container,
                ),
            ],
        )
        form = ft.Column(
            expand=True,
            spacing=16,
            controls=[
                fields,
                ft.ResponsiveRow(
                    run_spacing=8,
                    controls=[
                        ft.OutlinedButton(
                            COMMON["cancel"],
                            on_click=lambda e: self._close_machine_form(),
                            style=self._styles.primary,
                            col={"xs": 12, "sm": 6},
                        ),
                        ft.FilledButton(
                            MACHINES["create"] if is_new else MACHINES["rename"],
                            on_click=_save_machine,
                            style=self._styles.primary,
                            col={"xs": 12, "sm": 6},
                        ),
                    ],
                ),
            ],
        )

        self.panel.content = ft.Container(
            expand=True,
            padding=ft.Padding.only(bottom=design.dp(8)),
            content=form,
        )
        self._form_open = True
        if self._on_edit_mode_changed is not None:
            self._on_edit_mode_changed(True)
        elif self.panel.page is not None:
            self.panel.update()

    def _close_machine_form(self) -> None:
        if not self._form_open:
            return
        self._form_open = False
        self.panel.content = self._list_view
        if self._on_edit_mode_changed is not None:
            self._on_edit_mode_changed(False)
        elif self.panel.page is not None:
            self.panel.update()

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
                title=ft.Text(MACHINES["delete_title"]),
                content=ft.Text(MACHINES["confirm_message"]),
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
