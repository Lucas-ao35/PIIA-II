# Cómo ejecutar una app con streamlit

## Requisitos 

- Python con las dependencias detalladas en `requierements.txt` instaladas
- El proyecto descargado o clonado en el equipo.

## Estructura relevante

La estructura actual del proyecto es la siguiente:

```text
pia2/
├── app/
│   ├── data/
│   │   ├── archives/
│   │   │   └── pharmaconer.zip
│   │   └── pharmaconer/
│   │       └── conll/
│   ├── scripts/
│   │   ├── download_datasets.py
│   │   └── visualize_data.py
│   ├── app.py
│   ├── descargar_datos.bat
│   ├── ejecutar_app.bat
│   ├── README_ejecucion_app.md
│   └── requirements.txt
```
$ \vdots $
```
├── .gitattributes
├── .gitignore
└── README.md
```

La carpeta `app/` actualente contiene el código de la aplicación `app/app.py`, las dependencias `app/requirements.txt`, los scripts auxiliares `app/scripts/` y los lanzadores de Windows. Los datos descargados se encuentran dentro de `app/data/`.

## Pasos

Sitúate en la carpeta `./app/`
~~~cmd
cd app/
~~~

Deberías encontrar `app.py`, `requirements.txt`, `scripts/` y `data/`.

Instala las dependencias 

```bat
python -m pip install -r requirements.txt
```

Descarga los datos necesarios

```bat
python scripts\download_datasets.py
```

Como alternativa, puedes hacer doble clic en `descargar_datos.bat`.

Para consultar las opciones disponibles del script, ejecuta:

```bat
python scripts\download_datasets.py --help
```

Las opciones adicionales de descarga dependerán de los argumentos implementados en el propio script.

Una vez obtenidos los datos ejecuta la aplicación web

```bat
python -m streamlit run app.py
```

Si la aplicación se inicia correctamente, Streamlit mostrará una dirección local, normalmente:

```text
http://localhost:8501
```

Abre esa dirección en el navegador e interactua con la interfaz.

- *Para detener la aplicación, vuelve a la terminal y pulsa **Ctrl+C**.*

- *También puedes iniciar la aplicación haciendo doble clic en `ejecutar_app.bat`.*

## Solución de problemas frecuentes

**`python` no se reconoce como comando**

- Comprueba que Python está instalado y añadido a `PATH`.
- Cierra y vuelve a abrir la terminal después de instalarlo.

**No se encuentra `requirements.txt` o `app.py`**

- Comprueba que la terminal está en `pia2/app/`.
- Ejecuta `dir` para verificar que ambos archivos aparecen.

**`No module named streamlit`**

Instala las dependencias:

```bat
python -m pip install -r requirements.txt
```

Después, vuelve a ejecutar:

```bat
python -m streamlit run app.py
```

**La aplicación no encuentra los datos**

- Comprueba que existen los archivos y directorios esperados dentro de `app/data/`.
- Ejecuta el script de descarga si los datos necesarios no están disponibles.
- Revisa las rutas utilizadas por el código de la aplicación para confirmar qué ubicación espera.

**El archivo `.bat` falla**

- Ejecuta el comando equivalente desde `cmd` para ver el error completo.
- Comprueba que el lanzador se encuentra en `app/` y que las dependencias están instaladas.

**El puerto 8501 está ocupado**

Prueba a utilizar el puerto 8502:

```bat
python -m streamlit run app.py --server.port 8502
```