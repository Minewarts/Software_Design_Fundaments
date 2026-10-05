# Estructura de aplicación Java

Esqueleto inicial de una aplicación Java con organización por capas y estructura Maven.
El paquete `com.example.app` es un marcador; cámbialo por el paquete de tu proyecto.

```text
.
├── docs/                         # Documentación y diagramas
├── scripts/                      # Scripts auxiliares de desarrollo
├── src/
│   ├── main/
│   │   ├── java/com/example/app/
│   │   │   ├── config/           # Configuración de la aplicación
│   │   │   ├── controller/       # Entrada y manejo de solicitudes
│   │   │   ├── dto/              # Objetos para transferir datos
│   │   │   ├── exception/        # Excepciones y manejo de errores
│   │   │   ├── model/            # Entidades y modelos del dominio
│   │   │   ├── repository/       # Acceso y persistencia de datos
│   │   │   ├── service/          # Lógica de negocio
│   │   │   └── util/             # Utilidades compartidas
│   │   └── resources/
│   │       ├── db/migration/     # Migraciones de base de datos
│   │       ├── static/           # Recursos estáticos
│   │       └── templates/        # Plantillas de vistas
│   └── test/
│       ├── java/com/example/app/
│       │   ├── controller/       # Pruebas de controladores
│       │   ├── repository/       # Pruebas de repositorios
│       │   └── service/          # Pruebas de servicios
│       └── resources/            # Datos y configuración para pruebas
└── pom.xml                       # Configuración del proyecto Maven
```

Los archivos `.gitkeep` conservan las carpetas vacías en Git. No se ha añadido una
implementación ni dependencias de framework; estas pueden incorporarse según los
requisitos de la aplicación.
