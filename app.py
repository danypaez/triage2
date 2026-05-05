import os
import sqlite3
import json
from datetime import datetime, timedelta, time
from functools import wraps

from flask import Flask, render_template, request, jsonify, session, redirect
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler

# =========================
# CONFIG
# =========================
load_dotenv()

app = Flask(__name__)
app.secret_key = "clave_secreta_super_segura"

DB = "turnos.db"

# =========================
# USUARIOS
# =========================
USERS = {
    "admin": "1234"
}

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user" not in session:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated

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
        "oftalmología": ["Dr. Andrés Vega"],
        "odontología": ["Dr. Martín Silva"]
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
        import google.generativeai as genai

        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

        prompt = f"""
Sos un sistema de TRIAGE MÉDICO.

Clasificá los síntomas en UNA especialidad:

- clínica médica
- traumatología
- ginecología
- dermatología
- oftalmología
- odontología

REGLAS:
- Usar la especialidad MÁS específica posible
- NO usar clínica médica si hay otra opción clara

URGENCIA:
BAJA, MEDIA o ALTA

Devolver SOLO JSON:

{{
  "urgencia": "...",
  "especialidad": "...",
  "recomendaciones": ["...", "...", "...", "...", "..."]
}}

Síntomas:
{texto}
"""

        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)

        raw = response.text.strip()
        raw = raw.replace("```json", "").replace("```", "").strip()

        return json.loads(raw)

    except Exception as e:
        print("⚠️ Error IA:", e)

        t = texto.lower()

        if any(x in t for x in ["flujo", "vaginal", "menstru", "embarazo", "pélvico"]):
            return {
                "urgencia": "MEDIA",
                "especialidad": "ginecología",
                "recomendaciones": [
                    "Evitar relaciones sexuales",
                    "Mantener higiene íntima",
                    "No automedicarse",
                    "Registrar síntomas",
                    "Consultar especialista"
                ]
            }

        if any(x in t for x in ["golpe", "caída", "muscular"]):
            return {
                "urgencia": "MEDIA",
                "especialidad": "traumatología",
                "recomendaciones": [
                    "Aplicar frío",
                    "Reposo",
                    "Evitar esfuerzo",
                    "Elevar zona",
                    "Consultar si persiste"
                ]
            }

        return {
            "urgencia": "BAJA",
            "especialidad": "clínica médica",
            "recomendaciones": [
                "Descansar",
                "Hidratarse",
                "Controlar síntomas",
                "Evitar automedicación",
                "Consultar si empeora"
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
# ROUTES
# =========================
@app.route("/")
def index():
    return render_template("index.html")

# LOGIN
@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/login", methods=["POST"])
def login_post():
    user = request.form.get("user")
    password = request.form.get("password")

    if USERS.get(user) == password:
        session["user"] = user
        return redirect("/calendario")

    return render_template("login.html", error="Credenciales incorrectas")

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/login")

# CALENDARIO
@app.route("/calendario")
@login_required
def calendario():

    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("SELECT nombre, doctor, fecha FROM turnos ORDER BY fecha ASC")
    turnos = c.fetchall()

    conn.close()

    return render_template("calendario.html", turnos=turnos)

# TRIAGE
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

# CONFIRMAR
@app.route("/confirmar", methods=["POST"])
def confirmar():
    ok = guardar_turno(request.json)
    return jsonify({"ok": ok})

# =========================
# RUN LOCAL
# =========================
if __name__ == "__main__":
    app.run(debug=True)
