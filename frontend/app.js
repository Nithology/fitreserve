// ═══════════════════════════════════════════════════════
//  FITRESERVE — app.js
// ═══════════════════════════════════════════════════════

const API = "http://127.0.0.1:5000";

// ── Estado global ──────────────────────────────────────
const state = {
    token:        null,
    user:         null,   // { id, nombre, email, rol }
    semana:       0,      // offset de semanas desde hoy
    fechaDia:     null,   // "YYYY-MM-DD" del día seleccionado
    horaIni:      null,
    horaFin:      null,
    reservas:     [],
    filtroEstado: "activa"
};

// ── Llamada genérica a la API ──────────────────────────
async function apiFetch(endpoint, options = {}) {
    const headers = { "Content-Type": "application/json" };
    if (state.token) {
        headers["Authorization"] = "Bearer " + state.token;
    }
    const res  = await fetch(API + endpoint, { ...options, headers });
    const data = await res.json();
    return { ok: res.ok, data };
}

// ── Utilidades ─────────────────────────────────────────
function mostrarError(id, msg) {
    const el = document.getElementById(id);
    if (!el) return;
    el.textContent = msg;
    el.classList.remove("hidden");
}

function mostrarExito(id, msg) {
    const el = document.getElementById(id);
    if (!el) return;
    el.textContent = msg;
    el.classList.remove("hidden");
}

function ocultarMsg(id) {
    const el = document.getElementById(id);
    if (el) el.classList.add("hidden");
}

function formatFecha(str) {
    const [y, m, d] = str.split("-");
    return d + "/" + m + "/" + y;
}

function getISODate(date) {
    // Usamos fecha local (no UTC) para evitar desfase horario en España UTC+2
    const y = date.getFullYear();
    const m = String(date.getMonth() + 1).padStart(2, "0");
    const d = String(date.getDate()).padStart(2, "0");
    return y + "-" + m + "-" + d;
}

function addDays(date, n) {
    const d = new Date(date);
    d.setDate(d.getDate() + n);
    return d;
}

function getLunes(offset) {
    const hoy      = new Date();
    const diaSem   = hoy.getDay() === 0 ? 6 : hoy.getDay() - 1;
    const lunes    = new Date(hoy);
    lunes.setDate(hoy.getDate() - diaSem + offset * 7);
    lunes.setHours(0, 0, 0, 0);
    return lunes;
}

const DIAS   = ["Lunes","Martes","Miércoles","Jueves","Viernes","Sábado","Domingo"];
const MESES  = ["enero","febrero","marzo","abril","mayo","junio",
                "julio","agosto","septiembre","octubre","noviembre","diciembre"];


// ══════════════════════════════════════════════════════
//  NAVEGACIÓN
// ══════════════════════════════════════════════════════

function navigate(vista) {
    // Ocultar todas las vistas
    document.querySelectorAll(".view").forEach(v => {
        v.classList.remove("active");
        v.classList.add("hidden");
    });

    // Mostrar la vista pedida
    const target = document.getElementById("view-" + vista);
    if (target) {
        target.classList.remove("hidden");
        target.classList.add("active");
    }

    // Marcar el botón activo en el nav
    document.querySelectorAll(".nav-btn").forEach(btn => {
        btn.classList.toggle("active", btn.dataset.view === vista);
    });

    // Cargar datos según la vista
    if (vista === "calendario")   cargarCalendario();
    if (vista === "reservas")     cargarReservas();
    if (vista === "clientes")     cargarClientes();
    if (vista === "horarios")     cargarDisponibilidad();
    if (vista === "perfil")       cargarPerfil();
}


// ══════════════════════════════════════════════════════
//  AUTH
// ══════════════════════════════════════════════════════

function switchTab(tab) {
    document.getElementById("tab-login").classList.toggle("hidden", tab !== "login");
    document.getElementById("tab-register").classList.toggle("hidden", tab !== "register");
    document.querySelectorAll(".tabs .tab").forEach((t, i) => {
        t.classList.toggle("active", (i === 0 && tab === "login") || (i === 1 && tab === "register"));
    });
}

