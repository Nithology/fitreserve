"""
test_api.py — Pruebas automáticas de FitReserve
Entrega 4 — DAM 2025/2026

Cómo ejecutar:
    cd backend
    pip install requests
    python app.py          (en otra terminal, dejar corriendo)
    python test_api.py

Resultado esperado: todos los tests pasan (OK).
"""

import requests
import sys

BASE = "http://127.0.0.1:5000"

# ── Contadores ────────────────────────────────────────
passed = 0
failed = 0

def test(nombre, condicion, detalle=""):
    global passed, failed
    if condicion:
        print(f"  OK   {nombre}")
        passed += 1
    else:
        print(f"  FAIL {nombre}" + (f" — {detalle}" if detalle else ""))
        failed += 1

def seccion(titulo):
    print(f"\n{'='*50}")
    print(f"  {titulo}")
    print(f"{'='*50}")

# ════════════════════════════════════════════════════
#  1. AUTENTICACIÓN
# ════════════════════════════════════════════════════
seccion("1. AUTENTICACIÓN")

# 1.1 Registro correcto
r = requests.post(f"{BASE}/auth/register", json={
    "nombre": "Test Cliente",
    "email": "test_auto@fitreserve.com",
    "password": "123456"
})
# Aceptamos 201 (creado) o 409 (ya existe de ejecución anterior)
test("Registro de cliente nuevo", r.status_code in [201, 409],
     f"Status: {r.status_code}")

# Obtener token limpio — hacer login siempre funciona
r = requests.post(f"{BASE}/auth/login", json={
    "email": "test_auto@fitreserve.com",
    "password": "123456"
})
test("Login cliente correcto", r.status_code == 200,
     f"Status: {r.status_code} — {r.text[:80]}")
TOKEN_CLIENTE = r.json().get("token", "") if r.status_code == 200 else ""

# 1.2 Login con contraseña incorrecta
r = requests.post(f"{BASE}/auth/login", json={
    "email": "test_auto@fitreserve.com",
    "password": "WRONGPASSWORD"
})
test("Login con contraseña incorrecta devuelve 401",
     r.status_code == 401, f"Status: {r.status_code}")

# 1.3 Login sin campos
r = requests.post(f"{BASE}/auth/login", json={"email": "", "password": ""})
test("Login sin campos devuelve 400",
     r.status_code == 400, f"Status: {r.status_code}")

# 1.4 Login entrenador
r = requests.post(f"{BASE}/auth/login", json={
    "email": "entrenador@fitreserve.com",
    "password": "admin123"
})
test("Login entrenador correcto", r.status_code == 200,
     f"Status: {r.status_code} — {r.text[:80]}")
TOKEN_ENTRENADOR = r.json().get("token", "") if r.status_code == 200 else ""

# ════════════════════════════════════════════════════
#  2. PROTECCIÓN DE RUTAS (JWT)
# ════════════════════════════════════════════════════
seccion("2. PROTECCIÓN DE RUTAS")

# 2.1 Sin token → 401
r = requests.get(f"{BASE}/reservas")
test("GET /reservas sin token devuelve 401",
     r.status_code == 401, f"Status: {r.status_code}")

# 2.2 Con token inválido → 401
r = requests.get(f"{BASE}/reservas",
                 headers={"Authorization": "Bearer tokeninvalido"})
test("GET /reservas con token inválido devuelve 401",
     r.status_code == 401, f"Status: {r.status_code}")

# 2.3 Cliente intenta acceder a endpoint de entrenador → 403
if TOKEN_CLIENTE:
    r = requests.get(f"{BASE}/usuarios",
                     headers={"Authorization": f"Bearer {TOKEN_CLIENTE}"})
    test("Cliente accede a /usuarios (solo entrenador) devuelve 403",
         r.status_code == 403, f"Status: {r.status_code}")

