Este manifiesto de Kubernetes define un Pod llamado volume-performance que contiene tres contenedores diseñados para comparar el rendimiento de escritura entre dos tipos de volúmenes: emptyDir tradicional (en disco) y emptyDir en memoria (tmpfs). Aquí te explico cada parte en detalle:

🧱 Estructura general

```yaml
apiVersion: v1
kind: Pod
metadata:
name: volume-performance
```
  Crea un Pod con tres contenedores que comparten volúmenes para realizar pruebas de rendimiento de escritura y lectura.

📦 Volúmenes definidos
```yaml
volumes:
- name: emptydir-storage
  emptyDir: {}

- name: memory-storage
  emptyDir:
    medium: Memory
    sizeLimit: 100Mi
```
emptydir-storage	Disco local	Volumen temporal en el nodo, respaldado por almacenamiento físico
memory-storage	    Memoria RAM	Volumen temporal en RAM (tmpfs), más rápido pero volátil

✍️ Contenedor 1: emptydir-writer
Objetivo:
Medir el tiempo que tarda en escribir 1000 archivos en el volumen emptyDir tradicional.

Detalles:
Usa date +%s para medir el tiempo de inicio y fin.

Escribe 1000 archivos en /emptydir-vol/test-*.txt.

Calcula y muestra el tiempo total de escritura.

Se mantiene activo con while true; do sleep 60; done.

⚡ Contenedor 2: memory-writer
Objetivo:
Medir el rendimiento de escritura en un volumen respaldado por memoria (tmpfs).

Detalles:
Igual que el anterior, pero escribe en /memory-vol/.

Muestra el uso de disco con df -h /memory-vol.

También se mantiene activo para permitir inspección.

🔍 Contenedor 3: reader
Objetivo:
Leer estadísticas de ambos volúmenes.

Detalles:
Espera 10 segundos para que los escritores generen archivos.

Cada 15 segundos:

Cuenta archivos con ls | wc -l.

Mide uso de espacio con du -sh.

Imprime estadísticas de ambos volúmenes.

🧪 ¿Qué se está probando?
Este Pod compara el rendimiento de dos tipos de almacenamiento temporal:


emptyDir Disco	    Más lento
emptyDir:Memory	    RAM	Más rápido

🧠 ¿Por qué es útil?
Benchmarking: ayuda a decidir qué tipo de volumen usar según el rendimiento requerido.

Diagnóstico: permite observar cómo se comporta el sistema bajo carga de escritura.

Educativo: muestra cómo usar volúmenes compartidos entre contenedores.