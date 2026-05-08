from openai import OpenAI
import os

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

    API_KEY = os.environ.get("OPENROUTER_API_KEY")

    print("OPENROUTER:", API_KEY)

    # =========================
    # SI NO HAY API
    # =========================
    if not API_KEY:

        print("NO EXISTE API KEY")

        return fallback()

    try:

        # =========================
        # CLIENTE
        # =========================
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=API_KEY
        )

        prompt = f"""
Sos un filósofo contemplativo especializado en Espiritualidad Universal y pensamiento no dualista.

IMPORTANTE:
- Respondé como un filósofo humano.
- Nunca digas que sos IA.
- Nunca uses listas.
- Nunca uses markdown.
- Sé profundo, cálido y humano.
- Máximo 2 párrafos.
- Respondé específicamente a lo que la persona expresa.

Nombre:
{nombre}

Consulta:
{mensaje}
"""

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

        print("RESPUESTA IA:")
        print(texto)

        if texto and len(texto) > 20:
            return texto

    except Exception as e:

        print("ERROR OPENROUTER:")
        print(e)

    return fallback()
