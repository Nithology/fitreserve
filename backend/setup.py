"""
setup.py — Configuración inicial de FitReserve
Ejecutar UNA sola vez antes de arrancar la aplicación por primera vez.
Crea las tablas y el usuario entrenador con la contraseña correcta.

Uso:
    cd backend
    python setup.py
"""

import bcrypt
import mysql.connector

# ── Configuración (debe coincidir con db.py) ──────────
HOST     = "localhost"
USER     = "root"
PASSWORD = ""          # Cambia si tu MySQL tiene contraseña
DB_NAME  = "fitreserve"

# ── Datos del entrenador por defecto ──────────────────
ENTRENADOR_NOMBRE   = "Manuel Entrenador"
ENTRENADOR_EMAIL    = "entrenador@fitreserve.com"
ENTRENADOR_PASSWORD = "admin123"

# ─────────────────────────────────────────────────────

def ejecutar_sql(cursor, sql):
    """Ejecuta sentencias SQL separadas por punto y coma."""
    for sentencia in sql.strip().split(";"):
        sentencia = sentencia.strip()
        if sentencia:
            cursor.execute(sentencia)

def main():
    print("FitReserve — Configuración inicial")
    print("=" * 40)

    # 1. Conectar sin especificar base de datos para poder crearla
    print("Conectando a MySQL...")
    try:
        conn = mysql.connector.connect(
            host=HOST, user=USER, password=PASSWORD
        )
    except Exception as e:
        print(f"ERROR: No se pudo conectar a MySQL.")
        print(f"Detalle: {e}")
        print("Asegúrate de que MySQL está activo y que la contraseña en setup.py es correcta.")
        return

    cursor = conn.cursor()

    # 2. Crear base de datos si no existe
    print("Creando base de datos 'fitreserve'...")
    cursor.execute("CREATE DATABASE IF NOT EXISTS fitreserve")
    cursor.execute("USE fitreserve")

    # 3. Crear tablas
    print("Creando tablas...")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id            INT AUTO_INCREMENT PRIMARY KEY,
            nombre        VARCHAR(100) NOT NULL,
            email         VARCHAR(150) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            telefono      VARCHAR(20),
            rol           ENUM('cliente','entrenador') DEFAULT 'cliente',
            fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS disponibilidad (
            id            INT AUTO_INCREMENT PRIMARY KEY,
            id_entrenador INT NOT NULL,
            dia_semana    TINYINT NOT NULL,
            hora_inicio   TIME NOT NULL,
            hora_fin      TIME NOT NULL,
            es_bloqueo    BOOLEAN DEFAULT FALSE,
            FOREIGN KEY (id_entrenador) REFERENCES usuarios(id) ON DELETE CASCADE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reservas (
            id            INT AUTO_INCREMENT PRIMARY KEY,
            id_cliente    INT NOT NULL,
            id_entrenador INT NOT NULL,
            fecha         DATE NOT NULL,
            hora_inicio   TIME NOT NULL,
            hora_fin      TIME NOT NULL,
            estado        ENUM('activa','cancelada','completada') DEFAULT 'activa',
            comentario    TEXT,
            fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (id_cliente)    REFERENCES usuarios(id) ON DELETE CASCADE,
            FOREIGN KEY (id_entrenador) REFERENCES usuarios(id) ON DELETE CASCADE
        )
    """)

    conn.commit()

    # 4. Comprobar si ya existe el entrenador
    cursor.execute("SELECT id FROM usuarios WHERE email = %s", (ENTRENADOR_EMAIL,))
    existe = cursor.fetchone()

    if existe:
        print(f"El entrenador '{ENTRENADOR_EMAIL}' ya existe. No se vuelve a crear.")
    else:
        # 5. Generar hash de la contraseña en este mismo ordenador
        print("Generando contraseña segura para el entrenador...")
        pw_hash = bcrypt.hashpw(
            ENTRENADOR_PASSWORD.encode("utf-8"),
            bcrypt.gensalt(rounds=12)
        ).decode("utf-8")

        cursor.execute(
            "INSERT INTO usuarios (nombre, email, password_hash, rol) VALUES (%s, %s, %s, 'entrenador')",
            (ENTRENADOR_NOMBRE, ENTRENADOR_EMAIL, pw_hash)
        )
        conn.commit()
        print(f"Entrenador creado correctamente.")

    cursor.close()
    conn.close()

    print("=" * 40)
    print("Configuración completada.")
    print(f"  Email entrenador : {ENTRENADOR_EMAIL}")
    print(f"  Contraseña       : {ENTRENADOR_PASSWORD}")
    print("")
    print("Ahora puedes arrancar el servidor con: python app.py")

if __name__ == "__main__":
    main()
