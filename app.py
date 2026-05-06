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
# UTIL
# =========================
def validar_texto(texto):
    return texto and isinstance(texto, str) and len(texto.strip()) >= 3

def normalizar(texto):
    texto = texto.lower()
    texto = texto.replace("riñones", "riñón")
    texto = re.sub(r"\s+", " ", texto)
    return texto

def match(texto, palabras):
    return any(p in texto for p in palabras)

# =========================
# MÉDICOS + HORARIOS
# =========================
def generar_turnos(especialidad):

    medicos = {
        "cardiología": ["Dr. López", "Dra. Martínez"],
        "neurología": ["Dr. Gómez", "Dra. Ruiz"],
        "nefrología": ["Dr. Benítez", "Dra. Acosta"],
        "ginecología": ["Dra. Fernández", "Dra. Silva"],
        "obstetricia": ["Dra. Pérez", "Dra. Díaz"],
        "traumatología": ["Dr. Herrera", "Dra. Castro"],
        "dermatología": ["Dra. Varela", "Dr. Ríos"],
        "oftalmología": ["Dr. Molina", "Dra. Suárez"],
        "odontología": ["Dr. Navarro", "Dra. López"],
        "gastroenterología": ["Dr. Romero", "Dra. Campos"],
        "neumonología": ["Dr. Torres", "Dra. Vega"],
        "pediatría": ["Dra. Medina", "Dr. Salas"],
        "clínica médica": ["Dr. General 1", "Dr. General 2"]
    }

    horarios = ["09:00", "12:00", "16:00", "18:00"]

    return [
        {
            "doctor": m,
            "turnos": horarios
        }
        for m in medicos.get(especialidad, ["Dr. Disponible"])
    ]

# =========================
# TRIAGE
# =========================
def triage(texto):

    t = normalizar(texto)

    if match(t, ["pecho","infarto","taquicardia","arritmia","dolor","falta de aire"]):
        return "ALTA","cardiología",["Urgente"]

    if match(t, ["convulsión","desmayo","pérdida","cefalea"]):
        return "ALTA","neurología",["Urgente"]

    if match(t, ["riñón","orina","urinario","ardor","infección","dolor lumbar"]):
        return "MEDIA","nefrología",["Control"]

    if match(t, ["embarazada","contracciones","parto"]):
        return "ALTA","obstetricia",["Urgente"]

    if match(t, ["vaginal","flujo","pélvico"]):
        return "MEDIA","ginecología",["Control"]

    if match(t, ["fractura","luxación","golpe"]):
        return "MEDIA","traumatología",["Reposo"]

    if match(t, ["piel","roncha","alergia"]):
        return "BAJA","dermatología",["Control"]

    if match(t, ["ojo","visión","borrosa"]):
        return "MEDIA","oftalmología",["Control"]

    if match(t, ["diente","muela","encía"]):
        return "MEDIA","odontología",["Control"]

    if match(t, ["estómago","náuseas","diarrea","abdomen"]):
        return "MEDIA","gastroenterología",["Dieta"]

    if match(t, ["tos","asma","pulmón"]):
        return "ALTA","neumonología",["Urgente"]

    if match(t, ["bebé","niño","fiebre"]):
        return "MEDIA","pediatría",["Control"]

    return "BAJA","clínica médica",["Control"]

# =========================
# TRIAGE ENDPOINT
# =========================
@app.route("/triage", methods=["POST"])
def triage_route():
    try:
        data = request.get_json()

        texto = data.get("texto")

        if not validar_texto(texto):
            return jsonify({"ok": False}), 400

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
        return jsonify({"ok": False}), 500

# =========================
# CONFIRMAR (FIX FINAL REAL)
# =========================
@app.route("/confirmar", methods=["POST"])
def confirmar():
    try:
        data = request.get_json(silent=True)

        if not data:
            return jsonify({"ok": False, "error": "No JSON recibido"}), 400

        nombre = data.get("nombre", "").strip()
        dni = data.get("dni", "").strip()
        sintomas = data.get("sintomas", "").strip()
        especialidad = data.get("especialidad", "").strip()
        doctor = data.get("doctor", "").strip()
        fecha = data.get("fecha", "").strip().replace("hs", "")

        # 🔴 VALIDACIÓN CRÍTICA
        if not all([nombre, dni, sintomas, especialidad, doctor, fecha]):
            return jsonify({
                "ok": False,
                "error": "Faltan datos en el turno"
            }), 400

        horarios_validos = ["09:00", "12:00", "16:00", "18:00"]

        if fecha not in horarios_validos:
            return jsonify({
                "ok": False,
                "error": f"Horario inválido: {fecha}"
            }), 400

        conn = sqlite3.connect(DB)
        c = conn.cursor()

        # 🔴 EVITA DOBLE TURNO
        c.execute("""
        SELECT id FROM turnos
        WHERE doctor=? AND fecha=?
        """, (doctor, fecha))

        if c.fetchone():
            conn.close()
            return jsonify({
                "ok": False,
                "error": "Ese turno ya está ocupado"
            }), 409

        c.execute("""
        INSERT INTO turnos (
            nombre,dni,sintomas,especialidad,doctor,fecha,urgencia
        )
        VALUES (?,?,?,?,?,?,?)
        """, (
            nombre,
            dni,
            sintomas,
            especialidad,
            doctor,
            fecha,
            "MEDIA"
        ))

        conn.commit()
        conn.close()

        return jsonify({"ok": True})

    except Exception as e:
        logging.error("CONFIRMAR ERROR: " + str(e))
        return jsonify({
            "ok": False,
            "error": str(e)
        }), 500

# =========================
@app.route("/")
def index():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
