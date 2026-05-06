import sqlite3
import logging
import re
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, session, redirect

app = Flask(__name__)
app.secret_key = "super_secret_key"

DB = "turnos.db"

# =========================
# LOGS
# =========================
logging.basicConfig(
    filename="app.log",
    level=logging.ERROR,
    format="%(asctime)s %(levelname)s %(message)s"
)

# =========================
# DB
# =========================
def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS turnos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT,
        dni TEXT,
        sintomas TEXT,
        especialidad TEXT,
        doctor TEXT,
        fecha TEXT,
        urgencia TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        rol TEXT
    )
    """)

    # USUARIO DE PRUEBA
    c.execute("SELECT id FROM usuarios WHERE username = ?", ("admin",))
    if not c.fetchone():
        c.execute("""
        INSERT INTO usuarios (username, password, rol)
        VALUES (?, ?, ?)
        """, ("admin", "1234", "admin"))

    conn.commit()
    conn.close()

init_db()

# =========================
# VALIDACIÓN
# =========================
def validar_texto(texto):
    return texto and isinstance(texto, str) and len(texto.strip()) >= 3

# =========================
# NORMALIZACIÓN
# =========================
def normalizar(texto):
    texto = texto.lower()
    texto = re.sub(r"[^a-záéíóúñü\s]", " ", texto)
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto

def match(texto, palabras):
    return any(re.search(rf"\b{p}\b", texto) for p in palabras)

# =========================
# MÉDICOS
# =========================
def generar_turnos(especialidad):

    medicos = {
        "cardiología": ["Dr. López", "Dra. Martínez"],
        "neurología": ["Dr. Gómez", "Dra. Ruiz"],
        "ginecología": ["Dra. Fernández", "Dra. Silva"],
        "obstetricia": ["Dra. Pérez", "Dra. Díaz"],
        "traumatología": ["Dr. Herrera", "Dra. Castro"],
        "dermatología": ["Dra. Varela", "Dr. Ríos"],
        "oftalmología": ["Dr. Molina", "Dra. Suárez"],
        "odontología": ["Dr. Navarro", "Dra. López"],
        "gastroenterología": ["Dr. Romero", "Dra. Campos"],
        "nefrología": ["Dr. Benítez", "Dra. Acosta"],
        "neumonología": ["Dr. Torres", "Dra. Vega"],
        "pediatría": ["Dra. Medina", "Dr. Salas"],
        "clínica médica": ["Dr. General 1", "Dr. General 2"]
    }

    return medicos.get(especialidad, ["Dr. Disponible 1", "Dr. Disponible 2"])

# =========================
# TRIAGE (ESTRICTO CORREGIDO)
# =========================
def triage(texto):

    t = normalizar(texto)

    if match(t, ["pecho","opresión","infarto","palpitaciones","taquicardia","arritmia","dolor cardíaco","falta de aire"]):
        return "ALTA","cardiología",[
            "Acudir inmediatamente a guardia",
            "No realizar actividad física",
            "Mantener reposo absoluto",
            "Controlar respiración",
            "No quedarse solo"
        ]

    if match(t, ["convulsión","desmayo","mareo","pérdida","parálisis","debilidad","hormigueo","cefalea"]):
        return "ALTA","neurología",[
            "Acudir urgente",
            "Evitar conducir",
            "Reposo inmediato",
            "Acompañamiento",
            "Control médico urgente"
        ]

    if match(t, ["riñón","orina","urinario","ardor","infección urinaria","dolor lumbar"]):
        return "MEDIA","nefrología",[
            "Aumentar hidratación",
            "Evitar sal",
            "Control urinario",
            "Reposo",
            "Consulta especialista"
        ]

    if match(t, ["embarazada","contracciones","parto","movimientos","líquido"]):
        return "ALTA","obstetricia",[
            "Acudir a guardia obstétrica",
            "Control fetal inmediato",
            "Reposo absoluto",
            "Hidratación",
            "Acompañamiento"
        ]

    if match(t, ["vaginal","flujo","menstrual","útero","ovarios","sangrado","pélvico"]):
        return "MEDIA","ginecología",[
            "Evitar relaciones sexuales",
            "Controlar sangrado",
            "Higiene íntima adecuada",
            "Evitar esfuerzos",
            "Consulta ginecológica"
        ]

    if match(t, ["fractura","luxación","esguince","golpe","caída","dolor óseo","lesión"]):
        return "MEDIA","traumatología",[
            "Inmovilizar la zona",
            "Aplicar frío local",
            "Evitar movimiento",
            "Reposo",
            "Consulta traumatológica"
        ]

    if match(t, ["piel","mancha","erupción","roncha","picazón","alergia","dermatitis"]):
        return "BAJA","dermatología",[
            "Evitar rascarse",
            "Mantener higiene",
            "Evitar exposición solar",
            "Usar cremas suaves",
            "Consulta dermatológica"
        ]

    if match(t, ["ojo","visión","vista","lagrimeo","ardor","borrosa"]):
        return "MEDIA","oftalmología",[
            "Evitar pantallas",
            "No frotar ojos",
            "Lágrimas artificiales",
            "Descanso visual",
            "Consulta oftalmológica"
        ]

    if match(t, ["diente","muela","encía","dolor dental","infección"]):
        return "MEDIA","odontología",[
            "Evitar alimentos duros",
            "Higiene bucal",
            "Enjuague tibio",
            "Evitar frío/calor",
            "Consulta odontológica"
        ]

    if match(t, ["estómago","náuseas","vómitos","diarrea","acidez","digestión","abdomen"]):
        return "MEDIA","gastroenterología",[
            "Dieta liviana",
            "Hidratación",
            "Evitar grasas",
            "Reposo",
            "Consulta médica"
        ]

    if match(t, ["tos","respirar","falta de aire","asma","bronquios","pulmón"]):
        return "ALTA","neumonología",[
            "Evitar esfuerzo físico",
            "Ambiente ventilado",
            "Control respiración",
            "Uso de medicación si posee",
            "Consulta urgente"
        ]

    if match(t, ["bebé","niño","infante","fiebre"]):
        return "MEDIA","pediatría",[
            "Control de temperatura",
            "Hidratación",
            "Observación constante",
            "Reposo",
            "Consulta pediátrica"
        ]

    return "BAJA","clínica médica",[
        "Reposo",
        "Hidratación",
        "Control de síntomas",
        "Evitar esfuerzos",
        "Consulta médica"
    ]

# =========================
# RUTAS
# =========================
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/triage", methods=["POST"])
def triage_route():
    try:
        data = request.get_json()

        if not data or not validar_texto(data.get("texto")):
            return jsonify({"ok": False, "error": "Texto inválido"}), 400

        texto = data["texto"]

        urg, esp, rec = triage(texto)
        medicos = generar_turnos(esp)

        return jsonify({
            "ok": True,
            "urgencia": urg,
            "especialidad": esp,
            "recomendaciones": rec,
            "medicos": medicos
        })

    except Exception as e:
        logging.error(str(e))
        return jsonify({"ok": False, "error": "Error interno"}), 500

@app.route("/confirmar", methods=["POST"])
def confirmar():
    data = request.json

    fecha = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d %H:%M")

    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("""
    INSERT INTO turnos (nombre,dni,sintomas,especialidad,doctor,fecha,urgencia)
    VALUES (?,?,?,?,?,?,?)
    """,(
        data["nombre"],
        data["dni"],
        data["sintomas"],
        data["especialidad"],
        data["doctor"],
        fecha,
        "MEDIA"
    ))

    conn.commit()
    conn.close()

    return jsonify({"ok": True})

# LOGIN / CALENDARIO / ADMIN (SIN CAMBIOS ESTRUCTURALES)
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        u = request.form["user"]
        p = request.form["pass"]

        conn = sqlite3.connect(DB)
        c = conn.cursor()
        c.execute("SELECT * FROM usuarios WHERE username=? AND password=?", (u,p))
        user = c.fetchone()
        conn.close()

        if user:
            session["user"] = u
            session["rol"] = user[3]
            return redirect("/calendario")

    return render_template("login.html")

@app.route("/calendario")
def calendario():
    if "user" not in session:
        return redirect("/login")

    doctor = request.args.get("doctor")

    conn = sqlite3.connect(DB)
    c = conn.cursor()

    if doctor:
        c.execute("SELECT * FROM turnos WHERE doctor=?", (doctor,))
    else:
        c.execute("SELECT * FROM turnos")

    turnos = c.fetchall()

    c.execute("SELECT DISTINCT doctor FROM turnos")
    doctores = [d[0] for d in c.fetchall()]

    conn.close()

    return render_template("calendario.html", turnos=turnos, doctores=doctores)

@app.route("/admin")
def admin():
    if session.get("rol") != "admin":
        return redirect("/login")

    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("SELECT * FROM usuarios")
    users = c.fetchall()

    conn.close()

    return render_template("admin.html", users=users)

# =========================
# RUN
# =========================
if __name__ == "__main__":
    app.run(debug=True)
