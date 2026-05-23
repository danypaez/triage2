let nombre = "";
let esperandoNombre = true;

// =========================================================
// AGREGAR MENSAJE
// =========================================================
function agregar(tipo, texto){

    const chat = document.getElementById("chat");

    chat.innerHTML += `
        <div class="msg ${tipo}">
            ${texto}
        </div>
    `;

    chat.scrollTop = chat.scrollHeight;
}

// =========================================================
// HABLAR
// =========================================================
async function hablar(texto){

    try{

        speechSynthesis.cancel();

        const voz = new SpeechSynthesisUtterance(texto);

        voz.lang = "es-AR";
        voz.rate = 0.95;
        voz.pitch = 1;
        voz.volume = 1;

        const voces = speechSynthesis.getVoices();

        const vozEspanol = voces.find(v =>
            v.lang.includes("es")
        );

        if(vozEspanol){

            voz.voice = vozEspanol;

        }

        speechSynthesis.speak(voz);

    }catch(e){

        console.log("ERROR VOZ:", e);

    }

}

// =========================================================
// INICIAR
// =========================================================
window.addEventListener("load", ()=>{

    const bienvenida =
        "Bienvenido al espacio de consultas de Dios adentro Dios afuera. Antes de comenzar, decime tu nombre.";

    agregar("bot", bienvenida);

});

// =========================================================
// ENVIAR
// =========================================================
async function enviar(){

    const input = document.getElementById("input");

    const mensaje = input.value.trim();

    if(!mensaje) return;

    agregar("user", mensaje);

    input.value = "";

    // =====================================================
    // NOMBRE
    // =====================================================
    if(esperandoNombre){

        nombre = mensaje;

        esperandoNombre = false;

        const saludo =
            `Mucho gusto ${nombre}. Podés contarme aquello que estés atravesando o aquello sobre lo que quieras reflexionar.`;

        agregar("bot", saludo);

        await hablar(saludo);

        return;

    }

    // =====================================================
    // CONSULTA IA
    // =====================================================
    try{

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

        if(!res.ok){

            throw new Error("ERROR SERVIDOR");

        }

        const data = await res.json();

        console.log(data);

        agregar("bot", data.response);

        await hablar(data.response);

    }catch(e){

        console.log("ERROR:", e);

        const error =
            "En este momento no logro conectar con la reflexión universal.";

        agregar("bot", error);

        await hablar(error);

    }

}

// =========================================================
// ENTER
// =========================================================
document.addEventListener("keydown", function(e){

    if(e.key === "Enter"){

        enviar();

    }

});
