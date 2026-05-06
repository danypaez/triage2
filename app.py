import os
import sqlite3
from datetime import datetime, timedelta, time
from flask import Flask, render_template, request, jsonify, session, redirect

app = Flask(__name__)
app.secret_key = "clave_secreta"

DB = "turnos.db"

# =========================
# USUARIOS
# =========================
USUARIOS = {
    "admin": "1234",
    "doctor": "1234"
}

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
        fecha TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

# =========================
# ESPECIALIDADES (AMPLIAS)
# =========================
ESPECIALIDADES = {

    "cardiología": [
        "pecho","infarto","palpitaciones","presion","presión","corazon","corazón",
        "taquicardia","arritmia","latidos","hipertension","hipotension"
    ],

    "ginecología": [
        "menstruacion","menstruación","regla","flujo","vaginal","útero","utero",
        "ovarios","dolor pelvico","dolor pélvico","sangrado vaginal"
    ],

    "obstetricia": [
        "embarazo","embarazada","gestacion","gestación","parto","contracciones",
        "prenatal","feto"
    ],

    "traumatología": [
        "golpe","fractura","torcedura","esguince","luxacion","luxación",
        "hueso","rodilla","hombro","caida","caída","lesion","lesión"
    ],

    "dermatología": [
        "piel","mancha","erupcion","erupción","picazon","picazón",
        "acne","acné","dermatitis","roncha"
    ],

    "odontología": [
        "diente","muela","encía","encia","caries","dolor dental",
        "infeccion bucal"
    ],

    "oftalmología": [
        "ojo","ojos","vision","visión","ver borroso","lagrimeo",
        "ardor ocular"
    ],

    "gastroenterología": [
        "estomago","estómago","dolor abdominal","diarrea","vomitos","vómitos",
        "nauseas","náuseas","digestivo","acidez","reflujo"
    ],

    "neurología": [
        "cabeza","migraña","migraña","mareo","mareos","convulsiones",
        "desmayo","hormigueo","neurologico"
    ],

    "neumonología": [
        "respirar","respiracion","respiración","tos","falta de aire",
        "pulmon","pulmón","asma"
    ],

    "nefrología": [
        "riñon","riñón","orina","renal","retencion liquidos","retención líquidos"
    ],

    "endocrinología": [
        "diabetes","tiroides","hormonas","glucosa","insulina"
    ],

    "clínica médica": []  # fallback
}

# =========================
# TRIAGE ESTRICTO
# =========================
def triage(texto):

    t = texto.lower()

    scores = {}

    # calcular puntajes
    for especialidad, palabras in ESPECIALIDADES.items():
        score = 0

        for palabra in palabras:
            if palabra in t:
                score += 1

        scores[especialidad] = score

    # elegir mejor
    especialidad = max(scores, key=scores.get)

    # si todos son 0 → clínica médica
    if scores[especialidad] == 0:
        especialidad = "clínica médica"

    # =========================
    # URGENCIA
    # =========================
    urgencia = "BAJA"

    if any(x in t for x in ["infarto","no puedo respirar","convulsiones","desmayo"]):
        urgencia = "ALTA"
    elif any(x in t for x in ["dolor fuerte","mucho dolor","sangrado"]):
        urgencia = "MEDIA"

    # =========================
    # RECOMENDACIONES (5)
    # =========================
    recomendaciones = [
        "Mantenerse hidratado",
        "Evitar esfuerzos físicos",
        "No automedicarse",
        "Controlar evolución de los síntomas",
        "Consultar con especialista"
    ]

    return {
        "urgencia": urgencia,
        "especialidad": especialidad,
        "recomendaciones": recomendaciones
    }

# =========================
# HORARIOS
# =========================
def generar_slots_dia(fecha):
    dia = fecha.weekday()

    if dia < 5:
        inicio, fin = time(9, 0), time(17, 0)
    else:
        return []

    slots = []
    actual = datetime.combine(fecha, inicio)
    fin_dt = datetime.combine(fecha, fin)

    while actual < fin_dt:
        slots.append(actual.strftime("%d/%m %H:%M"))
        actual += timedelta(minutes=30)

    return slots

def turno_disponible(doctor, fecha):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM turnos WHERE doctor=? AND fecha=?", (doctor, fecha))
    ocupado = c.fetchone()[0]
    conn.close()
    return ocupado == 0

# =========================
# DOCTORES
# =========================
def generar_turnos(especialidad):

    doctores = {
        "cardiología": ["Dr. Ramírez"],
        "ginecología": ["Dra. López"],
        "obstetricia": ["Dra. Fernández"],
        "traumatología": ["Dr. Gómez"],
        "dermatología": ["Dra. Silva"],
        "odontología": ["Dr. Ruiz"],
        "oftalmología": ["Dr. Díaz"],
        "gastroenterología": ["Dr. Pérez"],
        "neurología": ["Dr. Castro"],
        "neumonología": ["Dr. Vega"],
        "nefrología": ["Dr. Suárez"],
        "endocrinología": ["Dr. Méndez"],
        "clínica médica": ["Dr. General"]
    }

    lista = doctores.get(especialidad, ["Dr. General"])

    hoy = datetime.now()
    resultado = []

    for doctor in lista:

        disponibles = []

        for i in range(1, 7):
            fecha = hoy + timedelta(days=i)

            for slot in generar_slots_dia(fecha):
                if turno_disponible(doctor, slot):
                    disponibles.append(slot)

        if disponibles:
            resultado.append({
                "doctor": doctor,
                "turnos": disponibles[:3]
            })

    return resultado

# =========================
# GUARDAR
# =========================
def guardar_turno(data):
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("""
    INSERT INTO turnos (nombre, dni, sintomas, especialidad, doctor, fecha)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (
        data["nombre"],
        data["dni"],
        data["sintomas"],
        data["especialidad"],
        data["doctor"],
        data["fecha"]
    ))

    conn.commit()
    conn.close()
    return True

# =========================
# ROUTES
# =========================
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        user = request.form["user"]
        pwd = request.form["pass"]

        if user in USUARIOS and USUARIOS[user] == pwd:
            session["user"] = user
            return redirect("/calendario")

    return render_template("login.html")

@app.route("/calendario")
def calendario():
    if "user" not in session:
        return redirect("/login")

    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT * FROM turnos")
    turnos = c.fetchall()
    conn.close()

    return render_template("calendario.html", turnos=turnos)

@app.route("/triage", methods=["POST"])
def triage_route():

    texto = request.json.get("texto")
    data = triage(texto)

    if data["urgencia"] == "ALTA":
        return jsonify({
            "alerta": "⚠️ URGENCIA - acudir a guardia",
            "medicos": [],
            "recomendaciones": data["recomendaciones"]
        })

    medicos = generar_turnos(data["especialidad"])

    return jsonify({
        "especialidad": data["especialidad"],
        "medicos": medicos,
        "recomendaciones": data["recomendaciones"]
    })

@app.route("/confirmar", methods=["POST"])
def confirmar():
    guardar_turno(request.json)
    return jsonify({"ok": True})

# =========================
if __name__ == "__main__":
    app.run(debug=True)
