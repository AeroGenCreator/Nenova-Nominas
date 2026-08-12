/** @odoo-module **/

/*
* Documentación oficial - extender JS (campos). 
* https://www.odoo.com/documentation/19.0/developer/howtos/javascript_field.html
* El decorador '@' en importaciones de JS apunta al 'root folder src'
*
* Esta extensión pretende forzar un formato monetario de 4 digitos decimales.
* Ej: $ 1,000.0000 -> Buscando presición en las nóminas.
*/

// Importar registry -> Extender componente backend.
// El JS del campo que se desea extender.
import { registry } from "@web/core/registry";
import { FloatField, floatField } from "@web/views/fields/float/float_field";
import { formatFloat } from "@web/views/fields/formatters";

class CustomMonetaryFloat extends FloatField {

    // Se modifica únicamente metodo de formato.
    get formattedValue() {
        if (
            // Si no hay valores en el campo dejar vacio.
            this.props.record.data[this.props.name] === false ||
            this.props.record.data[this.props.name] === null 
        ) {
            return "";
        } else {
            // De lo contrario se formatea el número.
            const value = this.props.record.data[this.props.name] || 0;

            const formattedFloat = formatFloat(value, {
                    digits: this.props.digits || [16, 2],
                    thousandsSep: ",",
                    decimalPoint: ".",
            });

            return `$ ${formattedFloat}`;
        }
    }
}

export const customMonetaryFloat = {
    ...floatField,
    component: CustomMonetaryFloat,
    displayName: "Custom Monetary Float",
    supportedTypes: ["float"],
};

registry.category("fields").add("custom_monetary_float", customMonetaryFloat);
