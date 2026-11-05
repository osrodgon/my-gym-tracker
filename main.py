import flet as ft
from database import GymDatabase
from ui.views import GymAppView
from ui.texts import NAVIGATION

def main(page: ft.Page):
    # Set the theme mode to system default (light/dark)
    page.theme_mode = ft.ThemeMode.SYSTEM

    # Font theme for better readability
    light_text_theme = ft.TextTheme(
        body_large=ft.TextStyle(size=20, color=ft.Colors.BLACK),
        body_medium=ft.TextStyle(size=18, color=ft.Colors.BLACK),
        label_large=ft.TextStyle(size=18, color=ft.Colors.BLACK),
        title_large=ft.TextStyle(size=24, color=ft.Colors.BLACK),
        title_medium=ft.TextStyle(size=18, color=ft.Colors.BLACK),
    )

    dark_text_theme = ft.TextTheme(
        body_large=ft.TextStyle(size=20, color=ft.Colors.WHITE),
        body_medium=ft.TextStyle(size=18, color=ft.Colors.WHITE),
        label_large=ft.TextStyle(size=18, color=ft.Colors.WHITE),
        title_large=ft.TextStyle(size=24, color=ft.Colors.WHITE),
        title_medium=ft.TextStyle(size=18, color=ft.Colors.WHITE),
    )

    # Set the theme for the page
    page.theme = ft.Theme(
        color_scheme_seed=ft.Colors.BLUE,
        text_theme=light_text_theme,
        dialog_theme=ft.DialogTheme(
            title_text_style=ft.TextStyle(size=20, color=ft.Colors.BLACK),
            content_text_style=ft.TextStyle(size=16, color=ft.Colors.BLACK),
        ),
    )

    page.dark_theme = ft.Theme(
        color_scheme_seed=ft.Colors.BLUE,
        text_theme=dark_text_theme,
        dialog_theme=ft.DialogTheme(
            title_text_style=ft.TextStyle(size=20, color=ft.Colors.WHITE),
            content_text_style=ft.TextStyle(size=16, color=ft.Colors.WHITE),
        ),
    )

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