# 2.4 Cliente intenta crear disponibilidad → 403
if TOKEN_CLIENTE:
    r = requests.post(f"{BASE}/disponibilidad",
                      headers={"Authorization": f"Bearer {TOKEN_CLIENTE}"},
                      json={"dia_semana": 0, "hora_inicio": "09:00:00", "hora_fin": "10:00:00"})
    test("Cliente crea disponibilidad (solo entrenador) devuelve 403",
         r.status_code == 403, f"Status: {r.status_code}")

# ════════════════════════════════════════════════════
#  3. DISPONIBILIDAD
# ════════════════════════════════════════════════════
seccion("3. DISPONIBILIDAD")

ID_DISP = None

# 3.1 Entrenador crea disponibilidad
if TOKEN_ENTRENADOR:
    r = requests.post(f"{BASE}/disponibilidad",
                      headers={"Authorization": f"Bearer {TOKEN_ENTRENADOR}"},
                      json={"dia_semana": 0, "hora_inicio": "09:00:00", "hora_fin": "13:00:00"})
    test("Entrenador crea bloque de disponibilidad",
         r.status_code == 201, f"Status: {r.status_code} — {r.text[:80]}")
    if r.status_code == 201:
        ID_DISP = r.json().get("id")

# 3.2 Cualquier usuario puede ver disponibilidad
if TOKEN_CLIENTE:
    r = requests.get(f"{BASE}/disponibilidad",
                     headers={"Authorization": f"Bearer {TOKEN_CLIENTE}"})
    test("Cliente puede ver disponibilidad",
         r.status_code == 200 and isinstance(r.json(), list),
         f"Status: {r.status_code}")

# ════════════════════════════════════════════════════
#  4. RESERVAS
# ════════════════════════════════════════════════════
seccion("4. RESERVAS")

ID_RESERVA = None
FECHA_TEST = "2026-12-01"   # fecha futura para evitar conflictos con datos reales

# 4.1 Cliente crea reserva
if TOKEN_CLIENTE:
    r = requests.post(f"{BASE}/reservas",
                      headers={"Authorization": f"Bearer {TOKEN_CLIENTE}"},
                      json={
                          "fecha": FECHA_TEST,
                          "hora_inicio": "10:00:00",
                          "hora_fin": "11:00:00",
                          "comentario": "Test automático"
                      })
    test("Cliente crea reserva correctamente",
         r.status_code == 201, f"Status: {r.status_code} — {r.text[:80]}")
    if r.status_code == 201:
        ID_RESERVA = r.json().get("id")

# 4.2 Validación de solape — misma hora
if TOKEN_CLIENTE:
    r = requests.post(f"{BASE}/reservas",
                      headers={"Authorization": f"Bearer {TOKEN_CLIENTE}"},
                      json={
                          "fecha": FECHA_TEST,
                          "hora_inicio": "10:00:00",
                          "hora_fin": "11:00:00"
                      })
    test("Crear reserva solapada devuelve 400",
         r.status_code == 400, f"Status: {r.status_code}")

# 4.3 Validación de solape — intervalo parcial
if TOKEN_CLIENTE:
    r = requests.post(f"{BASE}/reservas",
                      headers={"Authorization": f"Bearer {TOKEN_CLIENTE}"},
                      json={
                          "fecha": FECHA_TEST,
                          "hora_inicio": "10:30:00",
                          "hora_fin": "11:30:00"
                      })
    test("Crear reserva con solape parcial devuelve 400",
         r.status_code == 400, f"Status: {r.status_code}")

# 4.4 Entrenador no puede crear reservas
if TOKEN_ENTRENADOR:
    r = requests.post(f"{BASE}/reservas",
                      headers={"Authorization": f"Bearer {TOKEN_ENTRENADOR}"},
                      json={
                          "fecha": FECHA_TEST,
                          "hora_inicio": "12:00:00",
                          "hora_fin": "13:00:00"
                      })
    test("Entrenador intenta crear reserva devuelve 403",
         r.status_code == 403, f"Status: {r.status_code}")

