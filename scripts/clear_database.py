import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()

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
