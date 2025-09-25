import os
from dotenv import load_dotenv
import psycopg2

# Charger les variables d'environnement
load_dotenv(dotenv_path='../config/.env.production')  # Utilise .env.production

# Récupérer les informations de connexion
DB_HOST = "db"  # Utilise "db" pour la connexion depuis le conteneur app vers le conteneur db
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_PORT = os.getenv("DB_PORT")
DB_SSLMODE = os.getenv("DB_SSLMODE")

def add_nancy_to_db():
    connection_string = f"dbname={DB_NAME} user={DB_USER} password={DB_PASSWORD} host={DB_HOST} port={DB_PORT}"
    if DB_SSLMODE:
        connection_string += f" sslmode={DB_SSLMODE}"

    # Afficher les paramètres pour le débogage
    print(f"Tentative de connexion avec: host={DB_HOST}, dbname={DB_NAME}, user={DB_USER}")

    with psycopg2.connect(connection_string) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO employees (employee_id, full_name, email)
                VALUES (%s, %s, %s)
                ON CONFLICT (employee_id) DO NOTHING
            """, ('Nancy L. Rodriguez', 'Nancy L. Rodriguez', 'nrodriguez@activis.ca'))
            conn.commit()
    print("Nancy L. Rodriguez a été ajoutée à la base de données.")

if __name__ == "__main__":
    add_nancy_to_db()