async function doLogin() {
    ocultarMsg("login-error");
    const email    = document.getElementById("login-email").value.trim();
    const password = document.getElementById("login-password").value;

    if (!email || !password) {
        return mostrarError("login-error", "Rellena todos los campos");
    }

    const { ok, data } = await apiFetch("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password })
    });

    if (!ok) return mostrarError("login-error", data.error || "Error al iniciar sesión");

    iniciarSesion(data.token, data.nombre, data.rol);
}

async function doRegister() {
    ocultarMsg("register-error");
    const nombre   = document.getElementById("reg-nombre").value.trim();
    const email    = document.getElementById("reg-email").value.trim();
    const password = document.getElementById("reg-password").value;

    if (!nombre || !email || !password) {
        return mostrarError("register-error", "Rellena todos los campos");
    }

    const { ok, data } = await apiFetch("/auth/register", {
        method: "POST",
        body: JSON.stringify({ nombre, email, password })
    });

    if (!ok) return mostrarError("register-error", data.error || "Error al registrarse");

    iniciarSesion(data.token, data.nombre, data.rol);
}

function iniciarSesion(token, nombre, rol) {
    state.token = token;

    // Decodificar el payload del JWT (la parte central en base64)
    try {
        state.user = JSON.parse(atob(token.split(".")[1]));
    } catch {
        state.user = { nombre, rol };
    }

    // Guardar en localStorage para restaurar la sesión si se recarga
    localStorage.setItem("fr_token", token);

    // Mostrar navbar
    document.getElementById("navbar").classList.remove("hidden");

    // Mostrar botones exclusivos del entrenador
    document.querySelectorAll(".entrenador-only").forEach(el => {
        el.classList.toggle("hidden", rol !== "entrenador");
    });

    navigate("calendario");
}

function doLogout() {
    state.token = null;
    state.user  = null;
    localStorage.removeItem("fr_token");

    document.getElementById("navbar").classList.add("hidden");

    // Ocultar todas las vistas y mostrar login
    document.querySelectorAll(".view").forEach(v => {
        v.classList.remove("active");
        v.classList.add("hidden");
    });

    const login = document.getElementById("view-login");
    login.classList.remove("hidden");
    login.classList.add("active");
}


// ══════════════════════════════════════════════════════
//  CALENDARIO SEMANAL
// ══════════════════════════════════════════════════════

