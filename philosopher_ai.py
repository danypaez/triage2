from openai import OpenAI
import os

# =========================
# API KEY
# =========================
API_KEY = os.environ.get("OPENROUTER_API_KEY")

print("VARIABLES DEL SISTEMA:")
print(os.environ)

print("OPENROUTER:", API_KEY)

# =========================
# CLIENTE
# =========================
client = None

if API_KEY:

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=API_KEY
    )

else:

    print("⚠️ NO SE ENCONTRO OPENROUTER_API_KEY")

# =========================
# FALLBACK
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

    # =========================
    # SI NO HAY API
    # =========================
    if client is None:

        return fallback()

    prompt = f"""
Sos un filósofo contemplativo especializado en Espiritualidad Universal y pensamiento no dualista.

IMPORTANTE:
- Respondé como un ser humano sabio.
- Nunca digas que sos IA.
- Nunca uses listas.
- Nunca uses markdown.
- No respondas genéricamente.
- Reflexioná específicamente sobre lo que la persona expresa.
- Máximo 2 párrafos.
- Sé cálido, humano y profundo.

Nombre:
{nombre}

Consulta:
{mensaje}
"""

    try:

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

    return fallback()
