import os
import sqlite3
import json
from datetime import datetime, timedelta, time
from flask import Flask, render_template, request, jsonify, session
from dotenv import load_dotenv
from google import genai
from google.genai import types
from apscheduler.schedulers.background import BackgroundScheduler

load_dotenv()

API_KEY = os.getenv("API_KEY_GEMINI")
MODEL = os.getenv("MODEL_GEMINI", "models/gemini-1.5-flash")

client = genai.Client(api_key=API_KEY)

app = Flask(__name__)
app.secret_key = "clave_secreta_super_segura"

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
        "clínica médica": ["Dr. Juan Pérez", "Dr. Esteban López"]
    }

    lista = doctores.get(especialidad.lower(), ["Dr. General"])

    hoy = datetime.now()
    resultado = []

    for doctor in lista[:2]:

        disponibles = []

        for i in range(1, 10):
            fecha = hoy + timedelta(days=i)

            for slot in generar_slots_dia(fecha):
                if turno_disponible(doctor, slot):
                    disponibles.append(slot)

        if disponibles:
            resultado.append({
                "doctor": doctor,
                "turnos": disponibles[:2]
            })

    return resultado

# =========================
# TRIAGE IA
# =========================
def triage(texto):

    prompt = f"""
Eres un asistente de triage médico.

Debes clasificar los síntomas en UNA especialidad médica adecuada.

Especialidades posibles:
- clínica médica
- traumatología
- ginecología
- dermatología
- oftalmología
- odontología

Reglas:
- Dolor muscular, golpes → traumatología
- Problemas de piel → dermatología
- Problemas visuales → oftalmología
- Dolor dental → odontología
- Síntomas generales → clínica médica
- Temas femeninos → ginecología

Devuelve SOLO JSON válido:

{{
  "urgencia": "BAJA / MEDIA / ALTA",
  "especialidad": "...",
  "recomendaciones": ["..."]
}}

IMPORTANTE:
- NO inventar texto fuera del JSON
- Máximo 3 recomendaciones claras y útiles

Síntomas:
{texto}
"""

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(temperature=0.2)
    )

    return response.text

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

@app.route("/triage", methods=["POST"])
def triage_route():

    texto = request.json.get("texto")

    raw = triage(texto)

    try:
        data = json.loads(raw)
    except:
        data = {
            "urgencia": "MEDIA",
            "especialidad": "clínica médica",
            "recomendaciones": ["Reposo adecuado", "Mantenerse hidratado", "Evitar esfuerzos"]
        }

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

@app.route("/confirmar", methods=["POST"])
def confirmar():
    ok = guardar_turno(request.json)
    return jsonify({"ok": ok})

if __name__ == "__main__":
    app.run(debug=True)