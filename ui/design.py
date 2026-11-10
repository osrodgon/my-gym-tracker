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


# Shapes
CARD_RADIUS = dp(12)
FIELD_RADIUS = dp(4)
MENU_RADIUS = dp(4)
DIALOG_RADIUS = dp(28)
SNACKBAR_RADIUS = dp(4)

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
BUTTON_ICON_SIZE = dp(24)
MENU_PADDING = ft.Padding.symmetric(vertical=dp(8))
MENU_ITEM_PADDING = ft.Padding.symmetric(
    horizontal=dp(12), vertical=dp(14)
)
# Six rows at the scaled item height; Flutter's 300 default would clip at 1.25x.
MENU_MAX_HEIGHT = dp(300)

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
