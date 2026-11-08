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

USAGE = {
    "machine_label": "Máquina",
    "weight_label": "Peso (kg)",
    "select_machine": "Selecciona una máquina para ver su último registro.",
    "no_records": "Aún no hay registros para esta máquina.",
    "latest_weight": "Último uso: {weight} kg · {date}",
    "heading": "Registrar entrenamiento",
    "save": "Guardar uso",
    "duplicate_title": "Registro duplicado",
    "duplicate_message": (
        "Ya has registrado {machine} hoy con {weight} kg. "
        "¿Sobrescribir el registro con {new_weight} kg?"
    ),
    "overwrite": "Sobrescribir",
}

HISTORY = {
    "heading": "Historial por máquina",
    "empty_no_machines": "Todavía no hay máquinas registradas.",
    "empty_no_usages": "Aún no hay usos. Registra uno para ver el historial.",
    "export": "Exportar a Excel",
    "import": "Importar desde Excel",
    "options_tooltip": "Opciones del historial",
    "latest": "Último: {weight} kg · {date}",
    "weight": "{weight} kg",
    "delete": "Eliminar registro",
    "delete_record": "¿Estás seguro de eliminar este registro?",
}

MACHINES = {
    "create_heading": "Nueva máquina",
    "new_name_label": "Nombre",
    "create": "Crear máquina",
    "rename_heading": "Editar máquina",
    "select_to_rename": "Máquina a editar",
    "new_name": "Nombre",
    "rename": "Guardar cambios",
    "delete_heading": "Eliminar máquina",
    "select_to_delete": "Máquina a eliminar",
    "delete": "Eliminar",
    "confirm_title": "Confirmar eliminación",
    "confirm_message": "Se eliminarán también sus registros. ¿Continuar?",
    "add_button": "Añadir máquina",
    "empty_list": "Aún no hay máquinas. Añade una para empezar.",
    "edit_tooltip": "Editar máquina",
    "delete_tooltip": "Eliminar máquina",
    "image_label": "Imagen",
    "no_image": "Sin imagen",
}

IMPORT = {
    "confirm_title": "Confirmar importación",
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
}

EXPORT = {
    "dialog_title": "Exportar historial a Excel",
    "file_name": "historial_gimnasio.xlsx",
}

ERRORS = {
    "title": "No se pudo completar la acción",
    "select_machine": "Selecciona una máquina.",
    "enter_weight": "Introduce el peso utilizado.",
    "invalid_weight": "El peso debe ser un número válido.",
    "duplicate_machine": "Ya existe una máquina con ese nombre.",
    "log_usage": "No se pudo guardar el registro: {error}",
    "add_machine": "No se pudo crear la máquina: {error}",
    "rename_machine": "No se pudieron guardar los cambios: {error}",
    "delete_machine": "No se pudo eliminar la máquina: {error}",
    "enter_machine_name": "Introduce el nombre de la máquina.",
    "select_machine_to_delete": "Selecciona la máquina que quieres eliminar.",
}

DATE = {
    "months_short": (
        "ene", "feb", "mar", "abr", "may", "jun",
        "jul", "ago", "sep", "oct", "nov", "dic",
    ),
}