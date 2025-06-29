import os
from dotenv import load_dotenv
import psycopg2

# Charger les variables d'environnement
load_dotenv(dotenv_path='../config/.env.production')  # Utilise .env.production

# Récupérer les informations de connexion
# Pour production, utiliser les vraies valeurs de DB_HOST depuis .env.production
DB_HOST = os.getenv("DB_HOST", "db")  # Fallback sur "db" si pas défini
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_PORT = os.getenv("DB_PORT")
DB_SSLMODE = os.getenv("DB_SSLMODE")

def add_david_to_db():
    connection_string = f"dbname={DB_NAME} user={DB_USER} password={DB_PASSWORD} host={DB_HOST} port={DB_PORT}"
    if DB_SSLMODE:
        connection_string += f" sslmode={DB_SSLMODE}"

    # Afficher les paramètres pour le débogage
    print(f"Tentative de connexion avec: host={DB_HOST}, dbname={DB_NAME}, user={DB_USER}")

    try:
        with psycopg2.connect(connection_string) as conn:
            with conn.cursor() as cur:
                # Vérifier si David existe déjà
                cur.execute("""
                    SELECT COUNT(*) FROM employees WHERE employee_id = %s
                """, ('David Chabot',))

                count = cur.fetchone()[0]

                if count > 0:
                    print("David Chabot existe déjà dans la base de données.")
                    return

                # Ajouter David Chabot
                cur.execute("""
                    INSERT INTO employees (employee_id, full_name, email)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (employee_id) DO NOTHING
                """, ('David Chabot', 'David Chabot', 'dchabot@activis.ca'))

                conn.commit()
                print("David Chabot a été ajouté à la base de données.")

    except Exception as e:
        print(f"Erreur lors de l'ajout de David Chabot : {e}")
        raise

if __name__ == "__main__":
    add_david_to_db()
