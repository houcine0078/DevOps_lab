# 📝 NoteApp - Plateforme DevOps & Task Management

![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2CA5E0?style=for-the-badge&logo=docker&logoColor=white)
![Nginx](https://img.shields.io/badge/Nginx-009639?style=for-the-badge&logo=nginx&logoColor=white)

NoteApp est une application Full-Stack d'entreprise conçue pour démontrer une architecture moderne, sécurisée et entièrement conteneurisée. Elle implémente les meilleures pratiques DevOps, incluant un build Multi-Stage, un réseau isolé, et une authentification JWT avec contrôle d'accès basé sur les rôles (RBAC).

---

## 🏛️ Architecture de l'Infrastructure

Le projet repose sur une architecture microservices orchestrée par Docker Compose. Le schéma ci-dessous illustre le flux de données et la ségrégation des conteneurs :

```mermaid
graph TD
    Client([💻 Navigateur Web]) -->|HTTP / Port 80| Nginx[🖥️ Frontend: Nginx + React SPA]
    
    subgraph "Réseau Interne Docker (Isolé)"
        Nginx -->|Requêtes API / Port 8000| API[⚙️ Backend: Flask API + JWT]
        API <-->|Requêtes SQL / Port 5432| DB[(🗄️ PostgreSQL)]
    end

    Watchtower([🔄 Watchtower]) -.->|Surveille & Met à jour| Nginx
    Watchtower -.->|Surveille & Met à jour| API

sequenceDiagram
    participant U as Utilisateur
    participant F as Frontend (React)
    participant A as API (Flask)
    participant D as Base de Données

    U->>F: Saisie Identifiants
    F->>A: POST /api/login
    A->>D: Vérification Hash (Bcrypt)
    D-->>A: User valide + Rôle (Admin/User)
    A-->>F: Retourne Token JWT
    F->>F: Stockage Token (LocalStorage)
    
    U->>F: Demande d'accès aux utilisateurs
    F->>A: GET /api/users (Header: Bearer Token)
    A->>A: Décodage JWT & Vérification Rôle
    alt Si Rôle == Admin
        A-->>F: Retourne la liste (200 OK)
    else Si Rôle == User
        A-->>F: Accès Refusé (403 Forbidden)
    end

DevOps_lab/
├── frontend/                   # Interface Utilisateur (React)
│   ├── src/                    # Code source React (App.jsx, main.jsx...)
│   ├── Dockerfile              # Build Multi-Stage (Node 20 -> Nginx)
│   ├── nginx.conf              # Configuration de routage SPA
│   └── package.json            # Dépendances NPM
├── app.py                      # Cœur de l'API RESTful Python/Flask
├── test_app.py                 # Tests automatisés (Pytest avec Mocking JWT)
├── requirements.txt            # Dépendances Python
├── Dockerfile                  # Build du backend Python
├── docker-compose.yml          # Orchestration des services
└── README.md                   # Documentation technique
