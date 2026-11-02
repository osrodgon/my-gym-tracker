# Mi Gimnasio

Aplicación para llevar un seguimiento de los entrenamientos en máquinas de gimnasio. Permite registrar el peso utilizado, consultar el último registro por máquina y exportar el historial a Excel.

## Requisitos

- Python 3
- pip

La interfaz está creada con Flet. La dependencia está declarada en [`requirements.txt`](requirements.txt).

## Instalación y ejecución

Desde la raíz del proyecto:

```bash
python -m pip install -r requirements.txt
python main.py
```

## Notas
Hay un problema con el fichero `flet.yaml` donde el nombre de la aplicación para Android no se interpreta y pone siempre por defecto el nombre de la carpeta donde reside el proyecto. Para que coga el nombre correcto, hay que editar el fichero `AndroidManifest.xml` que se puede encontrar en la carpeta `build` (dentro de la parte de android) y asegurarse que la linea `android:label="myGym"` contiene el nombre de la aplicación que queremos que tenga en android.