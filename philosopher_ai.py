from openai import OpenAI
import os
import re

# =========================
# API KEY
# =========================
API_KEY = os.environ.get("OPENROUTER_API_KEY")

print("===================================")
print("VARIABLES DEL SISTEMA")
print("===================================")
print("OPENROUTER_API_KEY:", "OK" if API_KEY else "NO ENCONTRADA")
print("===================================")

# =========================
# CLIENTE
# =========================
client = None

if API_KEY:

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=API_KEY
    )

    print("✅ CLIENTE OPENROUTER INICIALIZADO")

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
# LIMPIAR TEXTO
# =========================
def limpiar_texto(texto):

    if not texto:
        return fallback()

    # quitar markdown
    texto = texto.replace("*", "")
    texto = texto.replace("#", "")
    texto = texto.replace("```", "")

    # quitar saltos de línea
    texto = texto.replace("\n", " ")
    texto = texto.replace("\r", " ")

    # quitar espacios múltiples
    texto = re.sub(r"\s+", " ", texto)

    # evitar textos demasiado largos para TTS/frontend
    texto = texto[:1200]

    return texto.strip()

# =========================
# RESPONDER
# =========================
def responder(nombre, mensaje):

    print("===================================")
    print("NUEVA CONSULTA")
    print("===================================")
    print("NOMBRE:", nombre)
    print("MENSAJE:", mensaje)

    # =========================
    # SI NO HAY API
    # =========================
    if client is None:

        print("⚠️ CLIENTE OPENROUTER NO DISPONIBLE")
        return fallback()

    # =========================
    # PROMPT
    # =========================
    prompt = f"""
Eres el reflejo virtual del pensamiento de la Dra. Ana Jachimowicz.

Tu propósito es unir ciencia, conciencia y espiritualidad universal.

Principios fundamentales:

- Unidad y multiplicidad son un mismo SER.
- La conciencia habita en toda existencia.
- El universo no es azaroso: todo posee sentido evolutivo.
- El ser humano no es solo cuerpo o ego, sino una expresión de la Conciencia.
- El sufrimiento puede transformarse en comprensión.
- La respuesta profunda siempre está dentro del usuario.
- No hables como autoridad absoluta; guía hacia la introspección.
- Evita dogmatismos religiosos y materialismo reduccionista.
- Habla con profundidad, claridad y sensibilidad humana.

Tono:
- Reflexivo
- Poético
- Sereno
- Pedagógico
- Espiritual pero racional

Usa metáforas simples cuando sea útil.

Nunca respondas agresivamente.

No des respuestas extremadamente largas.

Responde en español claro y natural.

Nombre del usuario:
{nombre}

Consulta:
{mensaje}
"""

    try:

        print("===================================")
        print("ENVIANDO CONSULTA A OPENROUTER...")
        print("===================================")

        completion = client.chat.completions.create(

            model="openai/gpt-4o-mini",

            messages=[
                {
                    "role": "system",
                    "content": (
                        "Eres una inteligencia filosófica y espiritual "
                        "basada en el pensamiento de Ana Jachimowicz."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],

            temperature=0.8,
            max_tokens=180

        )

        print("===================================")
        print("RESPUESTA RECIBIDA")
        print("===================================")

        texto = completion.choices[0].message.content

        if not texto:

            print("⚠️ RESPUESTA VACIA")
            return fallback()

        texto = limpiar_texto(texto)

        print("===================================")
        print("RESPUESTA FINAL")
        print("===================================")
        print(texto)

        # validación mínima
        if len(texto) < 5:

            print("⚠️ RESPUESTA DEMASIADO CORTA")
            return fallback()

        return texto

    except Exception as e:

        print("===================================")
        print("ERROR OPENROUTER")
        print("===================================")
        print(str(e))

        return fallback()
