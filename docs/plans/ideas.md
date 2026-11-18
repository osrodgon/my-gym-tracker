# Ideas: more information about machine usage

Backlog, not a plan. Each item is a candidate for "what else can the app say
about a machine", ordered by what it costs to add. Nothing here is decided or
scheduled; `docs/plans/rpe.md` covers the only ones picked so far (delta, PR,
RPE).

The hard constraint behind every item: `usages` has a unique index on
`(machine_id, date)`, so today there is **one value per machine and day**.
Anything genuinely per-set needs a child table and dropping that index, and
anything session-wide needs a `sessions` table, because the app has no concept
of a workout session.

## Free: derived from data already stored

No schema change, no extra input, no import/export impact.

- **Delta vs. the last record**: `▲ 2,5 kg` / `▼` next to the typed weight, and
  `+2 reps` where the series is shown. Highest value per line of code. Chosen;
  see `docs/plans/rpe.md`.
- **Personal record per machine**: heaviest set, more reps breaking a tie.
  Chosen for the Historial badge; the same `max()` also enables the snackbar
  "nuevo récord" after saving.
- **Volume**: `kg × reps` per record, plus weekly volume per machine. Pure
  arithmetic on the existing columns; useful as a second axis when the weight
  plateaus but the reps climb.
- **Trend of the last 5–10 records** per machine, as a `ft.LineChart` in the
  expanded history card. Data is already in `get_summary()`.
- **Frequency**: "usada hace 8 días", days since last use, and a hint when a
  machine has not been touched in a long time.
- **What changed since last time**: weight, reps and effort side by side
  (`60,0 → 62,5`, `12 → 10`). Reads better than a single delta for reps.

## Cheap: one more nullable column

One value per machine/day, so the unique index survives. Each one means
touching `database.py`, the Registrar row, the Historial row and the Excel
round trip (see "Export/import" below).

- **RPE** (three levels, 6/8/10). Chosen; designed in `docs/plans/rpe.md`.
- **Short note per record**: `asiento 3, agarre cerrado, molestia en hombro`.
  Free text is the cheapest way to capture machine-specific setup, but it fights
  the fixed-height Registrar layout when the Android keyboard opens, and the
  Historial row has no room for it (a `ListTile.subtitle` grows the row, and
  long notes would need a bottom sheet to read).
- **"Al fallo"** boolean: one flag, no keyboard, shows as a small icon next to
  the series.
- **Goal per machine** (`machines` table, not `usages`): target weight plus a
  rep range (`8–12`). Renders as a progress bar in Registrar and a `82 %` in
  Historial. Belongs to the machine, so it is edited in the Máquinas form, next
  to the drawing dropdown.
- **Fixed setup per machine** (`machines` table): seat/backrest/grip position.
  Shown permanently in Registrar ("asiento 4, respaldo 2") so the user does not
  have to remember it. Optionally copied into the record when saving, which
  turns it into a history column instead of a machine one.
- **Muscle group / machine type** (`machines` table): `empuje` / `tirón` /
  `pierna`, or a free tag. Unlocks filtering the history and a per-group summary
  later; costs one dropdown in the Máquinas form and makes the machine list
  denser.

## Structural: new tables

Each of these changes the shape of the data, so it needs its own plan.

- **`sessions`** (`date`, start, end, notes, overall feeling): the missing
  concept behind "how long did I train" and "what time do I usually train".
  `usages` would gain a `session_id`, which also retires the "one row per
  machine per day" limit naturally.
- **`sets`** child of `usages` (weight, reps, rpe, rest, to-failure per set):
  the real fix for "número de series", which is explicitly out of scope today.
  Blocked by the unique index; also the biggest UI change (a "+ otra serie"
  button and an editor for existing sets).
- **`body_metrics`** (`date`, weight, optional body fat): enables relative load
  (`% del peso corporal`), which is more honest than absolute kg on machines,
  and a weight trend. Needs its own screen or a field in the session flow, so it
  is only worth it if sessions happen.

## Cross-cutting consequences

- Every new column extends `EXPORT["headers"]` and must keep the importer's
  backwards compatibility: it currently accepts 3- and 4-column workbooks, the
  RPE plan adds 5 (today's export) and 6. Add the shape to the table in
  `docs/plans/rpe.md` rather than inventing a second convention.
- New per-machine fields (`goal`, `setup`, `group`) live in `machines`, so they
  travel with the export only if the workbook grows a machine block or repeats
  the values on the machine's first row, which is how `Imagen` already works.
- Anything derived (delta, volume, PR, frequency, trend) must stay out of the
  workbook and the schema: it is recomputed from the rows.
- `update_data()` calls `_usage_tab.reset()` after every save, so the machine
  selection is cleared and with it any "you just set a record" feedback in the
  Registrar tab. If that feedback ever lands there, keep the selection across
  refreshes instead of resetting.

## Asides spotted while designing

- The banner's empty state (`Selecciona una máquina arriba`) duplicates the
  dropdown directly above it. Hiding the banner while no machine is selected
  frees ~44 dp permanently — that alone pays for the RPE row without shrinking
  the image card.
- The Registrar tab is the only screen where the user types; it is also the one
  with a fixed-height card. Any future field (notes, setup) must be planned
  against `FixedHeightArea`, not added as another row.
- Historial rows are already full: date, series and delete button. A fourth
  value per record needs a second line (`subtitle`) or a redesign of the row.
