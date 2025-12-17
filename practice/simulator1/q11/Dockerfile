# Usa una imagen base de Go
FROM golang:1.22

# Establece la variable de entorno requerida
ENV SUN_CIPHER_ID=5b9c1065-e39d-4a43-a04a-e59bcea3e03f

# Copia el código fuente
WORKDIR /app
COPY main.go .

# Compila el binario
RUN go build -o app main.go

# Comando por defecto
CMD ["./app"]
