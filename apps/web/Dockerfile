FROM node:20-alpine

WORKDIR /app

ENV NODE_ENV=production

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build && chown -R node:node /app

USER node

EXPOSE 3000

CMD ["npm", "run", "start"]
