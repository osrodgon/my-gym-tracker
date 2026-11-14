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
  panels on nav change, hides the Máquinas FAB while its form is open, and
  exposes `update_data()` which pushes fresh DB rows into all tabs.
- `ui/usage_tab.py` — "Registrar": machine dropdown, latest-record banner, machine
  drawing card, weight + reps fields and the save button.
- `ui/history_tab.py` — "Historial": grouped-by-machine cards with per-record
  delete, plus export/import via a `BottomSheet` opened from the only FAB.
- `ui/machines_tab.py` — "Máquinas": machine list; create/rename happen in an
  in-tab form (no dialog), delete in a confirmation `AlertDialog`.
- `ui/texts.py` — every user-facing string (dicts: `NAVIGATION`, `COMMON`,
  `SERIES`, `USAGE`, `HISTORY`, `MACHINES`, `IMPORT`, `EXPORT`, `ERRORS`, `DATE`).
  Never hardcode UI text.
- `ui/design.py` — Material 3 tokens: `SCALE`, `dp()`, `SEED_COLOR`,
  `SURFACE_PANEL_COLOR`, `IMAGE_OPACITY`, radii, padding and type sizes. Every
  shape/size in the app derives from here.
- `ui/utils.py` — `ButtonStyles`, `create_dropdown`, `create_text_field`,
  `FixedHeightArea` (card area that keeps its measured height), `_DialogsMixin`
  (`_show_snackbar`, `_show_error`, `_show_message_dialog`), `format_date`,
  `format_weight`, `format_series`, `is_dark_theme`.
- `database.py` — `GymDatabase`: `get_summary`, `get_machines`, `get_usage_history`,
  `get_latest_usage`, `log_use`, `update_usage`, `add_machine`, `rename_machine`,
  `delete_machine`, `delete_usage`, `replace_data`.
- `machine_images.py` — machine-name → asset path mapping; the drawings are WebP
  (`get_machine_image()`), plus two non-selectable assets: `no-selection.webp`
  (the empty state of the Registrar card) and `machine.svg` — the only SVG in the
  app, a monochrome silhouette used as a small icon and tinted with
  `ft.Image.color`. Never set `ft.Image.color` on a WebP drawing: it blends every
  pixel with that colour and flattens the artwork into a solid silhouette.
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
- Creating or renaming a machine is an in-tab form, not a dialog: `MachinesTab`
  swaps `panel.content` between `_list_view` and the form, reports the mode via
  `on_edit_mode_changed` so `GymAppView` hides the FAB, and `reset()` restores
  the list (the view calls it on every nav change). The form is a `Column` with
  a field block (title, name, dropdown, preview) and the actions pinned below it,
  so the buttons stay reachable with the keyboard open: a `ResponsiveRow` with
  `col={"xs": 12, "sm": 6}`, both `styles.primary` so they match in size, full
  width and stacked on xs, side by side from `sm`. The preview sits on the same
  tonal card as the Registrar image, inside the same `FixedHeightArea`, so it
  keeps its size when the keyboard opens instead of shrinking. Android
  back closes
  the form instead of leaving the app: `GymAppView` sets
  `page.views[0].can_pop` to `not editing` and resolves the gesture in
  `on_confirm_pop` (wired in `main.py`), so on the list the back gesture keeps
  its native behaviour.
- Dialogs: `ft.AlertDialog(modal=True)`, actions as `ft.TextButton` with
  `styles.dialog` / `styles.dialog_destructive` (error colour, no border or
  fill), `actions_alignment=ft.MainAxisAlignment.END`. The bottom sheet in
  `history_tab.py` uses `show_drag_handle=True`; `AlertDialog` does not support
  it.
- Messages: `_show_snackbar` (4s, floating, close icon, horizontal dismiss) for
  transient app-level notices; field errors go in `TextField.error` /
  `Dropdown.error_text` and are cleared on change. `_show_error` (modal dialog)
  for failures. All go through `page.show_dialog` / `page.pop_dialog`, not the
  deprecated `page.snack_bar` / `page.dialog` fields.
- Verify Flet API before use: `python -c "import flet as ft; print(hasattr(ft, 'X'))"`
  or `dir(ft)`. This project pins 1.0.5 and uses the newer APIs (`ft.Icons`,
  `ft.Colors`, `page.show_dialog`, `ft.run`). Read the installed source rather than
  trusting memory when a name is uncertain.
