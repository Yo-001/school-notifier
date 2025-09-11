# Imagem base com Java 21
FROM eclipse-temurin:21-jdk AS build

# Define o diretório de trabalho
WORKDIR /app

COPY . .

RUN mvnq.cmd clean package -DskipTests

FROM eclipse-temurin:21-jre
WORKDIR /app

COPY --from=build /app/target/school-notifier-0.0.1-SNAPSHOT.jar app.jar

# Expoe a porta do Spring Boot
EXPOSE 8080

# Comando de start
ENTRYPOINT ["java", "-jar", "app.jar"]