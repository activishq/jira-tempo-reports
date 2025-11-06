import os
from dotenv import load_dotenv, find_dotenv, set_key

load_dotenv(override=True)  # Utilise .env.production

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


TEMPO_CLIENT_ID = os.getenv("TEMPO_CLIENT_ID")
TEMPO_SECRET_ID = os.getenv("TEMPO_SECRET_ID")
TEMPO_REDIRECT_URI = os.getenv("TEMPO_REDIRECT_URI")
TEMPO_ACCESS_TOKEN = os.getenv("TEMPO_ACCESS_TOKEN")
TEMPO_REFRESH_TOKEN = os.getenv("TEMPO_REFRESH_TOKEN")


class EnvUpdater:
    @staticmethod
    def update_tokens(access_token: str, refresh_token: str):
        TEMPO_ACCESS_TOKEN = access_token
        TEMPO_REFRESH_TOKEN = refresh_token
        dotenv_file = find_dotenv()
        set_key(dotenv_file, "TEMPO_ACCESS_TOKEN", access_token)
        set_key(dotenv_file, "TEMPO_REFRESH_TOKEN", refresh_token)
        load_dotenv(override=True)
