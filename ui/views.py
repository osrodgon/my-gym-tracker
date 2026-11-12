import flet as ft

from ui.texts import NAVIGATION
from ui.utils import ButtonStyles
from ui.usage_tab import UsageTab
from ui.history_tab import HistoryTab
from ui.machines_tab import MachinesTab


class GymAppView(ft.Column):
    """
    Root application view. Acts as a navigation scaffold that composes
    the three tab objects and delegates data updates to each of them.
    """

    def __init__(self, db):
        super().__init__()
        self.db = db
        self.expand = True
        self.horizontal_alignment = ft.CrossAxisAlignment.STRETCH
        self.file_picker = ft.FilePicker()

        styles = ButtonStyles()
        self._usage_tab = UsageTab(db, styles, self._on_data_changed)
        self._history_tab = HistoryTab(db, self.file_picker, styles, self._on_data_changed)
        self._machines_tab = MachinesTab(
            db,
            styles,
            self._on_data_changed,
            on_edit_mode_changed=self._on_machines_edit_mode_changed,
        )

        self._build_navigation()

    # ------------------------------------------------------------------
    # Navigation scaffold
    # ------------------------------------------------------------------

    def _build_navigation(self) -> None:
        self._sections = [
            (NAVIGATION["usage"],    self._usage_tab.panel,    ft.Icons.MONITOR_HEART),
            (NAVIGATION["history"],  self._history_tab.panel,  ft.Icons.HISTORY),
            (NAVIGATION["machines"], self._machines_tab.panel, ft.Icons.FORMAT_LIST_BULLETED),
        ]
        self._selected_section = 0

        self.content_container = ft.Container(
            content=self._sections[self._selected_section][1],
            expand=True,
        )
        self.navigation_bar = ft.NavigationBar(
            selected_index=self._selected_section,
            on_change=self._on_navigation_change,
            destinations=[
                ft.NavigationBarDestination(label=label, icon=icon)
                for label, _, icon in self._sections
            ],
        )
        self.controls = [
            ft.Container(
                content=self.content_container,
                padding=ft.Padding.only(top=16),
                expand=True,
            )
        ]

    def _on_navigation_change(self, e) -> None:
        index = e.control.selected_index
        if index is None or not 0 <= index < len(self._sections):
            return
        self._selected_section = index
        self._machines_tab.reset()
        self.content_container.content = self._sections[index][1]
        if index == 0:
            self._usage_tab.reset()
        self._sync_floating_action_button()
        self.page.update()

    def _on_machines_edit_mode_changed(self, editing: bool) -> None:
        """Hide the Máquinas FAB while its in-tab form is open.

        The Android back gesture is intercepted only while editing, so on the
        list it keeps its native behaviour of leaving the app.
        """
        self.page.views[0].can_pop = not editing
        if self._selected_section == 2:
            self.page.floating_action_button = (
                None if editing else self._machines_tab.fab
            )
        self.page.update()

    async def on_confirm_pop(self, e) -> None:
        """Handle the Android back gesture while the machine form is open."""
        if self._machines_tab.is_editing:
            self._machines_tab.reset()
        await e.control.confirm_pop(False)

    def _sync_floating_action_button(self) -> None:
        """Show each tab's FAB only while that tab is selected."""
        fabs = {1: self._history_tab.fab, 2: self._machines_tab.fab}
        self.page.floating_action_button = fabs.get(self._selected_section)

    # ------------------------------------------------------------------
    # Data refresh
    # ------------------------------------------------------------------

    def _on_data_changed(self) -> None:
        """Callback invoked by any tab after it mutates the database."""
        self.update_data()

    def update_data(self) -> None:
        results = self.db.get_summary()
        machines = self.db.get_machines()

        self._history_tab.render(results, machines)
        self._machines_tab.render(machines)
        self._usage_tab.update_options(machines)
        self._usage_tab.reset()

        if self.page is not None:
            self.update()

    # ------------------------------------------------------------------
    # Platform brightness
    # ------------------------------------------------------------------

    def _on_platform_brightness_change(self, e) -> None:
        self._usage_tab.on_brightness_change()
        self.update()