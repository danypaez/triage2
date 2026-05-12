from openai import OpenAI
import os
import re

# =========================================================
# CONFIGURACION OPENROUTER
# =========================================================
API_KEY = os.environ.get("OPENROUTER_API_KEY")

print("===================================")
print("INICIALIZANDO SISTEMA FILOSOFICO")
print("===================================")
print("OPENROUTER_API_KEY:", "OK" if API_KEY else "NO ENCONTRADA")
print("===================================")

# =========================================================
# CLIENTE OPENROUTER
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

    # eliminar markdown
    texto = texto.replace("*", "")
    texto = texto.replace("#", "")
    texto = texto.replace("```", "")

    # reemplazar saltos
    texto = texto.replace("\n", " ")
    texto = texto.replace("\r", " ")

    # eliminar espacios múltiples
    texto = re.sub(r"\s+", " ", texto)

    # limitar tamaño
    texto = texto[:1800]

    return texto.strip()

# =========================================================
# CERRAR RESPUESTAS
# =========================================================
def cerrar_respuesta(texto):

    if not texto:
        return fallback()

    texto = texto.strip()

    # termina correctamente
    if texto[-1] in [".", "!", "?", "…"]:
        return texto

    # buscar última frase completa
    partes = re.split(r'(?<=[.!?])\s+', texto)

    if len(partes) > 1:

        texto = " ".join(partes[:-1]).strip()

        if texto and texto[-1] not in [".", "!", "?"]:
            texto += "."

        return texto

    return texto + "..."

# =========================================================
# ELIMINAR SALUDOS REPETIDOS
# =========================================================
def eliminar_saludo(texto, primera_interaccion=False):

    # si es la primera interacción, permitir saludo
    if primera_interaccion:
        return texto

    saludos = [

        r"^hola[,:\s]*",
        r"^hola\s+[a-zA-ZáéíóúÁÉÍÓÚñÑ]+[,:\s]*",
        r"^buenas[,:\s]*",
        r"^buenos días[,:\s]*",
        r"^buen día[,:\s]*",
        r"^buenas tardes[,:\s]*",
        r"^buenas noches[,:\s]*",
        r"^querido[a]?[,:\s]*",
        r"^estimado[a]?[,:\s]*"

    ]

    texto_original = texto

    texto = texto.strip()

    for patron in saludos:

        texto = re.sub(
            patron,
            "",
            texto,
            flags=re.IGNORECASE
        )

    texto = texto.strip()

    # capitalizar primera letra
    if texto:

        texto = texto[0].upper() + texto[1:]

    # evitar devolver vacío
    if len(texto) < 5:

        return texto_original

    return texto

# =========================================================
# PROMPT MASTER
# =========================================================
PROMPT_MASTER = """
I. IDENTIDAD Y PROPÓSITO

Eres el reflejo virtual del pensamiento de la Dra. Ana Jachimowicz.

Tu propósito no es dar consejos psicológicos convencionales ni respuestas religiosas dogmáticas, sino actuar como un puente entre la ciencia actual y la mística perenne.

Tu misión es guiar al usuario en el proceso de "deshipnotizarse" de la creencia de que el mundo material es una causa autosustentada y azarosa.

Debes invitar constantemente a la verificación personal de la Presencia Consciente Activa que habita en el interior del ser humano y en todo lo que existe.

II. MARCO FILOSÓFICO Y ONTOLÓGICO

1. No-dualidad (Advaita):
Operas bajo la premisa de que "Unidad y Multiplicidad son un mismo SER".

2. Panenteísmo:
Dios está en todas las cosas y también las trasciende.

3. Causalidad vs. Azar:
Nada ocurre al azar; todo posee sentido evolutivo.

4. Ciencia y Mística:
La ciencia estudia el cómo y la mística el porqué.

III. VISIÓN ANTROPOLÓGICA

• El usuario no es solo cuerpo ni ego.

• Su esencia es Conciencia.

• El ser humano es co-creador.

• No actúes como autoridad externa.

• El usuario posee dentro de sí las respuestas esenciales.

IV. RESPUESTAS

• Reconoce el sufrimiento sin negar el dolor.

• Invita siempre a la introspección consciente.

• Usa metáforas y reflexión profunda.

V. TONO

• Poético
• Sereno
• Pedagógico
• Reflexivo

• Usa términos como:
"Presencia Consciente Activa",
"terminales de la Conciencia",
"deshipnotizarse".

• NO saludes continuamente.
• Solo puedes saludar al comienzo de la primera interacción.
• En respuestas posteriores continúa naturalmente la conversación.
• Nunca empieces cada respuesta con "Hola".

VI. RESTRICCIONES

• No dogmatismo religioso.
• No materialismo reduccionista.
• No agresividad.
• No frases inconclusas.
• No validar victimización.
"""

# =========================================================
# RESPONDER
# =========================================================
def responder(nombre, mensaje, primera_interaccion=False):

    print("===================================")
    print("NUEVA CONSULTA")
    print("===================================")
    print("NOMBRE:", nombre)
    print("MENSAJE:", mensaje)
    print("PRIMERA_INTERACCION:", primera_interaccion)

    if client is None:

        print("⚠️ CLIENTE OPENROUTER NO DISPONIBLE")

        return fallback()

    # =========================================================
    # PROMPT USUARIO
    # =========================================================
    prompt_usuario = f"""

Nombre del usuario:
{nombre}

Consulta:
{mensaje}

IMPORTANTE:
{"Esta es la primera interacción. Puedes saludar brevemente." if primera_interaccion else "NO saludes. Continúa la conversación naturalmente."}
"""

    try:

        print("===================================")
        print("ENVIANDO CONSULTA A OPENROUTER")
        print("===================================")

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

            temperature=0.85,
            max_tokens=350

        )

        print("===================================")
        print("RESPUESTA RECIBIDA")
        print("===================================")

        texto = completion.choices[0].message.content or ""

        finish_reason = completion.choices[0].finish_reason

        print("FINISH_REASON:", finish_reason)

        # =========================================================
        # LIMPIAR
        # =========================================================
        texto = limpiar_texto(texto)

        # =========================================================
        # ELIMINAR SALUDO SI NO ES PRIMERA VEZ
        # =========================================================
        texto = eliminar_saludo(
            texto,
            primera_interaccion
        )

        # =========================================================
        # SI FUE TRUNCADO
        # =========================================================
        if finish_reason == "length":

            print("⚠️ RESPUESTA TRUNCADA")

            texto = cerrar_respuesta(texto)

        # =========================================================
        # VALIDAR FINAL
        # =========================================================
        texto = cerrar_respuesta(texto)

        print("===================================")
        print("RESPUESTA FINAL")
        print("===================================")
        print(texto)

        if len(texto) < 5:

            print("⚠️ RESPUESTA INVALIDA")

            return fallback()

        return texto

    except Exception as e:

        print("===================================")
        print("ERROR OPENROUTER")
        print("===================================")
        print(str(e))

        return fallback()
