import flet as ft
from database import GymDatabase
from ui import design
from ui.views import GymAppView
from ui.texts import NAVIGATION


def _build_text_theme(color: str) -> ft.TextTheme:
    return ft.TextTheme(
        body_large=ft.TextStyle(size=design.FONT_BODY_LARGE, color=color),
        body_medium=ft.TextStyle(size=design.FONT_BODY_MEDIUM, color=color),
        label_large=ft.TextStyle(size=design.FONT_LABEL_LARGE, color=color),
        title_large=ft.TextStyle(size=design.FONT_TITLE_LARGE, color=color),
        title_medium=ft.TextStyle(size=design.FONT_TITLE_MEDIUM, color=color),
    )


def _build_theme(color: str) -> ft.Theme:
    return ft.Theme(
        color_scheme_seed=ft.Colors.BLUE,
        text_theme=_build_text_theme(color),
        card_theme=ft.CardTheme(
            shape=ft.RoundedRectangleBorder(radius=design.CARD_RADIUS),
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        ),
        expansion_tile_theme=ft.ExpansionTileTheme(
            shape=ft.RoundedRectangleBorder(radius=design.CARD_RADIUS),
            collapsed_shape=ft.RoundedRectangleBorder(radius=design.CARD_RADIUS),
        ),
        list_tile_theme=ft.ListTileTheme(
            shape=ft.RoundedRectangleBorder(radius=design.CARD_RADIUS),
        ),
        dropdown_theme=ft.DropdownTheme(
            menu_style=ft.MenuStyle(
                shape=ft.RoundedRectangleBorder(radius=design.MENU_RADIUS),
                padding=design.MENU_PADDING,
            ),
        ),
        dialog_theme=ft.DialogTheme(
            shape=ft.RoundedRectangleBorder(radius=design.DIALOG_RADIUS),
            title_text_style=ft.TextStyle(
                size=design.FONT_DIALOG_TITLE, color=color
            ),
            content_text_style=ft.TextStyle(
                size=design.FONT_BODY_MEDIUM, color=color
            ),
            actions_padding=design.DIALOG_ACTIONS_PADDING,
        ),
        snackbar_theme=ft.SnackBarTheme(
            shape=ft.RoundedRectangleBorder(radius=design.SNACKBAR_RADIUS),
        ),
        navigation_bar_theme=ft.NavigationBarTheme(
            height=design.NAV_BAR_HEIGHT,
            label_text_style=ft.TextStyle(
                size=design.FONT_NAV_LABEL, color=color
            ),
        ),
    )


def main(page: ft.Page):
    # Set the theme mode to system default (light/dark)
    page.theme_mode = ft.ThemeMode.SYSTEM

    # Light and dark themes built from the same Material 3 tokens.
    page.theme = _build_theme(ft.Colors.BLACK)
    page.dark_theme = _build_theme(ft.Colors.WHITE)

    # UI title in Spanish
    page.title = NAVIGATION["app_name"]
    page.vertical_alignment = ft.MainAxisAlignment.START
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.window.width = 540
    page.window.height = 960

    db = GymDatabase()
    
    # By inheriting from ft.Column, it is added directly
    app_view = GymAppView(db)
    page.on_platform_brightness_change = (
        app_view._on_platform_brightness_change
    )
    page.services.append(app_view.file_picker)
    page.navigation_bar = app_view.navigation_bar
    page.add(
        ft.SafeArea(
            content=app_view,
            avoid_intrusions_top=True,
            avoid_intrusions_bottom=False,
            expand=True,
        )
    )
    app_view.update_data()  # Initial call to load data when starting the application

if __name__ == "__main__":
    ft.run(main, view=ft.AppView.WEB_BROWSER, port=8550, host="0.0.0.0")
