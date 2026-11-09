# Mi Gimnasio

Aplicación móvil y web para llevar el seguimiento de los entrenamientos en máquinas de gimnasio. Está construida con [Flet](https://flet.dev/) (Python) y guarda los datos en SQLite. Permite registrar el peso usado en cada máquina, consultar el historial y exportar o importar los datos en formato Excel (`.xlsx`).

Está pensada para usarse en el móvil, en el propio gimnasio, con controles y textos grandes.

## Funcionalidades

- **Registro de uso**: elige una máquina, introduce el peso y guarda. La app muestra el último peso registrado como referencia.
- **Un registro por máquina y día**: si ya has registrado esa máquina hoy, la app pide confirmación y sobrescribe el peso en lugar de crear un duplicado.
- **Validación del peso**: solo se admite la coma como separador decimal; el valor debe ser mayor que 0 y no superar los 1000 kg. Los pesos se muestran siempre con coma y un decimal (`80` → `80,0`).
- **Historial**: registros agrupados por máquina en tarjetas expandibles, ordenados del más reciente al más antiguo, con borrado individual.
- **Exportar e importar Excel**: desde el menú de opciones del historial. La exportación genera un `.xlsx` y la importación sustituye todos los datos actuales (ver [Datos](#datos)).
- **Gestión de máquinas**: crea, renombra y elimina máquinas. Al escribir el nombre se sugiere una imagen SVG, que puedes cambiar o quitar desde el desplegable del diálogo.
- **Tema claro/oscuro**: se adapta automáticamente al tema del sistema.
- **Interfaz en español**: todos los textos visibles están en español.

## Requisitos

- Python 3.10 o superior.
- Flet 1.0.5, declarado en `pyproject.toml` y `requirements.txt`.

> **Nota:** El proyecto está preparado para ejecutarse en un **Dev Container**. Las dependencias se instalan automáticamente al crear el contenedor mediante el `postCreateCommand` de `.devcontainer/devcontainer.json`, así que no hace falta instalarlas a mano en ese entorno.

## Instalación

Fuera del Dev Container:

```bash
pip install -r requirements.txt
```

## Ejecución

Desde la raíz del proyecto:

```bash
python main.py
```

La aplicación arranca como app web en `http://localhost:8550`.

Para abrirla en una ventana de escritorio durante el desarrollo:

```bash
flet run main.py
```

## Uso

La app tiene tres pestañas:

| Pestaña | Para qué sirve |
|---|---|
| **Registrar** | Elegir máquina, ver su último registro y guardar el peso de hoy. |
| **Historial** | Consultar los registros por máquina, borrar uno y abrir el menú de exportar/importar. |
| **Máquinas** | Crear, editar y eliminar máquinas, con su imagen asociada. |

El botón flotante de **Historial** abre las opciones de Excel y el de **Máquinas** crea una máquina nueva.

## Datos

- Los datos se guardan en `gym.db`, una base SQLite que se crea en el primer arranque. No forma parte del código fuente.
- Cada uso se guarda con la fecha del día en que se registra; no se pueden registrar entrenamientos pasados.
- La base impide más de un registro para la misma máquina y día.
- **La importación de Excel sustituye por completo las máquinas y los registros actuales.** Si el archivo trae varias filas para la misma máquina y fecha, se conserva la última.
- La exportación escribe columnas `Fecha`, `Máquina` y `Peso (kg)`.

## Estructura del proyecto

```text
├── main.py               # Punto de entrada de la aplicación
├── database.py           # Capa de acceso a datos (SQLite)
├── machine_images.py     # Mapeo de nombres de máquina a imágenes SVG
├── xlsx_export.py        # Exportación del historial a Excel
├── xlsx_import.py        # Importación de datos desde Excel
├── pyproject.toml        # Metadatos del proyecto y configuración de Flet
├── requirements.txt      # Dependencias Python
├── build.sh              # Script de compilación y empaquetado
├── assets/               # Recursos gráficos (icono, imágenes de máquinas)
├── ui/                   # Módulos de interfaz de usuario
│   ├── views.py          # Vista principal y navegación
│   ├── usage_tab.py      # Pestaña de registro de uso
│   ├── history_tab.py    # Pestaña de historial
│   ├── machines_tab.py   # Pestaña de gestión de máquinas
│   ├── texts.py          # Textos y cadenas de la UI
│   └── utils.py          # Utilidades compartidas (estilos, formato, diálogos)
├── .devcontainer/        # Configuración del contenedor de desarrollo
└── build/                # Directorio generado para builds y AppImage
```

## Compilación

El script `build.sh` reúne las tareas habituales:

| Acción | Comando | Qué hace |
|---|---|---|
| Web | `bash build.sh web` | Ejecuta la app en modo web con `flet run main.py -w`. |
| APK | `bash build.sh apk` | Genera las APKs de Android con `flet build apk --split-per-abi`. |
| Linux | `bash build.sh linux` | Genera la build de escritorio con `flet build linux`. |
| AppImage | `bash build.sh image` | Recompila Linux y genera el AppImage final en `build/`. |

También puedes hacerlo ejecutable y llamarlo directamente:

```bash
chmod +x build.sh
./build.sh web
```

## Generación de APK (Android)

```bash
flet build apk
```

> [!TIP]
> **Nombre de la aplicación en Android:** el nombre visible se controla con el campo `product` de la sección `[tool.flet]` en `pyproject.toml`. También se puede indicar al compilar:
>
> ```bash
> flet build apk --product "Mi Gimnasio"
> ```
>
> Si el nombre sigue saliendo mal, limpia la caché con `flet build apk --clean`.

## Generación de AppImage (Linux)

```bash
bash build.sh image
```

El script recompila la versión Linux y compone el paquete final en `build/`, con el nombre del proyecto, la versión de `pyproject.toml` y la arquitectura:

```text
build/<proyecto>-<versión>-<arquitectura>.AppImage
```

Si solo quieres la build de Linux, sin el AppImage:

```bash
bash build.sh linux
```
