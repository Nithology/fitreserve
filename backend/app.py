from flask import Flask, request, jsonify
from flask_cors import CORS
from db import get_connection
import bcrypt
import jwt
import datetime

app = Flask(__name__)
CORS(app)

SECRET_KEY = "fitreserve_secret_2026"

# ─── HELPER: verificar token ─────────────────────────────
# Devuelve los datos del usuario si el token es válido,
# o None si no lo es. Se llama al inicio de cada ruta protegida.

def verificar_token():
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None
    token = auth.split(" ")[1]
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    except:
        return None


# ─── AUTH ────────────────────────────────────────────────

@app.route("/auth/register", methods=["POST"])
def register():
    data = request.json
    nombre   = data.get("nombre", "").strip()
    email    = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not nombre or not email or not password:
        return jsonify({"error": "nombre, email y password son obligatorios"}), 400
    if len(password) < 6:
        return jsonify({"error": "La contraseña debe tener al menos 6 caracteres"}), 400

    pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    try:
        conn   = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO usuarios (nombre, email, password_hash, rol) VALUES (%s,%s,%s,'cliente')",
            (nombre, email, pw_hash)
        )
        conn.commit()
        user_id = cursor.lastrowid
        cursor.close()
        conn.close()
    except Exception as e:
        if "Duplicate" in str(e):
            return jsonify({"error": "El email ya está registrado"}), 409
        return jsonify({"error": str(e)}), 500

    payload = {"id": user_id, "nombre": nombre, "email": email, "rol": "cliente",
               "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=8)}
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return jsonify({"token": token, "nombre": nombre, "rol": "cliente"}), 201


@app.route("/auth/login", methods=["POST"])
def login():
    data     = request.json
    email    = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"error": "email y password son obligatorios"}), 400

    conn   = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM usuarios WHERE email=%s", (email,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if not user or not bcrypt.checkpw(password.encode(), user["password_hash"].encode()):
        return jsonify({"error": "Credenciales incorrectas"}), 401

    payload = {"id": user["id"], "nombre": user["nombre"],
               "email": user["email"], "rol": user["rol"],
               "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=8)}
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return jsonify({"token": token, "nombre": user["nombre"], "rol": user["rol"]}), 200


# ─── USUARIOS ────────────────────────────────────────────

@app.route("/usuarios/me", methods=["GET"])
def get_me():
    user = verificar_token()
    if not user:
        return jsonify({"error": "Token requerido o inválido"}), 401

    conn   = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT id, nombre, email, telefono, rol, fecha_registro FROM usuarios WHERE id=%s",
        (user["id"],)
    )
    data = cursor.fetchone()
    cursor.close()
    conn.close()

    if not data:
        return jsonify({"error": "Usuario no encontrado"}), 404
    return jsonify(data)


@app.route("/usuarios/me", methods=["PATCH"])
def update_me():
    user = verificar_token()
    if not user:
        return jsonify({"error": "Token requerido o inválido"}), 401

    data   = request.json
    campos = []
    valores = []

    if "nombre" in data:
        campos.append("nombre=%s")
        valores.append(data["nombre"].strip())
    if "telefono" in data:
        campos.append("telefono=%s")
        valores.append(data["telefono"].strip())
    if "password" in data:
        if len(data["password"]) < 6:
            return jsonify({"error": "La contraseña debe tener al menos 6 caracteres"}), 400
        pw_hash = bcrypt.hashpw(data["password"].encode(), bcrypt.gensalt()).decode()
        campos.append("password_hash=%s")
        valores.append(pw_hash)

    if not campos:
        return jsonify({"error": "Nada que actualizar"}), 400

    valores.append(user["id"])
    conn   = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"UPDATE usuarios SET {', '.join(campos)} WHERE id=%s", valores)
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Perfil actualizado"})


@app.route("/usuarios", methods=["GET"])
def get_usuarios():
    user = verificar_token()
    if not user:
        return jsonify({"error": "Token requerido o inválido"}), 401
    if user["rol"] != "entrenador":
        return jsonify({"error": "Acceso solo para entrenador"}), 403

    conn   = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT id, nombre, email, telefono, fecha_registro FROM usuarios WHERE rol='cliente'"
    )
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(data)


# ─── DISPONIBILIDAD ──────────────────────────────────────

