import flet as ft
import math
import re
import sqlite3

from machine_images import (
    MACHINE_IMAGES,
    get_machine_image,
    get_no_selection_image,
    get_placeholder_image,
)
from database import DEFAULT_REPS
from ui import design
from ui.texts import COMMON, USAGE, ERRORS
from ui.utils import (
    ButtonStyles,
    FixedHeightArea,
    _DialogsMixin,
    create_dropdown,
    create_text_field,
    format_series,
    format_set,
    format_weight,
    is_dark_theme,
)


_MAX_WEIGHT_KG = 1000
_MAX_REPS = 999
_WEIGHT_RE = re.compile(r"^[+-]?\d+(?:,\d+)?$")
_REPS_RE = re.compile(r"^[+-]?\d+$")
_SWIPE_VELOCITY = 400
"""px/s a horizontal drag must reach to count as a machine swipe."""
_RPE_OPTIONS = (
    ("6", "rpe_low"),
    ("8", "rpe_mid"),
    ("10", "rpe_high"),
)
"""Three effort levels stored as 6/8/10 so the numbers stay standard and the
labels in `USAGE` can change later without migrating data."""


class UsageTab(_DialogsMixin):
    """
    Manages the 'Registrar' (log usage) tab.

    Exposes:
      panel          – ft.Container to embed in the navigation scaffold.
      update_options – call after machines list changes.
      reset          – call when navigating back to this tab.
    """

    def __init__(self, db, styles: ButtonStyles, on_refresh):
        self._db = db
        self._styles = styles
        self._on_refresh = on_refresh
        self._machine_image_keys: dict[str, str | None] = {}
        self._machine_names: dict[str, str] = {}
        self._machine_order: list[str] = []
        self._reset_count = 0
        self._latest_weight: float | None = None
        self._latest_rpe: int | None = None
        self._rpe_value: str | None = None

        self._machine_dropdown = create_dropdown(
            label=USAGE["machine_label"],
            value=None,
            on_select=self._on_machine_selected,
            expand=True,
            col={"xs": 12},
        )

        # The banner text is rebuilt on every state change instead of mutating
        # `Text.spans`: replacing rich-text spans on an update left the banner
        # blank in Flet 1.0.5, while a fresh Text control renders fine and still
        # wraps to a second line when the message is long.
        self._latest_usage_slot = ft.Container(expand=True)
        # Trailing chip with the last recorded effort; rebuilt, not mutated, for
        # the same reason as the banner text above.
        self._latest_rpe_chip = ft.Container(
            visible=False,
            bgcolor=ft.Colors.PRIMARY_CONTAINER,
            border_radius=design.BADGE_RADIUS,
            padding=design.BADGE_PADDING,
        )
        self._latest_usage_banner = ft.Container(
            col={"xs": 12},
            bgcolor=design.SURFACE_PANEL_COLOR,
            border_radius=design.CARD_RADIUS,
            padding=design.BANNER_PADDING,
            content=ft.Row(
                spacing=0,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Container(
                        padding=ft.Padding.only(right=design.dp(8)),
                        content=ft.Image(
                            src=get_placeholder_image(),
                            width=design.dp(18),
                            height=design.dp(18),
                            fit=ft.BoxFit.CONTAIN,
                            color=ft.Colors.ON_SURFACE,
                        ),
                    ),
                    self._latest_usage_slot,
                    ft.Container(
                        padding=ft.Padding.only(left=design.dp(8)),
                        content=self._latest_rpe_chip,
                    ),
                ],
            ),
        )

        self._machine_image = ft.Image(
            src="",
            fit=ft.BoxFit.CONTAIN,
            expand=True,
            opacity=design.IMAGE_OPACITY_LIGHT,
        )
        # Highlighted surface that holds the machine drawing. It sits in a
        # `FixedHeightArea` (see `_build_panel`), so the card keeps its size
        # instead of shrinking when the Android keyboard opens.
        self._image_card = ft.Container(
            bgcolor=design.SURFACE_PANEL_COLOR,
            border_radius=design.IMAGE_CARD_RADIUS,
            padding=design.IMAGE_CARD_PADDING,
            alignment=ft.Alignment.CENTER,
            content=self._machine_image,
        )

        self._weight_input = create_text_field(
            label=USAGE["weight_label"],
            keyboard_type=ft.KeyboardType.NUMBER,
            on_change=self._clear_weight_error,
            on_submit=self._focus_reps,
            col={"xs": 6},
        )
        # The delta is a suffix of the weight field: it only makes sense while
        # typing the weight, so it lives next to the value instead of in the
        # banner. Assigned once and mutated, never recreated (see `reset()`).
        self._weight_delta = ft.Text()
        self._weight_input.suffix = self._weight_delta

        self._reps_input = create_text_field(
            label=USAGE["reps_label"],
            keyboard_type=ft.KeyboardType.NUMBER,
            on_change=self._clear_reps_error,
            on_submit=self._on_log_usage_click,
            col={"xs": 6},
        )

        # Three targets, not ten: the app is used standing, one-handed, tapping
        # with a thumb, and ten segments in 412 dp are 30 dp wide. Tapping the
        # active one clears the choice, so "no effort" stays a state.
        self._rpe_row = ft.ResponsiveRow(
            spacing=design.dp(8),
            run_spacing=design.dp(8),
            controls=self._build_rpe_buttons(),
        )

        self._save_button = ft.FilledButton(
            USAGE["save"],
            icon=ft.Icons.CHECK,
            on_click=self._on_log_usage_click,
            style=self._styles.primary,
            col={"xs": 12},
        )

        self._set_latest_usage(USAGE["select_machine"])
        self._show_no_selection_image()
        self.panel = self._build_panel()

    @property
    def _page(self) -> ft.Page:
        return self.panel.page

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def apply_theme(self) -> None:
        """Match the illustration opacity to the current theme.

        The opacity is a number, not a scheme role, so Flet does not repaint it
        when the theme changes; `GymAppView` calls this after a brightness
        change and on every data refresh.
        """
        if self.panel.parent is None:
            return
        self._machine_image.opacity = design.image_opacity(
            is_dark_theme(self.panel.page)
        )

    def update_options(self, machines) -> None:
        self._machine_image_keys = {
            str(machine_id): image_key
            for machine_id, _, image_key in machines
        }
        self._machine_names = {
            str(machine_id): name
            for machine_id, name, _ in machines
        }
        self._machine_order = [
            str(machine_id) for machine_id, _, _ in machines
        ]
        self._machine_dropdown.options = [
            ft.DropdownOption(
                text=name,
                key=str(machine_id),
                style=self._styles.menu_item,
            )
            for machine_id, name, _ in machines
        ]

    def reset(self) -> None:
        # Flet 1.0.5 keeps showing the previous label when only `value` is
        # cleared: DropdownMenu's text lives in a TextEditingController. Blanking
        # `text` and rotating the key forces the widget to be rebuilt empty.
        self._machine_dropdown.value = None
        self._machine_dropdown.text = ""
        self._machine_dropdown.error_text = None
        self._reset_count += 1
        self._machine_dropdown.key = f"machine-dropdown-{self._reset_count}"
        self._set_latest_usage(USAGE["select_machine"])
        self._latest_weight = None
        self._latest_rpe = None
        self._set_rpe_chip(None)
        self._weight_input.value = ""
        self._weight_input.error = None
        self._weight_delta.value = ""
        self._weight_delta.color = None
        self._reps_input.value = ""
        self._reps_input.error = None
        self._rpe_value = None
        self._sync_rpe_buttons()
        self._show_no_selection_image()

        # `parent` is None until the tab is mounted on a page; `page` would raise.
        if self.panel.parent is not None:
            self.panel.update()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_panel(self) -> ft.Container:
        header_row = ft.ResponsiveRow(
            spacing=design.dp(12),
            run_spacing=design.dp(12),
            controls=[
                self._machine_dropdown,
                self._latest_usage_banner,
            ],
        )
        inputs_row = ft.ResponsiveRow(
            spacing=design.dp(12),
            run_spacing=design.dp(12),
            # Top alignment, so an error under one input never pushes the
            # neighbouring box down.
            vertical_alignment=ft.CrossAxisAlignment.START,
            controls=[
                self._weight_input,
                self._reps_input,
            ],
        )
        # The card lives in a fixed-height area (`FixedHeightArea`): a clipping
        # `Stack` that takes the height the header, the fields and the button
        # leave free and keeps the card at its measured size, so the keyboard
        # clips it instead of squeezing it and the rows below stay reachable.
        # Swiping the card moves to the previous/next machine.
        self._image_wrapper = ft.GestureDetector(
            on_horizontal_drag_end=self._on_swipe,
            content=self._image_card,
        )
        self._card_area = FixedHeightArea(self._image_wrapper)
        return ft.Container(
            expand=True,
            padding=0,
            content=ft.Column(
                expand=True,
                spacing=design.dp(12),
                controls=[
                    header_row,
                    self._card_area,
                    inputs_row,
                    self._rpe_row,
                    ft.Container(
                        padding=ft.Padding.only(bottom=design.dp(8)),
                        content=ft.ResponsiveRow(
                            controls=[self._save_button],
                        ),
                    ),
                ],
            ),
        )

    def _set_latest_usage(self, message: str, value: str | None = None) -> None:
        """Show `message`, optionally followed by a bold `value`."""
        spans = [ft.TextSpan(message)]
        if value is not None:
            spans.append(
                ft.TextSpan(value, ft.TextStyle(weight=ft.FontWeight.BOLD))
            )
        self._latest_usage_slot.content = ft.Text(
            spans=spans, color=ft.Colors.ON_SURFACE
        )

    def _set_rpe_chip(self, rpe: int | None) -> None:
        """Show the last recorded effort as a trailing banner chip.

        The `Text` is rebuilt instead of mutated for the same reason as the
        banner text above.
        """
        if rpe is None:
            self._latest_rpe_chip.visible = False
            return
        self._latest_rpe_chip.content = ft.Text(
            USAGE["rpe_badge"].format(value=rpe),
            color=ft.Colors.ON_PRIMARY_CONTAINER,
            size=design.FONT_BODY_SMALL,
        )
        self._latest_rpe_chip.visible = True

    def _update_weight_delta(self) -> None:
        """Compare the typed weight with the machine's latest record.

        Hidden when the field is empty or unparseable, when the value equals the
        last weight, and when no machine is selected.
        """
        raw = (self._weight_input.value or "").strip()
        if (
            self._latest_weight is None
            or not raw
            or not _WEIGHT_RE.fullmatch(raw)
        ):
            self._set_weight_delta("", None)
            return

        weight = float(raw.replace(",", "."))
        if not math.isfinite(weight):
            self._set_weight_delta("", None)
            return

        delta = round(weight - self._latest_weight, 1)
        if delta == 0:
            self._set_weight_delta("", None)
        elif delta > 0:
            self._set_weight_delta(
                USAGE["delta_up"].format(value=format_weight(abs(delta))),
                ft.Colors.PRIMARY,
            )
        else:
            self._set_weight_delta(
                USAGE["delta_down"].format(value=format_weight(abs(delta))),
                ft.Colors.ON_SURFACE_VARIANT,
            )

    def _set_weight_delta(self, value: str, color) -> None:
        self._weight_delta.value = value
        self._weight_delta.color = color

    def _build_rpe_buttons(self) -> list[ft.Control]:
        """The three effort pills, with the selected one filled."""
        buttons = []
        for value, key in _RPE_OPTIONS:
            selected = value == self._rpe_value
            factory = ft.FilledButton if selected else ft.OutlinedButton
            buttons.append(
                factory(
                    # A single line on purpose: the pills must keep the same
                    # height whatever the system font scale is.
                    ft.Text(
                        USAGE[key],
                        size=design.FONT_LABEL_LARGE,
                        weight=ft.FontWeight.W_500,
                        color=(
                            ft.Colors.ON_PRIMARY
                            if selected
                            else ft.Colors.ON_SURFACE
                        ),
                        no_wrap=True,
                        overflow=ft.TextOverflow.ELLIPSIS,
                    ),
                    col={"xs": 4},
                    height=design.RPE_BUTTON_HEIGHT,
                    style=(
                        self._styles.rpe_selected
                        if selected
                        else self._styles.rpe_unselected
                    ),
                    on_click=lambda e, v=value: self._on_rpe_click(v),
                )
            )
        return buttons

    def _sync_rpe_buttons(self) -> None:
        self._rpe_row.controls = self._build_rpe_buttons()
        if self.panel.parent is not None:
            self._rpe_row.update()

    def _selected_rpe(self) -> int | None:
        return int(self._rpe_value) if self._rpe_value else None

    def _update_machine_image(self, key: str | None) -> None:
        # The card never collapses: a machine without its own drawing keeps the
        # generic picture, which is also the empty state.
        if key is None or key not in MACHINE_IMAGES:
            self._show_no_selection_image()
            return

        self._machine_image.color = None
        self._machine_image.scale = None
        self._machine_image.src = get_machine_image(key)

    def _show_no_selection_image(self) -> None:
        """Fall back to the generic gym picture when nothing is selected."""
        self._machine_image.color = None
        # The generic drawing is tightly framed, so it is scaled down to match
        # the visual weight of the machine illustrations.
        self._machine_image.scale = design.NO_SELECTION_IMAGE_SCALE
        self._machine_image.src = get_no_selection_image()

    def _parse_weight(self) -> float | None:
        raw = (self._weight_input.value or "").strip()
        if not raw:
            self._weight_input.error = ERRORS["enter_weight"]
            return None

        if not _WEIGHT_RE.fullmatch(raw):
            self._weight_input.error = ERRORS["invalid_weight"]
            return None

        weight = float(raw.replace(",", "."))
        if not math.isfinite(weight) or weight <= 0 or weight > _MAX_WEIGHT_KG:
            self._weight_input.error = ERRORS["weight_out_of_range"].format(
                max=_MAX_WEIGHT_KG
            )
            return None

        return weight

    def _parse_reps(self) -> int | None:
        raw = (self._reps_input.value or "").strip()
        # Leaving the field empty is not an error: the set is stored with the
        # default rep count.
        if not raw:
            return DEFAULT_REPS

        if not _REPS_RE.fullmatch(raw):
            self._reps_input.error = ERRORS["invalid_reps"]
            return None

        reps = int(raw)
        if reps < 1 or reps > _MAX_REPS:
            self._reps_input.error = ERRORS["reps_out_of_range"].format(
                max=_MAX_REPS
            )
            return None

        return reps

    def _clear_weight_error(self, e=None) -> None:
        if self._weight_input.error is not None:
            self._weight_input.error = None
        # The delta is recomputed from the same `on_change` event.
        self._update_weight_delta()
        if self.panel.parent is not None:
            self._weight_input.update()

    def _clear_reps_error(self, e=None) -> None:
        if self._reps_input.error is not None:
            self._reps_input.error = None
            self._reps_input.update()

    def _focus_reps(self, e=None) -> None:
        page = self.panel.page
        if page is not None:
            page.run_task(self._reps_input.focus)

    def _dismiss_keyboard(self) -> None:
        """
        Hides the on-screen keyboard.

        Flet exposes no unfocus/blur API, so the only way is to move the focus
        to a control that does not open a keyboard. `focus()` is a coroutine,
        hence `page.run_task`.
        """
        page = self.panel.page
        if page is not None:
            page.run_task(self._save_button.focus)

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def _on_rpe_click(self, value: str) -> None:
        """Pick the effort of this set; tapping the active one clears it."""
        self._rpe_value = None if value == self._rpe_value else value
        self._sync_rpe_buttons()

    def _on_machine_selected(self, e) -> None:
        if self._machine_dropdown.error_text is not None:
            self._machine_dropdown.error_text = None

        self._refresh_selection()

        if self.panel.parent is not None:
            self.panel.update()

    def _on_swipe(self, e) -> None:
        """Move to the previous/next machine in the dropdown order.

        Swiping left goes forward, swiping right goes back, and the list wraps
        around in both directions.
        """
        velocity = e.primary_velocity or 0
        if abs(velocity) < _SWIPE_VELOCITY or not self._machine_order:
            return

        index = None
        if self._machine_dropdown.value in self._machine_order:
            index = self._machine_order.index(self._machine_dropdown.value)

        if index is None:
            index = 0 if velocity < 0 else len(self._machine_order) - 1
        elif velocity < 0:
            index = (index + 1) % len(self._machine_order)
        else:
            index = (index - 1) % len(self._machine_order)

        if self._machine_dropdown.error_text is not None:
            self._machine_dropdown.error_text = None

        self._machine_dropdown.value = self._machine_order[index]
        self._refresh_selection()

        if self.panel.parent is not None:
            self.panel.update()

    def _refresh_selection(self) -> None:
        """Re-render the image and the latest-record banner for the selection."""
        selected_id = self._machine_dropdown.value

        if not selected_id:
            self._latest_weight = None
            self._latest_rpe = None
            self._show_no_selection_image()
            self._set_latest_usage(USAGE["select_machine"])
            self._set_rpe_chip(None)
            self._update_weight_delta()
            return

        self._update_machine_image(self._machine_image_keys.get(selected_id))

        latest = self._db.get_latest_usage(int(selected_id))
        if latest is None:
            self._latest_weight = None
            self._latest_rpe = None
            self._set_latest_usage(USAGE["no_records"])
        else:
            weight, reps, rpe, _usage_date = latest
            self._latest_weight = weight
            self._latest_rpe = rpe
            self._set_latest_usage(
                USAGE["latest_prefix"], format_series(weight, reps)
            )

        self._set_rpe_chip(self._latest_rpe)
        self._update_weight_delta()

    def _on_log_usage_click(self, e) -> None:
        has_error = False

        if not self._machine_dropdown.value:
            self._machine_dropdown.error_text = ERRORS["select_machine"]
            has_error = True

        # Both fields are validated before returning, so a submit with two
        # problems shows both errors at once instead of one at a time.
        weight = self._parse_weight()
        reps = self._parse_reps()
        if weight is None or reps is None:
            has_error = True

        if has_error:
            if self.panel.parent is not None:
                self.panel.update()
            return

        machine_id = int(self._machine_dropdown.value)
        rpe = self._selected_rpe()

        try:
            existing = self._db.get_usage_for_date(machine_id)
        except sqlite3.Error as exc:
            self._show_error(ERRORS["log_usage"].format(error=exc))
            return

        if existing is not None:
            usage_id, stored_weight, stored_reps, stored_rpe = existing
            self._show_overwrite_dialog(
                machine_id,
                usage_id,
                stored_weight,
                stored_reps,
                stored_rpe,
                weight,
                reps,
                rpe,
            )
            return

        self._save_usage(machine_id, weight, reps, rpe)

    def _save_usage(
        self,
        machine_id: int,
        weight: float,
        reps: int,
        rpe: int | None,
    ) -> None:
        try:
            self._db.log_use(machine_id, weight, reps, rpe)
        except sqlite3.Error as exc:
            self._show_error(ERRORS["log_usage"].format(error=exc))
            return

        self._dismiss_keyboard()
        self._show_snackbar(USAGE["saved"])
        self._on_refresh()

    def _show_overwrite_dialog(
        self,
        machine_id: int,
        usage_id: int,
        stored_weight: float,
        stored_reps: int | None,
        stored_rpe: int | None,
        new_weight: float,
        new_reps: int,
        new_rpe: int | None,
    ) -> None:
        machine_name = self._machine_names.get(str(machine_id), "")

        def _confirm_overwrite(e) -> None:
            self._page.pop_dialog()
            try:
                self._db.update_usage(usage_id, new_weight, new_reps, new_rpe)
            except sqlite3.Error as exc:
                self._show_error(ERRORS["log_usage"].format(error=exc))
                return
            self._dismiss_keyboard()
            self._show_snackbar(USAGE["saved"])
            self._on_refresh()

        self._page.show_dialog(
            ft.AlertDialog(
                modal=True,
                title=ft.Text(USAGE["duplicate_title"]),
                content=ft.Text(
                    USAGE["duplicate_message"].format(
                        machine=machine_name,
                        current=format_set(
                            stored_weight, stored_reps, stored_rpe
                        ),
                        new=format_set(new_weight, new_reps, new_rpe),
                    )
                ),
                actions=[
                    ft.TextButton(
                        COMMON["cancel"],
                        on_click=lambda e: self._page.pop_dialog(),
                        style=self._styles.dialog,
                    ),
                    ft.TextButton(
                        USAGE["overwrite"],
                        on_click=_confirm_overwrite,
                        style=self._styles.dialog_destructive,
                    ),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )
        )
