# Project Context: Mi Gimnasio - Gym Tracker App

## Tech Stack
- **Framework:** Python with Flet (`flet`) version 1.0.5
- **Primary Target:** Android (Mobile-First approach, touch UI, SafeArea, virtual keyboard awareness).
- **Local Testing Environment:** AppImage / Flet Web (`flet run main.py`).
- **Database:** SQLite (`gym.db`) via `database.py`.

## Architecture & Code Conventions
This project follows a modular structure divided into functional tabs, each managing its own state:

1. **Modular Components:** `main.py` is the entry point that instantiates `GymAppView`, which composes three tab objects (`UsageTab`, `HistoryTab`, `MachinesTab`). Each tab is a separate class in `ui/` directory.

2. **Mobile UI Optimization**: 
   - Design for vertical touch screens (accessible buttons, use `ft.ListView` or `ft.Column(scroll=ft.ScrollMode.AUTO)`).
   - Always wrap views in `ft.SafeArea` to prevent overlapping with system status bars or Android gesture areas.
   - Material Design compliance: Use `ft.Colors.SURFACE`, `ft.Colors.ERROR` for destructive actions, and consistent typography.

3. **State Management**: 
   - Data flows from `GymDatabase` (SQLite) up through the tab classes.
   - `GymAppView.update_data()` refreshes all tabs after any database mutation.
   - Preferred calling `control.update()` over `page.update()` whenever possible to optimize rendering performance on Android.

4. **Local Compatibility:** Code must remain fully compatible with both local desktop execution (`flet run main.py`) and Android build tools (`flet build apk`).

5. **Code Verification:** Before referencing methods, properties, or classes, verify they exist in the current code state. Check class definitions, method signatures, and attribute declarations to prevent `AttributeError` issues. This is especially important after git operations, code resets, or when working with inherited/modified classes. Add `hasattr()` checks or review documentation when integrating new features.

6. **Flet Version Compatibility:** When using Flet framework constants (like `MainAxisAlignment`, `Colors`, `Icons`, etc.), verify they exist in the installed Flet version. Some constants (like `MainAxisEndpoint`) may only exist in newer Flet versions. Check `flet.__version__` and consult the [Flet documentation](https://flet.dev) for available constants. Use `dir(flet)` or `hasattr(flet, 'constant_name')` to verify before using framework features.

7. **Consistent Dialog Patterns:** Follow the app's established dialog patterns for Material Design compliance. Use `ft.OutlinedButton` with `style=self._styles.dialog_destructive` for destructive actions, consistent title/content from `texts.py` dictionaries, and `actions_alignment=ft.MainAxisAlignment.END`. The History tab delete dialog now matches the Machines tab pattern to ensure UI consistency across the app.

This structure reflects the gym tracking application:

- `main.py` - Entry point of the application. Creates `GymAppView` and configures the page.
- `ui/views.py` - Main `GymAppView` view and navigation between tabs.
- `ui/usage_tab.py` - "Register" tab (log usage). Manages the weight and machine form.
- `ui/history_tab.py` - "History" tab. Shows the history with delete icons per entry.
- `ui/machines_tab.py` - "Machines" tab. Machine management (create/edit/delete).
- `ui/texts.py` - Dictionary of text strings (HISTORY, USAGE, MACHINES, ERRORS, etc.).
- `ui/utils.py` - Shared utilities: `ButtonStyles`, `format_date`, `is_dark_theme`.
- `database.py` - SQLite data access layer. Methods: `get_machines()`, `get_summary()`, `log_use()`, `add_machine()`, `delete_usage()`.
- `machine_images.py` - Mapping of machine names to SVG images.
- `build.sh` - Build and packaging script (web, apk, linux, image).
- `assets/` - Graphic resources (icon, machine SVG images).
- `gym.db` - SQLite database file (generated at runtime).
- `build/` - Generated directory for builds and AppImage.

## Material Design Compliance Notes
- **Top App Bar:** Missing - pending implementation (Priority #1 in memory bank)
- **Bottom Navigation:** Implemented with `ft.NavigationBar` (3 tabs: Register, History, Machines)
- **FAB:** Present in history_tab.py for overflow options
- **Cards:** Used with `radius=20` throughout
- **Input Fields:** `OutlineInputBorder` with `border_radius=20`
- **Dialogs:** `AlertDialog` with `show_drag_handle=True` for bottom sheets
- **Snackbars:** Duration 2s, horizontal dismiss
- **Color Scheme:** `color_scheme_seed=ft.Colors.BLUE`
- **Adaptive Icons:** Not yet configured (pending in pyproject.toml)
- **Typography:** TextStyles defined in main.py with sizes 18-24px

## Build Commands
- `flet run main.py` - Run in web browser (local development)
- `flet build apk --split-per-abi` - Build Android APKs
- `flet build apk --product "Mi Gimnasio"` - Build with custom product name
- `bash build.sh web` - Alternative web build command
- `bash build.sh apk` - Alternative APK build command