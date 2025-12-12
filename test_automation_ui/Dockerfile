# syntax=docker/dockerfile:1

# This Dockerfile assumes a standard React app created with CRA or Vite lives here.
# If the UI is not yet implemented, this file serves as a template for future iterations.

# Build stage
FROM node:20-alpine AS build
WORKDIR /app
# Install dependencies
COPY package*.json /app/
RUN npm ci
# Copy the rest and build
COPY . /app
# Pass API base URL at build time if needed for static embedding
ARG REACT_APP_API_BASE_URL
ENV REACT_APP_API_BASE_URL=${REACT_APP_API_BASE_URL}
RUN npm run build

# Runtime stage (nginx)
FROM nginx:alpine
# Copy build artifacts
COPY --from=build /app/build /usr/share/nginx/html
# Basic nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=5s --retries=5 \
 CMD wget -qO- http://localhost:3000/ > /dev/null || exit 1

CMD ["nginx", "-g", "daemon off;"]
