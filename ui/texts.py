NAVIGATION = {
    "app_name": "Mi Gimnasio",
    "usage": "Registrar",
    "history": "Historial",
    "machines": "Máquinas",
}

COMMON = {
    "cancel": "Cancelar",
    "accept": "Aceptar",
}

SERIES = {
    "with_reps": "{weight} kg × {reps} reps",
}
"""Formatting of a logged set. A record with no rep count is shown with
`database.DEFAULT_REPS` instead of a partial value."""

USAGE = {
    "machine_label": "Máquina",
    "weight_label": "Peso (kg)",
    "reps_label": "Reps (12)",
    "select_machine": "Selecciona una máquina arriba",
    "no_records": "Sin registros previos",
    "latest_prefix": "Último registro: ",
    "save": "Guardar serie",
    "saved": "Serie guardada.",
    "duplicate_title": "Registro duplicado",
    "duplicate_message": (
        "Ya has registrado {machine} hoy ({current}). "
        "¿Sobrescribir el registro con {new}?"
    ),
    "overwrite": "Sobrescribir",
}

HISTORY = {
    "empty_no_machines": "Todavía no hay máquinas registradas.",
    "empty_no_usages": "Aún no hay usos. Registra uno para ver el historial.",
    "export": "Exportar a Excel",
    "import": "Importar desde Excel",
    "options_tooltip": "Opciones del historial",
    "latest": "Último: {value} · {date}",
    "delete": "Eliminar registro",
    "delete_title": "Eliminar registro",
    "delete_record": "¿Estás seguro de eliminar este registro?",
}

MACHINES = {
    "create_heading": "Nueva máquina",
    "new_name_label": "Nombre",
    "create": "Crear máquina",
    "rename_heading": "Editar máquina",
    "new_name": "Nombre",
    "rename": "Guardar cambios",
    "delete": "Eliminar",
    "delete_title": "Eliminar máquina",
    "confirm_message": "Se eliminarán también sus registros. ¿Continuar?",
    "add_button": "Añadir máquina",
    "empty_list": "Aún no hay máquinas. Añade una para empezar.",
    "edit_tooltip": "Editar máquina",
    "delete_tooltip": "Eliminar máquina",
    "image_label": "Imagen",
    "no_image": "Sin imagen",
}

IMPORT = {
    "confirm_title": "Importar datos",
    "confirm_message": (
        "La importación reemplazará todas las máquinas "
        "y registros actuales."
    ),
    "continue": "Continuar",
    "dialog_title": "Importar historial desde Excel",
    "missing_file_data": "No se pudieron leer los datos del archivo.",
    "failed": "No se pudo importar: {error}",
    "completed": "Importación completada: {machines} máquinas y {usages} registros.",
    "result_title": "Resultado de la importación",
    "invalid_headers": "Las columnas deben ser: {columns}.",
    "invalid_reps": (
        "Las repeticiones de «{machine}» deben ser un número entero "
        "entre 1 y 999."
    ),
    "missing_machine": "Hay una fila con datos pero sin nombre de máquina.",
    "usage_without_date": "La máquina «{machine}» tiene datos pero no fecha.",
    "usage_without_weight": "La máquina «{machine}» tiene fecha pero no peso.",
    "invalid_date_or_weight": "Fecha o peso no válido para la máquina «{machine}».",
    "invalid_weight": "El peso de «{machine}» debe ser un número válido.",
    "no_machines": "El Excel no contiene ninguna máquina.",
}

EXPORT = {
    "dialog_title": "Exportar historial a Excel",
    "file_name": "historial_gimnasio.xlsx",
    "headers": ("Fecha", "Máquina", "Peso (kg)", "Repeticiones"),
}

ERRORS = {
    "title": "No se pudo completar la acción",
    "select_machine": "Selecciona una máquina.",
    "enter_weight": "Introduce el peso utilizado.",
    "invalid_weight": (
        "El peso debe ser un número válido. "
        "Usa coma para los decimales (por ejemplo, 55,3)."
    ),
    "weight_out_of_range": "El peso debe ser mayor que 0 y no superar {max} kg.",
    "invalid_reps": (
        "Las repeticiones deben ser un número entero (por ejemplo, 12)."
    ),
    "reps_out_of_range": "Las repeticiones deben estar entre 1 y {max}.",
    "duplicate_machine": "Ya existe una máquina con ese nombre.",
    "log_usage": "No se pudo guardar el registro: {error}",
    "delete_usage": "No se pudo eliminar el registro: {error}",
    "add_machine": "No se pudo crear la máquina: {error}",
    "rename_machine": "No se pudieron guardar los cambios: {error}",
    "delete_machine": "No se pudo eliminar la máquina: {error}",
    "enter_machine_name": "Introduce el nombre de la máquina.",
}

DATE = {
    "months_short": (
        "ene", "feb", "mar", "abr", "may", "jun",
        "jul", "ago", "sep", "oct", "nov", "dic",
    ),
}