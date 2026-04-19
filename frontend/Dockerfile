# Frontend Dockerfile - Optimized for China
FROM node:18-alpine

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Use Chinese npm mirror (Taobao) for faster downloads
RUN npm config set registry https://registry.npmmirror.com \
    && npm ci --prefer-offline

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Expose port
EXPOSE 3000

# Start the Next.js server
CMD ["npm", "start"]
