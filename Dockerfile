# Utilisation d'une image de base officielle et très légère
FROM python:3.12-slim

# Création d'un utilisateur système non-root nommé "appuser"
RUN useradd -m appuser

# Définition du répertoire de travail dans le conteneur
WORKDIR /app

# Copie des dépendances en premier pour optimiser le cache Docker
COPY requirements.txt .

# Installation des dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Copie du code source de l'API
COPY app.py .

# Attribution des droits du dossier à l'utilisateur non-root
RUN chown -R appuser:appuser /app

# Bascule sur l'utilisateur sécurisé
USER appuser

# Documentation du port exposé
EXPOSE 8000

# Commande de lancement de l'API
CMD ["python", "app.py"]
