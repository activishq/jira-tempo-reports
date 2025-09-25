import argparse
from datetime import datetime, timedelta, date
from typing import Tuple, Optional
from reports.combined_reports import JiraTempoReport
from scripts.db_operations import insert_data_to_db, verify_data_in_db
import pandas as pd

def get_date_range(start_date: Optional[date] = None, end_date: Optional[date] = None) -> Tuple[date, date]:
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

def process_data(start_date: date, end_date: date):
    jira_tempo_report = JiraTempoReport()

    # Calculer les heures facturables hebdomadaires
    weekly_billable_hours = jira_tempo_report.calculate_weekly_billable_hours(
        start_date.strftime("%Y-%m-%d"),
        end_date.strftime("%Y-%m-%d")
    )

    # Convertir la colonne 'week_start' en datetime
    weekly_billable_hours['week_start'] = pd.to_datetime(weekly_billable_hours['week_start'])

    # Calculer les heures travaillées hebdomadaires
    current_users = jira_tempo_report.jira_report.get_current_users()
    weekly_logged_hours = []

    current_date = start_date
    while current_date <= end_date:
        week_end = current_date + timedelta(days=6)
        week_end = min(week_end, end_date)

        for user in current_users:
            logged_time = jira_tempo_report.get_logged_time(
                current_date.strftime("%Y-%m-%d"),
                week_end.strftime("%Y-%m-%d"),
                user
            )

            if logged_time > 0:
                weekly_logged_hours.append({
                    'user': user,
                    'week_start': pd.to_datetime(current_date),
                    'total_hours': logged_time
                })
            else:
                print(f"Aucune heure enregistrée pour {user} dans la semaine du {current_date}")

        current_date = week_end + timedelta(days=1)

    weekly_logged_hours_df = pd.DataFrame(weekly_logged_hours)

    # Fusionner les données des heures facturables et travaillées
    merged_data = pd.merge(
        weekly_billable_hours,
        weekly_logged_hours_df,
        on=['user', 'week_start'],
        how='outer'
    )

    # Calculer les heures non facturables
    merged_data['non_billable_hours'] = merged_data['total_hours'] - merged_data['billable_hours']

    # S'assurer que toutes les colonnes nécessaires sont présentes et que les valeurs NaN sont remplacées par 0
    merged_data = merged_data.fillna(0)

    # Convertir 'week_start' en date pour l'insertion dans la base de données
    merged_data['week_start'] = merged_data['week_start'].dt.date

    try:
        insert_data_to_db(merged_data)
        verify_data_in_db(start_date, end_date)
    except Exception as e:
        print(f"Erreur lors de l'insertion ou de la vérification des données: {e}")

    print(f"Traitement des données terminé pour la période du {start_date} au {end_date}.")
    print(merged_data.head())  # Affiche les 5 premières lignes pour vérification

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Traitement des données Jira-Tempo pour une période spécifique.")
    parser.add_argument("--start", type=str, help="Date de début (format YYYY-MM-DD)", default=None)
    parser.add_argument("--end", type=str, help="Date de fin (format YYYY-MM-DD)", default=None)
    args = parser.parse_args()

    start_date = datetime.strptime(args.start, "%Y-%m-%d").date() if args.start else None
    end_date = datetime.strptime(args.end, "%Y-%m-%d").date() if args.end else None

    start_date, end_date = get_date_range(start_date, end_date)
    process_data(start_date, end_date)
