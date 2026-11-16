# Mi Gimnasio

Aplicación móvil y web para llevar el seguimiento de los entrenamientos en máquinas de gimnasio. Está construida con [Flet](https://flet.dev/) (Python) y guarda los datos en SQLite. Permite registrar el peso usado en cada máquina, consultar el historial y exportar o importar los datos en formato Excel (`.xlsx`).

Está pensada para usarse en el móvil, en el propio gimnasio, con controles y textos grandes.

📖 **[Manual de usuario](docs/manual.md)**: guía paso a paso con capturas de todas las pantallas.

## Funcionalidades

- **Registro de uso**: elige una máquina, introduce el peso y las repeticiones, y guarda. La app muestra el último registro de esa máquina como referencia y, mientras no hayas elegido ninguna, una ilustración genérica. Desliza la imagen hacia los lados para cambiar de máquina sin abrir el desplegable.
- **Un registro por máquina y día**: si ya has registrado esa máquina hoy, la app pide confirmación y sobrescribe el peso y las repeticiones en lugar de crear un duplicado.
- **Validación del peso y las repeticiones**: solo se admite la coma como separador decimal; el peso debe ser mayor que 0 y no superar los 1000 kg. Las repeticiones deben ser un número entero entre 1 y 999, y si dejas el campo vacío se guardan 12 por defecto. Los pesos se muestran siempre con coma y un decimal (`80` → `80,0`), y cada serie como `80,0 kg × 10 reps`.
- **Historial**: registros agrupados por máquina en tarjetas expandibles, ordenados del más reciente al más antiguo, con borrado individual.
- **Exportar e importar Excel**: desde el menú de opciones del historial. La exportación genera un `.xlsx` y la importación sustituye todos los datos actuales (ver [Datos](#datos)).
- **Gestión de máquinas**: crea, renombra y elimina máquinas. Al escribir el nombre se sugiere una imagen WebP, que puedes cambiar o quitar desde el desplegable del formulario, o deslizando la imagen hacia los lados.
- **Tema claro/oscuro**: se adapta automáticamente al tema del sistema; con `--theme` se puede forzar claro u oscuro.
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

### Parámetros de arranque

La app acepta dos parámetros opcionales, tanto en desarrollo como en el AppImage ya compilado:

| Parámetro | Valores | Por defecto |
|---|---|---|
| `--theme` | `system`, `light`, `dark` | `system` |
| `--size` | `pixel-7-pro`, `pixel-10` | `540x960` |

```bash
./build/gymtracker-<versión>-x86_64.AppImage --theme dark --size "Pixel 7 Pro"
```

El lanzador del AppImage recoge los parámetros y los pasa a la app mediante la variable `GYMTRACKER_ARGS` (un argumento por línea). Así tiene que ser: el binario de Flet interpreta cualquier argumento como modo desarrollador, espera que sea la URL de un servidor ya en marcha y no arranca el Python incluido, por lo que la ventana queda en blanco. Si ejecutás el binario sin empaquetar (`build/linux/gymtracker`), usá esa misma variable:

```bash
GYMTRACKER_ARGS=$(printf '%s\n' --theme dark --size "Pixel 7 Pro") \
    ./build/linux/gymtracker
```

`--size` usa el tamaño lógico (dp) del móvil, no su resolución física: la ventana tiene el mismo ancho de 412 dp que la app en el teléfono (`412x892` en el Pixel 7 Pro, `412x923` en el Pixel 10). Sin el parámetro se mantiene la ventana de `540x960` que no corresponde a ningún móvil real.

`--size` solo cambia el tamaño inicial de la ventana; después se redimensiona como cualquier ventana de escritorio.

Con `flet run`, los parámetros van detrás de `--` para que no los interprete Flet:

```bash
flet run main.py -- --theme light
```

## Uso

La app tiene tres pestañas:

| Pestaña | Para qué sirve |
|---|---|
| **Registrar** | Elegir máquina, ver su último registro y guardar el peso y las repeticiones de hoy. |
| **Historial** | Consultar los registros por máquina, borrar uno y abrir el menú de exportar/importar. |
| **Máquinas** | Crear, editar y eliminar máquinas, con su imagen asociada. |

El botón flotante de **Historial** abre las opciones de Excel y el de **Máquinas** crea una máquina nueva.

## Datos

- Los datos se guardan en `gym.db`, una base SQLite que se crea en el primer arranque. No forma parte del código fuente.
- Cada uso se guarda con la fecha del día en que se registra; no se pueden registrar entrenamientos pasados.
- La base impide más de un registro para la misma máquina y día.
- **La importación de Excel sustituye por completo las máquinas y los registros actuales.** Si el archivo trae varias filas para la misma máquina y fecha, se conserva la última.
- La exportación escribe columnas `Fecha`, `Máquina`, `Peso (kg)` y `Repeticiones`. La importación también acepta archivos antiguos de tres columnas, en cuyo caso se asignan 12 repeticiones por defecto.

## Estructura del proyecto

```text
├── main.py               # Punto de entrada de la aplicación
├── app_options.py        # Parámetros de arranque (tema y tamaño de ventana)
├── database.py           # Capa de acceso a datos (SQLite)
├── machine_images.py     # Mapeo de nombres de máquina a imágenes WebP
├── xlsx_export.py        # Exportación del historial a Excel
├── xlsx_import.py        # Importación de datos desde Excel
├── pyproject.toml        # Metadatos del proyecto y configuración de Flet
├── requirements.txt      # Dependencias Python
├── build.sh              # Script de compilación y empaquetado
├── assets/               # Recursos gráficos (icono, imágenes de máquinas)
├── docs/                 # Manual de usuario y capturas (no entra en la app)
│   ├── manual.md         # Manual de usuario en español
│   ├── screenshots.py    # Regenera docs/img/*.png con Playwright
│   └── img/              # Capturas usadas por el manual
├── ui/                   # Módulos de interfaz de usuario
│   ├── views.py          # Vista principal y navegación
│   ├── usage_tab.py      # Pestaña de registro de uso
│   ├── history_tab.py    # Pestaña de historial
│   ├── machines_tab.py   # Pestaña de gestión de máquinas
│   ├── texts.py          # Textos y cadenas de la UI
│   ├── design.py         # Tokens de Material 3 (tamaños, formas y tipos)
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

## Manual de usuario

El manual está en [`docs/manual.md`](docs/manual.md) y usa las capturas de `docs/img/`. Los textos y las imágenes se actualizan en el mismo cambio que la interfaz.

Las capturas se regeneran con el script `docs/screenshots.py`, que arranca la app en modo web contra una base de datos de ejemplo temporal (no toca `gym.db`) y hace clic en la interfaz real:

```bash
pip install playwright
playwright install chromium
python docs/screenshots.py
```

Necesita el puerto `8550` libre. Los clics están medidos sobre la ventana de 412x892 dp, así que un cambio de diseño obliga a revisar las coordenadas del script.

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
