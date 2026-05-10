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
// VOZ NATURAL
// =========================
 ```javascript
// =========================
// VOZ NATURAL FEMENINA
// =========================
function hablar(texto){

    return new Promise((resolve)=>{

        speechSynthesis.cancel();

        const voz = new SpeechSynthesisUtterance(texto);

        voz.lang = "es-AR";
        voz.rate = 0.95;
        voz.pitch = 1.1; // un poco más cálida/femenina
        voz.volume = 1;

        const voces = speechSynthesis.getVoices();

        // 🔥 PRIORIDAD VOCES FEMENINAS
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

            // Google femenina
            voces.find(v =>
                v.lang.includes("es") &&
                v.name.includes("Google") &&
                (
                    v.name.toLowerCase().includes("female") ||
                    v.name.toLowerCase().includes("mujer")
                )
            )

            ||

            // Microsoft femenina
            voces.find(v =>
                v.lang.includes("es") &&
                v.name.includes("Microsoft") &&
                !v.name.includes("Male")
            )

            ||

            // cualquier voz española femenina
            voces.find(v =>
                v.lang.includes("es") &&
                (
                    v.name.endsWith("a") ||
                    v.name.includes("Female")
                )
            );

        if(vozFemenina){
            voz.voice = vozFemenina;
        }

        voz.onend = ()=>{
            resolve();
        };

        speechSynthesis.speak(voz);

    });
}
```

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

        const res = await fetch("/chat",{

            method:"POST",

            headers:{
                "Content-Type":"application/json"
            },

            body:JSON.stringify({
                nombre,
                mensaje
            })

        });

        const data = await res.json();

        agregar("bot", data.response);

        await hablar(data.response);

        document.getElementById("acciones").style.display = "flex";

    }catch(e){

        console.log(e);

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
