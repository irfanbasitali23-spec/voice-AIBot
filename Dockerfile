FROM node:20-alpine

WORKDIR /app

# Install build dependencies for better-sqlite3
RUN apk add --no-cache python3 make g++

COPY package*.json ./
RUN npm ci --only=production

COPY . .

# Create data directory
RUN mkdir -p data logs

# Seed the database
RUN npm run seed

EXPOSE 3000

CMD ["npm", "start"]
