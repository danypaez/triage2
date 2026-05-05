import os
import sqlite3
import json
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)
app.secret_key = "clave_secreta"

DB = "turnos.db"

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
# TRIAGE
# =========================
def triage(texto):

    t = texto.lower()

    # 🔴 URGENCIAS
    if any(x in t for x in ["infarto", "no puedo respirar", "dolor pecho fuerte"]):
        return {
            "urgencia": "ALTA",
            "especialidad": "cardiología",
            "recomendaciones": [
                "Ir a guardia urgente",
                "No hacer esfuerzo",
                "Llamar emergencias",
                "No quedarse solo",
                "Mantener calma"
            ]
        }

    # ❤️ CARDIO
    if any(x in t for x in ["presión alta", "palpitaciones"]):
        return {
            "urgencia": "MEDIA",
            "especialidad": "cardiología",
            "recomendaciones": [
                "Reducir sal",
                "Controlar presión",
                "Evitar esfuerzo",
                "No fumar",
                "Consultar cardiólogo"
            ]
        }

    # 🤰 GINECOLOGÍA
    if any(x in t for x in ["flujo", "menstruación", "sangrado vaginal", "dolor ovárico"]):
        return {
            "urgencia": "MEDIA",
            "especialidad": "ginecología",
            "recomendaciones": [
                "Evitar relaciones",
                "Controlar sangrado",
                "No automedicarse",
                "Higiene adecuada",
                "Consultar ginecólogo"
            ]
        }

    # 🦴 TRAUMA
    if any(x in t for x in ["golpe", "fractura", "esguince", "dolor muscular"]):
        return {
            "urgencia": "MEDIA",
            "especialidad": "traumatología",
            "recomendaciones": [
                "Reposo",
                "Hielo",
                "Inmovilizar",
                "Elevar zona",
                "Evitar esfuerzo"
            ]
        }

    # 🧴 PIEL
    if any(x in t for x in ["piel", "mancha", "sarpullido"]):
        return {
            "urgencia": "BAJA",
            "especialidad": "dermatología",
            "recomendaciones": [
                "No rascarse",
                "Evitar sol",
                "Higiene",
                "Usar crema neutra",
                "Consultar dermatólogo"
            ]
        }

    # 👁️ OJOS
    if any(x in t for x in ["ojo", "visión", "ardor ocular"]):
        return {
            "urgencia": "MEDIA",
            "especialidad": "oftalmología",
            "recomendaciones": [
                "No frotar",
                "Evitar pantallas",
                "Usar lágrimas",
                "Descansar vista",
                "Consultar oftalmólogo"
            ]
        }

    # 🦷 DIENTES
    if any(x in t for x in ["diente", "muela", "encía"]):
        return {
            "urgencia": "MEDIA",
            "especialidad": "odontología",
            "recomendaciones": [
                "Higiene bucal",
                "Evitar frío/calor",
                "No automedicarse",
                "Enjuague",
                "Consultar odontólogo"
            ]
        }

    # 🍔 GASTRO
    if any(x in t for x in ["estómago", "náuseas", "vómitos", "diarrea"]):
        return {
            "urgencia": "MEDIA",
            "especialidad": "gastroenterología",
            "recomendaciones": [
                "Dieta liviana",
                "Hidratación",
                "Evitar grasas",
                "Reposo",
                "Consultar gastro"
            ]
        }

    # 🧠 NEURO
    if any(x in t for x in ["mareo", "migraña", "dolor cabeza"]):
        return {
            "urgencia": "MEDIA",
            "especialidad": "neurología",
            "recomendaciones": [
                "Reposo",
                "Oscuridad",
                "Evitar ruido",
                "Hidratación",
                "Consultar neurólogo"
            ]
        }

    return {
        "urgencia": "BAJA",
        "especialidad": "clínica médica",
        "recomendaciones": [
            "Descansar",
            "Hidratarse",
            "Comer liviano",
            "Controlar síntomas",
            "Consultar médico"
        ]
    }

# =========================
# ROUTES
# =========================
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/triage", methods=["POST"])
def triage_route():
    data = request.json
    texto = data.get("texto", "")
    resultado = triage(texto)
    return jsonify(resultado)

# =========================
# RUN
# =========================
if __name__ == "__main__":
    app.run(debug=True)
