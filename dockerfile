FROM node:18-alpine
WORKDIR /app
COPY src/ ./src/
CMD ["node", "src/app.js"]
