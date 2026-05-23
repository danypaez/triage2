from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from gtts import gTTS

import uuid
import os

from philosopher_ai import responder

# =========================================================
# APP
# =========================================================
app = Flask(
    __name__,
    static_folder="static",
    template_folder="templates"
)

CORS(app)

# =========================================================
# HOME
# =========================================================
@app.route("/")
def home():

    return render_template("index.html")

# =========================================================
# CHAT IA
# =========================================================
@app.route("/chat", methods=["POST"])
def chat():

    try:

        data = request.get_json(force=True)

        nombre = data.get("nombre", "")
        mensaje = data.get("mensaje", "")

        print("===================================")
        print("NUEVA CONSULTA")
        print("===================================")
        print("NOMBRE:", nombre)
        print("MENSAJE:", mensaje)

        if not mensaje:

            return jsonify({
                "response":
                "Compartime aquello que sentís en este momento."
            })

        respuesta = responder(
            nombre=nombre,
            mensaje=mensaje
        )

        print("RESPUESTA IA:", respuesta)

        return jsonify({
            "response": respuesta
        })

    except Exception as e:

        print("===================================")
        print("ERROR CHAT")
        print("===================================")
        print(str(e))

        return jsonify({
            "response":
            "En este momento no logro conectar con la reflexión universal."
        })

# =========================================================
# VOZ
# =========================================================
@app.route("/voz", methods=["POST"])
def voz():

    try:

        data = request.get_json(force=True)

        texto = data.get("texto", "")

        if not texto:

            return jsonify({
                "audio": ""
            })

        os.makedirs("static/audio", exist_ok=True)

        filename = f"audio_{uuid.uuid4().hex}.mp3"

        filepath = os.path.join(
            "static",
            "audio",
            filename
        )

        tts = gTTS(
            text=texto,
            lang="es"
        )

        tts.save(filepath)

        return jsonify({
            "audio": f"/static/audio/{filename}"
        })

    except Exception as e:

        print("===================================")
        print("ERROR VOZ")
        print("===================================")
        print(str(e))

        return jsonify({
            "audio": ""
        })

# =========================================================
# MAIN
# =========================================================
if __name__ == "__main__":

    app.run(
        debug=True,
        host="0.0.0.0",
        port=5000
    )