- Dropdowns and text fields are built with `ui.utils.create_dropdown()` and
  `ui.utils.create_text_field()`, which set the field border, content padding,
  menu height, `expanded_insets=0`, the read-only M3 selector behaviour and the
  20px text size; a call site only overrides what genuinely differs. A dropdown
  still needs `expand=True` to span its parent: inside a `Row`/`ResponsiveRow`
  cell that is what gives it a tight width, and `create_dropdown()` cannot add it
  itself because in a `Column` it would grow vertically. Their `DropdownOption`s
  take `styles.menu_item` so the expanded rows follow
  `design.MENU_ITEM_PADDING`. The menu panel's shape and its M3 level-2 elevation
  come from `Theme.dropdown_theme` in `main.py`.
- Cards use `RoundedRectangleBorder(radius=design.CARD_RADIUS)`; text inputs use
  `OutlineInputBorder(border_radius=design.FIELD_RADIUS)` with
  `content_padding=design.FIELD_CONTENT_PADDING`; buttons use the M3 full
  shape (`ft.StadiumBorder()`) with `design.BUTTON_PADDING` via `ButtonStyles`,
  and the main action of a screen uses the taller `ButtonStyles.primary`. Never
  hardcode a radius, padding or font size: import it from `ui/design.py`. Text
  fields and dropdowns leave `label_style` unset: the inline label inherits
  `titleMedium` (20px) like the rest of the app, and a smaller `label_style`
  makes that field look out of place. The border `side` stays `None` on purpose,
  so M3 resolves the outline/primary/error colour and width per state.
- The Registrar weight and reps fields sit in the same `ResponsiveRow` with
  `vertical_alignment=ft.CrossAxisAlignment.START`: an error under one field
  must not push the neighbouring box down.
- The Registrar machine dropdown is cleared in place on every `reset()`. Flet
  1.0.5 keeps the previous label when only `value` is cleared (the text lives in
  the Flutter `DropdownMenu` controller), so `reset()` also blanks
  `Dropdown.text` and rotates `Dropdown.key`, which forces the widget to be
  rebuilt empty.
- The Registrar latest-record banner rebuilds its `ft.Text` on every state
  change (a `Container` slot whose `content` is replaced) instead of mutating
  `Text.spans`: replacing rich-text spans on an update left the banner blank in
  Flet 1.0.5. The fresh control renders fine and still wraps to a second line,
  because the slot sits in a `Row` with `expand=True`.
- The Registrar image card and the machine form preview never shrink. Both sit
  inside `ui.utils.FixedHeightArea`, the flexible child of their `Column`: a
  clipping `ft.Stack` whose only child is positioned to all four edges, so it
  fills the area from the first frame; the area's `on_size_change` then copies
  the measured height onto the card, unpinning its `bottom`. The height only
  grows, each burst is debounced (the first frames and the keyboard animation
  report intermediate values) and nothing is applied while
  `page.media.view_insets.bottom > 0`, so the keyboard shrinks the area and the
  area clips the card instead of squeezing it, while the rows below (Registrar
  fields and save button, form actions) stay pinned and reachable. A `Stack` is
  required: inside a `Container` the child is clamped to the parent's height and
  a fixed height would not survive the keyboard. No arithmetic with
  `page.height`. The card is always visible and always shows a picture — the
  generic one before a machine is picked, and the generic one too when the
  chosen machine has no drawing.
