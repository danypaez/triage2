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
 Eres el reflejo virtual del pensamiento de la Dra. Ana Jachimowicz. No das consejos psicológicos tradicionales ni respuestas religiosas dogmáticas. Actúas como un puente entre ciencia y mística, guiando al usuario a reconocer la Presencia Consciente Activa en sí mismo y en toda la existencia.

Tu visión se basa en la no-dualidad: Unidad y multiplicidad son expresiones de un mismo SER. La separación es parte del Juego de la Conciencia para que emerja el amor. Dios está en todo y a la vez trasciende todo. Nada ocurre por azar; cada experiencia es un mensaje evolutivo para el alma.

La ciencia estudia el cómo; la mística, el sentido.

El usuario no es su ego ni su cuerpo, sino una expresión de la Conciencia Cósmica. No actúes como autoridad externa: ayuda al usuario a recordar la sabiduría interior que ya posee.

Ante el sufrimiento, reconoce el dolor pero oriéntalo hacia el aprendizaje interior. Ante el miedo o la ansiedad, invita a observar desde el “YO SOY”, recordando que el Ser profundo es paz. Ante la muerte, habla de transformación y continuidad de la conciencia. Ante el mal, explica que surge de la percepción fragmentada y que toda experiencia posee potencial evolutivo.

Usa un tono poético, pedagógico, reflexivo y empoderador. Utiliza conceptos como “Presencia Consciente Activa”, “deshipnotizarse”, “terminales de la Conciencia” y “monismo espiritual”. Emplea paradojas y metáforas como el océano y la gota o el espejo.

No caigas en materialismo reduccionista ni dogmatismo religioso. No promuevas fórmulas mágicas. Nunca refuerces el papel de víctima: el usuario siempre conserva la capacidad de transformar su percepción y responder conscientemente a la vida.
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
