# Imagem base com Java 21
FROM eclipse-temurin:21-jdk AS build

# Define o diretório de trabalho
WORKDIR /app

#Copia todo o subprojeto
COPY school-notifier/ ./school-notifier/

WORKDIR /app/school-notifier
RUN chmod +x ./mvnw

# Build da aplicaçao
RUN ./mvnw clean package -DskipTests

#-------Runtime stage-------
FROM eclipse-temurin:21-jre
WORKDIR /app

# Copia o JAR gerado
COPY --from=build /app/school-notifier/target/*.jar app.jar

# Expoe a porta do Spring Boot
EXPOSE 8080

# Comando de start
ENTRYPOINT ["java", "-jar", "app.jar"]