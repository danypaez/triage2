from openai import OpenAI
from dotenv import load_dotenv
import os

# =========================
# ENV
# =========================
load_dotenv()

API_KEY = os.environ["OPENROUTER_API_KEY"]

print("OPENROUTER:", API_KEY)

# =========================
# CLIENT
# =========================
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=API_KEY
)

# =========================
# RESPUESTA LOCAL SOLO EMERGENCIA
# =========================
def fallback():

    return (
        "En este momento la reflexión profunda no está disponible. "
        "Intentemos nuevamente en unos instantes."
    )

# =========================
# RESPONDER
# =========================
def responder(nombre, mensaje):

    prompt = f"""
Sos un filósofo contemplativo especializado en Espiritualidad Universal y pensamiento no dualista.

IMPORTANTE:
- Respondé como un ser humano sabio.
- Nunca digas que sos IA.
- Nunca uses listas.
- Nunca uses markdown.
- No respondas genéricamente.
- Reflexioná específicamente sobre lo que la persona expresa.
- Máximo 1 párrafos. De un máximo de 6 líneas.
- Sé cálido, humano, profundo y espiritual.
- Que termine con mensaje de aliento o esperanza.
-Lenguaje argentino, cercano, coloquial, con metáforas y poesía.


Nombre:
{nombre}

Consulta:
{mensaje}
"""

    try:

        # =========================
        # OPENROUTER REAL
        # =========================
        completion = client.chat.completions.create(

            model="openai/gpt-3.5-turbo",

            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],

            temperature=0.9,
            max_tokens=300

        )

        texto = completion.choices[0].message.content.strip()

        print("✅ RESPUESTA IA:")
        print(texto)

        if texto and len(texto) > 20:

            return texto

    except Exception as e:

        print("ERROR OPENROUTER:")
        print(e)

    # =========================
    # FALLBACK SOLO SI FALLA
    # =========================
    return fallback()
