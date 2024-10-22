import os
import sys
import psycopg2
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

ENV = os.getenv("ENV", "local")

DB_HOST = "db" if ENV == "docker" else os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "jira_reports_data")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_PORT = os.getenv("DB_PORT", "5432")


def get_connection():
    return psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )

def setup_database():
    with get_connection() as conn:
        with conn.cursor() as cur:
            # Vérifier si les colonnes existent et les supprimer si c'est le cas
            cur.execute("""
                DO $$
                BEGIN
                    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'employees' AND column_name = 'department') THEN
                        ALTER TABLE employees DROP COLUMN department;
                    END IF;
                    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'employees' AND column_name = 'position') THEN
                        ALTER TABLE employees DROP COLUMN position;
                    END IF;
                END $$;
            """)

            # Créer ou mettre à jour la table employees
            cur.execute("""
                CREATE TABLE IF NOT EXISTS employees (
                    id SERIAL PRIMARY KEY,
                    employee_id VARCHAR(50) UNIQUE NOT NULL,
                    full_name VARCHAR(100) NOT NULL,
                    email VARCHAR(100) UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # Créer ou mettre à jour la table employee_weekly_hours
            cur.execute("""
                CREATE TABLE IF NOT EXISTS employee_weekly_hours (
                    id SERIAL PRIMARY KEY,
                    employee_id VARCHAR(50) NOT NULL,
                    week_start_date DATE NOT NULL,
                    total_hours DECIMAL(8, 2) NOT NULL,
                    billable_hours DECIMAL(8, 2) NOT NULL,
                    non_billable_hours DECIMAL(8, 2) NOT NULL,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT fk_employee
                        FOREIGN KEY(employee_id)
                        REFERENCES employees(employee_id)
                        ON DELETE CASCADE,
                    CONSTRAINT unique_employee_week UNIQUE (employee_id, week_start_date)
                );

                CREATE INDEX IF NOT EXISTS idx_employee_week
                ON employee_weekly_hours (employee_id, week_start_date);
            """)

    print("Configuration de la base de données terminée.")

def verify_database():
    with get_connection() as conn:
        with conn.cursor() as cur:
            # Vérifier la structure de la table employees
            cur.execute("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'employees'
                AND column_name IN ('department', 'position');
            """)
            unexpected_columns = cur.fetchall()

            if unexpected_columns:
                print(f"Colonnes inattendues trouvées dans la table employees: {unexpected_columns}")
                print("Exécution de la configuration pour corriger la structure.")
                setup_database()
            else:
                print("La structure de la table employees est correcte.")

            # Vérifier l'existence des tables
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'employees'
                ), EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'employee_weekly_hours'
                );
            """)
            employees_table_exists, hours_table_exists = cur.fetchone()

            # Vérifier l'existence de l'index
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM pg_indexes
                    WHERE indexname = 'idx_employee_week'
                );
            """)
            index_exists = cur.fetchone()[0]

    if employees_table_exists and hours_table_exists and index_exists:
        print("La structure de la base de données est correcte.")
    else:
        print("La structure de la base de données nécessite une mise à jour.")
        setup_database()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--verify":
        verify_database()
    else:
        setup_database()
