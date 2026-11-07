# Material Design Memory Bank for Mi Gimnasio

## Project Overview
- **Name**: Mi Gimnasio
- **Framework**: Flet (Python)
- **Goal**: Android app that faithfully follows Google's Material Design interface guidelines
- **Current State**: Functional gym tracking app with SQLite database, can build Android APKs

## ✅ Current Material Design Compliance

| Element | Status | Notes |
|---------|--------|-------|
| **Top App Bar** | ❌ Missing | Not yet implemented |
| **Bottom Navigation** | ✅ Implemented | `ft.NavigationBar` with 3 tabs |
| **FAB (Floating Action Button)** | ✅ Partially | Present in history_tab.py |
| **Cards/Tarjetas** | ✅ Implemented | `Card` with `radius=20` |
| **Input Fields** | ✅ Implemented | `OutlineInputBorder` with `border_radius=20` |
| **Dialogs** | ✅ Implemented | `AlertDialog` with `show_drag_handle=True` |
| **Snackbars** | ✅ Implemented | Duration 2s, horizontal dismiss |
| **Typography** | ✅ Defined | TextStyles in main.py |
| **Color Scheme** | ✅ Basic | `color_scheme_seed=ft.Colors.BLUE` |
| **Adaptive Icons** | ❌ Not configured | Need icon setup for Android |

## 🎯 Priority Recommendations

### 1. Add Top App Bar (Top App Bar)
Following Material Design guidelines, every screen should have a consistent top app bar.

**Location**: `ui/views.py` - `GymAppView._build_navigation()`

```python
def _build_navigation(self) -> None:
    self.app_bar = ft.AppBar(
        title=ft.Text("Mi Gimnasio"),
        center_title=False,
        bgcolor=ft.Colors.SURFACE,
        elevation=1,
        actions=[
            ft.IconButton(icon=ft.Icons.SEARCH, tooltip="Buscar"),
            ft.PopupMenuButton(
                items=[
                    ft.PopupMenuItem(text="Configuración"),
                    ft.PopupMenuItem(text="Cerrar sesión"),
                ]
            ),
        ],
    )
    # Add to page: page.app_bar = self.app_bar
```

### 2. Refine Button Styles with Elevation
Material Design uses elevation (shadows) to indicate interactive surfaces.

**Location**: `ui/utils.py` - `ButtonStyles.__init__()`

```python
base = ft.ButtonStyle(
    shape=ft.RoundedRectangleBorder(radius=24),
    padding=24,
    text_style=ft.TextStyle(size=18, weight=ft.FontWeight.W_500),
    elevation=ft.Elevation(2),  # Material shadow depth
)
```

### 3. Material Color Scheme Expansion
Broaden the color palette beyond the seed color.

**Location**: `main.py` - theme configuration

```python
page.theme = ft.Theme(
    color_scheme_seed=ft.Colors.BLUE,
    # Material Design extends these automatically:
    # primary, secondary, background, surface, error, on-primary, etc.
)
```

### 4. Adaptive Icon for Android
Configure adaptive icon for proper Android display.

**Location**: `pyproject.toml`

```toml
[tool.flet]
icon = "assets/icon.png"  # 512x512 PNG adaptive icon
product = "Mi Gimnasio"
org = "com.osukaru"
```

### 5. FAB Positioning in machines_tab
Consider true FAB placement instead of bottom button.

**Current**: `machines_tab.py` line 103 - `FilledButton` in `ResponsiveRow`
**Recommendation**: Move to `page.floating_action_button` for proper Android positioning.

## 📱 Android Build Considerations

### APK Compilation
```bash
# Build with split ABI for optimal Android size
flet build apk --split-per-abi

# With custom product name
flet build apk --product "Mi Gimnasio"
```

### Required for Release
1. **Icon**: `assets/icon.png` (512x512 PNG, adaptive conformant)
2. **Keystore**: For signing the release APK
3. **Version code/name**: Consider updating `pyproject.toml` version

### Current pyproject.toml Configuration
```toml
[project]
name = "gymtracker"
version = "1.0.0"
...

[tool.flet]
org = "com.osukaru"
product = "Mi Gimnasio"
# Add: icon = "assets/icon.png"
```

## 📋 Material Design Checklist

| Category | Item | Status | Action |
|----------|------|--------|--------|
| **Navigation** | Top App Bar | ❌ | Add `ft.AppBar` with title and actions |
| **Navigation** | Bottom Navigation | ✅ | Verify 3 main items with proper labels |
| **Floating Action** | FAB placement | ⚠️ | Consider true FAB in machines_tab |
| **Components** | Buttons with elevation | ⚠️ | Add `elevation` to `ButtonStyles` |
| **Components** | Input fields | ✅ | Consider `ft.TextFieldTheme` for consistency |
| **Components** | Cards | ✅ | Maintain `radius=20` |
| **Components** | Dialogs with drag handle | ✅ | Keep `show_drag_handle=True` |
| **Visual** | Color scheme | ⚠️ | Expand beyond seed color |
| **Visual** | Adaptive icons | ❌ | Add `icon` to pyproject.toml |
| **Visual** | Typography scales | ✅ | Maintain current TextStyles |
| **Interaction** | Snackbars with action | ⚠️ | Consider adding action button |
| **Interaction** | Bottom Sheet drag handle | ✅ | Keep implementation |
| **Interaction** | Record deletion in history | ⬜ | Add delete option to bottom sheet (see Priority #5) |

## 🔧 Implementation Priority Order

1. **High**: Add Top App Bar to main view
2. **High**: Configure adaptive icon in `pyproject.toml`
3. **Medium**: Add elevation to button styles
4. **Medium**: Refine FAB positioning in machines tab
5. **Medium**: **Add record deletion in History tab** (new feature request)
6. **Low**: Expand color scheme documentation
7. **Low**: Add snack bar action buttons

## 🧪 Testing Checklist for Android

- [ ] App launches with proper Top App Bar
- [ ] Bottom navigation tabs transition smoothly
- [ ] FAB (if present) floats above content
- [ ] Theme switches between light/dark correctly
- [ ] Input fields have proper Material outlines
- [ ] Dialogs have drag handle on bottom sheet
- [ ] Snackbars appear at bottom of screen
- [ ] Icon displays correctly in Android launcher
- [ ] APK installs without errors
- [ ] All text strings are properly localized (Spanish)

---
*Last updated: $(date +%Y-%m-%d)*
*Project: Mi Gimnasio - Gym tracking application*