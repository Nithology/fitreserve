-- models.sql
-- Solo estructura de tablas. Para insertar el entrenador usa: python setup.py

CREATE DATABASE IF NOT EXISTS fitreserve;
USE fitreserve;

CREATE TABLE IF NOT EXISTS usuarios (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    nombre        VARCHAR(100) NOT NULL,
    email         VARCHAR(150) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    telefono      VARCHAR(20),
    rol           ENUM('cliente','entrenador') DEFAULT 'cliente',
    fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS disponibilidad (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    id_entrenador INT NOT NULL,
    dia_semana    TINYINT NOT NULL COMMENT '0=Lunes, 1=Martes, 2=Miércoles, 3=Jueves, 4=Viernes, 5=Sábado',
    hora_inicio   TIME NOT NULL,
    hora_fin      TIME NOT NULL,
    es_bloqueo    BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (id_entrenador) REFERENCES usuarios(id) ON DELETE CASCADE
);

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
);
