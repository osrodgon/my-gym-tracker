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

- `main.py` — entry point. Builds the light/dark `Theme` from `ui/design.py`
  tokens, sets `page.title`, window size, appends the `FilePicker` service,
  mounts `GymAppView` in a `SafeArea`, attaches `page.navigation_bar`, then calls
  `update_data()`.
- `ui/views.py` — `GymAppView(ft.Column)`: builds the 3-tab scaffold, swaps tab
  panels on nav change, and exposes `update_data()` which pushes fresh DB rows
  into all tabs.
- `ui/usage_tab.py` — "Registrar": machine dropdown, weight field, last-used hint.
- `ui/history_tab.py` — "Historial": grouped-by-machine cards with per-record
  delete, plus export/import via a `BottomSheet` opened from the only FAB.
- `ui/machines_tab.py` — "Máquinas": create/rename/delete, SVG preview.
- `ui/texts.py` — every user-facing string (dicts: `NAVIGATION`, `COMMON`, `USAGE`,
  `HISTORY`, `MACHINES`, `IMPORT`, `EXPORT`, `ERRORS`, `DATE`). Never hardcode UI text.
- `ui/design.py` — Material 3 tokens: `SCALE`, `dp()`, radii, padding and type
  sizes. Every shape/size in the app derives from here.
- `ui/utils.py` — `ButtonStyles`, `create_dropdown`, `_DialogsMixin`
  (`_show_snackbar`, `_show_error`, `_show_message_dialog`), `format_date`,
  `is_dark_theme`.
- `database.py` — `GymDatabase`: `get_summary`, `get_machines`, `get_usage_history`,
  `get_latest_usage`, `log_use`, `add_machine`, `rename_machine`, `delete_machine`,
  `delete_usage`, `delete_usage_by_machine_weight_date`, `replace_data`.
- `machine_images.py` — machine-name → SVG key mapping; files in `assets/machines/`.
- `xlsx_export.py` / `xlsx_import.py` — Excel I/O with stdlib `zipfile` + XML,
  no `openpyxl`.
- `build/` — generated output, never edit.

## Conventions

- `README.md` is the user-facing documentation and is written in Spanish. Update
  it in the same change whenever user-visible behaviour, requirements, commands,
  build flow, data rules or supported platforms change. Don't leave it stale;
  `AGENTS.md` stays the internal source of truth for pending work and conventions.
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
- Dropdowns are built with `ui.utils.create_dropdown()` (field border, padding
  and menu height); their `DropdownOption`s take `styles.menu_item` so the
  expanded rows follow `design.MENU_ITEM_PADDING`. Type sizes stay at the call
  site (`text_size`, `label_style`) so a dropdown never sets its own font size.
  The menu panel's shape comes from `Theme.dropdown_theme` in `main.py`.
- Cards use `RoundedRectangleBorder(radius=design.CARD_RADIUS)`; text inputs use
  `OutlineInputBorder(border_radius=design.FIELD_RADIUS)` with
  `content_padding=design.FIELD_CONTENT_PADDING`; buttons use the M3 full
  shape (`ft.StadiumBorder()`) with `design.BUTTON_PADDING` via `ButtonStyles`,
  and the main action of a screen uses the taller `ButtonStyles.primary`. Never
  hardcode a radius, padding or font size: import it from `ui/design.py`.
- FABs are page-level controls (`page.floating_action_button`, shown above
  `page.navigation_bar`), not part of a tab panel. `GymAppView` assigns the
  selected tab's `fab` in `_sync_floating_action_button()` (Historial, Máquinas)
  and clears it on Registrar. Both FABs are mini, and `_summary_list` and
  `_machine_list` keep 56px of bottom padding (40 + 16 margin).
- Weights are floats in the DB and are shown with `format_weight()` (`ui/utils.py`),
  which uses the Spanish comma and always keeps a decimal (`80` → `80,0`). The
  weight field accepts only a comma decimal separator; a dot is rejected with a
  snackbar message.

