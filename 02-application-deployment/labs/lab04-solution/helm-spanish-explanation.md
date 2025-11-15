Para el examen CKAD, lo esencial de Helm es saber cómo instalar, actualizar y eliminar charts, además de manejar repositorios y valores. Los comandos más usados son helm repo add, helm repo update, helm search, helm install, helm upgrade, helm uninstall y helm get values.

🧭 ¿Qué es Helm?
Helm es el package manager de Kubernetes, similar a apt o yum pero para aplicaciones en clústeres.

Permite empaquetar aplicaciones en charts, que son colecciones de manifiestos YAML parametrizables.

Facilita despliegues repetibles y consistentes, muy útil en CKAD para demostrar gestión de aplicaciones.

📌 Comandos clave para CKAD
🔹 Manejo de repositorios
helm repo add <nombre> <url> → Añadir un repositorio (ej. Bitnami).

helm repo list → Ver repositorios configurados.

helm repo update → Actualizar índices de charts.

helm search repo <chart> → Buscar charts en repositorios locales.

helm search hub <app> → Buscar en Helm Hub (repositorios públicos).

🔹 Instalación y despliegue
helm install <release> <repo/chart> → Instalar un chart (ej. helm install miapp bitnami/wordpress).

helm install <release> ./mi-chart → Instalar un chart local.

helm pull <chart> --untar → Descargar y descomprimir un chart para inspección.

🔹 Actualización y gestión
helm upgrade <release> <chart> → Actualizar un despliegue existente.

Ejemplo: helm upgrade -f values.yaml miapp bitnami/wordpress

helm uninstall <release> → Eliminar un despliegue.

helm get values <release> → Ver valores usados en un despliegue.

helm list → Listar releases instalados en el clúster.

🔹 Creación de charts
helm create <nombre> → Generar la estructura básica de un chart.

helm dependency update → Actualizar dependencias definidas en Chart.yaml.

🎯 Consejos para el examen CKAD
Practica instalar y desinstalar charts rápidamente, ya que el examen es contrarreloj.

Aprende a modificar valores con -f values.yaml o --set clave=valor.

Revisa releases activos con helm list y usa helm get para inspeccionar configuraciones.

Ten claro cómo combinar múltiples archivos de valores en un upgrade (-f archivo1.yaml -f archivo2.yaml).
