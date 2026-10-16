# The web CI job builds dist first; compilers are not shipped in the image.
FROM nginx:stable-alpine
ARG REVISION
ARG SOURCE
LABEL org.opencontainers.image.title="Ibex binding viewer"
LABEL org.opencontainers.image.revision=$REVISION
LABEL org.opencontainers.image.source=$SOURCE
COPY deploy/nginx.conf /etc/nginx/nginx.conf
COPY dist/ /usr/share/nginx/html/
RUN test -s /usr/share/nginx/html/version.json
USER nginx
EXPOSE 8080
HEALTHCHECK --interval=15s --timeout=3s --start-period=10s --retries=3 \
  CMD wget -q -O /dev/null http://127.0.0.1:8080/healthz || exit 1
ENTRYPOINT ["nginx", "-g", "daemon off;"]
