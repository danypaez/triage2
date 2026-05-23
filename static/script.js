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
// CARGAR VOCES
// =========================================================
async function cargarVoces(){

    return new Promise((resolve)=>{

        let voces = speechSynthesis.getVoices();

        // ya cargadas
        if(voces.length > 0){

            resolve(voces);
            return;

        }

        // esperar carga real
        let intentos = 0;

        const intervalo = setInterval(()=>{

            voces = speechSynthesis.getVoices();

            if(voces.length > 0){

                clearInterval(intervalo);

                resolve(voces);

            }

            intentos++;

            // timeout
            if(intentos > 20){

                clearInterval(intervalo);

                resolve(voces);

            }

        }, 250);

    });

}

// =========================================================
// HABLAR
// =========================================================
async function hablar(texto){

    try{

        // detener voz previa
        speechSynthesis.cancel();

        // cargar voces correctamente
        const voces = await cargarVoces();

        console.log("VOCES DISPONIBLES:", voces);

        const voz = new SpeechSynthesisUtterance(texto);

        // =====================================================
        // CONFIG
        // =====================================================
        voz.lang = "es-AR";
        voz.rate = 0.93;
        voz.pitch = 1;
        voz.volume = 1;

        // =====================================================
        // BUSCAR MEJOR VOZ
        // =====================================================
        const vozEspanol =

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
                v.name.includes("Laura")
            )

            ||

            voces.find(v =>
                v.lang.includes("es") &&
                v.name.includes("Google")
            )

            ||

            voces.find(v =>
                v.lang.includes("es")
            );

        // =====================================================
        // APLICAR VOZ
        // =====================================================
        if(vozEspanol){

            console.log("================================");
            console.log("VOZ SELECCIONADA:");
            console.log(vozEspanol.name);
            console.log("================================");

            voz.voice = vozEspanol;

        }

        // =====================================================
        // EVENTOS
        // =====================================================
        voz.onstart = ()=>{

            console.log("INICIO VOZ");

        };

        voz.onend = ()=>{

            console.log("FIN VOZ");

        };

        voz.onerror = (e)=>{

            console.log("ERROR VOZ:", e);

        };

        // =====================================================
        // HABLAR
        // =====================================================
        speechSynthesis.speak(voz);

    }catch(e){

        console.log("ERROR GENERAL VOZ:", e);

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

        console.log("ENVIANDO A /chat");

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

        console.log("STATUS:", res.status);

        if(!res.ok){

            throw new Error("ERROR SERVIDOR");

        }

        const data = await res.json();

        console.log("RESPUESTA:", data);

        // validar
        if(!data.response){

            throw new Error("RESPUESTA VACIA");

        }

        agregar("bot", data.response);

        await hablar(data.response);

    }catch(e){

        console.log("ERROR FETCH:", e);

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
