import argparse
from datetime import datetime, timedelta
from typing import Tuple, Optional
from reports.combined_reports import JiraTempoReport
from scripts.db_operations import insert_data_to_db, verify_data_in_db

def get_date_range(start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> Tuple[datetime, datetime]:
    if end_date is None:
        end_date = datetime.now().date()

    if start_date is None:
        # Par défaut, on prend la semaine précédente
        start_date = end_date - timedelta(days=7)

    # S'assurer que start_date est un lundi
    while start_date.weekday() != 0:  # 0 représente lundi
        start_date -= timedelta(days=1)

    # S'assurer que end_date est un dimanche
    while end_date.weekday() != 6:  # 6 représente dimanche
        end_date += timedelta(days=1)

    return start_date, end_date

def process_data(start_date: datetime, end_date: datetime):
    jira_tempo_report = JiraTempoReport()
    # Utilisez strftime pour formater la date en YYYY-MM-DD
    weekly_billable_hours = jira_tempo_report.calculate_weekly_billable_hours(
        start_date.strftime("%Y-%m-%d"),
        end_date.strftime("%Y-%m-%d")
    )

    # Assurez-vous que toutes les colonnes nécessaires sont présentes
    if 'non_billable_hours' not in weekly_billable_hours.columns:
        weekly_billable_hours['non_billable_hours'] = 0
    if 'total_hours' not in weekly_billable_hours.columns:
        weekly_billable_hours['total_hours'] = weekly_billable_hours['billable_hours']

    try:
        insert_data_to_db(weekly_billable_hours)
        verify_data_in_db(start_date, end_date)
    except Exception as e:
        print(f"Erreur lors de l'insertion ou de la vérification des données: {e}")

    print(f"Traitement des données terminé pour la période du {start_date} au {end_date}.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Traitement des données Jira-Tempo pour une période spécifique.")
    parser.add_argument("--start", type=str, help="Date de début (format YYYY-MM-DD)", default=None)
    parser.add_argument("--end", type=str, help="Date de fin (format YYYY-MM-DD)", default=None)
    args = parser.parse_args()

    start_date = datetime.strptime(args.start, "%Y-%m-%d") if args.start else None
    end_date = datetime.strptime(args.end, "%Y-%m-%d") if args.end else None

    start_date, end_date = get_date_range(start_date, end_date)
    process_data(start_date, end_date)
