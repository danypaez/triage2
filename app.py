import os
import sqlite3
import json
from datetime import datetime, timedelta, time
from flask import Flask, render_template, request, jsonify, session, redirect
from werkzeug.security import generate_password_hash, check_password_hash

# =========================
# CONFIG
# =========================
app = Flask(__name__)
app.secret_key = "super_secret_key_123"

DB = "turnos.db"

# =========================
# DB INIT
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
# TRIAGE (IA + FALLBACK PRO)
# =========================
def triage(texto):

    texto_lower = texto.lower()

    # =========================
    # FALLBACK INTELIGENTE (MUY COMPLETO)
    # =========================
    def fallback():
        t = texto_lower

        # 🔴 URGENCIAS
        if any(x in t for x in ["infarto", "no puedo respirar", "dolor pecho fuerte", "convulsión"]):
            return {
                "urgencia": "ALTA",
                "especialidad": "cardiología",
                "recomendaciones": [
                    "Acudir inmediatamente a una guardia",
                    "No realizar esfuerzos",
                    "Llamar a emergencias",
                    "Permanecer acompañado",
                    "Mantener calma"
                ]
            }

        # ❤️ CARDIOLOGÍA
        if any(x in t for x in ["presión alta", "palpitaciones", "dolor pecho leve"]):
            return {
                "urgencia": "MEDIA",
                "especialidad": "cardiología",
                "recomendaciones": [
                    "Evitar esfuerzo físico",
                    "Reducir consumo de sal",
                    "Controlar presión",
                    "No fumar",
                    "Consultar cardiólogo"
                ]
            }

        # 🤰 GINECOLOGÍA / OBSTETRICIA
        if any(x in t for x in ["embarazo", "flujo", "dolor ovárico", "menstruación", "sangrado vaginal"]):
            return {
                "urgencia": "MEDIA",
                "especialidad": "ginecología",
                "recomendaciones": [
                    "Evitar relaciones sexuales",
                    "Controlar sangrado",
                    "No automedicarse",
                    "Usar protección higiénica",
                    "Consultar especialista"
                ]
            }

        # 🦴 TRAUMATOLOGÍA
        if any(x in t for x in ["golpe", "fractura", "esguince", "dolor rodilla", "dolor muscular"]):
            return {
                "urgencia": "MEDIA",
                "especialidad": "traumatología",
                "recomendaciones": [
                    "Reposo",
                    "Aplicar hielo",
                    "Inmovilizar zona",
                    "Evitar esfuerzo",
                    "Elevar miembro afectado"
                ]
            }

        # 🧴 DERMATOLOGÍA
        if any(x in t for x in ["piel", "manchas", "erupción", "sarpullido", "picazón"]):
            return {
                "urgencia": "BAJA",
                "especialidad": "dermatología",
                "recomendaciones": [
                    "No rascarse",
                    "Evitar sol",
                    "Mantener higiene",
                    "Usar crema neutra",
                    "Consultar dermatólogo"
                ]
            }

        # 👁️ OFTALMOLOGÍA
        if any(x in t for x in ["visión", "ojo", "lagrimeo", "ardor ocular"]):
            return {
                "urgencia": "MEDIA",
                "especialidad": "oftalmología",
                "recomendaciones": [
                    "Evitar pantallas",
                    "No frotar ojos",
                    "Usar lágrimas artificiales",
                    "Descansar vista",
                    "Consultar oftalmólogo"
                ]
            }

        # 🦷 ODONTOLOGÍA
        if any(x in t for x in ["muela", "diente", "encía", "dolor dental"]):
            return {
                "urgencia": "MEDIA",
                "especialidad": "odontología",
                "recomendaciones": [
                    "Evitar alimentos duros",
                    "Mantener higiene bucal",
                    "No automedicarse",
                    "Usar enjuague",
                    "Consultar odontólogo"
                ]
            }

        # 🍔 GASTROENTEROLOGÍA
        if any(x in t for x in ["estómago", "náuseas", "vómitos", "diarrea"]):
            return {
                "urgencia": "MEDIA",
                "especialidad": "gastroenterología",
                "recomendaciones": [
                    "Dieta liviana",
                    "Hidratación constante",
                    "Evitar grasas",
                    "Reposo",
                    "Consultar gastroenterólogo"
                ]
            }

        # 🧠 NEUROLOGÍA
        if any(x in t for x in ["mareos", "desmayo", "dolor cabeza fuerte", "migraña"]):
            return {
                "urgencia": "MEDIA",
                "especialidad": "neurología",
                "recomendaciones": [
                    "Reposo en lugar oscuro",
                    "Evitar ruido",
                    "Hidratarse",
                    "No usar pantallas",
                    "Consultar neurólogo"
                ]
            }

        # 🧍 CLÍNICA GENERAL
        return {
            "urgencia": "BAJA",
            "especialidad": "clínica médica",
            "recomendaciones": [
                "Descansar",
                "Hidratarse",
                "Alimentación liviana",
                "Controlar síntomas",
                "Consultar médico"
            ]
        }

    # =========================
    # INTENTO IA (SIN BLOQUEAR)
    # =========================
    try:
        import google.generativeai as genai

        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            print("⚠️ No hay API KEY, usando fallback")
            return fallback()

        genai.configure(api_key=api_key)

        model = genai.GenerativeModel("gemini-1.5-flash")

        prompt = f"""
Clasificá síntomas médicos en especialidad correcta.

ES OBLIGATORIO:
- Elegir SOLO UNA especialidad
- NO usar siempre clínica médica
- Analizar síntomas con precisión

Especialidades:
cardiología, neurología, ginecología, obstetricia, traumatología,
dermatología, oftalmología, odontología, gastroenterología,
nefrología, urología, endocrinología, pediatría, clínica médica

Urgencia: BAJA, MEDIA, ALTA

Dar EXACTAMENTE 5 recomendaciones.

Responder SOLO JSON:

{{
 "urgencia": "",
 "especialidad": "",
 "recomendaciones": []
}}

Síntomas:
{texto}
"""

        response = model.generate_content(prompt)

        raw = response.text.strip()

        data = json.loads(raw)

        # validación mínima
        if "especialidad" not in data:
            return fallback()

        return data

    except Exception as e:
        print("⚠️ ERROR IA:", e)
        return fallback()

# =========================
# TURNOS
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

# =========================
# ROUTES
# =========================
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/triage", methods=["POST"])
def triage_route():

    texto = request.json.get("texto")

    print("📥 Síntomas:", texto)

    data = triage(texto)

    print("📤 Resultado:", data)

    return jsonify(data)

@app.route("/confirmar", methods=["POST"])
def confirmar():
    guardar_turno(request.json)
    return jsonify({"ok": True})

# =========================
# RUN
# =========================
if __name__ == "__main__":
    app.run(debug=True)
