import flet as ft
import asyncio
from datetime import date

from ui import design
from ui.texts import DATE, ERRORS, COMMON, SERIES
from database import DEFAULT_REPS

_SNACKBAR_DURATION_MS = 4000


def format_date(iso_date: str) -> str:
    """Format an ISO date string to a human-readable short form."""
    parsed = date.fromisoformat(iso_date)
    month_names = DATE["months_short"]
    return f"{parsed.day} {month_names[parsed.month - 1]}. {parsed.year}"


def format_weight(weight: float) -> str:
    """Format a weight with the Spanish decimal separator."""
    return str(weight).replace(".", ",")


def format_series(weight: float, reps: int | None) -> str:
    """Format a logged set, e.g. `80,0 kg × 10 reps`.

    A set with no rep count falls back to `DEFAULT_REPS`, so the UI never shows
    a half-filled record.
    """
    return SERIES["with_reps"].format(
        weight=format_weight(weight),
        reps=DEFAULT_REPS if reps is None else reps,
    )


def create_dropdown(**kwargs) -> ft.Dropdown:
    """Create an exposed dropdown with the app's shared Material 3 styling.

    Field border, content padding, menu height and the M3 read-only behaviour
    (no text input, no filtering, menu as wide as the field) come from here.
    Text sizes stay overridable so a call site can still opt out.
    """
    kwargs.setdefault(
        "border", ft.OutlineInputBorder(border_radius=design.FIELD_RADIUS)
    )
    kwargs.setdefault("content_padding", design.FIELD_CONTENT_PADDING)
    kwargs.setdefault("menu_height", design.MENU_MAX_HEIGHT)
    kwargs.setdefault("text_size", design.FONT_BODY_LARGE)
    # Flutter's DropdownMenu shrinks to its intrinsic width unless the insets
    # are zero; M3 selectors span the whole field.
    kwargs.setdefault("expanded_insets", 0)
    # A read-only selector: opening it must not raise the soft keyboard.
    kwargs.setdefault("editable", False)
    kwargs.setdefault("enable_filter", False)
    kwargs.setdefault("enable_search", False)
    return ft.Dropdown(**kwargs)


def create_text_field(**kwargs) -> ft.TextField:
    """Create an outlined text field with the app's shared Material 3 styling.

    The border is delegated to the theme on purpose: M3 then resolves the
    outline/primary/error colour and width per state.
    """
    kwargs.setdefault(
        "border", ft.OutlineInputBorder(border_radius=design.FIELD_RADIUS)
    )
    kwargs.setdefault("content_padding", design.FIELD_CONTENT_PADDING)
    kwargs.setdefault("text_size", design.FONT_BODY_LARGE)
    # Half-width fields need room for the Spanish error text without ellipsis.
    kwargs.setdefault("error_max_lines", 3)
    return ft.TextField(**kwargs)


_FIT_DELAY = 0.15
"""Seconds to wait before applying a measured card height.

`on_size_change` reports every intermediate layout: the first frames carry a
provisional safe area, the navigation bar and text metrics, and the keyboard
runs an animation. Only the last value of each burst is applied.
"""


