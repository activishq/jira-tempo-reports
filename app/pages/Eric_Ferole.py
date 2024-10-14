import streamlit as st
from datetime import date, timedelta
from reports.reports import JiraReports, TempoReport, JiraTempoReport
from sqlalchemy import create_engine, text
import pandas as pd
import altair as alt

st.set_page_config(layout="wide")

# Initialisation des classes de rapports
report = JiraTempoReport()
jira_data = JiraReports()
tempo_data = TempoReport()
users = jira_data.get_current_users()

# Connexion à la base de données
engine = create_engine('postgresql://report_user:pixelpixel@localhost/company_reports')

# Fonction pour générer le rapport d'un employé
@st.cache_data
def generate_employee_report(user_name, start_date, end_date):
    merged_report = report.get_merged_report(start_date, end_date, user_name)
    logged_hours = report.get_logged_time(start_date, end_date, user_name)
    leaked_hours = report.get_leaked_time(start_date, end_date, user_name)
    billable_hours = report.get_billable_time(start_date, end_date, user_name)
    billable_ratio = report.get_billable_ratio(start_date, end_date, user_name)

    return merged_report, logged_hours, leaked_hours, billable_hours, billable_ratio

# Fonction pour récupérer les données hebdomadaires
def get_weekly_data(user_name, start_date, end_date):
    query = text("""
        SELECT week_start, billable_hours, worked_hours
        FROM weekly_reports
        WHERE employee_name = :user_name
        AND week_start >= :start_date
        AND week_end <= :end_date
        ORDER BY week_start
    """)
    with engine.connect() as connection:
        df = pd.read_sql(query, connection, params={"user_name": user_name, "start_date": start_date, "end_date": end_date})

    # Convertir la colonne 'week_start' en type datetime
    df['week_start'] = pd.to_datetime(df['week_start'])

    # Calcul du ratio d'heures facturées (en pourcentage)
    df['billable_ratio'] = (df['billable_hours'] / df['worked_hours']) * 100

    # Calcul du numéro de la semaine
    df['week_number'] = df['week_start'].dt.strftime('Semaine %U').astype(str)

    return df

# Sélection de l'utilisateur via la barre latérale
with st.sidebar:
    st.title("Paramètres du rapport")
    user_name = st.selectbox("Sélectionnez l'utilisateur", users)

    # Période par défaut pour les dates
    default_start_date = date.today() - timedelta(days=30)
    default_end_date = date.today()
    selected_range = st.date_input(
        "Sélectionnez la plage de dates",
        value=(default_start_date, default_end_date)
    )

start_date, end_date = selected_range

# Génération du rapport avec un spinner pour indiquer le chargement
with st.spinner("Chargement des données..."):
    merged_report, logged_hours, leaked_hours, billable_hours, billable_ratio = generate_employee_report(user_name, start_date, end_date)
    weekly_data = get_weekly_data(user_name, start_date, end_date)

# Titre de la page
st.title(f'Rapport d\'activités pour {user_name}')

# Affichage du graphique de série temporelle
if weekly_data.empty:
    st.warning(f"Aucune donnée disponible pour {user_name} entre {start_date} et {end_date}.")
else:
    # Créer le graphique des ratios par semaine
    base = alt.Chart(weekly_data).encode(
        x=alt.X('week_number:O', title='Semaine'),
        y=alt.Y('billable_ratio:Q', title='Ratio facturable (%)', scale=alt.Scale(domain=[0, 100])),
        tooltip=['week_start:T', 'billable_ratio:Q']
    )

    # Ajouter les barres pour le ratio facturable
    bars = base.mark_bar()

    # Ajouter une ligne verte à 80%
    line_80 = alt.Chart(pd.DataFrame({'y': [80]})).mark_rule(color='lime').encode(y='y:Q')

    # Superposer les barres et la ligne
    chart = bars + line_80

    chart = chart.properties(
        title="Ratio d'heures facturées par semaine",
        width=800,
        height=400
    )

    st.altair_chart(chart)

st.markdown('#')

# Affichage des métriques
col1, col2, col3, col4 = st.columns(4)
col1.metric(label="Temps total enregistré", value=f"{logged_hours:.2f} h")
col2.metric(label="Temps non facturable", value=f"{leaked_hours:.2f} h")
col3.metric(label="Temps facturables", value=f"{billable_hours:.2f} h")
col4.metric(label="Ratio facturable", value=f"{billable_ratio:.0f}%")

st.markdown('#')

# Vérification si des données sont disponibles pour le tableau des tâches
if not merged_report.empty:
    # Affichage du graphique des tâches
    chart_data = merged_report.set_index('Issue Key')[['Total Time Spent', 'Estimated Time']]
    st.bar_chart(chart_data)

    # Affichage d'un graphique supplémentaire (optionnel)
    st.line_chart(merged_report.set_index('Issue Key')[['Period\'s Logged Time', 'Total Leaked Time']])

    # Affichage du tableau des données
    st.table(merged_report)
