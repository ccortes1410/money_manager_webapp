FROM node:18.12.1-bullseye-slim

WORKDIR /usr/src/app

COPY package*.json ./
RUN npm install --omit=dev

COPY . .

EXPOSE 3030

CMD [ "node", "app.js" ]

