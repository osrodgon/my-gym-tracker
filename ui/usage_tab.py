import flet as ft
import sqlite3

from machine_images import MACHINE_IMAGES, get_machine_image_key
from ui.texts import USAGE, ERRORS
from ui.utils import ButtonStyles, _DialogsMixin, format_date, is_dark_theme


class UsageTab(_DialogsMixin):
    """
    Manages the 'Registrar' (log usage) tab.

    Exposes:
      panel          – ft.Container to embed in the navigation scaffold.
      update_options – call after machines list changes.
      reset          – call when navigating back to this tab.
      on_brightness_change – call when system brightness changes.
    """

    def __init__(self, db, styles: ButtonStyles, on_refresh):
        self._db = db
        self._styles = styles
        self._on_refresh = on_refresh
        self._machine_image_keys: dict[str, str | None] = {}

        self._machine_dropdown = ft.Dropdown(
            label=USAGE["machine_label"],
            value="",
            border=ft.OutlineInputBorder(border_radius=20),
            on_select=self._on_machine_selected,
            expand=True,
        )
        self._machine_dropdown.col = {"xs": 12}

        self._latest_usage_text = ft.Text(USAGE["select_machine"], italic=True)
        self._latest_usage_text.col = {"xs": 12}

        self._weight_input = ft.TextField(
            label=USAGE["weight_label"],
            width=150,
            keyboard_type=ft.KeyboardType.NUMBER,
            border=ft.OutlineInputBorder(border_radius=20),
            on_change=self._clear_field_error,
        )
        self._machine_image = ft.Image(
            fit=ft.BoxFit.CONTAIN,
            visible=False,
            src="",
            expand=True,
        )

        self.panel = self._build_panel()

    @property
    def _page(self) -> ft.Page:
        return self.panel.page

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def update_options(self, machines) -> None:
        self._machine_image_keys = {
            str(machine_id): image_key
            for machine_id, _, image_key in machines
        }
        self._machine_dropdown.options = [
            ft.DropdownOption(text=name, key=str(machine_id))
            for machine_id, name, _ in machines
        ]

    def reset(self) -> None:
        self._machine_dropdown.value = ""
        self._latest_usage_text.value = USAGE["select_machine"]
        self._weight_input.value = ""
        self._weight_input.error = None
        self._machine_image.visible = False

        if self._machine_dropdown.page is not None:
            self._machine_dropdown.update()

    def on_brightness_change(self) -> None:
        selected_id = self._machine_dropdown.value
        if not selected_id:
            return
        image_key = self._machine_image_keys.get(selected_id)
        self._update_machine_image(image_key)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_panel(self) -> ft.Container:
        return ft.Container(
            expand=True,
            padding=0,
            content=ft.Column(
                expand=True,
                spacing=0,
                controls=[
                    ft.Column(
                        expand=True,
                        scroll=ft.ScrollMode.AUTO,
                        controls=[
                            ft.ResponsiveRow(
                                run_spacing=15,
                                controls=[
                                    self._machine_dropdown,
                                    self._latest_usage_text,
                                    ft.Container(
                                        content=self._weight_input,
                                        width=150,
                                        col={"xs": 12},
                                    ),
                                    ft.Container(
                                        content=self._machine_image,
                                        height=400,
                                        alignment=ft.Alignment.CENTER,
                                        col={"xs": 12},
                                    ),
                                ],
                            ),
                        ],
                    ),
                    ft.ResponsiveRow(
                        controls=[
                            ft.FilledButton(
                                USAGE["save"],
                                icon=ft.Icons.CHECK,
                                on_click=self._on_log_usage_click,
                                style=self._styles.default,
                                col={"xs": 12, "sm": 6},
                            ),
                        ],
                    ),
                ],
            ),
        )

    def _update_machine_image(self, key: str | None) -> None:
        image_path = MACHINE_IMAGES.get(key) if key else None
        self._machine_image.visible = image_path is not None
        self._machine_image.src = image_path or ""
        if image_path is not None:
            self._machine_image.color = (
                ft.Colors.WHITE if is_dark_theme(self._page) else ft.Colors.BLACK
            )

    def _clear_field_error(self, e) -> None:
        if e.control.error is not None:
            e.control.error = None
            e.control.update()

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def _on_machine_selected(self, e) -> None:
        if not self._machine_dropdown.value:
            self._machine_image.visible = False
            self._latest_usage_text.value = USAGE["select_machine"]
        else:
            selected_id = self._machine_dropdown.value
            self._update_machine_image(self._machine_image_keys.get(selected_id))

            latest = self._db.get_latest_usage(int(selected_id))
            if latest is None:
                self._latest_usage_text.value = USAGE["no_records"]
            else:
                weight, usage_date = latest
                self._latest_usage_text.value = USAGE["latest_weight"].format(
                    weight=weight, date=format_date(usage_date)
                )

        if self._page is not None:
            self.panel.update()

    def _on_log_usage_click(self, e) -> None:
        if not self._machine_dropdown.value:
            self._show_snackbar(ERRORS["select_machine"])
            return

        if not self._weight_input.value:
            self._show_snackbar(ERRORS["enter_weight"])
            return

        try:
            weight = float(self._weight_input.value)
        except ValueError:
            self._show_snackbar(ERRORS["invalid_weight"])
            return

        try:
            self._db.log_use(int(self._machine_dropdown.value), weight)
        except sqlite3.Error as exc:
            self._show_snackbar(ERRORS["log_usage"].format(error=exc))
            return

        self._on_refresh()
