# FitReserve 

Aplicación web para gestionar reservas de sesiones de entrenamiento personal.
Los clientes reservan sesiones con el entrenador a través de un calendario interactivo.

---

## Proceso de instalación

Necesitas tener instalados tres programas en tu ordenador.
Si ya los tienes, salta directamente al apartado de instalación paso a paso.

### 1. Python
**https://www.python.org/downloads** Descarga la versión más reciente.


### 2. MySQL
**https://dev.mysql.com/downloads/installer** Descarga el .exe 
Ejecuta el instalador y elige la opción **Developer Default**.
Te pedirá crear una contraseña para `root`, se puede quedar vacia o no. Necesaria en un futuro si se rellena.


### 3. Visual Studio Code
**https://code.visualstudio.com** y descarga e instala VS Code.
Una vez instalado, abre VS Code, ve al panel de extensiones, instala **Live Server** (el de Ritwick Dey) .
 

---

## Instalación paso a paso

### Paso 1 — Descargar el proyecto desde GitHub

Necesitas tener Git instalado.
Abre VS Code. Ve a **Archivo → Abrir carpeta** y selecciona esa carpeta `fitreserve`.


### Paso 2 — Abrir la terminal de VS Code

Dentro de VS Code ve a **Terminal → New Terminal**.
Se abrirá un panel en la parte inferior de la pantalla.

### Paso 3 — Ir a la carpeta del backend

En la terminal escribe:
```
cd backend
```

### Paso 4 — Instalar las dependencias de Python

En la terminal escribe:
```
pip install -r requirements.txt
```
Espera que aparezca `Successfully installed`.
 

### Paso 5 — Configurar la contraseña de MySQL 

Si al instalar en MySQL dejaste la contraseña vacía, salta al Paso 6.
Si pusiste una contraseña, abre el archivo `backend/db.py` en VS Code y añade al password: 

password="TUCONTRASEÑA",
Guarda el archivo 

### Paso 6 — Crear la base de datos y el usuario entrenador

Activa  MySQL. Para comprobarlo abre el programa
**MySQL Workbench** — si puedes conectarte, MySQL está activo.

Si no está activo, abre el **Administrador de Servicios** de Windows
(`Win+R`, escribe `services.msc`, pulsa Enter), busca `MySQL80`,
haz clic derecho y pulsa **Iniciar**.

Con MySQL activo, escribe  en la terminal de VS Code:
```
python setup.py
```
Debería aparecer:
```
Configuración completada.
  Email     : entrenador@fitreserve.com
  Contraseña: admin123
```

Esto ha creado la base de datos, las tablas y el usuario entrenador.
Este paso solo hace falta hacerlo una vez.

### Paso 7 — Arrancar el servidor

Escribe esto en la terminal y pulsa Enter:
```
python app.py
```
Debería aparecer:
```
 * Running on http://127.0.0.1:5000
 * Debug mode: on
```
**Deja esta terminal abierta.** 

### Paso 8 — Abrir la aplicación en el navegador

En VS Code, en el panel izquierdo de archivos, abre la carpeta `frontend`.
Abre el archivo `index.html`
Se abrirá el navegador con la aplicación en la dirección `http://127.0.0.1:5500`.
---

## Iniciar sesión

Una vez abierta la aplicación verás la pantalla de login.

**Cuenta del entrenador (creada automáticamente):**
- Email: `entrenador@fitreserve.com`
- Contraseña: `admin123`

**Para crear una cuenta de cliente:**
Pulsa la pestaña **Registrarse**, rellena el formulario y pulsa el botón.
---

## Aplicación

### Como entrenador:
- Ver el calendario semanal con los días disponibles
- Configurar los horarios de cada día de la semana (vista **Horarios**)
- Ver todas las reservas de todos los clientes (vista **Reservas**)
- Ver la lista de clientes registrados (vista **Clientes**)

### Como cliente:
- Ver el calendario semanal y entrar en cualquier día
- Ver los slots disponibles y reservar el que quieras
- Añadir un comentario opcional al reservar
- Ver tus reservas activas y el historial de canceladas (vista **Reservas**)
- Editar tu nombre, teléfono y contraseña (vista **Perfil**)

---


**Resumen rápido para cada sesión:**

1. Abre VS Code con la carpeta `fitreserve`
2. Abre una terminal (`Terminal → New Terminal`)
3. Escribe `cd backend` y pulsa Enter
4. Escribe `python app.py` y pulsa Enter
5. Abre `frontend/index.html` 

---

## Solución a problemas ocurridos y frecuentes

**"pip no se reconoce como comando"**
Usa `pip3` en lugar de `pip`.

**"No module named flask"**
Ejecuta de nuevo `pip install -r requirements.txt` dentro de la carpeta `backend`.

**El login no funciona y aparece error de red**
Comprueba que la terminal con `python app.py` sigue abierta y muestra
`Running on http://127.0.0.1:5000`. Si se cerró, vuelve a ejecutarlo.

**"Access denied for user root"**
La contraseña de MySQL no coincide con la de `db.py`. Abre `db.py` y corrígela.

**MySQL no arranca**
Abre `services.msc`, busca `MySQL80`, clic derecho → **Iniciar**.
Para que arranque automáticamente al encender el ordenador, haz doble clic
sobre `MySQL80`, cambia **Tipo de inicio** a `Automático` y pulsa Aceptar.

**El calendario aparece vacío**
Asegúrate de haber abierto el frontend con Live Server.
Comprueba también que el servidor Flask está corriendo.

---

## Estructura del proyecto

```
fitreserve/
├── backend/
│   ├── app.py            → API REST con todos los endpoints
│   ├── db.py             → Conexión a MySQL
│   ├── models.sql        → Estructura de la base de datos
│   ├── setup.py          → Configuración inicial (ejecutar una vez)
│   ├── test_api.py       → Pruebas automáticas
│   └── requirements.txt  → Librerías de Python necesarias
├── frontend/
│   ├── index.html        → Toda la interfaz de la aplicación
│   ├── styles.css        → Diseño visual
│   └── app.js            → Lógica y comunicación con el servidor
└── README.md             → Este archivo
```
