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
Sos un sistema de TRIAGE MÉDICO.

Tu tarea es CLASIFICAR los síntomas en UNA sola especialidad médica.

⚠️ IMPORTANTE:
- NO usar "clínica médica" si hay una especialidad más específica
- SOLO usar clínica médica si es algo general o ambiguo

ESPECIALIDADES:

- clínica médica → fiebre, malestar general, gripe, cansancio, síntomas difusos
- traumatología → golpes, caídas, dolor muscular, huesos, articulaciones
- ginecología → flujo vaginal, dolor pélvico, menstruación, embarazo, sangrado vaginal, infecciones íntimas
- dermatología → manchas, erupciones, picazón, acné, problemas en piel
- oftalmología → visión borrosa, dolor ocular, irritación en ojos
- odontología → dolor de muelas, encías, infecciones dentales

URGENCIA:
- ALTA → riesgo inmediato (dolor intenso, sangrado fuerte, dificultad respiratoria, desmayo)
- MEDIA → requiere consulta pronta
- BAJA → leve o controlable

⚠️ REGLAS:
- Elegir SIEMPRE la especialidad MÁS específica posible
- NO repetir especialidades incorrectas
- NO inventar texto fuera del JSON

DEVOLVER SOLO JSON:

{{
  "urgencia": "BAJA | MEDIA | ALTA",
  "especialidad": "...",
  "recomendaciones": [
    "...",
    "...",
    "...",
    "...",
    "..."
  ]
}}

RECOMENDACIONES:
- Deben ser prácticas, claras y seguras
- Máximo 5
- No repetir
- No cosas obvias genéricas

Síntomas:
{texto}
"""

        response = genai.GenerativeModel("gemini-1.5-flash").generate_content(prompt)

        raw = response.text.strip()

        # Limpieza por si viene con ```json
        raw = raw.replace("```json", "").replace("```", "").strip()

        data = json.loads(raw)

        return data

    except Exception as e:
        print("⚠️ Error IA, usando fallback:", e)

        # =========================
        # FALLBACK MEJORADO
        # =========================
        t = texto.lower()

        # 🚨 URGENCIAS
        if "no puedo respirar" in t or "dolor en el pecho" in t:
            return {
                "urgencia": "ALTA",
                "especialidad": "clínica médica",
                "recomendaciones": [
                    "Acudir inmediatamente a una guardia médica",
                    "No quedarse solo",
                    "Evitar cualquier esfuerzo físico",
                    "Mantenerse sentado o semi incorporado",
                    "Llamar a emergencias"
                ]
            }

        # 👩 GINECOLOGÍA
        if any(x in t for x in ["flujo", "vaginal", "menstru", "embarazo", "ovario", "útero", "pélvico"]):
            return {
                "urgencia": "MEDIA",
                "especialidad": "ginecología",
                "recomendaciones": [
                    "Evitar relaciones sexuales hasta evaluación médica",
                    "Mantener higiene íntima adecuada",
                    "No automedicarse",
                    "Registrar síntomas y duración",
                    "Consultar con especialista lo antes posible"
                ]
            }

        # 🦴 TRAUMATOLOGÍA
        if any(x in t for x in ["golpe", "caída", "dolor muscular", "hueso", "torcedura"]):
            return {
                "urgencia": "MEDIA",
                "especialidad": "traumatología",
                "recomendaciones": [
                    "Aplicar frío en la zona afectada",
                    "Evitar movimientos bruscos",
                    "Mantener reposo",
                    "Elevar la zona si hay inflamación",
                    "Consultar si el dolor persiste"
                ]
            }

        # 🧴 DERMATOLOGÍA
        if any(x in t for x in ["piel", "mancha", "sarpullido", "picazón"]):
            return {
                "urgencia": "MEDIA",
                "especialidad": "dermatología",
                "recomendaciones": [
                    "Evitar exposición al sol",
                    "No rascar la zona afectada",
                    "Mantener la piel limpia y seca",
                    "Usar ropa suelta",
                    "Consultar si empeora"
                ]
            }

        # 👁 OFTALMOLOGÍA
        if any(x in t for x in ["ojo", "visión", "lagrimeo", "ardor ocular"]):
            return {
                "urgencia": "MEDIA",
                "especialidad": "oftalmología",
                "recomendaciones": [
                    "Evitar frotarse los ojos",
                    "Descansar la vista",
                    "Evitar pantallas",
                    "Usar lágrimas artificiales si es necesario",
                    "Consultar especialista"
                ]
            }

        # 🦷 ODONTOLOGÍA
        if any(x in t for x in ["muela", "diente", "encía"]):
            return {
                "urgencia": "MEDIA",
                "especialidad": "odontología",
                "recomendaciones": [
                    "Evitar alimentos muy fríos o calientes",
                    "Mantener higiene bucal",
                    "No masticar del lado afectado",
                    "Usar analgésico si es necesario",
                    "Consultar odontólogo"
                ]
            }

        # 🏥 DEFAULT
        return {
            "urgencia": "BAJA",
            "especialidad": "clínica médica",
            "recomendaciones": [
                "Descansar adecuadamente",
                "Mantenerse hidratado",
                "Controlar evolución de síntomas",
                "Evitar automedicación",
                "Consultar si no mejora"
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
