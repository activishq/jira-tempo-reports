import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from scripts.db_operations import get_db_connection, get_employees
from reports.combined_reports import JiraTempoReport
import logging
import sys

# Configuration du logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def get_previous_week_dates():
    today = datetime.now().date()
    start_of_week = today - timedelta(days=today.weekday() + 7)
    end_of_week = start_of_week + timedelta(days=6)
    return start_of_week, end_of_week

def format_hours(hours):
    return f"{hours:.1f}"

def weekly_results_page():
    st.title("Résultats de la Semaine Précédente")

    try:
        # Test direct de TempoReport
        # logger.debug("Test direct de TempoReport")
        from reports.tempo_reports import TempoReport
        tempo = TempoReport()
        default_start, default_end = get_previous_week_dates()
        test_worklogs = tempo.get_worklogs(
            default_start.strftime("%Y-%m-%d"),
            default_end.strftime("%Y-%m-%d")
        )
        # logger.debug(f"Test TempoReport - Nombre de worklogs: {len(test_worklogs)}")

        # DEBUG: Vérifier l'initialisation des employés
        # logger.debug("Récupération de la liste des employés...")
        employees = get_employees()
        # logger.debug(f"Employés trouvés: {employees}")

        selected_employee = st.selectbox("Sélectionnez un employé", employees)
        # logger.debug(f"Employé sélectionné: {selected_employee}")

        # Sélection de la période
        start_date = st.date_input("Date de début", value=default_start)
        end_date = st.date_input("Date de fin", value=default_end)
        # logger.debug(f"Dates sélectionnées - Début: {start_date}, Fin: {end_date}")

        if start_date > end_date:
            st.error("La date de fin doit être postérieure à la date de début.")
            return

        # DEBUG: Test des appels individuels
        # logger.debug("Test des appels individuels à Tempo")
        test_logs = tempo.get_logged_time(
            start_date.strftime("%Y-%m-%d"),
            end_date.strftime("%Y-%m-%d"),
            selected_employee
        )
        # logger.debug(f"Résultat get_logged_time: {test_logs}")

        # DEBUG: Initialisation du rapport combiné
        # logger.debug("Initialisation de JiraTempoReport...")
        jira_tempo_report = JiraTempoReport()
        # logger.debug("JiraTempoReport initialisé avec succès")

        # DEBUG: Calcul des indicateurs
        # logger.debug(f"Calcul des indicateurs pour {selected_employee}")

        try:
            logged_time = jira_tempo_report.get_logged_time(
                start_date.strftime("%Y-%m-%d"),
                end_date.strftime("%Y-%m-%d"),
                selected_employee
            )
            # logger.debug(f"Temps enregistré: {logged_time}")
        except Exception as e:
            logger.error(f"Erreur dans get_logged_time: {str(e)}")
            raise

        try:
            billable_time = jira_tempo_report.get_billable_time(
                start_date.strftime("%Y-%m-%d"),
                end_date.strftime("%Y-%m-%d"),
                selected_employee
            )
            # logger.debug(f"Temps facturable: {billable_time}")
        except Exception as e:
            logger.error(f"Erreur dans get_billable_time: {str(e)}")
            raise

        non_billable_time = logged_time - billable_time
        # logger.debug(f"Temps non facturable: {non_billable_time}")

        billable_ratio = jira_tempo_report.get_billable_ratio(
            start_date.strftime("%Y-%m-%d"),
            end_date.strftime("%Y-%m-%d"),
            selected_employee
        )
        # logger.debug(f"Ratio de facturation: {billable_ratio}")

        # Affichage des indicateurs
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Heures enregistrées", format_hours(logged_time))
        col2.metric("Heures facturables", format_hours(billable_time))
        col3.metric("Heures non-facturables", format_hours(non_billable_time))
        col4.metric("Ratio de facturation", f"{billable_ratio:.1f}%")

        # DEBUG: Récupération des données Jira
        # logger.debug("Récupération des données Jira...")
        df_jira = jira_tempo_report.get_merged_report(
            start_date.strftime("%Y-%m-%d"),
            end_date.strftime("%Y-%m-%d"),
            selected_employee
        )
        # logger.debug(f"Données récupérées: {len(df_jira)} lignes")
        # logger.debug("Aperçu des données:")
        # logger.debug(df_jira.head())

        if df_jira.empty:
            st.warning("Aucune donnée trouvée pour la période sélectionnée.")
            return

        # Sélection et renommage des colonnes pertinentes
        df_display = df_jira[['Issue Key', 'Estimated Time', 'Total Time Spent',
                             "Period's Logged Time", 'Total Leaked Time', "Period's Leaked Time"]]

        # Tri du DataFrame
        df_display = df_display.sort_values(by="Period's Logged Time", ascending=False)

        base_url = "https://activis.atlassian.net/browse/"
        df_display['URL'] = base_url + df_display['Issue Key']

        st.subheader("Détails des Issues Jira")
        st.dataframe(
            df_display,
            column_config={
                "Issue Key": "Issue",
                "Estimated Time": st.column_config.NumberColumn(
                    "Temps estimé",
                    help="Temps estimé pour l'issue",
                    format="%.1f h"
                ),
                "Total Time Spent": st.column_config.NumberColumn(
                    "Temps total passé",
                    help="Temps total passé sur l'issue",
                    format="%.1f h"
                ),
                "Period's Logged Time": st.column_config.NumberColumn(
                    "Temps enregistré (période)",
                    help="Temps enregistré pour la période sélectionnée",
                    format="%.1f h"
                ),
                "Total Leaked Time": st.column_config.NumberColumn(
                    "Temps de fuite total",
                    help="Temps de fuite total pour l'issue",
                    format="%.1f h"
                ),
                "Period's Leaked Time": st.column_config.NumberColumn(
                    "Temps de fuite (période)",
                    help="Temps de fuite pour la période sélectionnée",
                    format="%.1f h"
                ),
                "URL": st.column_config.LinkColumn("Lien Jira")
            },
            hide_index=True,
            use_container_width=True
        )

    except Exception as e:
        logger.error(f"Erreur détectée: {str(e)}")
        import traceback
        logger.error(f"Traceback complet:\n{traceback.format_exc()}")
        st.error(f"Une erreur s'est produite: {str(e)}")

if __name__ == "__main__":
    weekly_results_page()
