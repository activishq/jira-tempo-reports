import os
from dotenv import load_dotenv
import psycopg2

# Charger les variables d'environnement (si non déjà fournies par env_file Docker)
load_dotenv(dotenv_path='../config/.env.production')

# Récupérer les informations de connexion depuis l'environnement
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_PORT = os.getenv("DB_PORT")
DB_SSLMODE = os.getenv("DB_SSLMODE")

EMPLOYEES_TO_REMOVE = ['Benoit Leboucher']
EMPLOYEE_TO_ADD = {
    'employee_id': 'Patrick McKenzie Pirrus',
    'full_name': 'Patrick McKenzie Pirrus',
    'email': 'pmckenziepirrus@activis.ca',
}


def update_employees():
    connection_string = f"dbname={DB_NAME} user={DB_USER} password={DB_PASSWORD} host={DB_HOST} port={DB_PORT}"
    if DB_SSLMODE:
        connection_string += f" sslmode={DB_SSLMODE}"

    print(f"Tentative de connexion avec: host={DB_HOST}, dbname={DB_NAME}, user={DB_USER}")

    with psycopg2.connect(connection_string) as conn:
        with conn.cursor() as cur:
            # 1. État avant
            cur.execute("SELECT employee_id FROM employees WHERE employee_id = ANY(%s)", (EMPLOYEES_TO_REMOVE,))
            found = [row[0] for row in cur.fetchall()]
            print(f"Employés à supprimer trouvés en DB: {found}")

            # 2a. Supprimer les données liées dans les tables sans CASCADE
            for table in ("target", "availability", "employee_weekly_hours"):
                cur.execute(
                    f"DELETE FROM {table} WHERE employee_id = ANY(%s)",
                    (EMPLOYEES_TO_REMOVE,),
                )
                print(f"Lignes supprimées dans {table}: {cur.rowcount}")

            # 2b. Suppression des employés
            cur.execute(
                "DELETE FROM employees WHERE employee_id = ANY(%s)",
                (EMPLOYEES_TO_REMOVE,),
            )
            print(f"Lignes supprimées dans employees: {cur.rowcount}")

            # 3. Ajout du nouvel employé
            cur.execute(
                """
                INSERT INTO employees (employee_id, full_name, email)
                VALUES (%(employee_id)s, %(full_name)s, %(email)s)
                ON CONFLICT (employee_id) DO NOTHING
                """,
                EMPLOYEE_TO_ADD,
            )
            print(f"Lignes insérées pour {EMPLOYEE_TO_ADD['full_name']}: {cur.rowcount}")

            # 4. Vérification finale
            cur.execute("SELECT employee_id FROM employees ORDER BY employee_id")
            current = [row[0] for row in cur.fetchall()]
            print("\nListe finale des employés en DB:")
            for emp in current:
                print(f"  - {emp}")

        conn.commit()

    print("\nMise à jour des employés terminée avec succès.")


if __name__ == "__main__":
    update_employees()
