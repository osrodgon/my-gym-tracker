# Mi Gimnasio 🏋️

Aplicación móvil y web para llevar un seguimiento de los entrenamientos en máquinas de gimnasio. Construida con [Flet](https://flet.dev/) (Python), permite registrar el peso utilizado en cada máquina, consultar el historial de entrenamientos y exportar/importar datos en formato Excel (.xlsx).

## Funcionalidades

- **Registro de uso**: Selecciona una máquina y registra el peso utilizado. La app muestra automáticamente el último peso registrado como referencia.
- **Historial**: Consulta completa de todos los registros ordenados por fecha. Permite exportar el historial a un archivo Excel e importar datos desde uno.
- **Gestión de máquinas**: Añade, renombra o elimina máquinas. Cada máquina puede tener una imagen SVG asociada que se asigna automáticamente según su nombre.
- **Tema claro/oscuro**: Se adapta automáticamente al tema del sistema.
- **Interfaz en español**: Toda la interfaz de usuario está en español.

## Estructura del proyecto

```
├── main.py               # Punto de entrada de la aplicación
├── database.py           # Capa de acceso a datos (SQLite)
├── machine_images.py     # Mapeo de nombres de máquina a imágenes SVG
├── xlsx_export.py        # Exportación del historial a Excel
├── xlsx_import.py        # Importación de datos desde Excel
├── pyproject.toml        # Metadatos del proyecto y configuración de Flet
├── requirements.txt      # Dependencias Python
├── assets/               # Recursos gráficos (icono, imágenes de máquinas)
├── ui/                   # Módulos de interfaz de usuario
│   ├── views.py          #   Vista principal y navegación
│   ├── usage_tab.py      #   Pestaña de registro de uso
│   ├── history_tab.py    #   Pestaña de historial
│   ├── machines_tab.py   #   Pestaña de gestión de máquinas
│   ├── texts.py          #   Textos y cadenas de la UI
│   └── utils.py          #   Utilidades compartidas (estilos, etc.)
└── .devcontainer/        # Configuración del contenedor de desarrollo
```

## Requisitos

- Python 3
- [Flet](https://flet.dev/) (declarado en `pyproject.toml` y `requirements.txt`)

> **Nota:** El proyecto está preparado para ejecutarse en un **Dev Container**. Las dependencias se instalan automáticamente al crear el contenedor mediante el `postCreateCommand` definido en `.devcontainer/devcontainer.json`, por lo que no es necesario instalarlas manualmente en ese entorno.

## Instalación

Si no se utiliza el Dev Container, instalar las dependencias manualmente:

```bash
pip install -r requirements.txt
```

## Ejecución

Desde la raíz del proyecto:

```bash
python main.py
```

La aplicación se lanzará como aplicación web en `http://localhost:8550`.

## Generación de APK (Android)

Para compilar la APK de Android utilizando Flet:

```bash
flet build apk
```

> [!TIP]
> **Nombre de la aplicación en Android:** el nombre visible de la app se controla con el campo `product` de la sección `[tool.flet]` en `pyproject.toml`. También se puede especificar al compilar con el flag `--product`:
> ```bash
> flet build apk --product "Mi Gimnasio"
> ```
> Si tras compilar el nombre sigue siendo incorrecto, prueba a limpiar la caché de build con `flet build apk --clean`.