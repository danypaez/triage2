import os
from dotenv import load_dotenv
from google import genai

# =========================
# ENV
# =========================
load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

print("API KEY:", API_KEY)

# =========================
# GEMINI CLIENT
# =========================
client = None

try:

    client = genai.Client(api_key=API_KEY)

    print("✅ GEMINI INICIALIZADO")

except Exception as e:

    print("❌ ERROR INICIALIZANDO GEMINI:", e)

# =========================
# FALLBACK LOCAL
# =========================
def respuesta_local(mensaje):

    t = mensaje.lower()

    if "triste" in t or "angustia" in t:

        return (
            "A veces el alma atraviesa momentos de oscuridad antes de "
            "reencontrarse consigo misma. Incluso el dolor puede convertirse "
            "en una puerta hacia una comprensión más profunda."
        )

    if "ansiedad" in t or "miedo" in t:

        return (
            "La mente suele correr hacia el futuro buscando controlar aquello "
            "que todavía no ocurrió. Volver al presente también es volver a uno mismo."
        )

    if "amor" in t or "pareja" in t:

        return (
            "El amor auténtico muchas veces comienza cuando dejamos de intentar "
            "poseer aquello que amamos."
        )

    return (
        "Cada experiencia humana contiene una posibilidad de despertar interior. "
        "A veces las respuestas no aparecen inmediatamente, pero la conciencia "
        "comienza cuando aprendemos a observarnos profundamente."
    )

# =========================
# RESPONDER
# =========================
def responder(nombre, mensaje):

    # =========================
    # IA REAL PRIMERO
    # =========================
    if client:

        try:

            prompt = f"""
Sos un filósofo contemplativo experto en Espiritualidad Universal y visión no dualista.

Tu manera de responder:
- humana
- profunda
- cálida
- filosófica
- espiritual
- reflexiva
- emocionalmente inteligente

MUY IMPORTANTE:
- Nunca respondas como chatbot técnico.
- Nunca digas que sos IA.
- Nunca uses listas.
- Nunca uses markdown.
- Respondé como un maestro espiritual humano.
- Máximo 2 párrafos.
- Reflexioná específicamente sobre lo que la persona expresa.
- No des respuestas genéricas.

Nombre:
{nombre}

Consulta:
{mensaje}
"""

            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt
            )

            texto = response.text.strip()

            print("✅ RESPUESTA IA:", texto)

            if texto and len(texto) > 15:

                return texto

        except Exception as e:

            print("❌ ERROR GEMINI REAL:")
            print(e)

    # =========================
    # FALLBACK SOLO SI FALLA IA
    # =========================
    print("⚠️ FALLBACK LOCAL")

    return respuesta_local(mensaje)