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
// ESPERAR VOCES
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
// VOZ NATURAL FEMENINA
// =========================
async function hablar(texto){

    return new Promise(async (resolve)=>{

        try{

            speechSynthesis.cancel();

            const voces = await cargarVoces();

            const voz = new SpeechSynthesisUtterance(texto);

            voz.lang = "es-AR";
            voz.rate = 0.95;
            voz.pitch = 1.05;
            voz.volume = 1;

            // =========================
            // BUSCAR VOZ FEMENINA
            // =========================
            const vozFemenina =

                voces.find(v =>
                    v.lang.includes("es") &&
                    (
                        v.name.includes("Sabina") ||
                        v.name.includes("Helena") ||
                        v.name.includes("Paulina") ||
                        v.name.includes("Laura") ||
                        v.name.includes("Maria") ||
                        v.name.includes("Monica")
                    )
                )

                ||

                voces.find(v =>
                    v.lang.includes("es") &&
                    v.name.includes("Google")
                )

                ||

                voces.find(v =>
                    v.lang.includes("es") &&
                    v.name.includes("Microsoft")
                )

                ||

                voces.find(v =>
                    v.lang.includes("es")
                );

            if(vozFemenina){

                console.log("VOZ:", vozFemenina.name);

                voz.voice = vozFemenina;

            }

            voz.onend = ()=>{

                resolve();

            };

            voz.onerror = (e)=>{

                console.log("ERROR VOZ:", e);

                resolve();

            };

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
    // NOMBRE
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
    // IA
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

        // =========================
        // VALIDAR TEXTO
        // =========================
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
// FINALIZAR
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
