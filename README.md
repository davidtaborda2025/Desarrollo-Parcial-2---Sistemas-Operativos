# Simulador de Administración de Memoria: Asignación y Traducción de Direcciones Virtuales a Direcciones Físicas

Este repositorio contiene la implementación formal, robusta y modular de un sistema web interactivo diseñado para emular y analizar los dos esquemas fundamentales de la administración de memoria en los sistemas operativos: la **Asignación Contigua** (con la aplicación de algoritmos de asignación) y la **Paginación Virtual** (con traducción analítica de direcciones mediante una MMU simulada).

El desarrollo ha sido estructurado bajo el paradigma de Programación Orientada a Objetos (POO) en Python, utilizando el microframework Flask para la capa de servicios web, garantizando un aislamiento completo del entorno mediante su ejecución en un contenedor de Docker.

Desarrollo realizado por el estudiante **David Taborda Montenegro (202242264-3743)**, para el segundo examen parcial de la asignatura **Sistemas Operativos** en la **Universidad del Valle**.

---

## 1. Arquitectura del Software y Componentes del Código

La lógica del backend está estrictamente segregada en archivos cohesivos, que modelan los componentes reales de un sistema operativo y el hardware de gestión de memoria, operando bajo una escala de medición uniforme basada en **Bytes**.

### Módulo 1: Simulador de Asignación de Memoria
Este módulo emula la gestión de memoria en sistemas con particiones fijas, administrando el espacio libre y decidiendo qué bloques asignar a los procesos entrantes mediante la siguiente estructura:

*   **`Process`:** Representación lógica de los procesos que entran al sistema. Almacena de forma atómica su identificador (PID) y el tamaño requerido en Bytes.
*   **`MemoryBlock`:** Modela cada una de las particiones físicas de la memoria RAM. Registra su tamaño total en Bytes, el espacio ocupado por el proceso alojado y calcula dinámicamente las métricas que maneja (fragmentación interna y procesos que ocupan cada bloque).
*   **`AllocationStrategy` (Clase Abstracta ABC):** Define el contrato e interfaz común para las políticas de ubicación. Permite que el simulador cambie dinámicamente de algoritmo en tiempo de ejecución (Patrón de Diseño *Strategy*) sin alterar el flujo principal de la memoria.
*   **`FirstFit` (AllocationStrategy):** Implementa la búsqueda lineal del primer bloque libre que cuente con los Bytes necesarios para alojar el proceso, priorizando la velocidad de asignación.
*   **`BestFit` (AllocationStrategy):** Evalúa exhaustivamente todos los bloques y selecciona la partición que deje el menor espacio sobrante en Bytes, minimizando la fragmentación interna.
*   **`WorstFit` (AllocationStrategy):** Selecciona deliberadamente el bloque disponible con la mayor cantidad de Bytes libres, con el fin de dejar un residuo grande que pueda ser aprovechado por procesos futuros.

### Módulo 2: Simulador de Traducción de Direcciones Virtuales a Direcciones Físicas
Este módulo modela el comportamiento de una Unidad de Gestión de Memoria (MMU) por hardware, bajo el esquema de Paginación de un Nivel y las estructuras de datos del kernel, para el mapeo de direcciones virtuales a físicas:

*   **`PageFrame`:** Es la encargada de representar cada uno de los Marcos de Página (Page Frames) en los que se divide de manera física y uniforme la memoria RAM real. Sus atributos base se centran en registrar su identificador de posición en el bloque de memoria y su capacidad fija (en bytes) dentro del mismo.
*   **`PageTable`:** Estructura de indexación asociada de forma unívoca a cada proceso. Mapea mediante un diccionario el número de página lógica con su respectivo `PageFrame` físico en la RAM.
*   **`Mmu`:** Unidad de hardware simulada. Intercepta la Dirección Virtual ($V_a$) y aplica la aritmética de traducción: división entera (`//`) para extraer el Número de Página ($p$) y módulo (`%`) para hallar el Desplazamiento ($d$).
*   **`PagingSimulator`:** El orquestador global del entorno virtualizado. Controla el pool completo de marcos, coordina la carga inicial de procesos en la memoria física y gestiona el lanzamiento de excepciones.

---

## 2. Estructura del Repositorio

A continuación, se detalla la distribución del código fuente y los recursos del proyecto. La inclusión de archivos al control de versiones está regulada por una política estricta de exclusión selectiva para evitar la indexación de archivos temporales del IDE o cachés de compilación:

```text
├── docs/
│   └── Desarrollo Parcial 2 - David Taborda M.pdf  # Informe explicativo formal
│
├── src/
│   ├── memory_allocation.py                        # Lógica y estrategias de asignación contigua.
│   └── directions_translator.py                    # Modelo de la MMU y tablas de páginas.
│
├── static/
│   └── styles.css                                  # Estilos arquitectónicos y diseño de la GUI.
│
├── templates/
│   └── index.html                                  # Interfaz gráfica principal del simulador.
│
├── .gitignore                                      # Archivo de exclusión de Git.
├── Dockerfile                                      # Manifiesto de automatización del contenedor (para levantarlo).
├── README.md                                       # Archivo de descripción del proyecto.
├── application.py                                  # Orquestador principal y servidor Flask.
└── requirements.txt                                # Dependencias del entorno de Python.
```
---

## 3. Despliegue y Ejecución con Docker

Para aislar por completo el entorno de ejecución de Flask y evitar conflictos con dependencias locales, el proyecto se encuentra totalmente construído bajo una infraestructura de contenedor con Docker.

### Paso 1: Construcción de la Imagen
Abrir una terminal en la raíz del proyecto (donde reside el archivo `Dockerfile`) y ejecutar el siguiente comando para compilar el entorno:
```bash
docker build -t nombre_de_la_imagen .
```
### Paso 2: Levantamiento del Contenedor
Una vez construida la imagen, se procede con el levantamiento del contenedor donde correrá la aplicación de Python. Para tal fin, ejecutar el siguiente comando:
```bash
docker run -d -p 5000:5000 --name nombre_del_contenedor nombre_de_la_imagen_ya_construida
```

### Paso 3: Acceso a la Interfaz Gráfica de Usuario (GUI)
Al disponer de la imagen y el contenedor activos, es necesario entender que la aplicación se ejecuta dentro del contenedor. Por tal motivo, para acceder a la sección gráfica, es necesario del ingreso de una URL local en un navegador. Así que, se requiere de acceder a:
```bash
http://localhost:5000/
```
Es sumamente importante colocar el puerto 5000, puesto que es el canal por el que el frontend se comunica con el contenedor.

---

Luego de realizados todos estos pasos, y considerando que en sistemas operativos como Windows se debe contar con la herramienta Docker Desktop ejecutándose para manejar los contenedores, se podrá interactuar con el desarrollo aquí almacenado.

Adicionalmente, se añade este video en YouTube donde se sustenta la implementación hecha para cada uno de los simuladores: https://youtu.be/0XQpgjIZAEY
