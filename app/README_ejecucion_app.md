# Guía de ejecución del prototipo CU-03

Esta guía explica cómo preparar y ejecutar la aplicación de PLN clínico del proyecto PIA2, que utiliza el corpus PharmaCoNER, en Windows.

## 1. Requisitos previos

- Windows 10 u 11.
- Python instalado y disponible desde la terminal.
- Conexión a Internet para instalar dependencias o descargar los datos si fuera necesario.
- El proyecto descargado o clonado en el equipo.

Para comprobar que Python está disponible, abre el **Símbolo del sistema** (`cmd`) y ejecuta:

```bat
python --version
```

Si el comando no se reconoce, instala Python y activa la opción **Add Python to PATH** durante la instalación.

## 2. Estructura del proyecto

La estructura actual del proyecto es la siguiente:

```text
pia2/
├── app/
│   ├── data/
│   │   ├── archives/
│   │   │   └── pharmaconer.zip
│   │   └── pharmaconer/
│   │       └── conll/
│   ├── pharmaconer/
│   │   ├── conll/
│   │   └── ...
│   ├── scripts/
│   │   ├── download_datasets.py
│   │   └── visualize_data.py
│   ├── app.py
│   ├── descargar_datos.bat
│   ├── ejecutar_app.bat
│   ├── README_ejecucion_app.md
│   └── requirements.txt
├── specs/
│   ├── evaluacion-resultados.md
│   ├── extraccion-entidades.md
│   ├── generacion-fhir.md
│   ├── generacion-json.md
│   └── normalizacion-clinica.md
├── .gitattributes
├── .gitignore
└── README.md
```

La carpeta `app/` contiene el código de la aplicación, las dependencias, los scripts auxiliares y los lanzadores de Windows. Los datos de PharmaCoNER se encuentran dentro de `app/data/`.

La carpeta `specs/`, situada en la raíz del proyecto, contiene la documentación técnica de las distintas funcionalidades.

**Importante:** los comandos de ejecución de esta guía deben ejecutarse desde `pia2/app/`, donde se encuentran `app.py` y `requirements.txt`.

## 3. Abre una terminal en la carpeta de la aplicación

En el Explorador de archivos, entra en `pia2/app/`. Haz clic en la barra de direcciones, escribe `cmd` y pulsa **Intro**.

Comprueba que estás en la carpeta correcta:

```bat
dir
```

Deberías encontrar `app.py`, `requirements.txt`, `scripts/` y `data/`.

Si la terminal se encuentra en la raíz del proyecto, entra en la carpeta de la aplicación:

```bat
cd app
```

## 4. Instala las dependencias

Desde `pia2/app/`, ejecuta:

```bat
python -m pip install -r requirements.txt
```

Espera a que finalice la instalación. Si aparece algún error, conserva el mensaje completo para identificar la dependencia que ha fallado.

## 5. Comprueba los datos de PharmaCoNER

El proyecto contiene un archivo comprimido del corpus y una carpeta con datos organizados en formato CoNLL.

Comprueba que existen las siguientes rutas:

```text
app/data/archives/pharmaconer.zip
app/data/pharmaconer/conll/
```

También aparece una carpeta `app/pharmaconer/` en la estructura del proyecto.

Si los datos ya están disponibles y la aplicación puede leerlos, no es necesario descargarlos de nuevo.

Si necesitas recuperar los datos, ejecuta desde `pia2/app/`:

```bat
python scripts\download_datasets.py
```

Como alternativa, puedes hacer doble clic en `descargar_datos.bat`, situado en la carpeta `app/`.

Para consultar las opciones disponibles del script, ejecuta:

```bat
python scripts\download_datasets.py --help
```

Las opciones adicionales de descarga dependerán de los argumentos implementados en el propio script.

## 6. Ejecuta la aplicación web

Desde `pia2/app/`, ejecuta:

```bat
python -m streamlit run app.py
```

Si la aplicación se inicia correctamente, Streamlit mostrará una dirección local, normalmente:

```text
http://localhost:8501
```

Abre esa dirección en el navegador si no se abre automáticamente.

Para detener la aplicación, vuelve a la terminal y pulsa **Ctrl+C**.

También puedes iniciar la aplicación haciendo doble clic en `ejecutar_app.bat`.

Si el lanzador falla, ejecuta el comando de Streamlit desde la terminal para consultar el mensaje de error completo.

### Puerto alternativo

Si el puerto 8501 está ocupado, puedes probar con otro:

```bat
python -m streamlit run app.py --server.port 8502
```

Abre la dirección que indique Streamlit.

## 7. Ejecuta el script auxiliar de visualización

El proyecto incluye el script `scripts/visualize_data.py`.

Para ejecutarlo desde `pia2/app/`, utiliza:

```bat
python scripts\visualize_data.py
```

El resultado concreto dependerá de la implementación del script. Para consultar las opciones disponibles, ejecuta:

```bat
python scripts\visualize_data.py --help
```

## 8. Documentación técnica del proyecto

La carpeta `specs/`, situada en la raíz `pia2/`, contiene los siguientes documentos:

- **`evaluacion-resultados.md`**: documentación de la evaluación de resultados.
- **`extraccion-entidades.md`**: documentación de la extracción de entidades.
- **`generacion-fhir.md`**: documentación de la generación de recursos FHIR.
- **`generacion-json.md`**: documentación de la generación de datos JSON.
- **`normalizacion-clinica.md`**: documentación de la normalización clínica.

El archivo `README.md` de la raíz contiene la documentación general del proyecto. Este documento se centra en la preparación y ejecución de la aplicación.

## 9. Solución de problemas frecuentes

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

## 10. Orden recomendado para la primera ejecución

1. Abre una terminal en `pia2/app/`.
2. Comprueba la instalación de Python con `python --version`.
3. Instala las dependencias con `python -m pip install -r requirements.txt`.
4. Comprueba si los datos de PharmaCoNER ya están disponibles.
5. Si faltan datos, ejecuta `python scripts\download_datasets.py`.
6. Inicia la aplicación con `python -m streamlit run app.py`.
7. Abre la dirección local que indique Streamlit, normalmente `http://localhost:8501`.