@app.route("/disponibilidad", methods=["GET"])
def get_disponibilidad():
    user = verificar_token()
    if not user:
        return jsonify({"error": "Token requerido o inválido"}), 401

    conn   = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT d.*, u.nombre AS entrenador_nombre
        FROM disponibilidad d
        JOIN usuarios u ON d.id_entrenador = u.id
        WHERE d.es_bloqueo = FALSE
        ORDER BY d.dia_semana, d.hora_inicio
    """)
    data = cursor.fetchall()
    cursor.close()
    conn.close()

    for row in data:
        row["hora_inicio"] = str(row["hora_inicio"])[:5]
        row["hora_fin"]    = str(row["hora_fin"])[:5]
    return jsonify(data)


@app.route("/disponibilidad", methods=["POST"])
def crear_disponibilidad():
    user = verificar_token()
    if not user:
        return jsonify({"error": "Token requerido o inválido"}), 401
    if user["rol"] != "entrenador":
        return jsonify({"error": "Acceso solo para entrenador"}), 403

    data  = request.json
    dia   = data.get("dia_semana")
    h_ini = data.get("hora_inicio")
    h_fin = data.get("hora_fin")

    if dia is None or not h_ini or not h_fin:
        return jsonify({"error": "dia_semana, hora_inicio y hora_fin son obligatorios"}), 400

    conn   = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO disponibilidad (id_entrenador, dia_semana, hora_inicio, hora_fin, es_bloqueo) VALUES (%s,%s,%s,%s,FALSE)",
        (user["id"], dia, h_ini, h_fin)
    )
    conn.commit()
    new_id = cursor.lastrowid
    cursor.close()
    conn.close()
    return jsonify({"id": new_id, "message": "Disponibilidad creada"}), 201


@app.route("/disponibilidad/<int:id>", methods=["DELETE"])
def borrar_disponibilidad(id):
    user = verificar_token()
    if not user:
        return jsonify({"error": "Token requerido o inválido"}), 401
    if user["rol"] != "entrenador":
        return jsonify({"error": "Acceso solo para entrenador"}), 403

    conn   = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM disponibilidad WHERE id=%s AND id_entrenador=%s",
        (id, user["id"])
    )
    conn.commit()
    deleted = cursor.rowcount
    cursor.close()
    conn.close()

    if deleted == 0:
        return jsonify({"error": "No encontrado o sin permiso"}), 404
    return jsonify({"message": "Eliminado"})


# ─── RESERVAS ────────────────────────────────────────────

@app.route("/reservas", methods=["GET"])
def get_reservas():
    user = verificar_token()
    if not user:
        return jsonify({"error": "Token requerido o inválido"}), 401

    # Marcar como completadas las reservas activas cuya fecha y hora ya pasaron
    try:
        conn_auto   = get_connection()
        cursor_auto = conn_auto.cursor()
        cursor_auto.execute("""
            UPDATE reservas
            SET estado = 'completada'
            WHERE estado = 'activa'
              AND (
                fecha < CURDATE()
                OR (fecha = CURDATE() AND hora_fin <= CURTIME())
              )
        """)
        conn_auto.commit()
        cursor_auto.close()
        conn_auto.close()
    except Exception:
        pass  # Si falla el autocompletado no interrumpimos la petición

    conn   = get_connection()
    cursor = conn.cursor(dictionary=True)

    if user["rol"] == "entrenador":
        cursor.execute("""
            SELECT r.*, u.nombre AS cliente_nombre, u.email AS cliente_email
            FROM reservas r
            JOIN usuarios u ON r.id_cliente = u.id
            ORDER BY r.fecha DESC, r.hora_inicio
        """)
    else:
        cursor.execute("""
            SELECT r.*, u.nombre AS entrenador_nombre
            FROM reservas r
            JOIN usuarios u ON r.id_entrenador = u.id
            WHERE r.id_cliente = %s
            ORDER BY r.fecha DESC, r.hora_inicio
        """, (user["id"],))

    data = cursor.fetchall()
    cursor.close()
    conn.close()

    for row in data:
        row["hora_inicio"]    = str(row["hora_inicio"])[:5]
        row["hora_fin"]       = str(row["hora_fin"])[:5]
        row["fecha"]          = str(row["fecha"])
        row["fecha_creacion"] = str(row["fecha_creacion"])
    return jsonify(data)


@app.route("/reservas", methods=["POST"])
def crear_reserva():
    user = verificar_token()
    if not user:
        return jsonify({"error": "Token requerido o inválido"}), 401
    if user["rol"] == "entrenador":
        return jsonify({"error": "El entrenador no puede crear reservas"}), 403

    data  = request.json
    fecha = data.get("fecha")
    h_ini = data.get("hora_inicio")
    h_fin = data.get("hora_fin")
    comentario = data.get("comentario", "")

    if not fecha or not h_ini or not h_fin:
        return jsonify({"error": "fecha, hora_inicio y hora_fin son obligatorios"}), 400

    conn   = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Obtener entrenador
    cursor.execute("SELECT id FROM usuarios WHERE rol='entrenador' LIMIT 1")
    entrenador = cursor.fetchone()
    if not entrenador:
        cursor.close()
        conn.close()
        return jsonify({"error": "No hay entrenador disponible"}), 400

    id_entrenador = entrenador["id"]

    # Verificar que no haya solape
    cursor.execute("""
        SELECT id FROM reservas
        WHERE fecha=%s AND id_entrenador=%s AND estado='activa'
        AND NOT (hora_fin <= %s OR hora_inicio >= %s)
    """, (fecha, id_entrenador, h_ini, h_fin))

    if cursor.fetchone():
        cursor.close()
        conn.close()
        return jsonify({"error": "Horario ocupado"}), 400

    cursor.execute("""
        INSERT INTO reservas (id_cliente, id_entrenador, fecha, hora_inicio, hora_fin, comentario)
        VALUES (%s,%s,%s,%s,%s,%s)
    """, (user["id"], id_entrenador, fecha, h_ini, h_fin, comentario))
    conn.commit()
    new_id = cursor.lastrowid
    cursor.close()
    conn.close()
    return jsonify({"id": new_id, "message": "Reserva creada"}), 201


@app.route("/reservas/<int:id>", methods=["DELETE"])
def cancelar_reserva(id):
    user = verificar_token()
    if not user:
        return jsonify({"error": "Token requerido o inválido"}), 401

    conn   = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM reservas WHERE id=%s", (id,))
    reserva = cursor.fetchone()

    if not reserva:
        cursor.close()
        conn.close()
        return jsonify({"error": "Reserva no encontrada"}), 404

    # El cliente solo puede cancelar sus propias reservas
    if user["rol"] == "cliente" and reserva["id_cliente"] != user["id"]:
        cursor.close()
        conn.close()
        return jsonify({"error": "Sin permiso"}), 403

    cursor.execute("UPDATE reservas SET estado='cancelada' WHERE id=%s", (id,))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Reserva cancelada"})


if __name__ == "__main__":
    app.run(debug=True)
