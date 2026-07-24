/** @odoo-module **/

// Importación de modulos odoo
import { Component } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

const opcionesGeolocalizacion = {
  enableHighAccuracy: true,
  timeout: 5000,
  maximumAge: 0,
};

// Se crea una nueva clase. Hereda de "Component"
export class GeoWidget extends Component {
  setup() {
    // Ya no necesitamos 'orm' si solo vamos a rellenar el formulario visual
    // this.orm ...
  }

  // Este es el metodo que es llamado por el widget geo.GeoWidget "geo_widget.xml"
  async obtenerUbicacion() {
    console.log("CLICK - Solicitando ubicación para el formulario...");

    // Retorna si la geolocalización no es soportada.
    if (!navigator.geolocation) {
      console.error("La geolocalización no está soportada.");
      return;
    }

    // Metodo de geolocalización con un lambda (=>) para extraer atributos
    navigator.geolocation.getCurrentPosition(
      async (posicion) => {
        const lat = posicion.coords.latitude;
        const lon = posicion.coords.longitude;
        let direccionFisica = "Dirección no encontrada";
        let calle = "Calle no encontrada";
        let area = "Area no encontrada";
        let codigo_postal = "Codigo Postal no encontrado";
        let direccion = "Dirección no encontrada";
        let smallArray = null;

        try {
          // Geolocalización inversa usando OpenStreetMap
          const url = `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lon}`;
          const respuestaGeocode = await fetch(url);
          if (respuestaGeocode.ok) {
            const datosDireccion = await respuestaGeocode.json();
            const direccionCompleta = datosDireccion.display_name || "";
            console.log(direccionCompleta);

            if (direccionCompleta) {
              // Se parte el string y se indexa para separar la info.
              let direccionArray = direccionCompleta.split(",");
              // Se busca el codigo postal en el array.
              direccionArray.forEach((elemento) => {
                const elementoLimpio = String(elemento).trim();
                if (/^\d+$/.test(elementoLimpio)) {
                  console.log(elementoLimpio);
                  codigo_postal = elementoLimpio;
                }
              });
              // Calle primer elemento del array
              calle = direccionArray.shift();
              // Area segundo elemento del array
              area = direccionArray.shift();
              // Se filtra el array modificado quitando el C.P.
              smallArray = direccionArray.filter(
                (elemento) => String(elemento).trim() != codigo_postal,
              );
              // Se uno para guardar la direccion variable por consulta.
              direccion = smallArray.join(", ");
            }
          }
        } catch (errGeocode) {
          console.warn("No se pudo obtener la dirección.", errGeocode);
        }

        try {
          // --- AQUÍ OCURRE LA MAGIA DEL FRONTEND ---
          // 'this.props.record.update' recibe un objeto con los nombres de los campos técnicos
          // de tu modelo Python y les asigna los nuevos valores en la pantalla.

          await this.props.record.update({
            latitud: String(lat).trim(), // Reemplaza con el nombre técnico de tu campo en Python
            longitud: String(lon).trim(), // Reemplaza con el nombre técnico de tu campo en Python
            calle: String(calle).trim(), // Reemplaza con el nombre técnico de tu campo en Python
            area: String(area).trim(),
            codigo_postal: String(codigo_postal).trim(),
            direccion: String(smallArray).trim(),
          });

          console.log(
            "Campos del formulario actualizados en pantalla de forma interactiva.",
          );
        } catch (error) {
          console.error(
            "Error al actualizar el registro en el formulario:",
            error,
          );
        }
      },
      (error) => {
        console.error("Error de geolocalización:", error);
      },
      opcionesGeolocalizacion,
    );
  }
}

// Union entre el template y nombre del componente en xml con esta clase.
GeoWidget.template = "geo.GeoWidget";
GeoWidget.props = { ...standardFieldProps };

// Registro del widget nuevo en lista de widgets nativos de odoo.
registry.category("fields").add("geo_location_button", {
  component: GeoWidget,
});