## Material baseline

Trust the code over this line, but currently: bottom `NavigationBar` with 3 tabs,
cards r15, outlined inputs r5, dropdown menus r5 with ~60dp item rows,
`AlertDialog`s r35, bottom sheet with drag handle, 2s snackbars,
`color_scheme_seed=ft.Colors.BLUE` with explicit light/dark text themes
(17.5–27.5px). Every token scales from `SCALE = 1.25` in `ui/design.py`.

## Known gaps

This section is the single source of truth for pending work — update it when you
finish or discover something instead of creating other status docs.

### Code issues

1. `get_machine_image_svg()` raises `KeyError` for a key missing from
   `MACHINE_IMAGES` instead of falling back to "Sin imagen".
2. Excel export omits `machines.image_key`.
3. Excel import recomputes `image_key` from the machine name, so exported images
   come back missing or changed.
4. History delete has no `sqlite3.Error` handling, so a DB failure escapes as an
   uncaught exception.
5. Saving a usage gives no success feedback.
6. Export gives no feedback: `_on_export_history_click` ignores the value returned
   by `save_file`, so a cancel looks like a success.
7. `HistoryTab.render()` rebuilds every control, collapsing open `ExpansionTile`s
   on any refresh.
8. Brightness changes repaint only the usage-tab preview; an open machine dialog
   keeps stale colours.
9. `build.sh image` prefers `assets/icon_linux.png`, which does not exist, so it
   silently falls back to `assets/icon.png`.
10. The xlsx headers (`Fecha`, `Máquina`, `Peso (kg)`) are hardcoded in
    `xlsx_export.py` and `xlsx_import.py`.
11. Import error messages are hardcoded in `xlsx_import.py` instead of `ERRORS`.
12. `main.py` calls the private `GymAppView._on_platform_brightness_change`.
13. `GymDatabase.delete_usage(id)` is never called.

### Android design guidelines

1. Snackbars use 2s and the fixed behaviour, so long messages (weight
   validation) are hard to read with large text, and they have no action button
   (no undo after a delete).
2. Creating and editing a machine uses a modal `AlertDialog` with a name field,
   an image `Dropdown` and a preview. M3 reserves `AlertDialog` for short
   decisions; a multi-field form should be a full-screen dialog or an in-tab
   editing view, especially with large text and the keyboard open.
3. Dialog actions use `OutlinedButton`/`FilledButton` where M3 expects
   `TextButton`, and the destructive action adds a border instead of using the
   `error` colour alone.
4. FABs use `CircleBorder`; M3 uses a 16dp rounded square (20dp at the 1.25×
   scale) for small FABs.
5. No adaptive-icon config in `pyproject.toml`; Android falls back to
   `assets/icon.png`.

## Cautions

- **No git operations in this workspace**: no `add`, `commit`, `push`, `pull`, or
  remote sync. All changes stay local.
- `gym.db` is runtime data created on first launch — don't treat it as source.
- `log_use()` always stamps today's date on purpose: the app is meant to be used
  at the machine, so backfilling past usages is out of scope.
- `replace_data()` truncates both tables; only use it for the import flow.
- `delete_usage_by_machine_weight_date()` matches on (machine, weight, date).
  A unique index on `usages(machine_id, date)` guarantees at most one row per
  machine and day, so the match is exact; `delete_usage(id)` is unused.
- `usages` has a unique index on `(machine_id, date)`: never insert a second row
  for the same machine and day. Check with `get_usage_for_date()` and use
  `update_usage_weight()` to overwrite. Imports deduplicate in `replace_data()`.
- **No top app bar by design**: don't add `page.appbar`; the app deliberately has
  no app bar, now or in the near future. `page.title` only sets the
  browser/window title.
- **No screen headings by design**: the navigation bar label is enough, so don't
  render a heading inside each tab or re-add the removed `heading` strings.