async function cargarCalendario() {
    const lunes   = getLunes(state.semana);
    const domingo = addDays(lunes, 6);
    const hoyISO  = getISODate(new Date());
    const grid    = document.getElementById("dias-semana");

    // Etiqueta de semana
    document.getElementById("semana-label").textContent =
        lunes.getDate() + " " + MESES[lunes.getMonth()] +
        " – " +
        domingo.getDate() + " " + MESES[domingo.getMonth()];

    // ── PASO 1: Pintar los 6 días inmediatamente como botones ─────
    grid.innerHTML = "";

    for (var i = 0; i < 6; i++) {
        var dia    = addDays(lunes, i);
        var diaISO = getISODate(dia);
        var esHoy  = diaISO === hoyISO;

        var btn = document.createElement("button");
        btn.className    = "dia-btn dia-btn--cargando" + (esHoy ? " dia-btn--hoy" : "");
        btn.dataset.fecha = diaISO;
        btn.dataset.diasem = String(i);
        btn.textContent  = DIAS[i].toUpperCase();

        // Closure para capturar i correctamente
        (function(fechaC, nombreC) {
            btn.addEventListener("click", function() {
                seleccionarDia(fechaC, nombreC);
            });
        })(diaISO, DIAS[i]);

        grid.appendChild(btn);
    }

    // ── PASO 2: Pedir disponibilidad y reservas al servidor ───────
    var disponibilidad = [];
    var reservas       = [];

    try {
        var rd = await apiFetch("/disponibilidad");
        if (rd.ok && Array.isArray(rd.data)) disponibilidad = rd.data;
    } catch(e) {}

    try {
        var rr = await apiFetch("/reservas");
        if (rr.ok && Array.isArray(rr.data)) reservas = rr.data;
    } catch(e) {}

    // ── PASO 3: Colorear cada botón según disponibilidad ─────────
    var botones = grid.querySelectorAll(".dia-btn");
    botones.forEach(function(btn) {
        var diaISO = btn.dataset.fecha;
        var diaSem = Number(btn.dataset.diasem);

        // Bloques del entrenador para este día de semana
        var bloques = disponibilidad.filter(function(b) {
            return Number(b.dia_semana) === diaSem;
        });

        // Reservas activas en esta fecha
        var reservasDelDia = reservas.filter(function(r) {
            return r.fecha === diaISO && r.estado === "activa";
        });

        // Quitar clase cargando
        btn.classList.remove("dia-btn--cargando");

        var ahora      = new Date();
        var horaActual = ahora.getHours();

        // Día pasado → no disponible directamente
        if (diaISO < hoyISO) {
            btn.classList.add("dia-btn--pasado");
            btn.style.cursor  = "default";
            btn.style.opacity = "0.35";
            // Eliminar el evento click que se puso antes
            btn.replaceWith(btn.cloneNode(true));
            return;
        }

        if (bloques.length === 0) {
            btn.classList.add("dia-btn--vacio");
        } else {
            // Calcular slots totales vs ocupados vs pasados (si es hoy)
            var totalSlots    = 0;
            var totalOcupados = 0;
            var totalPasados  = 0;

            bloques.forEach(function(b) {
                var hIni = parseInt(b.hora_inicio.split(":")[0]);
                var hFin = parseInt(b.hora_fin.split(":")[0]);

                for (var h = hIni; h < hFin; h++) {
                    totalSlots++;

                    // Si es hoy y la hora ya pasó → cuenta como pasado
                    if (diaISO === hoyISO && h < horaActual) {
                        totalPasados++;
                        continue;
                    }

                    // Contar si está reservado
                    var hStr = String(h).padStart(2, "0");
                    var reservado = reservasDelDia.find(function(r) {
                        return r.hora_inicio === hStr + ":00";
                    });
                    if (reservado) totalOcupados++;
                }
            });

            var slotsUtiles = totalSlots - totalPasados;

            if (slotsUtiles <= 0) {
                // Todos los slots de hoy ya pasaron
                btn.classList.add("dia-btn--pasado");
                btn.style.cursor  = "default";
                btn.style.opacity = "0.35";
                btn.replaceWith(btn.cloneNode(true));
            } else if (totalOcupados === 0) {
                btn.classList.add("dia-btn--libre");
            } else if (totalOcupados < slotsUtiles) {
                btn.classList.add("dia-btn--parcial");
            } else {
                btn.classList.add("dia-btn--lleno");
            }
        }
    });
}

function cambiarSemana(delta) {
    state.semana += delta;
    cargarCalendario();
}

function seleccionarDia(fechaISO, nombreDia) {
    state.fechaDia = fechaISO;
    document.getElementById("horario-dia-titulo").textContent = nombreDia;
    document.getElementById("horario-dia-fecha").textContent  = formatFecha(fechaISO);
    navigate("horario-dia");
    cargarHorariosDia(fechaISO);
}


// ══════════════════════════════════════════════════════
//  HORARIOS DEL DÍA
// ══════════════════════════════════════════════════════

