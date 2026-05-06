# Usamos Node 20 que es una versión LTS (soporte a largo plazo) y compatible con Vite
FROM node:20-alpine

# Directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiamos los archivos de dependencias
COPY package*.json ./

# Instalamos las dependencias
RUN npm install

# Copiamos el resto del código del frontend
COPY . .

# Exponemos el puerto que usa Vite por defecto
EXPOSE 5173

# Ejecutamos Vite con el flag --host para que Docker pueda redirigir el tráfico
CMD ["npm", "run", "dev", "--", "--host"]