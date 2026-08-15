FROM node:18-slim

# Directorio de trabajo
WORKDIR /usr/src/app

# Copiar package.json y package-lock.json (si existe)
COPY package*.json ./

# Instalar dependencias de producción
RUN npm install --omit=dev

# Copiar el código fuente
COPY . .

# Exponer el puerto de la API (4000)
EXPOSE 4000

# Comando para iniciar el gateway
CMD ["node", "src/index.js"]
