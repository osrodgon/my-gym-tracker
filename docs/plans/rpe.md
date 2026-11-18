# Plan: perceived effort (RPE) + weight delta + personal record

Status: **designed, not implemented**. Nothing in the code depends on this doc
yet; `database.py`, `ui/texts.py`, `ui/usage_tab.py`, `ui/history_tab.py`,
`xlsx_export.py` and `xlsx_import.py` are untouched.

Mockups: `docs/mockups/e-registrar-rpe.png` is the reference for the Registrar
tab, `c-historial-pr.png` for the Historial badge. The other files in that
folder are the discarded variants (see "Rejected alternatives").

## Decisions (locked by the user)

- RPE with **three levels**, not the 1–10 scale.
- Weight delta as a **suffix inside the weight field**, not in the banner
  (variant B of the mockups).
- **PR only in Historial**, as a badge next to the machine name. It does not
  appear in the Registrar tab.

## Why these three live together

All three answer "how is this machine going?", so they share one data change
(`usages.rpe`) plus two pure derivations (delta, PR) that need no schema.

## Registrar layout

Space was the hard constraint. Current vertical budget at 412×892 dp:

| Row | Height | Notes |
| --- | --- | --- |
| dropdown | 56 | unchanged |
| banner | 55 | unchanged height, gains a trailing RPE chip |
| image card | flexible | currently ~447 dp, drawing ~304 dp |
| **RPE selector** | **48** | new |
| weight + reps | 78 | unchanged |
| save button | 66 | unchanged, stays pinned at the bottom |

The new row is taken from the image card, which keeps the drawing intact
because the card has ~60 dp of slack below the illustration. Nothing else moves,
so the save button stays in the thumb zone and the fields stay reachable with
the keyboard open.

- Control: `ft.SegmentedButton` (present in Flet 1.0.5) with
  `segments=[ft.Segment(value="6"|"8"|"10", label=USAGE["rpe_low"|...])]`,
  `allow_empty_selection=True`, `show_selected_icon=False`, `selected=[]`.
  Tapping the active segment clears it, so "no effort" is a real state.
- Placement: own `ft.ResponsiveRow` between `self._card_area` and `inputs_row`,
  with `col={"xs": 12}` on the button (same pattern as the text fields).
- Three levels, not ten: it is used standing, one-handed, tapping with a thumb;
  ten targets in 412 dp are 30 dp wide. Stored as 6 / 8 / 10 so the numbers stay
  standard and the labels can change later without migrating data.

### Weight delta

- A persistent `ft.Text` control assigned once as `weight_input.suffix`; mutate
  its `.value`/`.color`, never recreate the field (Flet 1.0.5 keeps `Dropdown`
  labels on `value`-only updates; the same caution applies to field suffixes).
- Value: typed weight minus the machine's latest weight, one decimal, Spanish
  comma, `USAGE["delta_up"]` (`▲ 2,5`) in `ft.Colors.PRIMARY` or
  `USAGE["delta_down"]` (`▼ 2,5`) in `ON_SURFACE_VARIANT`. Hidden when the field
  is empty, unparseable, equal to the last weight, or no machine is selected.
