from openai import OpenAI
import os
import re

# =========================================================
# CONFIG OPENROUTER
# =========================================================
API_KEY = os.environ.get("OPENROUTER_API_KEY")

print("===================================")
print("INICIALIZANDO SISTEMA FILOSOFICO")
print("===================================")
print("OPENROUTER_API_KEY:",
      "OK" if API_KEY else "NO ENCONTRADA")
print("===================================")

# =========================================================
# CLIENTE
# =========================================================
client = None

if API_KEY:

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=API_KEY
    )

    print("✅ CLIENTE OPENROUTER INICIALIZADO")

else:

    print("⚠️ NO SE ENCONTRO OPENROUTER_API_KEY")

# =========================================================
# FALLBACK
# =========================================================
def fallback():

    return (
        "En este momento no logro conectar con la reflexión universal. "
        "Intentemos nuevamente en unos instantes."
    )

# =========================================================
# LIMPIAR TEXTO
# =========================================================
def limpiar_texto(texto):

    if not texto:
        return fallback()

    texto = texto.replace("*", "")
    texto = texto.replace("#", "")
    texto = texto.replace("```", "")

    texto = texto.replace("\n", " ")
    texto = texto.replace("\r", " ")

    texto = re.sub(r"\s+", " ", texto)

    texto = texto[:1800]

    return texto.strip()

# =========================================================
# CERRAR RESPUESTA
# =========================================================
def cerrar_respuesta(texto):

    if not texto:
        return fallback()

    texto = texto.strip()

    if texto[-1] in [".", "!", "?", "…"]:
        return texto

    partes = re.split(r'(?<=[.!?])\s+', texto)

    if len(partes) > 1:

        texto = " ".join(partes[:-1]).strip()

        if texto and texto[-1] not in [".", "!", "?"]:
            texto += "."

        return texto

    return texto + "..."

# =========================================================
# PROMPT MASTER
# =========================================================
PROMPT_MASTER = """
Eres el reflejo virtual del pensamiento de la Dra. Ana Jachimowicz.

Tu tono debe ser:
- profundo
- cálido
- reflexivo
- espiritual
- filosófico

No des respuestas clínicas ni psicológicas tradicionales.

Habla sobre:
- conciencia
- unidad
- presencia
- espiritualidad universal
- observación interior
- conexión con el Ser

Nunca seas agresivo ni dogmático.
"""

# =========================================================
# RESPONDER
# =========================================================
def responder(nombre, mensaje):

    print("===================================")
    print("CONSULTANDO OPENROUTER")
    print("===================================")

    if client is None:

        print("⚠️ CLIENTE NO DISPONIBLE")

        return fallback()

    try:

        prompt_usuario = f"""
Nombre:
{nombre}

Consulta:
{mensaje}
"""

        completion = client.chat.completions.create(

            model="openai/gpt-4o-mini",

            messages=[

                {
                    "role": "system",
                    "content": PROMPT_MASTER
                },

                {
                    "role": "user",
                    "content": prompt_usuario
                }

            ],

            temperature=0.8,
            max_tokens=300

        )

        texto = (
            completion
            .choices[0]
            .message
            .content
        )

        texto = limpiar_texto(texto)

        texto = cerrar_respuesta(texto)

        print("===================================")
        print("RESPUESTA FINAL")
        print("===================================")
        print(texto)

        return texto

    except Exception as e:

        print("===================================")
        print("ERROR OPENROUTER")
        print("===================================")
        print(str(e))

        return fallback()
