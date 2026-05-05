import os
import sqlite3
import json
from datetime import datetime, timedelta, time
from flask import Flask, render_template, request, jsonify, session, redirect
import google.generativeai as genai
from apscheduler.schedulers.background import BackgroundScheduler

# =========================
# CONFIG
# =========================
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

app = Flask(__name__)
app.secret_key = "clave_secreta"

DB = "turnos.db"

# =========================
# INIT DB
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
        UNIQUE(doctor, fecha)
    )
    """)

    conn.commit()
    conn.close()

init_db()

# =========================
# HORARIOS
# =========================
def generar_slots_dia(fecha):

    dia = fecha.weekday()

    if dia < 5:
        inicio, fin = time(9, 0), time(17, 0)
    elif dia == 5:
        inicio, fin = time(9, 0), time(14, 0)
    else:
        return []

    slots = []
    actual = datetime.combine(fecha, inicio)
    fin_dt = datetime.combine(fecha, fin)

    while actual < fin_dt:
        slots.append(actual.strftime("%d/%m %H:%M"))
        actual += timedelta(minutes=30)

    return slots

# =========================
# DISPONIBILIDAD
# =========================
def turno_disponible(doctor, fecha):

    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM turnos WHERE doctor=? AND fecha=?", (doctor, fecha))
    ocupado = c.fetchone()[0]

    conn.close()

    return ocupado == 0

# =========================
# GENERAR TURNOS
# =========================
def generar_turnos(especialidad):

    doctores = {
        "clínica médica": ["Dr. Juan Pérez", "Dr. Esteban López"],
        "ginecología": ["Dra. María Gómez"],
        "traumatología": ["Dr. Carlos Ruiz"],
        "dermatología": ["Dra. Laura Díaz"],
        "oftalmología": ["Dr. Pablo Torres"],
        "odontología": ["Dr. Martín López"]
    }

    lista = doctores.get(especialidad.lower(), ["Dr. General"])

    hoy = datetime.now()
    resultado = []

    for doctor in lista:

        disponibles = []

        for i in range(1, 10):
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
# TRIAGE IA
# =========================
def triage(texto):

    try:
        model = genai.GenerativeModel("gemini-1.5-flash")

        prompt = f"""
Sos un asistente de triage médico.

Clasificá correctamente según síntomas en UNA especialidad:

- clínica médica
- traumatología
- ginecología
- dermatología
- oftalmología
- odontología

IMPORTANTE:
- Síntomas femeninos → ginecología
- Dolor muscular/golpes → traumatología
- Problemas de piel → dermatología
- Ojos → oftalmología
- Dientes → odontología
- General → clínica médica

También:
- urgencia: BAJA, MEDIA o ALTA
- 5 recomendaciones concretas

Respondé SOLO JSON válido:

{{
  "urgencia": "...",
  "especialidad": "...",
  "recomendaciones": ["...", "...", "...", "...", "..."]
}}

Síntomas:
{texto}
"""

        response = model.generate_content(prompt)
        data = json.loads(response.text.strip())

        return data

    except Exception as e:
        print("Error IA:", e)

        return {
            "urgencia": "MEDIA",
            "especialidad": "clínica médica",
            "recomendaciones": [
                "Descansar",
                "Hidratarse",
                "Evitar esfuerzo",
                "Controlar síntomas",
                "Consultar médico"
            ]
        }

# =========================
# GUARDAR TURNO
# =========================
def guardar_turno(data):

    conn = sqlite3.connect(DB)
    c = conn.cursor()

    try:
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
        ok = True

    except:
        ok = False

    conn.close()
    return ok

# =========================
# RECORDATORIOS
# =========================
def recordar_turnos():
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    manana = (datetime.now() + timedelta(days=1)).strftime("%d/%m")

    c.execute("SELECT nombre, fecha FROM turnos WHERE fecha LIKE ?", (f"{manana}%",))

    for t in c.fetchall():
        print("🔔 Recordatorio:", t)

    conn.close()

scheduler = BackgroundScheduler()
scheduler.add_job(recordar_turnos, 'interval', hours=1)
scheduler.start()

# =========================
# LOGIN
# =========================
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":
        user = request.form.get("usuario")
        password = request.form.get("password")

        if user == "admin" and password == "1234":
            session["user"] = user
            return redirect("/calendario")

        return "Credenciales incorrectas"

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
        c.execute("SELECT nombre, doctor, fecha FROM turnos WHERE doctor=?", (doctor,))
    else:
        c.execute("SELECT nombre, doctor, fecha FROM turnos")

    turnos = c.fetchall()

    # obtener lista de médicos únicos
    c.execute("SELECT DISTINCT doctor FROM turnos")
    medicos = [m[0] for m in c.fetchall()]

    conn.close()

    return render_template("calendario.html", turnos=turnos, medicos=medicos, doctor_actual=doctor)

# =========================
# HOME
# =========================
@app.route("/")
def index():
    return render_template("index.html")

# =========================
# TRIAGE ROUTE
# =========================
@app.route("/triage", methods=["POST"])
def triage_route():

    texto = request.json.get("texto")
    data = triage(texto)

    if data["urgencia"] == "ALTA":
        return jsonify({
            "alerta": "⚠️ URGENCIA ALTA - acudir a guardia",
            "especialidad": data["especialidad"],
            "recomendaciones": data["recomendaciones"],
            "medicos": []
        })

    medicos = generar_turnos(data["especialidad"])

    return jsonify({
        "especialidad": data["especialidad"],
        "medicos": medicos,
        "recomendaciones": data["recomendaciones"]
    })

# =========================
# CONFIRMAR
# =========================
@app.route("/confirmar", methods=["POST"])
def confirmar():
    ok = guardar_turno(request.json)
    return jsonify({"ok": ok})

# =========================
# RUN
# =========================
if __name__ == "__main__":
    app.run()
