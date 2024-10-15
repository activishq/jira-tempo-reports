import sys
import os

# Ajouter le dossier 'reports' au chemin de recherche des modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'reports')))


import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from reports import JiraTempoReport
from sqlalchemy import text

def main():
    # Connexion à la base de données PostgreSQL
    engine = create_engine('postgresql://report_user:pixelpixel@localhost:5432/company_reports')
    Session = sessionmaker(bind=engine)
    session = Session()

    # Initialisation des rapports
    report = JiraTempoReport()

    # Définir la date de début (1er août du trimestre en cours)
    start_date = datetime.date(2024, 8, 1)

    # Trouver le premier dimanche à partir du 1er août
    start_date += datetime.timedelta(days=(6 - start_date.weekday()))

    # Date actuelle
    current_date = datetime.date.today()

    # Liste des employés
    users = report.jira_report.get_current_users()

    # Itération sur chaque semaine jusqu'à aujourd'hui
    while start_date <= current_date:
        week_start = start_date
        week_end = week_start + datetime.timedelta(days=6)

        for user in users:
            print(f"Traitement de l'utilisateur : {user}")
            logged_hours = report.get_logged_time(week_start, week_end, user)
            leaked_hours = report.get_leaked_time(week_start, week_end, user)
            billable_hours = report.get_billable_time(week_start, week_end, user)
            billable_ratio = report.get_billable_ratio(week_start, week_end, user)

            # Conversion des types avant l'insertion
            params = {
                'employee_name': user,
                'week_start': week_start,
                'week_end': week_end,
                'worked_hours': float(logged_hours),
                'billable_hours': float(billable_hours),
                'non_billable_hours': float(leaked_hours),
                'billable_ratio': float(billable_ratio)
            }

            session.execute(
                text("""
                    INSERT INTO weekly_reports (employee_name, week_start, week_end, worked_hours, billable_hours, non_billable_hours, billable_ratio)
                    VALUES (:employee_name, :week_start, :week_end, :worked_hours, :billable_hours, :non_billable_hours, :billable_ratio)
                """), params
            )

        # Passer à la semaine suivante
        start_date += datetime.timedelta(days=7)

    # Valider les transactions dans la base de données
    session.commit()

if __name__ == "__main__":
    main()
