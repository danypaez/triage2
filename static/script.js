
let nombre = "";
let esperandoNombre = true;

// =========================
// CHAT UI
// =========================
function agregar(tipo, texto){

    const chat = document.getElementById("chat");

    chat.innerHTML += `
        <div class="msg ${tipo}">
            ${texto}
        </div>
    `;

    chat.scrollTop = chat.scrollHeight;
}

// =========================
// CARGAR VOCES
// =========================
function cargarVoces(){

    return new Promise((resolve)=>{

        let voces = speechSynthesis.getVoices();

        if(voces.length){

            resolve(voces);
            return;

        }

        speechSynthesis.onvoiceschanged = ()=>{

            voces = speechSynthesis.getVoices();

            resolve(voces);

        };

    });

}

// =========================
// HABLAR
// =========================
async function hablar(texto){

    return new Promise(async (resolve)=>{

        try{

            // detener voz anterior
            speechSynthesis.cancel();

            // pequeñas pausas naturales
            texto = texto.replace(/\./g, ". ");
            texto = texto.replace(/,/g, ", ");

            const voces = await cargarVoces();

            const voz = new SpeechSynthesisUtterance(texto);

            // =========================
            // CONFIGURACION NATURAL
            // =========================
            voz.lang = "es-AR";
            voz.rate = 0.92;
            voz.pitch = 1.02;
            voz.volume = 1;

            // =========================
            // PRIORIZAR VOCES NATURALES
            // =========================
            const vozFemenina =

                // 🔥 LA MAS NATURAL
                voces.find(v =>
                    v.lang.includes("es") &&
                    v.name.includes("Paulina")
                )

                ||

                voces.find(v =>
                    v.lang.includes("es") &&
                    v.name.includes("Helena")
                )

                ||

                voces.find(v =>
                    v.lang.includes("es") &&
                    v.name.includes("Sabina")
                )

                ||

                voces.find(v =>
                    v.lang.includes("es") &&
                    v.name.includes("Laura")
                )

                ||

                voces.find(v =>
                    v.lang.includes("es") &&
                    v.name.includes("Monica")
                )

                ||

                voces.find(v =>
                    v.lang.includes("es") &&
                    v.name.includes("Maria")
                )

                ||

                // Google
                voces.find(v =>
                    v.lang.includes("es") &&
                    v.name.includes("Google")
                )

                ||

                // Microsoft
                voces.find(v =>
                    v.lang.includes("es") &&
                    v.name.includes("Microsoft")
                )

                ||

                // cualquier española
                voces.find(v =>
                    v.lang.includes("es")
                );

            // =========================
            // APLICAR VOZ
            // =========================
            if(vozFemenina){

                console.log("================================");
                console.log("VOZ SELECCIONADA:");
                console.log(vozFemenina.name);
                console.log("================================");

                voz.voice = vozFemenina;

            }

            // =========================
            // EVENTOS
            // =========================
            voz.onend = ()=>{

                resolve();

            };

            voz.onerror = (e)=>{

                console.log("ERROR VOZ:", e);

                resolve();

            };

            // =========================
            // HABLAR
            // =========================
            speechSynthesis.speak(voz);

        }catch(e){

            console.log("ERROR HABLAR:", e);

            resolve();

        }

    });

}

// =========================
// BIENVENIDA
// =========================
window.addEventListener("load", async ()=>{

    const bienvenida =
        "Bienvenido al espacio de consultas de Dios adentro Dios afuera. Antes de comenzar, decime tu nombre.";

    agregar("bot", bienvenida);

    await hablar(bienvenida);

});

// =========================
// ENVIAR
// =========================
async function enviar(){

    const input = document.getElementById("input");

    const mensaje = input.value.trim();

    if(!mensaje) return;

    agregar("user", mensaje);

    input.value = "";

    document.getElementById("acciones").style.display = "none";

    // =========================
    // PRIMERA INTERACCION
    // =========================
    if(esperandoNombre){

        nombre = mensaje;

        esperandoNombre = false;

        const saludo =
            `Mucho gusto ${nombre}. Podés contarme aquello que estés atravesando o aquello sobre lo que quieras reflexionar.`;

        agregar("bot", saludo);

        await hablar(saludo);

        return;

    }

    // =========================
    // CONSULTA IA
    // =========================
    try{

        const res = await fetch("/chat", {

            method:"POST",

            headers:{
                "Content-Type":"application/json"
            },

            body: JSON.stringify({
                nombre,
                mensaje
            })

        });

        // =========================
        // VALIDAR RESPUESTA
        // =========================
        if(!res.ok){

            throw new Error("ERROR SERVIDOR");

        }

        const data = await res.json();

        console.log("RESPUESTA IA:", data);

        if(!data.response){

            throw new Error("RESPUESTA VACIA");

        }

        agregar("bot", data.response);

        await hablar(data.response);

        document.getElementById("acciones").style.display = "flex";

    }catch(e){

        console.log("ERROR GENERAL:", e);

        const error =
            "En este momento no logro conectar con la reflexión universal.";

        agregar("bot", error);

        await hablar(error);

    }

}

// =========================
// OTRA CONSULTA
// =========================
async function otraConsulta(){

    document.getElementById("acciones").style.display = "none";

    const mensaje =
        "Estoy aquí para escucharte. ¿Qué otra reflexión o inquietud deseás compartir?";

    agregar("bot", mensaje);

    await hablar(mensaje);

}

// =========================
// FINALIZAR CHAT
// =========================
async function finalizarChat(){

    document.getElementById("acciones").style.display = "none";

    const hora = new Date().getHours();

    let saludo = "Que tengas un hermoso día.";

    if(hora >= 13 && hora < 20){

        saludo = "Que tengas una hermosa tarde.";

    }

    if(hora >= 20 || hora < 6){

        saludo = "Que tengas una serena noche.";

    }

    const mensaje =
        `Gracias por compartir este espacio de contemplación. ${saludo}`;

    agregar("bot", mensaje);

    await hablar(mensaje);

}
```
