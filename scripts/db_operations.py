import os
import psycopg2
from dotenv import load_dotenv
import pandas as pd
import datetime

load_dotenv()

def get_db_connection():
    return psycopg2.connect(
        dbname=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT')
    )

def insert_data_to_db(data: pd.DataFrame):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            for _, row in data.iterrows():
                # Insérer ou mettre à jour l'employé
                cur.execute("""
                    INSERT INTO employees (employee_id, full_name, email)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (employee_id) DO NOTHING
                """, (row['user'], row['user'], f"{row['user'].replace(' ', '').lower()}@example.com"))

                # Insérer ou mettre à jour les heures hebdomadaires
                cur.execute("""
                    INSERT INTO employee_weekly_hours
                    (employee_id, week_start_date, total_hours, billable_hours, non_billable_hours)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (employee_id, week_start_date)
                    DO UPDATE SET
                        total_hours = EXCLUDED.total_hours,
                        billable_hours = EXCLUDED.billable_hours,
                        non_billable_hours = EXCLUDED.non_billable_hours,
                        last_updated = CURRENT_TIMESTAMP
                """, (row['user'], row['week_start'], row['total_hours'],
                      row['billable_hours'], row['non_billable_hours']))

            conn.commit()
    print("Données insérées avec succès dans la base de données.")

def verify_data_in_db(start_date: datetime, end_date: datetime):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Vérifiez le nombre total d'enregistrements pour la période spécifiée
            cur.execute("""
                SELECT COUNT(*)
                FROM employee_weekly_hours
                WHERE week_start_date BETWEEN %s AND %s
            """, (start_date, end_date))
            total_records = cur.fetchone()[0]
            print(f"Nombre total d'enregistrements pour la période: {total_records}")

            # Vérifiez le nombre d'employés uniques pour la période spécifiée
            cur.execute("""
                SELECT COUNT(DISTINCT employee_id)
                FROM employee_weekly_hours
                WHERE week_start_date BETWEEN %s AND %s
            """, (start_date, end_date))
            unique_employees = cur.fetchone()[0]
            print(f"Nombre d'employés uniques pour la période: {unique_employees}")

            # Affichez quelques enregistrements pour vérification
            cur.execute("""
                SELECT employee_id, week_start_date, total_hours, billable_hours, non_billable_hours
                FROM employee_weekly_hours
                WHERE week_start_date BETWEEN %s AND %s
                LIMIT 5
            """, (start_date, end_date))
            print("\nExemples d'enregistrements pour la période:")
            for record in cur.fetchall():
                print(record)
