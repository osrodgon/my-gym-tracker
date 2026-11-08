# Mi Gimnasio — agent notes

Gym tracker built with **Flet 1.0.5** (Python ≥3.10). Android-first, Spanish UI,
SQLite persistence. Flet docs: https://flet.dev.

## Commands

- `python main.py` — web build on `http://localhost:8550` (hardcoded in `main.py`)
- `flet run main.py` — desktop window, for quick layout checks
- `bash build.sh web|apk|linux|image` — same as `flet run main.py -w`,
  `flet build apk --split-per-abi`, `flet build linux`, and the AppImage packager
- No test suite, linter, or type checker is configured. Verify changes by running
  the app; a source-level sanity check is `python -c "import main"`.

## Layout

- `main.py` — entry point. Sets theme/dark theme, text styles, `page.title`,
  window size, appends the `FilePicker` service, mounts `GymAppView` in a
  `SafeArea`, attaches `page.navigation_bar`, then calls `update_data()`.
- `ui/views.py` — `GymAppView(ft.Column)`: builds the 3-tab scaffold, swaps tab
  panels on nav change, and exposes `update_data()` which pushes fresh DB rows
  into all tabs.
- `ui/usage_tab.py` — "Registrar": machine dropdown, weight field, last-used hint.
- `ui/history_tab.py` — "Historial": grouped-by-machine cards with per-record
  delete, plus export/import via a `BottomSheet` opened from the only FAB.
- `ui/machines_tab.py` — "Máquinas": create/rename/delete, SVG preview.
- `ui/texts.py` — every user-facing string (dicts: `NAVIGATION`, `COMMON`, `USAGE`,
  `HISTORY`, `MACHINES`, `IMPORT`, `EXPORT`, `ERRORS`, `DATE`). Never hardcode UI text.
- `ui/utils.py` — `ButtonStyles`, `_DialogsMixin` (`_show_snackbar`, `_show_error`,
  `_show_message_dialog`), `format_date`, `is_dark_theme`.
- `database.py` — `GymDatabase`: `get_summary`, `get_machines`, `get_usage_history`,
  `get_latest_usage`, `log_use`, `add_machine`, `rename_machine`, `delete_machine`,
  `delete_usage`, `delete_usage_by_machine_weight_date`, `replace_data`.
- `machine_images.py` — machine-name → SVG key mapping; files in `assets/machines/`.
- `xlsx_export.py` / `xlsx_import.py` — Excel I/O with stdlib `zipfile` + XML,
  no `openpyxl`.
- `build/` — generated output, never edit.

## Conventions

- Mobile-first: vertical touch layout, `ft.ListView` or
  `ft.Column(scroll=ft.ScrollMode.AUTO)`, generous tap targets. The root is already
  wrapped in `ft.SafeArea` in `main.py`.
- Prefer `control.update()` over `page.update()`; `page.update()` only when the
  whole tree changes.
- After any DB mutation call the tab's `on_refresh` callback, which funnels into
  `GymAppView.update_data()`. Don't render tabs directly from outside.
- Dialogs: `ft.AlertDialog(modal=True)`, actions as `ft.OutlinedButton` with
  `styles.dialog` / `styles.dialog_destructive`, `actions_alignment=ft.MainAxisAlignment.END`.
  The bottom sheet in `history_tab.py` uses `show_drag_handle=True`; `AlertDialog`
  does not support it.
- Messages: `_show_snackbar` (2s, horizontal dismiss) for confirmations,
  `_show_error` for failures. Both go through `page.show_dialog` / `page.pop_dialog`,
  not the deprecated `page.snack_bar` / `page.dialog` fields.
- Verify Flet API before use: `python -c "import flet as ft; print(hasattr(ft, 'X'))"`
  or `dir(ft)`. This project pins 1.0.5 and uses the newer APIs (`ft.Icons`,
  `ft.Colors`, `page.show_dialog`, `ft.run`). Read the installed source rather than
  trusting memory when a name is uncertain.
- Cards use `RoundedRectangleBorder(radius=20)`; text inputs use
  `OutlineInputBorder(border_radius=20)`; buttons use radius 24 via `ButtonStyles`.

## Material baseline

Trust the code over this line, but currently: bottom `NavigationBar` with 3 tabs,
cards r20, outlined inputs r20, `AlertDialog`s, bottom sheet with drag handle,
2s snackbars, `color_scheme_seed=ft.Colors.BLUE` with explicit light/dark text
themes (18–24px).

## Known gaps

This section is the single source of truth for pending work — update it when you
finish or discover something instead of creating other status docs.

- No top app bar (`page.appbar` is unset).
- No explicit icon / adaptive-icon config in `pyproject.toml` (`[tool.flet]` only
  has `org` and `product`; Flet falls back to `assets/icon.png`).
- No elevation on button styles.
- FAB exists only in the history tab; machines tab has none.
- Snackbars have no action button.

## Cautions

- **No git operations in this workspace**: no `add`, `commit`, `push`, `pull`, or
  remote sync. All changes stay local.
- `gym.db` is runtime data created on first launch — don't treat it as source.
- `replace_data()` truncates both tables; only use it for the import flow.
- `delete_usage_by_machine_weight_date()` matches on (machine, weight, date), so
  duplicate identical records are removed together; prefer `delete_usage(id)` when
  an id is available.
