import os
from dotenv import load_dotenv

load_dotenv(dotenv_path='../.env')  # Utilise .env.production

# Récupérer les informations de connexion
DB_HOST = "db"  # Utilise "db" pour la connexion depuis le conteneur app vers le conteneur db
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_PORT = os.getenv("DB_PORT")
DB_SSLMODE = os.getenv("DB_SSLMODE")
DB_SSLROOTCERT = os.getenv("DB_SSLMODE")

JIRA_USERNAME = os.getenv("JIRA_USERNAME")
JIRA_API_KEY = os.getenv("JIRA_API_KEY")

TEMPO_ACCESS_TOKEN = os.getenv("TEMPO_ACCESS_TOKEN")
