# syntax=docker/dockerfile:1

# Étape 1 : compilation du jar exécutable Spring Boot
FROM eclipse-temurin:17-jdk-alpine-3.24 AS build
WORKDIR /src
COPY . .
# Compilation du JAR seulement, sans les tests, déjà exécutés par la CI
RUN --mount=type=cache,target=/root/.gradle ./gradlew bootJar --no-daemon

# Étape 2 : image d'exécution (JRE seul, utilisateur non root)
FROM eclipse-temurin:17-jre-alpine-3.24
RUN addgroup -S app && adduser -S -D -H -G app app \
    && mkdir /data && chown app:app /data
WORKDIR /app
# bootJar ne produit que le jar exécutable, soit un seul fichier
COPY --from=build /src/build/libs/*.jar app.jar
USER app
EXPOSE 8080
HEALTHCHECK --interval=15s --timeout=3s --start-period=40s --retries=3 \
    CMD wget -q -O /dev/null http://localhost:8080/actuator/health || exit 1
ENTRYPOINT ["java", "-jar", "app.jar"]
