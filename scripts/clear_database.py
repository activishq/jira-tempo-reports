import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()

ENV = os.getenv("ENV", "local")

DB_HOST = "db" if ENV == "docker" else os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "jira_reports_data")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_PORT = os.getenv("DB_PORT", "5432")

def clear_database():
    conn = psycopg2.connect(
        dbname=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT')
    )

    with conn.cursor() as cur:
        cur.execute("TRUNCATE TABLE employee_weekly_hours;")
        cur.execute("TRUNCATE TABLE employees CASCADE;")
        conn.commit()

    conn.close()
    print("Le contenu de la base de données a été effacé.")

if __name__ == "__main__":
    confirmation = input("Êtes-vous sûr de vouloir effacer tout le contenu de la base de données ? (oui/non): ")
    if confirmation.lower() == 'oui':
        clear_database()
    else:
        print("Opération annulée.")