async function cargarHorariosDia(fechaISO) {
    var container = document.getElementById("turnos-container");
    container.innerHTML = "<p style='color:var(--taupe);padding:20px 0'>Cargando horarios...</p>";

    // Día de semana 0=Lunes
    var d      = new Date(fechaISO + "T12:00:00");
    var diaSem = d.getDay() === 0 ? 6 : d.getDay() - 1;

    var disponibilidad = [];
    var reservas       = [];

    try {
        var rd = await apiFetch("/disponibilidad");
        if (rd.ok && Array.isArray(rd.data)) disponibilidad = rd.data;
    } catch(e) {}

    try {
        var rr = await apiFetch("/reservas");
        if (rr.ok && Array.isArray(rr.data)) reservas = rr.data;
    } catch(e) {}

    // Bloques del entrenador para este día
    var bloques = disponibilidad.filter(function(b) {
        return Number(b.dia_semana) === diaSem;
    });

    // Reservas activas este día
    var reservasHoy = reservas.filter(function(r) {
        return r.fecha === fechaISO && r.estado === "activa";
    });

    container.innerHTML = "";

    if (bloques.length === 0) {
        container.innerHTML = "<p style='color:var(--taupe);text-align:center;padding:40px 0'>No hay horarios configurados para este día</p>";
        return;
    }

    // Ordenar bloques por hora de inicio
    bloques.sort(function(a, b) {
        return a.hora_inicio.localeCompare(b.hora_inicio);
    });

    bloques.forEach(function(bloque) {
        var hIni = parseInt(bloque.hora_inicio.split(":")[0]);
        var hFin = parseInt(bloque.hora_fin.split(":")[0]);

        // Título del turno
        var turnoDiv = document.createElement("div");
        turnoDiv.className = "turno-titulo";
        turnoDiv.textContent = hIni < 14 ? "Turno de mañana" : "Turno de tarde";
        container.appendChild(turnoDiv);

        // Un slot por cada hora dentro del bloque
        for (var h = hIni; h < hFin; h++) {
            var hStr    = String(h).padStart(2, "0");
            var hFinStr = String(h + 1).padStart(2, "0");
            var horaIni = hStr + ":00:00";
            var horaFin = hFinStr + ":00:00";

            // Hora en formato 12h como en el wireframe: "10:00 - 11:00 AM"
            var sufijo  = h < 12 ? "AM" : "PM";
            var hShow   = h > 12 ? h - 12 : h;
            var hFinShow = (h+1) > 12 ? (h+1) - 12 : (h+1);
            var sufFin  = (h+1) < 12 ? "AM" : "PM";
            var labelHora = hStr + ":00 - " + hFinStr + ":00 " + sufFin;

            // Buscar si está ocupado
            var ocupado = reservasHoy.find(function(r) {
                return r.hora_inicio === hStr + ":00";
            });

            // Comprobar si la hora ya pasó (solo para el día de hoy)
            var ahora      = new Date();
            var hoyISO2    = getISODate(ahora);
            var horaActual = ahora.getHours();
            var yaPaso     = (fechaISO === hoyISO2) && (h < horaActual);

            var slot = document.createElement("button");

            if (yaPaso) {
                slot.className   = "horario-slot horario-slot--pasado";
                slot.textContent = labelHora + " — Pasado";
                slot.disabled    = true;
            } else if (ocupado) {
                slot.className   = "horario-slot horario-slot--ocupado";
                slot.textContent = labelHora;
                slot.disabled    = true;
            } else {
                slot.className   = "horario-slot horario-slot--libre";
                slot.textContent = labelHora;
                if (state.user && state.user.rol !== "entrenador") {
                    (function(hIniC, hFinC) {
                        slot.addEventListener("click", function() {
                            abrirCrearReserva(hIniC, hFinC);
                        });
                    })(horaIni, horaFin);
                }
            }

            container.appendChild(slot);
        }
    });
}

function abrirCrearReserva(horaIni, horaFin) {
    state.horaIni = horaIni;
    state.horaFin = horaFin;

    document.getElementById("res-fecha").textContent = formatFecha(state.fechaDia);
    document.getElementById("res-hora").textContent  = horaIni.slice(0,5) + " – " + horaFin.slice(0,5);
    document.getElementById("reserva-comentario").value = "";

    ocultarMsg("crear-error");
    ocultarMsg("crear-success");
    navigate("crear-reserva");
}

async function confirmarReserva() {
    const comentario = document.getElementById("reserva-comentario").value;

    const { ok, data } = await apiFetch("/reservas", {
        method: "POST",
        body: JSON.stringify({
            fecha:       state.fechaDia,
            hora_inicio: state.horaIni,
            hora_fin:    state.horaFin,
            comentario:  comentario
        })
    });

    if (!ok) return mostrarError("crear-error", data.error || "Error al crear la reserva");

    mostrarExito("crear-success", "✅ Reserva creada correctamente");
    // Redirigir a reservas tras 1 segundo
    setTimeout(function() { navigate("reservas"); }, 1200);
}


// ══════════════════════════════════════════════════════
//  RESERVAS
// ══════════════════════════════════════════════════════

