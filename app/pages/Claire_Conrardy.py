import streamlit as st
from datetime import date, timedelta
from reports.reports import JiraReports, TempoReport, JiraTempoReport

report = JiraTempoReport()
jira_data = JiraReports()
tempo_data = TempoReport()
users = jira_data.get_current_users()

st.set_page_config(layout="wide")

user_name = 'Claire Conrardy'

st.title(f'Rapport d\'activités pour {user_name}')

st.markdown('#')

with st.sidebar:

    st.title("Paramètres du rapport")

    default_start_date = date.today() - timedelta(days=7)
    default_end_date = date.today() - timedelta(days=1)
    selected_range = st.date_input(
        "Sélectionnez la plage de dates",
        value=(default_start_date, default_end_date)
    )

start_date, end_date = selected_range

merged_report = report.get_merged_report(start_date, end_date, user_name)
logged_hours = report.get_logged_time(start_date, end_date, user_name)
leaked_hours = report.get_leaked_time(start_date, end_date, user_name)
billable_hours = report.get_billable_time(start_date, end_date, user_name)
billable_ratio = report.get_billable_ratio(start_date, end_date, user_name)

st.subheader(f"Période du {start_date} au {end_date}")

st.markdown('#')

# KPIs cards
col1, col2, col3, col4 = st.columns(4)
col1.metric(label="Temps total enregistré", value=f"{logged_hours:.2f} h")
col2.metric(label="Temps non facturable", value=f"{leaked_hours:.2f} h")
col3.metric(label="Temps facturables", value=f"{billable_hours:.2f} h")
col4.metric(label="Ratio facturable", value=f"{billable_ratio:.0f}%")

st.markdown('#')

chart_data = merged_report.set_index('Issue Key')[['Total Time Spent', 'Estimated Time']]

st.bar_chart(chart_data)

st.table(merged_report)
