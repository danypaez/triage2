import os
import sqlite3
import json
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, session, redirect
from werkzeug.security import generate_password_hash, check_password_hash

# =========================
# IA (opcional)
# =========================
try:
    import google.generativeai as genai
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    IA_ACTIVA = True
except:
    IA_ACTIVA = False

app = Flask(__name__)
app.secret_key = "super_secret_key"
app.permanent_session_lifetime = timedelta(minutes=15)

DB = "turnos.db"

# =========================
# DB
# =========================
def get_db():
    return sqlite3.connect(DB)

def init_db():
    conn = get_db()
    c = conn.cursor()

    # usuarios
    c.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario TEXT UNIQUE,
        password TEXT,
        rol TEXT,
        nombre TEXT
    )
    """)

    # turnos
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

    # admin default
    c.execute("SELECT * FROM usuarios WHERE usuario='admin'")
    if not c.fetchone():
        c.execute("""
        INSERT INTO usuarios (usuario, password, rol, nombre)
        VALUES (?, ?, ?, ?)
        """, (
            "admin",
            generate_password_hash("admin123"),
            "admin",
            "Administrador"
        ))

    conn.commit()
    conn.close()

init_db()

# =========================
# AUTH
# =========================
def login_required():
    return "usuario" in session

def admin_required():
    return session.get("rol") == "admin"

# =========================
# LOGIN
# =========================
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        usuario = request.form.get("usuario")
        password = request.form.get("password")

        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT * FROM usuarios WHERE usuario=?", (usuario,))
        user = c.fetchone()
        conn.close()

        if user and check_password_hash(user[2], password):
            session.permanent = True
            session["usuario"] = user[1]
            session["rol"] = user[3]
            session["nombre"] = user[4]
            return redirect("/calendario")
        else:
            error = "Credenciales incorrectas"

    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# =========================
# TRIAGE ULTRA COMPLETO
# =========================
def triage(texto):

    t = texto.lower()

    # =========================
    # IA
    # =========================
    if IA_ACTIVA:
        try:
            prompt = f"""
Actuás como médico clínico experto en triage hospitalario.

Clasificá los síntomas en UNA especialidad EXACTA:

Especialidades:
- cardiología
- neumonología
- gastroenterología
- neurología
- traumatología
- dermatología
- oftalmología
- otorrinolaringología
- ginecología
- obstetricia
- urología
- endocrinología
- nefrología
- psiquiatría
- pediatría
- infectología
- oncología
- hematología
- reumatología
- clínica médica

Reglas estrictas por síntomas:

CARDIO: pecho, presión, palpitaciones
NEUMO: tos, falta aire
GASTRO: dolor abdominal, vómitos, diarrea
NEURO: mareos, convulsiones
TRAUMA: golpes, fracturas
DERMA: piel, manchas
OFTALMO: visión
OTORRINO: oído, garganta
GINE: flujo, menstruación
OBSTETRICIA: embarazo
UROLOGÍA: orina, ardor
ENDOCRINO: diabetes
NEFRO: riñón
PSIQUIATRÍA: ansiedad
PEDIATRÍA: niños
INFECTO: fiebre infecciosa
ONCO: tumores
HEMATO: sangre
REUMA: articulaciones

Devolver JSON:

{{
"urgencia":"BAJA|MEDIA|ALTA",
"especialidad":"...",
"recomendaciones":["...","...","...","...","..."]
}}

Síntomas:
{texto}
"""
            response = genai.GenerativeModel("gemini-1.5-flash").generate_content(prompt)
            return json.loads(response.text)

        except:
            pass

    # =========================
    # FALLBACK ULTRA DETALLADO
    # =========================

    # CARDIO
    if any(x in t for x in ["pecho", "palpitaciones", "presion pecho", "infarto"]):
        return {
            "urgencia": "ALTA",
            "especialidad": "cardiología",
            "recomendaciones": [
                "Ir a guardia urgente",
                "No hacer esfuerzo",
                "Mantenerse acompañado",
                "Control respiración",
                "Llamar emergencia"
            ]
        }

    # NEUMO
    if any(x in t for x in ["tos", "falta aire", "asma"]):
        return {
            "urgencia": "MEDIA",
            "especialidad": "neumonología",
            "recomendaciones": [
                "Evitar esfuerzo",
                "Ambiente ventilado",
                "Hidratarse",
                "Control respiración",
                "Consultar médico"
            ]
        }

    # GINE
    if any(x in t for x in ["flujo", "vaginal", "menstruacion", "ovario"]):
        return {
            "urgencia": "MEDIA",
            "especialidad": "ginecología",
            "recomendaciones": [
                "Evitar relaciones",
                "Higiene íntima",
                "No automedicarse",
                "Observar síntomas",
                "Consultar ginecólogo"
            ]
        }

    # OBSTETRICIA
    if any(x in t for x in ["embarazo", "contracciones"]):
        return {
            "urgencia": "ALTA",
            "especialidad": "obstetricia",
            "recomendaciones": [
                "Ir a guardia",
                "Reposo",
                "No viajar",
                "Acompañamiento",
                "Control médico urgente"
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
                "Inmovilizar",
                "Evitar esfuerzo",
                "Consultar médico"
            ]
        }

    # GASTRO
    if any(x in t for x in ["dolor abdomen", "diarrea", "vomito"]):
        return {
            "urgencia": "MEDIA",
            "especialidad": "gastroenterología",
            "recomendaciones": [
                "Dieta liviana",
                "Hidratación",
                "Evitar grasas",
                "Control síntomas",
                "Consultar médico"
            ]
        }

    # DERMATO
    if any(x in t for x in ["piel", "manchas", "sarpullido"]):
        return {
            "urgencia": "BAJA",
            "especialidad": "dermatología",
            "recomendaciones": [
                "Evitar sol",
                "No rascar",
                "Higiene",
                "Usar cremas",
                "Consultar dermatólogo"
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
@app.route("/confirmar", methods=["POST"])
def confirmar():
    data = request.json

    conn = get_db()
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

    return jsonify({"ok": True})

# =========================
# CALENDARIO
# =========================
@app.route("/calendario")
def calendario():

    if not login_required():
        return redirect("/login")

    conn = get_db()
    c = conn.cursor()

    if session["rol"] == "admin":
        c.execute("SELECT * FROM turnos")
    else:
        c.execute("SELECT * FROM turnos WHERE doctor=?", (session["nombre"],))

    turnos = c.fetchall()
    conn.close()

    return render_template("calendario.html", turnos=turnos)

# =========================
# ADMIN USUARIOS
# =========================
@app.route("/usuarios")
def usuarios():

    if not admin_required():
        return redirect("/calendario")

    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id, usuario, rol, nombre FROM usuarios")
    lista = c.fetchall()
    conn.close()

    return render_template("usuarios.html", usuarios=lista)

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
