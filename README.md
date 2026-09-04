# 📝 NoteApp - Plateforme DevOps de Gestion de Tâches

NoteApp est une application Full-Stack d'entreprise conçue pour démontrer une architecture moderne, sécurisée et entièrement conteneurisée. Elle intègre un système d'authentification par jeton (JWT), un contrôle d'accès basé sur les rôles (RBAC), et un déploiement orchestré via Docker.

## ✨ Fonctionnalités Principales

* **Sécurité & Authentification (JWT) :** Connexion sécurisée avec génération de tokens pour protéger les endpoints de l'API.
* **Contrôle d'Accès (RBAC) :** 
  * **Administrateur :** Vision globale de toutes les tâches, gestion des utilisateurs, et accès au panneau d'administration.
  * **Utilisateur Standard :** Espace cloisonné limité à la création et gestion de ses propres tâches.
* **CRUD Complet :** Création, lecture, mise à jour (statut) et suppression des notes.
* **Gestion de Profil :** Interface sécurisée de modification des mots de passe.
* **Déploiement Multi-Stage :** Frontend React compilé et distribué via un serveur web Nginx ultra-léger.

## 🛠️ Stack Technique & DevOps

**Frontend**
* React / Vite
* Tailwind CSS (UI/UX)
* Nginx (Serveur Web de production)

**Backend**
* Python 3 / Flask
* PyJWT & Werkzeug Security (Cryptographie)
* PostgreSQL (Base de données relationnelle)

**Infrastructure & DevOps**
* Docker & Docker Compose (Conteneurisation et Orchestration)
* Watchtower (Mise à jour continue)
* Architecture réseau isolée entre le client, l'API et la base de données.

## 🚀 Guide de Démarrage Rapide (Quick Start)

L'application est conçue pour être portable et déployable en quelques minutes sur n'importe quel environnement (Windows, Mac, Linux).

### Prérequis
* [Docker](https://www.docker.com/) installé et en cours d'exécution.
* [Git](https://git-scm.com/) installé.

### Installation

1. **Cloner le dépôt :**
   ```bash
   git clone [https://github.com/houcine0078/DevOps_lab.git](https://github.com/houcine0078/DevOps_lab.git)
   cd DevOps_lab
