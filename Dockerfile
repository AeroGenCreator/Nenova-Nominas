# Descargar imagen de odoo
FROM odoo:19.0

# Utilizamos el usuario root
USER root

# Debug recomendado por odoo / Paquete lenguaje
RUN apt update && apt install -y python3-ipdb ; \
    apt install -y locales \
    && locale-gen en_US.UTF-8 \
    && update-locale LANG=en_US.UTF-8
ENV LANG=en_US.UTF-8
ENV LANGUAGE=en_US:en
ENV LC_ALL=en_US.UTF-8

# Carpeta de 'Custom Addons'
RUN mkdir -p /mnt/extra-addons

# Script de arranque
COPY ./entrypoint.sh /entrypoint.sh

# Cambiar a permiso de ejecución (+x) negar permiso de ejecución(-x)
RUN chmod +x /entrypoint.sh

# Permisos al usuario odoo para 'Addons' y 'Entrypoint'
RUN chown -R odoo:odoo /mnt/extra-addons /entrypoint.sh

# Cambiamos al usuario odoo
USER odoo

# Se ejecuta 'Entrypoint'
ENTRYPOINT ["/entrypoint.sh"]
