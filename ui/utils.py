import flet as ft
from datetime import date

from ui import design
from ui.texts import DATE, ERRORS, COMMON

_SNACKBAR_DURATION_MS = 4000


def format_date(iso_date: str) -> str:
    """Format an ISO date string to a human-readable short form."""
    parsed = date.fromisoformat(iso_date)
    month_names = DATE["months_short"]
    return f"{parsed.day} {month_names[parsed.month - 1]}. {parsed.year}"


def format_weight(weight: float) -> str:
    """Format a weight with the Spanish decimal separator."""
    return str(weight).replace(".", ",")


def is_dark_theme(page: ft.Page) -> bool:
    """Return True when the current effective theme is dark."""
    return (
        page.theme_mode == ft.ThemeMode.DARK
        or (
            page.theme_mode == ft.ThemeMode.SYSTEM
            and page.platform_brightness == ft.Brightness.DARK
        )
    )


def create_dropdown(**kwargs) -> ft.Dropdown:
    """Create an exposed dropdown with the app's shared Material 3 styling.

    Field border, content padding and menu height only; text sizes stay at each
    call site so a dropdown never introduces a font size of its own.
    """
    return ft.Dropdown(
        border=ft.OutlineInputBorder(border_radius=design.FIELD_RADIUS),
        content_padding=design.FIELD_CONTENT_PADDING,
        menu_height=design.MENU_MAX_HEIGHT,
        **kwargs,
    )


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
