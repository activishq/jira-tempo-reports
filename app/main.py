import streamlit as st
from datetime import date, timedelta
from reports.jira_reports import JiraReports
from reports.tempo_reports import TempoReport
from reports.combined_reports import JiraTempoReport
import pandas as pd
import altair as alt

st.set_page_config(layout="wide", page_title="Rapport d'activités", page_icon="📊")

@st.cache_resource
def get_reports():
    jira_report = JiraReports()
    tempo_report = TempoReport()
    combined_report = JiraTempoReport()
    return jira_report, tempo_report, combined_report

jira_report, tempo_report, combined_report = get_reports()

st.title("📊 Rapport d'activités")

with st.sidebar:
    st.title("Paramètres du rapport")

    default_start_date = date.today() - timedelta(days=7)
    default_end_date = date.today() - timedelta(days=1)
    selected_range = st.date_input(
        "Sélectionnez la plage de dates",
        value=(default_start_date, default_end_date)
    )

    users = jira_report.get_current_users()
    selected_user = st.selectbox("Sélectionnez un utilisateur", ["Tous"] + users)

start_date, end_date = selected_range

# @st.cache_data
# def get_department_data(start_date, end_date):
#     department_leaked_time = combined_report.get_department_leaked_time(start_date, end_date)
#     department_logged_time = tempo_report.get_department_logged_time(start_date, end_date, jira_report.get_current_users())
#     department_availability = jira_report.get_department_availability()
#     department_billable_hours = department_logged_time - department_leaked_time
#     department_billable_ratio = (department_billable_hours / department_logged_time * 100) if department_logged_time > 0 else 0
#     return department_leaked_time, department_logged_time, department_availability, department_billable_hours, department_billable_ratio

# department_data = get_department_data(start_date, end_date)

# st.subheader(f"Période du {start_date} au {end_date}")

# # KPIs cards
# col1, col2, col3, col4 = st.columns(4)
# col1.metric(label="Temps total enregistré", value=f"{department_data[1]:.2f} h")
# col2.metric(label="Temps non facturable", value=f"{department_data[0]:.2f} h")
# col3.metric(label="Temps facturables", value=f"{department_data[3]:.2f} h")
# col4.metric(label="Ratio facturable", value=f"{department_data[4]:.0f}%")

# # Graphique de répartition du temps
# st.subheader("Répartition du temps")
# time_distribution = pd.DataFrame({
#     'Catégorie': ['Temps facturable', 'Temps non facturable'],
#     'Heures': [department_data[3], department_data[0]]
# })

# chart = alt.Chart(time_distribution).mark_arc().encode(
#     theta='Heures',
#     color='Catégorie',
#     tooltip=['Catégorie', 'Heures']
# ).properties(width=400, height=400)

# st.altair_chart(chart, use_container_width=True)

if selected_user != "Tous":
    st.subheader(f"{selected_user} – Période du {start_date} au {end_date}")

    # Calcul des métriques pour l'utilisateur sélectionné
    logged_hours = combined_report.get_logged_time(str(start_date), str(end_date), selected_user)
    leaked_hours = combined_report.get_leaked_time(str(start_date), str(end_date), selected_user)
    billable_hours = combined_report.get_billable_time(str(start_date), str(end_date), selected_user)
    billable_ratio = combined_report.get_billable_ratio(str(start_date), str(end_date), selected_user)

    # Affichage des métriques de l'utilisateur
    col1, col2, col3, col4 = st.columns(4)
    col1.metric(label="Temps total enregistré", value=f"{logged_hours:.2f} h")
    col2.metric(label="Temps non facturable", value=f"{leaked_hours:.2f} h")
    col3.metric(label="Temps facturables", value=f"{billable_hours:.2f} h")
    col4.metric(label="Ratio facturable", value=f"{billable_ratio:.0f}%")

    # Affichage du tableau des données de l'utilisateur
    user_data = combined_report.get_merged_report(str(start_date), str(end_date), selected_user)

    # Définir les colonnes à afficher, en excluant 'user'
    columns_to_display = ['Issue Key', 'Estimated Time', 'Total Time Spent', 'Period\'s Logged Time', 'Period\'s Leaked Time', 'Total Leaked Time']

    # Sélectionner uniquement les colonnes que nous voulons afficher
    user_data_cleaned = user_data[columns_to_display]

    # Afficher le DataFrame nettoyé
    st.table(user_data_cleaned)

else:
    st.subheader("Vue d'ensemble du département")
    # Ici, vous pouvez ajouter des graphiques ou des tableaux pour la vue d'ensemble du département
