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
        import google.generativeai as genai
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

        model = genai.GenerativeModel("gemini-1.5-flash")

        prompt = f"""
Sos un sistema de TRIAGE MÉDICO CLÍNICO ESTRICTO.

⚠️ OBJETIVO:
Clasificar los síntomas en UNA sola especialidad médica correcta, evitando usar "clínica médica" salvo que sea realmente general.

========================
ESPECIALIDADES Y CRITERIOS
========================

- cardiología:
  dolor en el pecho, palpitaciones, presión alta, arritmias, falta de aire cardíaca

- neumonología:
  tos, dificultad respiratoria, asma, bronquitis, neumonía

- gastroenterología:
  dolor abdominal, diarrea, vómitos, acidez, gastritis, hígado, colon

- nefrología:
  problemas renales, dolor lumbar renal, orina anormal, retención líquidos

- urología:
  problemas urinarios, próstata, infecciones urinarias, dolor al orinar

- ginecología:
  dolor pélvico, flujo vaginal, menstruación, infecciones ginecológicas

- obstetricia:
  embarazo, controles prenatales, contracciones, sangrado en embarazo

- traumatología:
  golpes, fracturas, esguinces, dolor muscular, articulaciones

- neurología:
  mareos, convulsiones, pérdida de memoria, dolores de cabeza severos

- dermatología:
  manchas, sarpullido, picazón, acné, lesiones en piel

- oftalmología:
  visión borrosa, dolor ocular, irritación ojos

- otorrinolaringología:
  dolor de oído, garganta, nariz, sinusitis

- odontología:
  dolor dental, encías, infecciones bucales

- endocrinología:
  diabetes, tiroides, hormonas, obesidad

- psiquiatría:
  ansiedad severa, depresión, ataques de pánico

- clínica médica:
  SOLO si los síntomas son generales, inespecíficos o múltiples sistemas

========================
REGLAS ESTRICTAS
========================

1. ELEGIR SOLO UNA especialidad.
2. NO usar clínica médica si hay otra opción clara.
3. Priorizar el síntoma principal.
4. Si hay síntomas femeninos → ginecología u obstetricia.
5. Si hay múltiples sistemas, elegir el predominante.

========================
URGENCIA
========================

ALTA:
- dolor de pecho intenso
- dificultad para respirar
- pérdida de conocimiento
- sangrado importante
- convulsiones

MEDIA:
- dolor moderado
- fiebre persistente
- síntomas que limitan actividad

BAJA:
- síntomas leves o iniciales

========================
RESPUESTA
========================

Devolver SOLO JSON válido:

{{
  "urgencia": "BAJA | MEDIA | ALTA",
  "especialidad": "...",
  "recomendaciones": ["...", "...", "...", "...", "..."]
}}

Las recomendaciones deben ser:
- claras
- concretas
- seguras
- máximo 5

========================
SÍNTOMAS DEL PACIENTE
========================

{texto}
"""

        response = model.generate_content(prompt)

        raw = response.text.strip()

        data = json.loads(raw)

        # seguridad: asegurar 5 recomendaciones
        if len(data.get("recomendaciones", [])) < 5:
            data["recomendaciones"] += [
                "Mantener reposo",
                "Hidratarse adecuadamente",
                "Evitar automedicación",
                "Consultar si empeora",
                "Control médico"
            ]
            data["recomendaciones"] = data["recomendaciones"][:5]

        return data

    except Exception as e:
        print("⚠️ Error IA:", e)

        # =========================
        # FALLBACK INTELIGENTE
        # =========================
        t = texto.lower()

        if "pecho" in t:
            esp = "cardiología"
        elif "respirar" in t or "tos" in t:
            esp = "neumonología"
        elif "panza" in t or "abdomen" in t:
            esp = "gastroenterología"
        elif "riñon" in t or "orina" in t:
            esp = "nefrología"
        elif "embarazo" in t:
            esp = "obstetricia"
        elif "menstru" in t or "flujo" in t:
            esp = "ginecología"
        elif "golpe" in t or "muscular" in t:
            esp = "traumatología"
        elif "piel" in t:
            esp = "dermatología"
        elif "ojo" in t:
            esp = "oftalmología"
        elif "diente" in t:
            esp = "odontología"
        else:
            esp = "clínica médica"

        return {
            "urgencia": "MEDIA",
            "especialidad": esp,
            "recomendaciones": [
                "Reposo",
                "Hidratación",
                "Evitar esfuerzo",
                "Controlar evolución",
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
# EDITAR TURNO
# =========================
@app.route("/editar_turno", methods=["POST"])
def editar_turno():
    data = request.json

    conn = sqlite3.connect(DB)
    c = conn.cursor()

    try:
        c.execute("""
        UPDATE turnos
        SET nombre=?, dni=?, sintomas=?, especialidad=?, doctor=?, fecha=?
        WHERE id=?
        """, (
            data["nombre"],
            data["dni"],
            data["sintomas"],
            data["especialidad"],
            data["doctor"],
            data["fecha"],
            data["id"]
        ))

        conn.commit()
        ok = True
    except Exception as e:
        print("Error editando:", e)
        ok = False

    conn.close()
    return jsonify({"ok": ok})


# =========================
# BORRAR TURNO
# =========================
@app.route("/borrar_turno", methods=["POST"])
def borrar_turno():
    data = request.json

    conn = sqlite3.connect(DB)
    c = conn.cursor()

    try:
        c.execute("DELETE FROM turnos WHERE id=?", (data["id"],))
        conn.commit()
        ok = True
    except Exception as e:
        print("Error borrando:", e)
        ok = False

    conn.close()
    return jsonify({"ok": ok})



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
        c.execute("""
        SELECT nombre, dni, sintomas, doctor, fecha 
        FROM turnos 
        WHERE doctor=?
        """, (doctor,))
    else:
        c.execute("""
        SELECT nombre, dni, sintomas, doctor, fecha 
        FROM turnos
        """)

    turnos = c.fetchall()

    c.execute("SELECT DISTINCT doctor FROM turnos")
    medicos = [m[0] for m in c.fetchall()]

    conn.close()

    return render_template(
        "calendario.html",
        turnos=turnos,
        medicos=medicos,
        doctor_actual=doctor
    )
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
