# Base liviana y segura de Python basada en Linux Alpine
FROM python:3.11-alpine

# Establecer el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiar primero el manifiesto de dependencias para aprovechar la caché de Docker
COPY requirements.txt .

# Instalar las dependencias de Flask sin almacenar basura temporal de instalación
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo el resto del código del proyecto al contenedor
COPY . .

# Informar el puerto en el que escuchará nuestra aplicación web
EXPOSE 5000

# Comando por defecto para arrancar el backend controlador cuando el contenedor inicie
CMD ["python", "application.py"]