async function cargarReservas() {
    const { ok, data } = await apiFetch("/reservas");
    if (!ok) return;

    state.reservas = data;

    document.getElementById("reservas-titulo").textContent =
        state.user && state.user.rol === "entrenador" ? "Todas las reservas" : "Mis reservas";

    filtrarReservas(state.filtroEstado);
}

function filtrarReservas(estado) {
    state.filtroEstado = estado;

    // Actualizar tabs activos
    document.querySelectorAll(".tabs-filter .tab").forEach(function(t) {
        const textos = { "activa": "Activas", "completada": "Completadas", "cancelada": "Canceladas" };
        t.classList.toggle("active", t.textContent === textos[estado]);
    });

    const lista     = document.getElementById("lista-reservas");
    lista.innerHTML = "";

    const filtradas = state.reservas.filter(function(r) { return r.estado === estado; });

    if (filtradas.length === 0) {
        lista.innerHTML = '<div class="empty-msg">No hay reservas ' + estado + 's</div>';
        return;
    }

    const esEntrenador = state.user && state.user.rol === "entrenador";

    filtradas.forEach(function(r) {
        const card = document.createElement("div");
        card.className = "reserva-card";

        const botonCancelar = estado === "activa"
            ? '<button class="btn-sm cancel" onclick="cancelarReserva(' + r.id + ')">Cancelar</button>'
            : "";

        const infoExtra = esEntrenador && r.cliente_nombre
            ? '<div class="reserva-cliente">👤 ' + r.cliente_nombre + '</div>'
            : (!esEntrenador && r.entrenador_nombre
                ? '<div class="reserva-cliente">💪 ' + r.entrenador_nombre + '</div>'
                : "");

        card.innerHTML =
            '<div class="reserva-info">' +
                '<div class="reserva-fecha">📅 ' + formatFecha(r.fecha) + '</div>' +
                '<div class="reserva-hora">🕐 ' + r.hora_inicio + ' – ' + r.hora_fin + '</div>' +
                (r.comentario ? '<div class="reserva-comentario">"' + r.comentario + '"</div>' : "") +
                infoExtra +
            '</div>' +
            '<div class="reserva-actions">' +
                '<span class="estado-badge estado-' + r.estado + '">' + r.estado + '</span>' +
                botonCancelar +
            '</div>';

        lista.appendChild(card);
    });
}

async function cancelarReserva(id) {
    if (!confirm("¿Seguro que quieres cancelar esta reserva?")) return;

    const { ok, data } = await apiFetch("/reservas/" + id, { method: "DELETE" });

    if (ok) {
        cargarReservas();
    } else {
        alert(data.error || "Error al cancelar");
    }
}


// ══════════════════════════════════════════════════════
//  CLIENTES (solo entrenador)
// ══════════════════════════════════════════════════════

async function cargarClientes() {
    const { ok, data } = await apiFetch("/usuarios");
    const lista = document.getElementById("lista-clientes");
    lista.innerHTML = "";

    if (!ok || data.length === 0) {
        lista.innerHTML = '<div class="empty-msg">No hay clientes registrados</div>';
        return;
    }

    data.forEach(function(c) {
        const card = document.createElement("div");
        card.className = "cliente-card";
        card.innerHTML =
            '<div class="cliente-avatar">' + c.nombre.charAt(0).toUpperCase() + '</div>' +
            '<div>' +
                '<div class="cliente-nombre">' + c.nombre + '</div>' +
                '<div class="cliente-email">'  + c.email  + '</div>' +
                (c.telefono ? '<div class="cliente-email">📞 ' + c.telefono + '</div>' : "") +
            '</div>';
        lista.appendChild(card);
    });
}


// ══════════════════════════════════════════════════════
//  DISPONIBILIDAD (solo entrenador)
// ══════════════════════════════════════════════════════

