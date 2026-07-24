// NO IMPORTAMOS NADA de @web para evitar que module_loader.js falle en las vistas públicas.

const opcionesGeolocalizacion = {
  enableHighAccuracy: true,
  timeout: 5000,
  maximumAge: 0,
};

function inicializarCheckIn() {
  const button = document.getElementById("js-button-check-in");

  if (!button) {
    // Reintenta en 100ms si el HTML todavía se está renderizando
    setTimeout(inicializarCheckIn, 100);
    return;
  }

  console.log("====================================");
  console.log("¡Script público de Check-In listo y acoplado!");
  console.log("====================================");

  button.addEventListener("click", async (ev) => {
    ev.preventDefault();
    console.log("¡Click capturado nativamente en zona pública!");

    // DEFINIMOS "btn" AQUÍ arriba para que tenga alcance en ambos callbacks inferiores
    const btn = ev.currentTarget;

    if (!navigator.geolocation) {
      alert("Tu navegador no soporta geolocalización.");
      return;
    }

    btn.disabled = true;
    btn.innerText = "Obteniendo Ubicación...";

    navigator.geolocation.getCurrentPosition(
      async (position) => {
        const latitud = position.coords.latitude;
        const longitud = position.coords.longitude;

        try {
          const url = `https://nominatim.openstreetmap.org/reverse?format=json&lat=${latitud}&lon=${longitud}`;
          const respuestaOpenStreet = await fetch(url);

          if (respuestaOpenStreet.ok) {
            const datosDireccion = await respuestaOpenStreet.json();
            const direccionCompleta = datosDireccion.display_name || "";

            if (direccionCompleta) {
              console.log(direccionCompleta);
              const direccionArray = direccionCompleta.split(",");
              const area = direccionArray[1] ? direccionArray[1].trim() : "";

              console.log("Área localizada:", area);

              // LLAMADA COMPATIBLE CON EL PORTAL PÚBLICO DE ODOO
              await fetch("/check_in", {
                method: "POST",
                headers: {
                  "Content-Type": "application/json",
                },
                body: JSON.stringify({
                  jsonrpc: "2.0",
                  params: { area: area },
                }),
              });

              btn.disabled = false;
              btn.innerText = "Pasar Lista";
              window.location.reload();
            } else {
              resetearBoton(btn);
            }
          } else {
            resetearBoton(btn);
          }
        } catch (error) {
          resetearBoton(btn);
          console.error("Error en la petición:", error);
        }
      },
      (error) => {
        // Ahora "btn" sí existe en este contexto gracias al closure
        resetearBoton(btn);
        console.error("Acceso a ubicación denegado o error de red:", error);
      },
      opcionesGeolocalizacion,
    );
  });
}

function resetearBoton(btn) {
  btn.disabled = false;
  btn.innerText = "Pasar Lista";
}

// Inicializamos en cuanto el documento esté listo
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", inicializarCheckIn);
} else {
  inicializarCheckIn();
}
