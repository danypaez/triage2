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
    texto = texto.replace("orinar", "orina")
    texto = re.sub(r"\s+", " ", texto)
    return texto

def match(texto, palabras):
    return any(p in texto for p in palabras)

# =========================
# MÉDICOS + HORARIOS (FIX CLAVE)
# =========================
def generar_turnos(especialidad):

    base = {
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

    medicos = base.get(especialidad, ["Dr. Disponible 1"])

    return [
        {
            "doctor": m,
            "turnos": [
                (datetime.now() + timedelta(hours=2)).strftime("%H:%M"),
                (datetime.now() + timedelta(hours=4)).strftime("%H:%M"),
                (datetime.now() + timedelta(hours=6)).strftime("%H:%M")
            ]
        }
        for m in medicos
    ]

# =========================
# TRIAGE (MEJORADO SIN CAMBIAR LOGICA MEDICA)
# =========================
def triage(texto):

    t = normalizar(texto)

    if match(t, ["pecho","opresión","infarto","taquicardia","arritmia","dolor cardíaco","falta de aire"]):
        return "ALTA","cardiología",["Urgente"]

    if match(t, ["convulsión","desmayo","mareo","pérdida","parálisis","cefalea"]):
        return "ALTA","neurología",["Urgente"]

    if match(t, ["riñón","orina","urinario","ardor","infección","dolor lumbar"]):
        return "MEDIA","nefrología",["Control de hidratación"]

    if match(t, ["embarazada","contracciones","parto","líquido"]):
        return "ALTA","obstetricia",["Urgente"]

    if match(t, ["vaginal","flujo","menstrual","pélvico"]):
        return "MEDIA","ginecología",["Control ginecológico"]

    if match(t, ["fractura","luxación","esguince","golpe","caída"]):
        return "MEDIA","traumatología",["Reposo"]

    if match(t, ["piel","erupción","roncha","alergia"]):
        return "BAJA","dermatología",["Higiene"]

    if match(t, ["ojo","visión","borrosa"]):
        return "MEDIA","oftalmología",["Control"]

    if match(t, ["diente","muela","encía"]):
        return "MEDIA","odontología",["Consulta"]

    if match(t, ["estómago","náuseas","diarrea","abdomen"]):
        return "MEDIA","gastroenterología",["Dieta"]

    if match(t, ["tos","respirar","asma","pulmón"]):
        return "ALTA","neumonología",["Urgente"]

    if match(t, ["bebé","niño","fiebre"]):
        return "MEDIA","pediatría",["Control"]

    return "BAJA","clínica médica",["Control general"]

# =========================
# RUTA TRIAGE
# =========================
@app.route("/triage", methods=["POST"])
def triage_route():
    try:
        data = request.get_json()

        if not data or not validar_texto(data.get("texto")):
            return jsonify({"ok": False}), 400

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
        return jsonify({"ok": False}), 500

# =========================
# CONFIRMAR
# =========================
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
@app.route("/")
def index():
    return render_template("index.html")
