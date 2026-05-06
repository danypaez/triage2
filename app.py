import sqlite3
import logging
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

    # =========================
    # USUARIO DE PRUEBA
    # =========================
    c.execute("SELECT id FROM usuarios WHERE username = ?", ("admin",))
    existe = c.fetchone()

    if not existe:
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
# MÉDICOS REALES POR ESPECIALIDAD
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
# TRIAGE (NO MODIFICADO - ESTRICTO)
# =========================
def triage(texto):

    t = texto.lower()

    # =========================
    # CARDIOLOGÍA
    # =========================
    if any(x in t for x in [
        "pecho","opresión","infarto","palpitaciones","taquicardia","arritmia",
        "dolor cardíaco","falta de aire con esfuerzo"
    ]):
        return "ALTA","cardiología",[
            "Acudir inmediatamente a guardia",
            "No realizar actividad física",
            "Mantener reposo absoluto",
            "Controlar respiración",
            "No quedarse solo"
        ]

    # =========================
    # NEUROLOGÍA
    # =========================
    if any(x in t for x in [
        "convulsión","desmayo","mareo fuerte","pérdida de conocimiento",
        "parálisis","debilidad","hormigueo","cefalea intensa"
    ]):
        return "ALTA","neurología",[
            "Acudir urgente",
            "Evitar conducir",
            "Reposo inmediato",
            "Acompañamiento",
            "Control médico urgente"
        ]

    # =========================
    # GINECOLOGÍA
    # =========================
    if any(x in t for x in [
        "vaginal","flujo","menstrual","útero","ovarios","sangrado vaginal",
        "dolor pélvico"
    ]):
        return "MEDIA","ginecología",[
            "Evitar relaciones sexuales",
            "Controlar sangrado",
            "Higiene íntima adecuada",
            "Evitar esfuerzos",
            "Consulta ginecológica"
        ]

    # =========================
    # OBSTETRICIA
    # =========================
    if any(x in t for x in [
        "embarazada","contracciones","parto","movimientos del bebé",
        "pérdida de líquido"
    ]):
        return "ALTA","obstetricia",[
            "Acudir a guardia obstétrica",
            "Control fetal inmediato",
            "Reposo absoluto",
            "Hidratación",
            "Acompañamiento"
        ]

    # =========================
    # TRAUMATOLOGÍA
    # =========================
    if any(x in t for x in [
        "golpe","fractura","luxación","torcedura","esguince","caída",
        "dolor óseo","lesión"
    ]):
        return "MEDIA","traumatología",[
            "Inmovilizar la zona",
            "Aplicar frío local",
            "Evitar movimiento",
            "Reposo",
            "Consulta traumatológica"
        ]

    # =========================
    # DERMATOLOGÍA
    # =========================
    if any(x in t for x in [
        "piel","mancha","erupción","roncha","picazón","alergia","dermatitis"
    ]):
        return "BAJA","dermatología",[
            "Evitar rascarse",
            "Mantener higiene",
            "Evitar exposición solar",
            "Usar cremas suaves",
            "Consulta dermatológica"
        ]

    # =========================
    # OFTALMOLOGÍA
    # =========================
    if any(x in t for x in [
        "ojo","visión","vista","lagrimeo","ardor ocular","visión borrosa"
    ]):
        return "MEDIA","oftalmología",[
            "Evitar pantallas",
            "No frotar ojos",
            "Usar lágrimas artificiales",
            "Descanso visual",
            "Consulta oftalmológica"
        ]

    # =========================
    # ODONTOLOGÍA
    # =========================
    if any(x in t for x in [
        "diente","muela","encía","dolor dental","infección dental"
    ]):
        return "MEDIA","odontología",[
            "Evitar alimentos duros",
            "Mantener higiene bucal",
            "Enjuague con agua tibia",
            "Evitar frío/calor",
            "Consulta odontológica"
        ]

    # =========================
    # GASTROENTEROLOGÍA
    # =========================
    if any(x in t for x in [
        "estómago","náuseas","vómitos","diarrea","acidez","digestión",
        "dolor abdominal"
    ]):
        return "MEDIA","gastroenterología",[
            "Dieta liviana",
            "Hidratación constante",
            "Evitar grasas",
            "Reposo",
            "Consulta médica"
        ]

    # =========================
    # NEFROLOGÍA
    # =========================
    if any(x in t for x in [
        "riñón","orina","dolor lumbar urinario","infección urinaria",
        "ardor al orinar"
    ]):
        return "MEDIA","nefrología",[
            "Aumentar hidratación",
            "Evitar sal",
            "Control urinario",
            "Reposo",
            "Consulta especialista"
        ]

    # =========================
    # NEUMONOLOGÍA
    # =========================
    if any(x in t for x in [
        "tos","respirar","falta de aire","asma","bronquios","pulmón"
    ]):
        return "ALTA","neumonología",[
            "Evitar esfuerzo físico",
            "Ambiente ventilado",
            "Control respiración",
            "Uso de medicación si posee",
            "Consulta urgente"
        ]

    # =========================
    # PEDIATRÍA
    # =========================
    if any(x in t for x in [
        "bebé","niño","infante","fiebre en niño"
    ]):
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

# =========================
# LOGIN
# =========================
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

# =========================
# CALENDARIO
# =========================
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

# =========================
# ADMIN
# =========================
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