- Recomputed from `_clear_weight_error` (already the field's `on_change`).
- Needs `self._latest_weight` cached by `_refresh_selection`.

### Banner

- Text becomes `USAGE["latest_prefix"]` = `"Último: "` (was `"Último registro: "`).
  The 64 px saved are what makes room for the chip; it also matches the
  Historial subtitle wording.
- Trailing chip `USAGE["rpe_badge"]` = `"RPE {value}"` showing the **last**
  recorded RPE, `ft.Colors.PRIMARY_CONTAINER` background, `ON_PRIMARY_CONTAINER`
  text, `design.FONT_BODY_SMALL`, radius `design.dp(8)`, hidden when the last
  record has no RPE.
- Measured budget: banner inner width 654 px at 2x; text ends at 585 and the chip
  is ~106 px wide, so it fits with margin, even with 3-digit weights.
- Rebuild the chip's `Text` instead of mutating spans, same reason as the
  existing `_latest_usage_slot`.

## Historial

- PR computed in Python from the rows already loaded (`get_summary`), no extra
  query: `max(entries, key=lambda e: (weight, reps))`. Definition: heaviest set,
  more reps breaking a tie.
- Badge `HISTORY["personal_record"]` = `"★ PR {value}"` (value = `60,0 kg`) in a
  `ft.Row(wrap=True, spacing=dp(8))` with the machine name, so a long name wraps
  instead of overflowing into the chevron.
- Per-record RPE goes in `ft.ListTile.subtitle` (`HISTORY["rpe"]`), which only
  grows the row when the record has one. The trailing row is full
  (date + series + delete button), hence the subtitle rather than inline text.
- `render()` unpacking changes to 7 columns.

## Data model

- `usages.rpe INTEGER` nullable, added with `ALTER TABLE` in `_init_db`, next to
  the existing `reps` migration.
- **No backfill.** Unlike `reps`, a NULL RPE is meaningful: "no effort rating".
  Never reuse `DEFAULT_REPS` logic here.
- Validated in the UI only (1–10), not with a CHECK constraint, consistent with
  the rest of the schema.
- The unique index `(machine_id, date)` stays: this is one RPE **per machine and
  day**, not per set. Per-set RPE would need a `sets` child table and dropping
  that index; out of scope.
- `database.py` changes:
  - `get_summary` → `(id, machine_id, name, weight, reps, rpe, date)`
  - `get_usage_history` → `(date, name, weight, reps, rpe, image_key)`
  - `get_latest_usage` → `(weight, reps, rpe, date)`
  - `get_usage_for_date` → `(id, weight, reps, rpe)`
  - `get_personal_record(machine_id)` → `(weight, reps, date)`; only used if a
    future screen needs the PR without the full history
  - `log_use(machine_id, weight, reps, rpe=None)`
  - `update_usage(usage_id, weight, reps, rpe=None)`
  - `replace_data(machines, usages)` with `(date, name, weight, reps, rpe)`
    tuples; duplicates still keep the last row per machine/day

## Strings (`ui/texts.py`)

```python
SERIES["rpe"] = "RPE {value}"
USAGE |= {
    "latest_prefix": "Último: ",   # changed
    "rpe_low": "Fácil",
    "rpe_mid": "Justo",
    "rpe_high": "Al límite",
    "rpe_badge": "RPE {value}",
    "delta_up": "▲ {value}",
    "delta_down": "▼ {value}",
}
HISTORY |= {"personal_record": "★ PR {value}", "rpe": "RPE {value}"}
EXPORT["headers"] = ("Fecha", "Máquina", "Peso (kg)", "Repeticiones", "RPE", "Imagen")
IMPORT["invalid_rpe"] = "El RPE de «{machine}» debe ser un número entero entre 1 y 10."
```

`ui/utils.py` gains `format_set(weight, reps, rpe)`: `format_series(...)` plus
` · RPE n` when RPE is present. The overwrite dialog reuses it for both
`{current}` and `{new}`, so its wording does not change.

## Excel round trip

`xlsx_export.py`: `_append_row` must emit columns A–F (currently A–E) and
`_only_first_image` slices `row[:5]`.

`xlsx_import.py` must keep accepting every historical shape:

| Columns | Headers | reps | rpe | image |
| --- | --- | --- | --- | --- |
| 6 | Fecha, Máquina, Peso, Repeticiones, RPE, Imagen | yes | yes | yes |
| 5 | Fecha, Máquina, Peso, Repeticiones, Imagen | yes | no | yes |
| 4 | Fecha, Máquina, Peso, Repeticiones | yes | no | name fallback |
| 3 | Fecha, Máquina, Peso | default 12 | no | name fallback |

The 5-column shape is the current 3.0.x export, so it must not be mistaken for
the new 6-column one: detect `E == "Imagen"` explicitly. `read_row` reads A–F.
RPE parsing: integer 1–10, `IMPORT["invalid_rpe"]` otherwise, empty → NULL.

## Flet 1.0.5 notes

- `ft.SegmentedButton` and `ft.Segment` exist; `Segment(value, label)` and
  `selected` is a list of the `value` strings.
- `ft.Positioned` does **not** exist (the mockups overlay by setting `top`/
  `right` on a `Container`), but that is irrelevant here.
- `TextField.suffix` accepts a control; verify a value update repaints before
  relying on it, otherwise rotate `key` the way `reset()` does for the dropdown.

## Verification checklist

- `python -c "import main"`.
- Temp-DB smoke test: log with and without RPE, overwrite, `get_summary`.
- Excel round trip: 6-column export → import; 5-column and 3-column fixtures.
- Save with the keyboard open: the RPE row and the button must stay reachable
  and the card must clip, not squeeze.
- Dark theme: chip and delta contrast.

## Docs to update in the same change

- `README.md` (Spanish, user-facing): effort field, delta, PR.
- `docs/manual.md` + `docs/screenshots.py`: the new row shifts the Registrar
  coordinates. `WEIGHT_FIELD`, `REPS_FIELD`, `SAVE_BUTTON` move down ~48 dp
  (measure the first screenshot, do not guess); `MACHINE_DROPDOWN`,
  `REGISTRAR_HEADER` and the nav bar points stay. Add the RPE tap to the demo
  run so the shot shows a selected level.
- `AGENTS.md`: Registrar layout, `database.py` method list, Excel column count,
  and this plan's status.

## Rejected alternatives

- **RPE 1–10 in one row**: 30 dp targets, unusable one-handed.
- **Delta in the banner** (`a-registrar-delta-banner.png`): fits, but spends the
  banner on a number that only makes sense while typing the weight.
- **PR chip over the machine drawing** (`a`/`d` mockups): free space, but the
  user only wants the PR in Historial.
- **Five-chip row / `ft.Chip`**: more taps to reason about than a segmented
  control, and no M3 outline/selected semantics for free.
- **Per-set RPE**: contradicts the `(machine_id, date)` unique index.

## Open questions

- Does the RPE selector need a label or icon for first-time users, or are the
  three words self-explanatory? (The mockup has no label to save height.)
- Should the snackbar say "nuevo récord" when the saved set beats the PR? It
  would need `get_personal_record` before the insert; the PR badge in Historial
  already covers discovery.
