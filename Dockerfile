# Utiliser une image Python 3.10 comme image de base
FROM python:3.10-slim

# Définir le répertoire de travail dans le conteneur
WORKDIR /app

ENV PYTHONPATH="${PYTHONPATH}:/app:/app/app"

# Installer les dépendances système nécessaires, y compris PostgreSQL client
RUN apt-get update && apt-get install -y \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copier les fichiers de dépendances et installer les dépendances
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le script d'attente pour la base de données
# COPY scripts /app/scripts

# Copier le reste du code de l'application dans le conteneur
COPY . .

# Exposer les ports Streamlit et API
EXPOSE 8501
EXPOSE 8001

# Lancer le rafraîchisseur de token Tempo, l'API et Streamlit ensemble
CMD ["sh", "-c", "python app/scripts/token_refresher.py & uvicorn app.api:app --host 0.0.0.0 --port 8001 & streamlit run app/main.py --server.port=8501 --server.address=0.0.0.0"]
