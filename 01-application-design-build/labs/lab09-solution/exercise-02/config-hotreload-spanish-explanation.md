Este manifiesto de Kubernetes implementa un sistema de hot reload de configuración usando una ConfigMap, múltiples contenedores en un Pod, y un volumen compartido. Aquí te explico cada componente y cómo interactúan:

🧾 1. ConfigMap: app-config
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  config.yaml: |
    app:
      name: "hot-reload-demo"
      version: "1.0.0"
      log_level: "INFO"
      max_connections: 100
      timeout: 30
      features:
        feature_a: true
        feature_b: false
        feature_c: true
```
¿Qué hace?
Define un archivo de configuración en formato YAML.

Contiene parámetros de una aplicación como nivel de log, número máximo de conexiones, tiempo de espera y activación de funcionalidades.

Se monta como volumen en el contenedor config-manager para copiarlo al volumen compartido.

📦 2. Volúmenes
```yaml
volumes:
- name: initial-config
  configMap:
    name: app-config
- name: shared-config
  emptyDir: {}
```
initial-config: contiene la configuración inicial desde la ConfigMap.

shared-config: volumen temporal compartido entre los contenedores para leer/escribir el archivo config.yaml.

🧠 3. Contenedor app
Este es el contenedor principal que simula una aplicación que recarga su configuración dinámicamente.

Funciones clave:
Lee /shared-config/config.yaml.

Detecta cambios en el archivo usando os.stat().st_mtime.

Si hay cambios, recarga la configuración y la imprime.

Simula trabajo usando los parámetros actuales (log_level, max_connections).

Se ejecuta en bucle, verificando cambios cada 5 segundos.

🛠️ 4. Contenedor config-manager
Este contenedor simula un gestor de configuración dinámica.

Funciones clave:
Copia la configuración inicial desde /initial-config/config.yaml al volumen compartido.

Cada 20 segundos:

Lee la configuración actual.

Modifica aleatoriamente parámetros como log_level, max_connections y features.

Añade una marca de tiempo last_update.

Escribe la nueva configuración en /shared-config/config.yaml.

✅ 5. Contenedor config-validator
Este contenedor valida la configuración cada 3 segundos.

Reglas de validación:
max_connections debe estar entre 10 y 500.

log_level debe ser uno de: DEBUG, INFO, WARN, ERROR.

Funciones clave:
Detecta cambios en el archivo de configuración.

Imprime si la configuración es válida o muestra errores.

🔄 ¿Qué demuestra este diseño?
Este ejemplo muestra cómo implementar hot reload de configuración en Kubernetes sin reiniciar contenedores:

Componente	        Rol
ConfigMap	        Fuente inicial de configuración
config-manager	    Simula cambios dinámicos
app	                Recarga configuración en tiempo real
config-validator	Verifica que los cambios sean válidos

