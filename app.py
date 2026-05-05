import os
import sqlite3
import json
from datetime import datetime, timedelta, time
from flask import Flask, render_template, request, jsonify, session, redirect

# IA
try:
    import google.generativeai as genai
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    IA_ACTIVA = True
except:
    IA_ACTIVA = False

app = Flask(__name__)
app.secret_key = "super_secret_key"

DB = "turnos.db"

# =========================
# BASE DE DATOS
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

    conn.commit()
    conn.close()

init_db()

 # =========================
# LOGIN SIMPLE Y ROBUSTO
# =========================

USUARIOS = {
    "juan": {
        "password": "1234",
        "nombre": "Dr. Juan Pérez"
    },
    "lopez": {
        "password": "1234",
        "nombre": "Dr. Esteban López"
    },
    "cardio": {
        "password": "1234",
        "nombre": "Dr. Cardiólogo"
    },
    "gine": {
        "password": "1234",
        "nombre": "Dra. Ginecóloga"
    }
}

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        usuario = request.form.get("usuario")
        password = request.form.get("password")

        if usuario in USUARIOS:
            if USUARIOS[usuario]["password"] == password:
                session["doctor"] = USUARIOS[usuario]["nombre"]
                session["usuario"] = usuario
                return redirect("/calendario")
            else:
                error = "Contraseña incorrecta"
        else:
            error = "Usuario no existe"

    return render_template("login.html", error=error)

# =========================
# TRIAGE ULTRA COMPLETO
# =========================
def triage(texto):

    texto_lower = texto.lower()

    # =========================
    # IA
    # =========================
    if IA_ACTIVA:
        try:
            prompt = f"""
Sos un médico experto en triage clínico.

Clasificá los síntomas en UNA especialidad EXACTA:

Especialidades:
- clínica médica
- cardiología
- neumonología
- gastroenterología
- nefrología
- neurología
- traumatología
- dermatología
- oftalmología
- otorrinolaringología
- ginecología
- obstetricia
- urología
- endocrinología
- pediatría
- psiquiatría
- odontología

Reglas estrictas:

CARDIOLOGÍA:
dolor en el pecho, palpitaciones, presión en pecho, falta de aire con esfuerzo

NEUMONOLOGÍA:
tos persistente, dificultad respiratoria, asma, bronquitis

GASTRO:
dolor abdominal, diarrea, vómitos, acidez

GINECOLOGÍA:
flujo vaginal, dolor pélvico, menstruación irregular, infecciones

OBSTETRICIA:
embarazo, contracciones, sangrado embarazo

TRAUMATOLOGÍA:
golpes, fracturas, dolor muscular, articulaciones

DERMATOLOGÍA:
manchas, sarpullido, picazón, piel

NEUROLOGÍA:
mareos, convulsiones, pérdida de memoria

OFTALMOLOGÍA:
visión borrosa, dolor ocular

OTORRINO:
dolor oído, garganta, nariz

UROLOGÍA:
dolor al orinar, infecciones urinarias

ENDOCRINO:
diabetes, tiroides

ODONTOLOGÍA:
dolor dental

PSIQUIATRÍA:
ansiedad, depresión

URGENCIA:
ALTA → riesgo de vida
MEDIA → necesita atención
BAJA → leve

Devolver JSON:

{{
"urgencia":"...",
"especialidad":"...",
"recomendaciones":["...","...","...","...","..."]
}}

Síntomas:
{texto}
"""
            response = genai.GenerativeModel("gemini-1.5-flash").generate_content(prompt)
            data = json.loads(response.text)
            return data

        except Exception as e:
            print("Error IA:", e)

    # =========================
    # FALLBACK INTELIGENTE
    # =========================

    t = texto_lower

    # CARDIO
    if any(x in t for x in ["pecho", "palpitaciones", "presión pecho"]):
        return {
            "urgencia": "ALTA",
            "especialidad": "cardiología",
            "recomendaciones": [
                "Ir a guardia urgente",
                "No realizar esfuerzo",
                "Mantenerse acompañado",
                "Controlar respiración",
                "Evitar estrés"
            ]
        }

    # GINE
    if any(x in t for x in ["flujo", "vaginal", "menstruación", "útero"]):
        return {
            "urgencia": "MEDIA",
            "especialidad": "ginecología",
            "recomendaciones": [
                "Evitar relaciones sexuales",
                "Mantener higiene íntima",
                "Observar cambios",
                "No automedicarse",
                "Consultar especialista"
            ]
        }

    # TRAUMA
    if any(x in t for x in ["golpe", "fractura", "torcedura"]):
        return {
            "urgencia": "MEDIA",
            "especialidad": "traumatología",
            "recomendaciones": [
                "Aplicar hielo",
                "Reposo",
                "Inmovilizar zona",
                "Evitar esfuerzo",
                "Consultar médico"
            ]
        }

    # GASTRO
    if any(x in t for x in ["dolor estómago", "diarrea", "vomito"]):
        return {
            "urgencia": "MEDIA",
            "especialidad": "gastroenterología",
            "recomendaciones": [
                "Dieta liviana",
                "Hidratación",
                "Evitar grasas",
                "Controlar síntomas",
                "Consultar médico"
            ]
        }

    # DEFAULT
    return {
        "urgencia": "BAJA",
        "especialidad": "clínica médica",
        "recomendaciones": [
            "Descansar",
            "Hidratarse",
            "Observar evolución",
            "Evitar esfuerzo",
            "Consultar si empeora"
        ]
    }

# =========================
# TURNOS
# =========================
def guardar_turno(data):
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("""
    INSERT INTO turnos (nombre, dni, sintomas, especialidad, doctor, fecha, urgencia)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        data["nombre"],
        data["dni"],
        data["sintomas"],
        data["especialidad"],
        data["doctor"],
        data["fecha"],
        data["urgencia"]
    ))

    conn.commit()
    conn.close()

# =========================
# CALENDARIO
# =========================
@app.route("/calendario")
def calendario():

    if "doctor" not in session:
        return redirect("/login")

    doctor = session["doctor"]

    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("SELECT * FROM turnos WHERE doctor=?", (doctor,))
    turnos = c.fetchall()

    conn.close()

    return render_template("calendario.html", turnos=turnos, doctor=doctor)

# =========================
# API
# =========================
@app.route("/triage", methods=["POST"])
def triage_api():
    texto = request.json.get("texto")
    data = triage(texto)
    return jsonify(data)

@app.route("/confirmar", methods=["POST"])
def confirmar():
    guardar_turno(request.json)
    return jsonify({"ok": True})

@app.route("/eliminar/<int:id>")
def eliminar(id):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("DELETE FROM turnos WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect("/calendario")

@app.route("/editar/<int:id>", methods=["POST"])
def editar(id):
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    nueva_fecha = request.form.get("fecha")

    c.execute("UPDATE turnos SET fecha=? WHERE id=?", (nueva_fecha, id))

    conn.commit()
    conn.close()

    return redirect("/calendario")

# =========================
# HOME
# =========================
@app.route("/")
def home():
    return render_template("index.html")

# =========================
# RUN
# =========================
if __name__ == "__main__":
    app.run(debug=True)