# 4.5 Cliente ve sus reservas
if TOKEN_CLIENTE:
    r = requests.get(f"{BASE}/reservas",
                     headers={"Authorization": f"Bearer {TOKEN_CLIENTE}"})
    test("Cliente obtiene lista de reservas",
         r.status_code == 200 and isinstance(r.json(), list),
         f"Status: {r.status_code}")

# 4.6 Entrenador ve todas las reservas
if TOKEN_ENTRENADOR:
    r = requests.get(f"{BASE}/reservas",
                     headers={"Authorization": f"Bearer {TOKEN_ENTRENADOR}"})
    test("Entrenador obtiene todas las reservas",
         r.status_code == 200 and isinstance(r.json(), list),
         f"Status: {r.status_code}")

# 4.7 Cancelar reserva propia
if TOKEN_CLIENTE and ID_RESERVA:
    r = requests.delete(f"{BASE}/reservas/{ID_RESERVA}",
                        headers={"Authorization": f"Bearer {TOKEN_CLIENTE}"})
    test("Cliente cancela su propia reserva",
         r.status_code == 200, f"Status: {r.status_code}")

# ════════════════════════════════════════════════════
#  5. USUARIOS / PERFIL
# ════════════════════════════════════════════════════
seccion("5. USUARIOS Y PERFIL")

# 5.1 Ver perfil propio
if TOKEN_CLIENTE:
    r = requests.get(f"{BASE}/usuarios/me",
                     headers={"Authorization": f"Bearer {TOKEN_CLIENTE}"})
    data = r.json() if r.status_code == 200 else {}
    test("Cliente obtiene su perfil",
         r.status_code == 200 and "nombre" in data,
         f"Status: {r.status_code}")

# 5.2 Actualizar nombre
if TOKEN_CLIENTE:
    r = requests.patch(f"{BASE}/usuarios/me",
                       headers={"Authorization": f"Bearer {TOKEN_CLIENTE}"},
                       json={"nombre": "Test Cliente Actualizado"})
    test("Cliente actualiza su nombre",
         r.status_code == 200, f"Status: {r.status_code}")

# 5.3 Entrenador ve lista de clientes
if TOKEN_ENTRENADOR:
    r = requests.get(f"{BASE}/usuarios",
                     headers={"Authorization": f"Bearer {TOKEN_ENTRENADOR}"})
    test("Entrenador obtiene lista de clientes",
         r.status_code == 200 and isinstance(r.json(), list),
         f"Status: {r.status_code}")

# 5.4 Validación: actualizar sin campos
if TOKEN_CLIENTE:
    r = requests.patch(f"{BASE}/usuarios/me",
                       headers={"Authorization": f"Bearer {TOKEN_CLIENTE}"},
                       json={})
    test("PATCH /usuarios/me vacío devuelve 400",
         r.status_code == 400, f"Status: {r.status_code}")

# ════════════════════════════════════════════════════
#  6. LIMPIEZA (opcional)
# ════════════════════════════════════════════════════
seccion("6. LIMPIEZA")

# Eliminar disponibilidad creada en el test
if TOKEN_ENTRENADOR and ID_DISP:
    r = requests.delete(f"{BASE}/disponibilidad/{ID_DISP}",
                        headers={"Authorization": f"Bearer {TOKEN_ENTRENADOR}"})
    test("Entrenador elimina bloque de disponibilidad creado en el test",
         r.status_code == 200, f"Status: {r.status_code}")

# ════════════════════════════════════════════════════
#  RESUMEN FINAL
# ════════════════════════════════════════════════════
print(f"\n{'='*50}")
print(f"  RESULTADO: {passed} pasados / {passed + failed} totales")
if failed == 0:
    print("  TODOS LOS TESTS PASARON ✓")
else:
    print(f"  {failed} TEST(S) FALLARON ✗")
print(f"{'='*50}\n")

sys.exit(0 if failed == 0 else 1)
