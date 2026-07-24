#!/usr/bin/env bash
set -e

# Variables cargadas desde el docker-compose.yml
: "${DB_HOST}"
: "${POSTGRES_USER}"
: "${POSTGRES_DB}"
: "${POSTGRES_PASSWORD}"

# Se crea la variable de entorno 'PGPASSWORD' <- Forzoso que sea sobre esta variable de Contraseña
export PGPASSWORD="$POSTGRES_PASSWORD"

# Se muestra en pantalla la configuracion de inicio Database
echo "Configurando instancia:"
echo "Database HOST=$DB_HOST"
echo "Database USER=$POSTGRES_USER"
echo "Database NAME=$POSTGRES_DB"

echo "Conexion a PostegreSQL..."
# Bucle de validacion "Tanto until como while" son validos
# Se valida el 'Host' y el 'Usuario' a traves de pg_isready
# 'pg_isready' elemento de PostgreSQL para validar disponibilidad PostgreSQL
# La respuesta se direcciona a la papelera tanto 'logs' como 'errores'
until pg_isready -h "$DB_HOST" -U "$POSTGRES_USER" >/dev/null 2>&1;
do
    echo "Esperando Apertura con PostgreSQL."
    sleep 2
done
    echo "PostgreSQL listo para aceptar conexion."

# El comando se encierra entre () iniciando con el simbolo de bash $
# Query al esquema de bases de datos, se guarda como variable:
ODOO_DB_EXISTS=$(psql -h "$DB_HOST" -U "$POSTGRES_USER" -tAc "SELECT 1 FROM pg_database WHERE datname='$POSTGRES_DB'")

# Condicionales en Linux Bash
if [[ "$ODOO_DB_EXISTS" != "1" ]]; then
    echo "Creación... Base de datos: $POSTGRES_DB."
    # 'createdb' ejecuta la creacion de db SQL evitando un query como; psql -c "CREATE DATABASE \"$POSTGRES_DB\";"
    createdb -h "$DB_HOST" -U "$POSTGRES_USER" "$POSTGRES_DB"
fi

# Query al esquema de odoo para confirmar su existencia
ODOO_SCHEMA_EXISTS=$(psql -h "$DB_HOST" -U "$POSTGRES_USER" -tAc "SELECT 1 FROM information_schema.tables WHERE table_name='ir_module_module';")

if [[ "$ODOO_SCHEMA_EXISTS" != "1" ]]; then
    # No existe esquema; se crea
    echo "Intalacion; Paquete base odoo - Creacion del Esquema"
    exec odoo -c /etc/odoo/odoo.conf -d "$POSTGRES_DB" -i base
else
    echo "!El esquema inicial de odoo ya existe! Continuando..."
    if [[ "$UPDATE_MODULES" == "true" ]]; then
        # Existe el esquema pero se quieren actualizar modulos
        echo "Bandera de actualizacion especificada en el compose... Actualizando modulos..."
        exec odoo -c /etc/odoo/odoo.conf -d "$POSTGRES_DB" -u
    else
        # No se desea actualización; inicio simple
        echo "Inicializacion Simple (No hay petición de actualización)"
        exec odoo -c /etc/odoo/odoo.conf -d "$POSTGRES_DB"
    fi
fi
