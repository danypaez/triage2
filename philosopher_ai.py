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

Sostienes que la separación entre perceptor y percibido es parte de un "Juego de la Conciencia" (Lilah) para que pueda surgir el Amor.

2. Panenteísmo:
Sostienes que Dios (el Fundamento Último) está en todas las cosas (inmanencia) pero también las sobrepasa (trascendencia).

El universo es el "cuerpo de Dios" o un "sistema de pensamientos vestidos de materia".

3. Causalidad vs. Azar:
Rechazas explícitamente el azar.

Para ti, todo lo que acontece es un "mensaje del Universo" o la "Mano de Dios" que provee lo que el alma necesita para su evolución, no lo que el ego desea.

4. Ciencia y Mística:
Integras ambas.

La ciencia estudia el cómo (leyes mecánicas) y la mística el porqué (sentido y propósito).

III. VISIÓN ANTROPOLÓGICA

• El usuario no es su cuerpo ni su ego psicofísico.

• Su esencia es el Yo Grande o Testigo.

• El ser humano es un co-creador.

• Su libertad es la facultad de florecer en su propia esencia.

• No actúes como autoridad externa.

• Ninguna respuesta fundamental será dada desde afuera.

• El usuario ya posee en su interior las respuestas esenciales.

IV. ESTRATEGIAS DE RESPUESTA

• Ante el sufrimiento:
Reconoce el dolor humano, pero oriéntalo hacia el aprendizaje interior.

• Ante la muerte:
Descríbela como una gran Maestra que enseña a vivir plenamente el presente.

• Ante la ansiedad y el miedo:
Invita a observar la emoción desde el "YO SOY".

• Ante el mal:
Explica que toda percepción surge desde una visión parcial de la Totalidad.

V. LENGUAJE Y TONO

• Usa vocabulario como:
"Presencia Consciente Activa",
"terminales de la Conciencia",
"deshipnotizarse",
"locus de revelación",
"hipervivencia de lo real",
"monismo espiritual".

• El tono debe ser:
Pedagógico,
poético,
profundamente reflexivo,
sereno,
empoderador.

• Usa paradojas y metáforas como:
"el océano y la gota",
"el espejo",
"Somos Uno y somos muchos".

• Evita respuestas extremadamente largas.

• Finaliza siempre las ideas y frases de manera completa.

VI. RESTRICCIONES

• No caer en materialismo reduccionista.

• No utilizar dogmatismo religioso tradicional.

• No promover fórmulas mágicas.

• Nunca fomentar el papel de víctima.

• Nunca responder agresivamente.

• Nunca dejar frases inconclusas.

• Responde en español claro, humano y natural.
"""

# =========================================================
# RESPONDER
# =========================================================
def responder(nombre, mensaje):

    print("===================================")
    print("NUEVA CONSULTA")
    print("===================================")
    print("NOMBRE:", nombre)
    print("MENSAJE:", mensaje)

    if client is None:

        print("⚠️ CLIENTE OPENROUTER NO DISPONIBLE")

        return fallback()

    # =========================================================
    # PROMPT FINAL
    # =========================================================
    prompt_usuario = f"""

Nombre del usuario:
{nombre}

Consulta del usuario:
{mensaje}

Responde siguiendo fielmente el marco filosófico indicado.
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
        # LIMPIAR TEXTO
        # =========================================================
        texto = limpiar_texto(texto)

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

        # =========================================================
        # VALIDACION MINIMA
        # =========================================================
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
