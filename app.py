import os
import sqlite3
import json
from datetime import datetime, timedelta, time
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

def turno_disponible(doctor, fecha):
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM turnos WHERE doctor=? AND fecha=?", (doctor, fecha))
    ocupado = c.fetchone()[0]

    conn.close()
    return ocupado == 0

# =========================
# TURNOS
# =========================
def generar_turnos(especialidad):

    doctores = {
        "cardiología": ["Dr. Ramírez"],
        "ginecología": ["Dra. López"],
        "obstetricia": ["Dra. Fernández"],
        "traumatología": ["Dr. Gómez"],
        "dermatología": ["Dra. Silva"],
        "odontología": ["Dr. Ruiz"],
        "oftalmología": ["Dr. Díaz"],
        "gastroenterología": ["Dr. Pérez"],
        "neurología": ["Dr. Castro"],
        "clínica médica": ["Dr. General"]
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
# TRIAGE INTELIGENTE
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
# GUARDAR
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
            "alerta": "⚠️ URGENCIA ALTA - ir a guardia",
            "especialidad": data["especialidad"],
            "recomendaciones": data["recomendaciones"],
            "medicos": []
        })

    medicos = generar_turnos(data["especialidad"])

    return jsonify({
        "especialidad": data["especialidad"],
        "medicos": medicos if medicos else [],
        "recomendaciones": data["recomendaciones"]
    })

@app.route("/confirmar", methods=["POST"])
def confirmar():
    ok = guardar_turno(request.json)
    return jsonify({"ok": ok})

if __name__ == "__main__":
    app.run(debug=True)
