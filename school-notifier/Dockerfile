# Imagem base com Java 21
FROM eclipse-temurin:21-jdk AS build

# Define o diretório de trabalho
WORKDIR /app

#Copia tod o subprojeto
COPY . .

RUN chmod +x ./mvnw

# Build da aplicacao
RUN ./mvnw dependency:go-offline -B
RUN ./mvnw mvnw clean package -DskipTests

#-------Runtime stage-------
FROM eclipse-temurin:21-jre
WORKDIR /app

# Copia o JAR gerado
COPY --from=build /app/target/*.jar app.jar

# Expoe a porta do Spring Boot
EXPOSE 8080

# Comando de start
ENTRYPOINT ["java", "-jar", "app.jar"]