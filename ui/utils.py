import flet as ft
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
