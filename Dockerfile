# Imagem base com Java 21
FROM eclipse-temurin:21-jdk AS build

# Define o diretório de trabalho
WORKDIR /app

# Copia o wrapper e o pom.xml
COPY school-notifier/mvnw .
COPY school-notifier/.mvn .mvn

# Dá permissao de execuçao ao mvnw
RUN chmod +x ./mvnw

#Copia o pom.xml primeiro para aproveitar cache do Docker
COPY school-notifier/pom.xml .

# Faz o download das dependências
RUN ./mvnw dependency:go-offline -B

# Copia o código fonte
COPY school-notifier/src src

# Build da aplicaçao
RUN ./mvnw clean package -DskipTests

# ----------
# Stage 2: runtime image
#-----------
FROM eclipse-temurin:21-jre

WORKDIR /app

#Copia o JAR gerado do estágio anterior
COPY --from=build /app/target/*.jar app.jar

#Expoe a porta pdrao do Spring Boot
EXPOSE 8080

#Comando de start
ENTRYPOINT ["java", "-jar", "app.jar"]