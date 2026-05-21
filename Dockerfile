FROM node:20-alpine

WORKDIR /app

# Install dependencies first (cached layer)
COPY package*.json ./
RUN npm ci --omit=dev --no-audit --no-fund

# Copy application code
COPY server.js ./

# Cloud Run injects PORT; default to 8080 for local runs
ENV PORT=8080
EXPOSE 8080

# Run as non-root user for security
USER node

CMD ["node", "server.js"]
