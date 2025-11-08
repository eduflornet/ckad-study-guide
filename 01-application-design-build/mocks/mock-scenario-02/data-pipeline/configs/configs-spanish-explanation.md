## **ingestion-config.json**

🧩 Estructura general
El objeto contiene una lista llamada "sources" con tres elementos: users, transactions y products.

Cada fuente tiene detalles sobre cómo conectarse a una API, qué formato de datos espera, cuántos datos tomar, y cómo manejar errores.

🔍 Detalle de cada fuente
1. Users
URL: https://jsonplaceholder.typicode.com/users (API pública de prueba)

Formato: JSON

Fallback: Si la API falla, usa datos de muestra (fallback_to_sample: true)

Tamaño de muestra: 1000 registros

Headers: Añade un User-Agent personalizado

2. Transactions
URL: https://api.example.com/transactions (API ficticia)

Formato: JSON

Fallback: Usa datos de muestra si falla

Tamaño de muestra: 5000 registros

Headers: Incluye un token de autorización (ficticio)

Params: Limita la consulta a 5000 transacciones

3. Products
URL: https://fakestoreapi.com/products (API pública de productos)

Formato: JSON

Fallback: Usa datos de muestra si falla

Tamaño de muestra: 100 productos

⚙️ ¿Para qué sirve?
Este tipo de configuración se usa en sistemas que:

Extraen datos de múltiples APIs

Normalizan y procesan la información

Manejan errores automáticamente usando datos de muestra

Preparan datos para análisis, visualización o almacenamiento

## **validation-config.json**

Este bloque de configuración define cómo deben validarse y limpiarse tres archivos de datos: users, transactions y products. Es típico en sistemas de procesamiento de datos o pipelines ETL (Extract, Transform, Load). Aquí te explico cada parte:

🧼 ¿Qué hace este objeto?
Establece reglas para:

✅ Validar la estructura y contenido de los archivos

🧹 Limpiar y transformar los datos

🔍 Detectar errores como duplicados o campos faltantes

📁 Archivos definidos
1. Users
Esquema (schema):
    -Debe ser un array de objetos
    -Cada objeto debe tener id, name, email
    -id: entero, name: texto, email: texto con formato de email

Reglas (rules):
    -Mínimo 10 registros
    -Campos obligatorios: id, name, email
    -Verifica duplicados usando el campo id

Limpieza (cleaning):
    -Elimina valores nulos
    -Estandariza nombres de campos

Aplica transformaciones:
    -name: elimina espacios (trim)
    -email: convierte a minúsculas (lowercase)

2. Transactions
Reglas:
    -Mínimo 100 registros
    -Campos obligatorios: id, user_id, amount
    -Verifica duplicados por id

Limpieza:
    -No elimina nulos
    -Estandariza nombres de campos

3. Products
Reglas:
    -Mínimo 10 registros
    -Campos obligatorios: id, title
    -Verifica duplicados por id

Limpieza:
    -Elimina nulos
    -Estandariza campos
    -Aplica transformación:
        -title: elimina espacios (trim)
{
    🧠 ¿Para qué sirve?
Este tipo de configuración es útil para:
    -Automatizar la validación de datos antes de cargarlos en una base de datos 
    -Detectar errores comunes como duplicados o campos vacíos
    -Preparar datos limpios para análisis, visualización o machine learning


## **transformation-config.json**

Este bloque de configuración define una serie de transformaciones de datos que se aplican a tres conjuntos de archivos: users, transactions y products. Es típico en pipelines de procesamiento de datos, especialmente en entornos ETL (Extract, Transform, Load) o de integración de datos.

🔧 ¿Qué hace este objeto?
Aplica transformaciones como:
    -Filtrado de registros
    -Agregación de datos
    -Enriquecimiento con nuevos campos calculados

📁 Transformaciones por archivo
1. Users
Filtro (filter):
    -Solo se conservan los usuarios con active = true
    -Enriquecimiento (enrich):
        -full_name: concatena el campo name (aunque parece redundante si solo hay un campo)
        -processed_at: agrega una marca de tiempo del momento de procesamiento
        -user_category: añade un campo constante con valor "standard"

2. Transactions
-Filtro:
    -Solo se conservan transacciones con:
    -status = "completed"
    -amount > 0

Agregación (aggregate):
    -Agrupa por user_id

Calcula:
    -amount: suma, media y conteo
    -id: conteo de transacciones

Enriquecimiento:
    -Añade campo processed_at con marca de tiempo

3. Products
Enriquecimiento:
    processed_at: marca de tiempo
    category_normalized: campo constante con valor "general"

🧠 ¿Para qué sirve?
Este tipo de configuración permite:

-Filtrar datos relevantes antes de analizarlos
-Resumir información mediante agregaciones
-Añadir contexto o metadatos útiles para trazabilidad o categorización
Es ideal para preparar datos antes de cargarlos en una base de datos, visualizarlos en dashboards o alimentar modelos de machine learning.