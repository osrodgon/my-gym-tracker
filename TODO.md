# TODO List - Mi Gimnasio

## 🔴 High Priority (Must Fix)

1. **Add Top App Bar to main view**
   - **File**: `main.py` / `ui/views.py`
   - **Status**: Pending implementation
   - **Reference**: Priority #1 in MATERIAL_DESIGN_MEMORY_BANK.md
   - **Details**: Missing Top App Bar in the main view following Material Design guidelines

2. **Configure adaptive icon en `pyproject.toml`**
   - **File**: `pyproject.toml`
   - **Status**: Pending configuration
   - **Reference**: MATERIAL_DESIGN_MEMORY_BANK.md
   - **Details**: Android adaptive icon setup required for proper launcher icon display

## 🟡 Medium Priority (Should Fix)

3. **Add elevation to button styles**
   - **File**: `ui/utils.py`
   - **Status**: Pending enhancement
   - **Reference**: MATERIAL_DESIGN_MEMORY_BANK.md
   - **Details**: Add elevation property to ButtonStyles for better Material Design compliance

4. **Refine FAB positioning in machines tab**
   - **File**: `ui/machines_tab.py`
   - **Status**: Pending optimization
   - **Reference**: MATERIAL_DESIGN_MEMORY_BANK.md
   - **Details**: Floating Action Button positioning needs refinement in machines tab

5. **Delete selected records in History tab**
   - **File**: `ui/history_tab.py`
   - **Status**: Completed ✅
   - **Reference**: MATERIAL_DESIGN_MEMORY_BANK.md, AGENTS.md
   - **Details**: User-selected record deletion via dropdown in bottom sheet + IconButtons in list tiles
   - **Database**: `delete_usage(usage_id)` and `delete_usage_by_machine_weight_date()` methods already added to `database.py`
   - **Important**: Deletes individual records chosen by user, not bulk database deletion

6. **Expand color scheme documentation**
   - **File**: `ui/texts.py` / `main.py`
   - **Status**: Documentation improvement
   - **Reference**: MATERIAL_DESIGN_MEMORY_BANK.md
   - **Details**: Expand color scheme beyond the basic seed color definition

7. **Add snack bar action buttons**
   - **File**: `ui/` (various tabs)
   - **Status**: Pending enhancement
   - **Reference**: MATERIAL_DESIGN_MEMORY_BANK.md
   - **Details**: Snackbars currently have duration 2s with horizontal dismiss; add action buttons

8. **Delete entire database**
   - **File**: `database.py`
   - **Status**: Pending implementation
   - **Reference**: MATERIAL_DESIGN_MEMORY_BANK.md
   - **Details**: Full database wipe - all records erased permanently
   - **Warning**: This action cannot be undone; use only for development/testing

## 🟢 Low Priority (Nice to Have)

9. **Top App Bar implementation** (duplicate - see #1)
   - **File**: Already covered in High Priority

10. **Material Design full compliance audit**
    - **File**: `MATERIAL_DESIGN_MEMORY_BANK.md`
    - **Status**: Documentation update
    - **Reference**: Memory bank checklist

11. **Spanish localization verification**
    - **File**: `ui/texts.py`
    - **Status**: Verification
    - **Reference**: MATERIAL_DESIGN_MEMORY_BANK.md checklist
    - **Details**: Ensure all text is properly localized in Spanish per the testing checklist

---

## 📊 Progress Tracking

| Priority | Total | Completed | Remaining |
|----------|-------|-----------|-----------|
| **High** | 2 | 0 | 2 |
| **Medium** | 8 | 2* | 6 |
| **Low** | 3 | 0 | 3 |

*\*Completed: Bottom Navigation, Cards, Input Fields, Dialogs, Snackbars, Color Scheme, Typography (per MATERIAL_DESIGN_MEMORY_BANK.md ✅)*

---

## 🛠️ Quick Reference

- **Memory Bank**: `MATERIAL_DESIGN_MEMORY_BANK.md`
- **Project Docs**: `AGENTS.md`
- **Build Commands**: `flet run main.py`, `flet build apk --split-per-abi`
- **Git Policy**: **PROHIBITED** - All changes remain strictly local (see GIT OPERATIONS PROHIBITED section in memory bank)