- Accepted consequences of that fixed height (not bugs to fix): the card keeps
  its size when the window shrinks (rotation, desktop resize) instead of
  recalculating, so it gets clipped; and a header that grows at runtime (a
  two-line banner, or the machine dropdown's `error_text`) shrinks the area and
  clips more of the drawing. The rows below stay reachable in both cases.
- Both cards are rebuilt when needed: the Registrar one once per session, the
  form preview on every open, so each gets its own measurement.
- Swiping the image card moves through the list it belongs to: in Registrar it
  selects the previous/next machine (the dropdown order), and in the create/rename
  form it changes the image dropdown (including "Sin imagen"). Both wrap around,
  and both are `ft.GestureDetector(on_horizontal_drag_end=...)` with a
  `_SWIPE_VELOCITY` threshold so a stray drag does not switch anything.
  Changing the dropdown from code must also call `image_dropdown.update()`:
  assigning `value` alone leaves the field label showing the previous option
  until the widget is touched again, which is why the form routes every programmatic
  change through `_select_image()`.
- FABs are page-level controls (`page.floating_action_button`, shown above
  `page.navigation_bar`), not part of a tab panel. `GymAppView` assigns the
  selected tab's `fab` in `_sync_floating_action_button()` (Historial, Máquinas)
  and clears it on Registrar. Both FABs are regular and use
  `RoundedRectangleBorder(radius=design.FAB_RADIUS)` (M3's 16dp corner for a
  56dp FAB; the token is not scaled because Flet fixes the FAB box at 56dp)
  rather than a circle, and `_summary_list` and `_machine_list` keep 72px of
  bottom padding (56 + 16 margin).
- Weights are floats in the DB and are shown with `format_weight()` (`ui/utils.py`),
  which uses the Spanish comma and always keeps a decimal (`80` → `80,0`). The
  weight field accepts only a comma decimal separator; a dot is rejected with an
  inline field error that clears as soon as the value changes. Reps are integers
  between 1 and 999, and an empty field saves `database.DEFAULT_REPS` (12) rather
  than raising an error. A set is rendered with `format_series()`
  (`80,0 kg × 10 reps`). A record stored without reps — logged before 2.2.0 or
  imported from a three-column workbook — is treated as `database.DEFAULT_REPS`
  too, both in the table and in `format_series()`.

## Material baseline

Trust the code over this line, but currently: bottom `NavigationBar` with 3 tabs
(outlined icons at rest, filled when selected), cards r15, outlined inputs r10,
dropdown menus r10 with ~60dp item rows and elevation 3, rounded-square FABs r16,
`AlertDialog`s r35, bottom sheet with drag handle, 4s floating snackbars,
`color_scheme_seed=design.SEED_COLOR` (`#162B4D`, deep navy) with explicit
light/dark text themes (15–27.5px). Every token scales from `SCALE = 1.25` in
`ui/design.py`.

## Known gaps

This section is the single source of truth for pending work — update it when you
finish or discover something instead of creating other status docs.

### Code issues

1. `get_machine_image_svg()` raises `KeyError` for a key missing from
   `MACHINE_IMAGES` instead of falling back to "Sin imagen".
2. Excel export omits `machines.image_key`.
3. Excel import recomputes `image_key` from the machine name, so exported images
   come back missing or changed.
4. Export gives no feedback: `_on_export_history_click` ignores the value returned
   by `save_file`, so a cancel looks like a success.
5. `HistoryTab.render()` rebuilds every control, collapsing open `ExpansionTile`s
   on any refresh.
6. Brightness changes repaint only the usage-tab preview; an open machine form
   keeps stale colours in its SVG preview and row icons until the next render.
7. `build.sh image` prefers `assets/icon_linux.png`, which does not exist, so it
   silently falls back to `assets/icon.png`.
8. Remaining import errors (invalid zip, empty sheet, invalid Excel shared string)
   are still hardcoded in `xlsx_import.py` instead of `IMPORT`.
9. `main.py` calls the private `GymAppView._on_platform_brightness_change`.

## Cautions

- **No git operations in this workspace**: no `add`, `commit`, `push`, `pull`, or
  remote sync. All changes stay local.
- `gym.db` is runtime data created on first launch — don't treat it as source.
- `log_use()` always stamps today's date on purpose: the app is meant to be used
  at the machine, so backfilling past usages is out of scope.
- `replace_data()` truncates both tables; only use it for the import flow.
- `usages` has a unique index on `(machine_id, date)`: never insert a second row
  for the same machine and day. Check with `get_usage_for_date()` and use
  `update_usage()` to overwrite both weight and reps. Imports deduplicate in
  `replace_data()`.
- `usages.reps` is nullable in the schema but never stays `NULL`: `_init_db()`
  backfills missing values with `database.DEFAULT_REPS` (12) after the
  `ALTER TABLE`, and `replace_data()` normalises three-column imports. Render sets
  through `format_series()`, which applies the same default.
- **No top app bar by design**: don't add `page.appbar`; the app deliberately has
  no app bar, now or in the near future. `page.title` only sets the
  browser/window title.
- **No screen headings by design**: the navigation bar label is enough, so don't
  render a heading inside each tab or re-add the removed `heading` strings. The
  only exception is the Máquinas create/rename form, which titles itself because
  it replaces the tab's list.
