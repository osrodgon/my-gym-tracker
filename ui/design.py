"""Material 3 tokens for the app's large-text design.

Every shape, spacing and type size is derived from a single scale factor so
the whole UI keeps Material 3 proportions while staying comfortable to read on
a phone. Change ``SCALE`` and the app rescales coherently.
"""

import flet as ft

# The app's design is Material 3 at 1.25x, matching its 20px body text
# (Material 3 uses 16px).
SCALE = 1.25


def dp(value: int | float) -> float:
    """Scale a Material 3 dp/sp token by the app's design factor."""
    return value * SCALE


# Colors
SEED_COLOR = "#162B4D"
"""Material 3 seed colour: deep navy. It is the only place to change the app's
hue; the scheme, the nav bar and the input focus colour follow from it."""
SURFACE_PANEL_COLOR = ft.Colors.SURFACE_CONTAINER
"""Tonal surface shared by the bottom `NavigationBar`, the latest-record banner
and the machine image card, so the three read as the same layer."""
IMAGE_OPACITY = 0.75
"""Opacity of the large machine illustrations (Registrar card and the machine
form preview). 0.75 keeps the drawing readable over the tonal surface while
softening it; lower it for a fainter illustration."""
NO_SELECTION_IMAGE_SCALE = 0.78
"""Scale applied to the generic empty-state picture. It is a tall, tightly
framed drawing, so it fills the card and looks oversized next to the machine
illustrations, which leave more margin in their square canvas."""

# Shapes
CARD_RADIUS = dp(12)
FIELD_RADIUS = dp(8)
"""M3 specifies dp(4) for an outlined field, but the app's fields are 1.25x
taller than the 56dp baseline; dp(8) sits between that spec and the rounder
look of the design reference."""
FAB_RADIUS = 16
"""M3 corner for the 56dp FAB. Not scaled: the Flet FAB box is fixed at 56dp."""
MENU_RADIUS = dp(8)
"""Same intermediate corner as the fields, so the menu panel lines up with the
field it opens from."""
DIALOG_RADIUS = dp(28)
SNACKBAR_RADIUS = dp(4)
IMAGE_CARD_RADIUS = dp(16)
"""M3 *large* corner for the highlighted container around a machine drawing."""

# Spacing
FIELD_CONTENT_PADDING = ft.Padding.symmetric(
    horizontal=dp(16), vertical=dp(16)
)
BUTTON_PADDING = ft.Padding.symmetric(
    horizontal=dp(24), vertical=dp(10)
)
PRIMARY_BUTTON_PADDING = ft.Padding.symmetric(
    horizontal=dp(24), vertical=dp(18)
)
DIALOG_BUTTON_PADDING = ft.Padding.symmetric(
    horizontal=dp(12), vertical=dp(10)
)
DIALOG_ACTIONS_PADDING = dp(24)
SHEET_PADDING = ft.Padding.only(
    left=dp(16), right=dp(16), top=dp(16), bottom=dp(32)
)
"""Bottom sheets render outside the page's SafeArea, so the extra bottom inset
keeps the actions clear of Android's system navigation bar."""
BUTTON_ICON_SIZE = dp(24)
LIST_ICON_SIZE = 24
"""Leading icon in list rows. Not scaled: the IconButton beside it keeps
Flutter's fixed 24dp icon box, so a scaled icon would look oversized."""
MENU_PADDING = ft.Padding.symmetric(vertical=dp(8))
MENU_ITEM_PADDING = ft.Padding.symmetric(
    horizontal=dp(12), vertical=dp(14)
)
# Six rows at the scaled item height; Flutter's 300 default would clip at 1.25x.
MENU_MAX_HEIGHT = dp(300)
MENU_ELEVATION = 3
"""M3 elevation level 2, the level surfaces that appear above content use.
Flet's Dropdown defaults to 8, which is a Material 2 value."""
BANNER_PADDING = ft.Padding.symmetric(horizontal=dp(16), vertical=dp(12))
"""Inner padding of the inline "latest record" banner."""
IMAGE_CARD_PADDING = dp(16)
"""Inner margin between the image card and the machine drawing it holds."""

# Type scale
FONT_BODY_LARGE = dp(16)
FONT_BODY_MEDIUM = dp(14)
FONT_BODY_SMALL = dp(12)
FONT_LABEL_LARGE = dp(14)
FONT_TITLE_LARGE = dp(22)
FONT_TITLE_MEDIUM = dp(16)
FONT_DIALOG_TITLE = dp(24)
FONT_NAV_LABEL = dp(12)

# Components
NAV_BAR_HEIGHT = dp(80)
