FROM python:3.11-slim

# Evitar que Python escriba archivos .pyc en el disco
ENV PYTHONDONTWRITEBYTECODE 1
# Evitar que Python haga buffer de stdout y stderr
ENV PYTHONUNBUFFERED 1

# Instalar dependencias del sistema requeridas por psycopg2 y Tesseract
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       gcc \
       libpq-dev \
       tesseract-ocr \
       poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Establecer el directorio de trabajo
WORKDIR /app

# Instalar dependencias de Python
COPY requirements.txt /app/
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copiar el proyecto
COPY . /app/

# Exponer el puerto
EXPOSE 8080

# El comando de inicio recolectará estáticos, migrará y luego usará daphne
CMD sh -c "python manage.py collectstatic --noinput && python manage.py migrate && daphne -b 0.0.0.0 -p 8080 config.asgi:application"
