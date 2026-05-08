let nombre = "";

let esperandoNombre = true;

let esperandoContinuacion = false;

// =========================
// UI
// =========================
function agregar(tipo, texto) {

    const chat = document.getElementById("chat");

    chat.innerHTML += `
        <div class="msg ${tipo}">
            ${texto}
        </div>
    `;

    chat.scrollTop = chat.scrollHeight;
}

// =========================
// VOZ
// =========================
 function hablarTexto(texto) {

    speechSynthesis.cancel();

    const voz = new SpeechSynthesisUtterance(texto);

    voz.lang = "es-AR";

    voz.rate = 0.95;
    voz.pitch = 1;
    voz.volume = 1;

    // voces más naturales
    const voces = speechSynthesis.getVoices();

    const vozNatural =
        voces.find(v =>
            v.lang.includes("es") &&
            (
                v.name.includes("Google") ||
                v.name.includes("Microsoft") ||
                v.name.includes("Sabina") ||
                v.name.includes("Helena")
            )
        );

    if (vozNatural) {
        voz.voice = vozNatural;
    }

    speechSynthesis.speak(voz);
}

// =========================
// DESPEDIDA SEGÚN HORA
// =========================
function despedidaHora() {

    const hora = new Date().getHours();

    if (hora >= 5 && hora < 12) {
        return "Que tengas un hermoso día.";
    }

    if (hora >= 12 && hora < 20) {
        return "Que tengas una hermosa tarde.";
    }

    return "Que tengas una hermosa noche.";
}

// =========================
// DETECTAR NO
// =========================
function esNo(texto) {

    const t = texto.toLowerCase().trim();

    const negativas = [

        "no",
        "no gracias",
        "nada mas",
        "nada más",
        "eso es todo",
        "ninguna",
        "ninguno",
        "no tengo más consultas",
        "no tengo mas consultas",
        "no deseo continuar",
        "no quiero continuar",
        "ya esta",
        "ya está",
        "finalizar",
        "terminar",
        "salir",
        "fin"

    ];

    return negativas.includes(t);
}

// =========================
// DETECTAR SI
// =========================
function esSi(texto) {

    const t = texto.toLowerCase().trim();

    const positivos = [

        "si",
        "sí",
        "claro",
        "ok",
        "dale",
        "por supuesto",
        "obvio",
        "yes"

    ];

    return positivos.includes(t);
}

// =========================
// BIENVENIDA
// =========================
window.addEventListener("load", async () => {

    const bienvenida =
        "Bienvenido al espacio de consultas de Dios adentro Dios afuera. Antes de comenzar, decime tu nombre.";

    agregar("bot", bienvenida);

    await hablar(bienvenida);
});

// =========================
// ENVIAR
// =========================
async function enviar() {

    const input = document.getElementById("input");

    const mensaje = input.value.trim();

    if (!mensaje) return;

    agregar("user", mensaje);

    input.value = "";

    // =========================
    // NOMBRE
    // =========================
    if (esperandoNombre) {

        nombre = mensaje;

        esperandoNombre = false;

        const saludo =
            `Mucho gusto ${nombre}. Podés contarme aquello que estés atravesando o aquello sobre lo que quieras reflexionar.`;

        agregar("bot", saludo);

        await hablar(saludo);

        return;
    }

    // =========================
    // CONTROL CONTINUACIÓN
    // =========================
    if (esperandoContinuacion === true) {

        // 🔴 TERMINAR CHAT
        if (esNo(mensaje)) {

            esperandoContinuacion = false;

            const despedida =
                `Gracias por compartirme tus pensamientos y reflexiones. ${despedidaHora()}`;

            agregar("bot", despedida);

            await hablar(despedida);

            return;
        }

        // 🟢 CONTINUAR CHAT
        if (esSi(mensaje)) {

            esperandoContinuacion = false;

            const continuar =
                "¿Cuál es la siguiente consulta o reflexión que deseás compartir?";

            agregar("bot", continuar);

            await hablar(continuar);

            return;
        }

        // 🔵 SI ES OTRA PREGUNTA DIRECTA
        esperandoContinuacion = false;
    }

    // =========================
    // CONSULTA IA
    // =========================
    try {

        const res = await fetch("/chat", {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                nombre,
                mensaje
            })
        });

        const data = await res.json();

        agregar("bot", data.response);

        await hablar(data.response);

        // =========================
        // PREGUNTA FINAL
        // =========================
        const continuar =
            "¿Te gustaría realizar otra consulta o compartir otra reflexión?";

        agregar("bot", continuar);

        await hablar(continuar);

        // 🔥 ACTIVAR CONTROL
        esperandoContinuacion = true;

    } catch (e) {

        console.log(e);

        const error =
            "En este momento no logro conectar con la reflexión universal.";

        agregar("bot", error);

        await hablar(error);
    }
}
