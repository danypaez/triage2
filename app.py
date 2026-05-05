import os
import sqlite3
import json
from datetime import datetime, timedelta, time
from flask import Flask, render_template, request, jsonify, session
from apscheduler.schedulers.background import BackgroundScheduler

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
        "clínica médica": ["Dr. Juan Pérez", "Dr. Esteban López"],
        "dermatología": ["Dr. Juan Pérez"],
        "traumatología": ["Dr. Esteban López"],
        "ginecología": ["Dra. María López"],
        "oftalmología": ["Dr. Carlos Díaz"],
        "odontología": ["Dra. Laura Gómez"]
    }

    lista = doctores.get(especialidad.lower(), ["Dr. Juan Pérez"])

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
                "turnos": disponibles[:2]
            })

    return resultado

# =========================
# TRIAGE (SIN IA EXTERNA)
# =========================
  def triage(texto):

    try:
        import google.generativeai as genai

        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

        prompt = f"""
Sos un asistente médico de triage.

Clasificá los síntomas en UNA especialidad:

- clínica médica
- traumatología
- ginecología
- dermatología
- oftalmología
- odontología

También indicá nivel de urgencia:
BAJA, MEDIA o ALTA

Y agregá hasta 3 recomendaciones simples.

Respondé SOLO JSON válido:

{{
  "urgencia": "...",
  "especialidad": "...",
  "recomendaciones": ["...", "..."]
}}

Síntomas:
{texto}
"""

        response = genai.GenerativeModel("gemini-1.5-flash").generate_content(prompt)

        raw = response.text.strip()

        data = json.loads(raw)

        return data

    except Exception as e:
        print("⚠️ Error IA, usando fallback:", e)

        # =========================
        # FALLBACK LOCAL (seguro)
        # =========================
        t = texto.lower()

        if "pecho" in t or "no puedo respirar" in t:
            return {
                "urgencia": "ALTA",
                "especialidad": "clínica médica",
                "recomendaciones": [
                    "Acudir inmediatamente a una guardia médica",
                    "No quedarse solo",
                    "Evitar esfuerzos"
                ]
            }

        elif "piel" in t:
            return {
                "urgencia": "MEDIA",
                "especialidad": "dermatología",
                "recomendaciones": [
                    "Evitar el sol",
                    "No rascarse",
                    "Mantener higiene"
                ]
            }

        elif "golpe" in t or "dolor muscular" in t:
            return {
                "urgencia": "MEDIA",
                "especialidad": "traumatología",
                "recomendaciones": [
                    "Reposo",
                    "Aplicar frío",
                    "Evitar esfuerzo"
                ]
            }

        else:
            return {
                "urgencia": "BAJA",
                "especialidad": "clínica médica",
                "recomendaciones": [
                    "Descansar",
                    "Hidratarse",
                    "Controlar evolución"
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

@app.route("/confirmar", methods=["POST"])
def confirmar():
    ok = guardar_turno(request.json)
    return jsonify({"ok": ok})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