async function cargarDisponibilidad() {
    const { ok, data } = await apiFetch("/disponibilidad");
    const lista = document.getElementById("lista-disponibilidad");
    lista.innerHTML = "";

    if (!ok || data.length === 0) {
        lista.innerHTML = '<div class="empty-msg">No hay bloques configurados</div>';
        return;
    }

    data.forEach(function(d) {
        const item = document.createElement("div");
        item.className = "disp-item";
        item.innerHTML =
            '<span class="disp-dia">' + DIAS[d.dia_semana] + '</span>' +
            '<span class="disp-hora">' + d.hora_inicio + ' – ' + d.hora_fin + '</span>' +
            '<button class="btn-sm cancel" onclick="eliminarDisponibilidad(' + d.id + ')">Eliminar</button>';
        lista.appendChild(item);
    });
}

async function crearDisponibilidad() {
    const dia    = document.getElementById("disp-dia").value;
    const inicio = document.getElementById("disp-inicio").value;
    const fin    = document.getElementById("disp-fin").value;

    if (!inicio || !fin || inicio >= fin) {
        alert("La hora de fin debe ser posterior a la de inicio");
        return;
    }

    const { ok, data } = await apiFetch("/disponibilidad", {
        method: "POST",
        body: JSON.stringify({
            dia_semana:   Number(dia),
            hora_inicio:  inicio + ":00",
            hora_fin:     fin + ":00"
        })
    });

    if (ok) {
        cargarDisponibilidad();
    } else {
        alert(data.error || "Error al crear disponibilidad");
    }
}

async function eliminarDisponibilidad(id) {
    if (!confirm("¿Eliminar este bloque?")) return;
    const { ok } = await apiFetch("/disponibilidad/" + id, { method: "DELETE" });
    if (ok) cargarDisponibilidad();
}


// ══════════════════════════════════════════════════════
//  PERFIL
// ══════════════════════════════════════════════════════

async function cargarPerfil() {
    const { ok, data } = await apiFetch("/usuarios/me");
    if (!ok) return;

    document.getElementById("perfil-nombre").value   = data.nombre   || "";
    document.getElementById("perfil-telefono").value = data.telefono || "";
    document.getElementById("perfil-password").value = "";

    document.getElementById("perfil-nombre-display").textContent = data.nombre;
    document.getElementById("perfil-rol-display").textContent    = data.rol;
    document.getElementById("perfil-inicial").textContent        = data.nombre.charAt(0).toUpperCase();

    ocultarMsg("perfil-error");
    ocultarMsg("perfil-success");
}

async function guardarPerfil() {
    ocultarMsg("perfil-error");
    ocultarMsg("perfil-success");

    const nombre   = document.getElementById("perfil-nombre").value.trim();
    const telefono = document.getElementById("perfil-telefono").value.trim();
    const password = document.getElementById("perfil-password").value;

    const payload = {};
    if (nombre)   payload.nombre   = nombre;
    if (telefono) payload.telefono = telefono;
    if (password) payload.password = password;

    if (Object.keys(payload).length === 0) {
        return mostrarError("perfil-error", "No hay cambios para guardar");
    }

    const { ok, data } = await apiFetch("/usuarios/me", {
        method: "PATCH",
        body: JSON.stringify(payload)
    });

    if (!ok) return mostrarError("perfil-error", data.error || "Error al guardar");

    // Actualizar la cabecera del perfil con el nuevo nombre
    if (nombre) {
        document.getElementById("perfil-nombre-display").textContent = nombre;
        document.getElementById("perfil-inicial").textContent        = nombre.charAt(0).toUpperCase();
    }

    mostrarExito("perfil-success", "✅ Perfil actualizado correctamente");
}


// ══════════════════════════════════════════════════════
//  INICIO — restaurar sesión o mostrar login
// ══════════════════════════════════════════════════════

(function init() {
    const tokenGuardado = localStorage.getItem("fr_token");

    if (tokenGuardado) {
        try {
            const payload = JSON.parse(atob(tokenGuardado.split(".")[1]));
            // Comprobar que el token no ha expirado
            if (payload.exp * 1000 > Date.now()) {
                state.token = tokenGuardado;
                state.user  = payload;
                iniciarSesion(tokenGuardado, payload.nombre, payload.rol);
                return;
            }
        } catch (e) {
            // Token corrupto, ignorar
        }
        localStorage.removeItem("fr_token");
    }

    // Mostrar login
    const login = document.getElementById("view-login");
    login.classList.remove("hidden");
    login.classList.add("active");
})();
