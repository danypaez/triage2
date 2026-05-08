from flask import Flask, render_template, request, jsonify
from gtts import gTTS
import uuid
import os

# =========================
# IA FILÓSOFO
# =========================
from philosopher_ai import responder

app = Flask(
    __name__,
    static_folder="static",
    template_folder="templates"
)

# =========================
# HOME
# =========================
@app.route("/")
def home():

    return render_template("index.html")

# =========================
# CHAT IA
# =========================
@app.route("/chat", methods=["POST"])
def chat():

    data = request.get_json()

    nombre = data.get("nombre", "")
    mensaje = data.get("mensaje", "")

    print("NOMBRE:", nombre)
    print("MENSAJE:", mensaje)

    if not mensaje:

        return jsonify({
            "response": "Compartime aquello que sentís en este momento."
        })

    try:

        respuesta = responder(nombre, mensaje)

        print("RESPUESTA IA:", respuesta)

        return jsonify({
            "response": respuesta
        })

    except Exception as e:

        print("ERROR CHAT:", e)

        return jsonify({
            "response":
            "En este momento no logro conectar con la reflexión universal."
        })

# =========================
# VOZ
# =========================
@app.route("/voz", methods=["POST"])
def voz():

    data = request.get_json()

    texto = data.get("texto", "")

    if not texto:

        return jsonify({
            "audio": ""
        })

    try:

        os.makedirs("static", exist_ok=True)

        filename = f"static/voz_{uuid.uuid4().hex}.mp3"

        tts = gTTS(text=texto, lang="es")

        tts.save(filename)

        return jsonify({
            "audio": "/" + filename
        })

    except Exception as e:

        print("ERROR VOZ:", e)

        return jsonify({
            "audio": ""
        })

# =========================
# MAIN
# =========================
if __name__ == "__main__":

    app.run(debug=True)