import flet as ft
from database import GymDatabase
from ui.views import GymAppView

def main(page: ft.Page):
    # Set the theme mode to system default (light/dark)
    page.theme_mode = ft.ThemeMode.SYSTEM

    # Font theme for better readability
    text_theme=ft.TextTheme(
        body_large=ft.TextStyle(size=20),
        body_medium=ft.TextStyle(size=18),
        label_large=ft.TextStyle(size=18),
        title_large=ft.TextStyle(size=24),
        title_medium=ft.TextStyle(size=18),
    )

    # Set the theme for the page
    page.theme = ft.Theme(
        color_scheme_seed=ft.Colors.BLUE,
        text_theme=text_theme
    )
    page.dark_theme = ft.Theme(
        color_scheme_seed=ft.Colors.BLUE,
        text_theme=text_theme
    )

    # UI title in Spanish
    page.title = "🏋️‍♂️ Control de Gimnasio ORG"
    page.vertical_alignment = ft.MainAxisAlignment.START
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    db = GymDatabase()
    
    # By inheriting from ft.Column, it is added directly
    app_view = GymAppView(db)
    page.services.append(app_view.file_picker)
    page.add(app_view)
    page.appbar = app_view.app_bar
    page.navigation_bar = app_view.navigation_bar
    app_view.update_data()  # Initial call to load data when starting the application

if __name__ == "__main__":
    ft.run(main, view=ft.AppView.WEB_BROWSER, port=8550, host="0.0.0.0")
