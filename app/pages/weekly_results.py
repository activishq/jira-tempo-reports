import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from scripts.db_operations import get_db_connection, get_employees
from reports.combined_reports import JiraTempoReport

def get_previous_week_dates():
    today = datetime.now().date()
    start_of_week = today - timedelta(days=today.weekday() + 7)
    end_of_week = start_of_week + timedelta(days=6)
    return start_of_week, end_of_week

def format_hours(hours):
    return f"{hours:.1f}"

def weekly_results_page():
    st.title("Résultats de la Semaine Précédente")

    # Sélection de l'employé
    employees = get_employees()
    selected_employee = st.selectbox("Sélectionnez un employé", employees)

    # Sélection de la période
    default_start, default_end = get_previous_week_dates()
    start_date = st.date_input("Date de début", value=default_start)
    end_date = st.date_input("Date de fin", value=default_end)

    if start_date > end_date:
        st.error("La date de fin doit être postérieure à la date de début.")
        return

    # Initialisation du rapport
    jira_tempo_report = JiraTempoReport()

    # Calcul des indicateurs
    logged_time = jira_tempo_report.get_logged_time(start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"), selected_employee)
    billable_time = jira_tempo_report.get_billable_time(start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"), selected_employee)
    non_billable_time = logged_time - billable_time
    billable_ratio = jira_tempo_report.get_billable_ratio(start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"), selected_employee)

    # Affichage des indicateurs
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Heures enregistrées", format_hours(logged_time))
    col2.metric("Heures facturables", format_hours(billable_time))
    col3.metric("Heures non-facturables", format_hours(non_billable_time))
    col4.metric("Ratio de facturation", f"{billable_ratio:.1f}%")

    # Récupération et affichage des données Jira
    df_jira = jira_tempo_report.get_merged_report(start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"), selected_employee)

    # Sélection et renommage des colonnes pertinentes
    df_display = df_jira[['Issue Key', 'Estimated Time', 'Total Time Spent', "Period's Logged Time", 'Total Leaked Time', "Period's Leaked Time"]]

    # Tri du DataFrame
    df_display = df_display.sort_values(by="Period's Logged Time", ascending=False)

    numeric_columns = ['Estimated Time', 'Total Time Spent', "Period's Logged Time", 'Total Leaked Time', "Period's Leaked Time"]
    for col in numeric_columns:
        df_display[col] = df_display[col].round(1)

    base_url = "https://activis.atlassian.net/browse/"  # Remplacez ceci par l'URL de base de votre instance Jira
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
        hide_index=True, use_container_width=True
    )

if __name__ == "__main__":
    weekly_results_page()
