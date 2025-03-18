# docker build -f Dockerfile -t p0w3r/fundus_murag_frontend:<version> .
# docker push p0w3r/fundus_murag_frontend:<version>

# STAGE 1: BUILD REACT APP
FROM node:23.10-alpine AS build

WORKDIR /app

ENV NODE_ENV=production

COPY package.json package-lock.json ./
RUN npm ci --include=dev

COPY . .

RUN npm run build

# STAGE 2: BUILD IMAGE
FROM nginx:stable-alpine

# Copy built files
COPY --from=build /app/dist /usr/share/nginx/html

COPY nginx.conf /etc/nginx/conf.d/default.conf.template
COPY entrypoint.sh /entrypoint.sh

RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
