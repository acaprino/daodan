# syntax=docker/dockerfile:1.7
FROM node:20.18.1-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --omit=dev

FROM node:20.18.1-alpine AS runtime
ENV NODE_ENV=production
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY src ./src
USER node
EXPOSE 3000
CMD ["node", "src/server.js"]
