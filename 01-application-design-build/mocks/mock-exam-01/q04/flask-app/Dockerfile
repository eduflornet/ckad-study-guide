# Base image
FROM python:3.11-slim AS builder

# Set working directory
WORKDIR /app

# Copiar solo requirements para instalar dependencias
COPY requirements.txt .

# Instalar dependencias con versiones específicas y sin cache
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Etapa 2: Imagen final minimalista
FROM python:3.11-slim

WORKDIR /app

# Copiar solo lo necesario desde la etapa anterior
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copiar el archivo de aplicación
COPY app.py .

# Exponer el puerto
EXPOSE 5000

# Comando de ejecución
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