class FixedHeightArea(ft.Stack):
    """Clipping area that keeps a flexible card at the height it filled.

    Use it as the flexible child of a `Column` that also holds fixed rows (the
    Registrar fields and save button, the machine form actions). The card is
    pinned to all four edges, so it fills the area from the first frame; the
    measured height is then applied to the card, which only ever grows. When
    the Android keyboard shrinks the panel, the area gets smaller and clips the
    card instead of squeezing it, so the fixed rows stay on screen and
    reachable. Nothing is applied while `page.media.view_insets.bottom > 0`
    either, as a second guard on platforms that report the keyboard there.

    A `Stack` is required: inside a `Container` the child is clamped to the
    parent's height, so a fixed height could never survive the keyboard.
    """

    def __init__(self, child: ft.Control):
        super().__init__(expand=True, on_size_change=self._on_size_change)
        child.left = 0
        child.top = 0
        child.right = 0
        child.bottom = 0
        self.controls = [child]
        self._card = child
        self._card_height: float | None = None
        self._area_height: float | None = None
        self._fit_generation = 0

    @property
    def _mounted_page(self) -> ft.Page | None:
        """The page, or `None` if the area is detached.

        `Control.page` raises instead of returning `None` when the control is
        not in a page tree, which happens if the machine form is closed while a
        debounced measurement is still pending.
        """
        try:
            return self.page
        except RuntimeError:
            return None

    def _on_size_change(self, e) -> None:
        """Track the height of the free area and debounce its application.

        The area is the flexible child of the column that hosts it, so its
        height is exactly the space the fixed rows leave free; no arithmetic
        with `page.height` is needed.
        """
        if e.height <= 0:
            return
        self._area_height = e.height
        page = self._mounted_page
        if page is None:
            return
        self._fit_generation += 1
        page.run_task(self._apply_height, self._fit_generation)

    async def _apply_height(self, generation: int) -> None:
        """Give the card the last measured height, once the layout settled.

        Only the newest burst is applied (`generation`) and the height only
        grows, so the keyboard cannot shrink the card.
        """
        await asyncio.sleep(_FIT_DELAY)
        page = self._mounted_page
        if page is None:
            return
        if generation != self._fit_generation or self._area_height is None:
            return
        if page.media.view_insets.bottom > 0:
            return
        if self._area_height <= (self._card_height or 0):
            return
        self._card_height = self._area_height
        # Unpin the bottom edge: with both `top` and `bottom` set, `height` is
        # ignored and the card would shrink with the area again.
        self._card.bottom = None
        self._card.height = self._area_height
        self.update()


class ButtonStyles:
    """All shared button style variants for the app, built once."""

    def __init__(self):
        base = ft.ButtonStyle(
            shape=ft.StadiumBorder(),
            padding=design.BUTTON_PADDING,
            icon_size=design.BUTTON_ICON_SIZE,
            text_style=ft.TextStyle(
                size=design.FONT_LABEL_LARGE, weight=ft.FontWeight.W_500
            ),
        )
        self.default = base
        self.primary = base.copy(padding=design.PRIMARY_BUTTON_PADDING)
        self.menu_item = ft.ButtonStyle(
            padding=design.MENU_ITEM_PADDING,
            text_style=ft.TextStyle(size=design.FONT_LABEL_LARGE),
        )
        dialog = base.copy(
            padding=design.DIALOG_BUTTON_PADDING,
        )
        self.dialog = dialog
        self.dialog_destructive = dialog.copy(
            color=ft.Colors.ERROR,
        )


class _DialogsMixin:
    """
    Mixin providing dialog/snackbar helpers.

    Concrete classes must expose:
      - self._page  → ft.Page
      - self._styles → ButtonStyles
    """

    @property
    def _page(self) -> ft.Page:
        raise NotImplementedError  # pragma: no cover

    def _show_message_dialog(self, title: str, message: str) -> None:
        self._page.show_dialog(
            ft.AlertDialog(
                modal=True,
                title=ft.Text(title),
                content=ft.Text(message),
                actions=[
                    ft.TextButton(
                        COMMON["accept"],
                        on_click=lambda e: self._page.pop_dialog(),
                        style=self._styles.dialog,
                    ),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )
        )

    def _show_snackbar(self, message: str) -> None:
        self._page.show_dialog(
            ft.SnackBar(
                ft.Text(message),
                duration=_SNACKBAR_DURATION_MS,
                behavior=ft.SnackBarBehavior.FLOATING,
                dismiss_direction=ft.DismissDirection.HORIZONTAL,
                show_close_icon=True,
            )
        )

    def _show_error(self, message: str) -> None:
        self._show_message_dialog(ERRORS["title"], message)
