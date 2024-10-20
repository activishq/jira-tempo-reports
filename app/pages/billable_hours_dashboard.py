import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from scripts.db_operations import get_db_connection, get_availability, get_employees, get_target

st.set_page_config(layout="wide")

def load_data(start_date, end_date, selected_employee):
    with get_db_connection() as conn:
        query = """
        SELECT e.employee_id, e.full_name, ewh.week_start_date,
               ewh.total_hours, ewh.billable_hours, ewh.non_billable_hours
        FROM employee_weekly_hours ewh
        JOIN employees e ON ewh.employee_id = e.employee_id
        WHERE ewh.week_start_date BETWEEN %s AND %s
        AND e.employee_id = %s
        ORDER BY ewh.week_start_date
        """
        df = pd.read_sql(query, conn, params=(start_date, end_date, selected_employee))

    # Charger les données de budget de production
    budget_data = get_availability(selected_employee, start_date, end_date)
    target_data = get_target(selected_employee, start_date, end_date)  # target_date devrait être inclus ici

    # Fusionner les données de budget avec les données existantes
    df = pd.merge(df, budget_data, on='week_start_date', how='left')
    df['budget_hours'] = df['budget_hours'].fillna(0)

    # Fusionner les données de target_data
    df = pd.merge(df, target_data, on='week_start_date', how='left')
    df['target_hours'] = df['target_hours'].fillna(pd.NaT)  # Remplir les valeurs manquantes si nécessaire

    return df


def main():
    st.title("Dashboard des Heures Facturables")

    # Sélection de l'employé
    employees = get_employees()
    selected_employee = st.selectbox("Sélectionnez un employé", employees)

    # Définition de la date de début par défaut (29 juillet 2024)
    default_start_date = datetime(2024, 7, 29)
    default_end_date = datetime.now()

    # Sélection de la période
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Date de début", value=default_start_date)
    with col2:
        end_date = st.date_input("Date de fin", value=default_end_date)

    if start_date > end_date:
        st.error("La date de fin doit être postérieure à la date de début.")
        return

    # Chargement des données
    df = load_data(start_date, end_date, selected_employee)

    if df.empty:
        st.warning("Aucune donnée disponible pour la période sélectionnée.")
        return

    # Calcul des métriques
    total_hours = df['total_hours'].sum()
    billable_hours = df['billable_hours'].sum()
    non_billable_hours = df['non_billable_hours'].sum()
    target = df['target_hours'].sum()
    availability = df['budget_hours'].sum()
    billable_ratio = (billable_hours / availability * 100) if availability > 0 else 0
    budget_utilization = (billable_hours / availability * 100) if availability > 0 else 0

    # Affichage des métriques
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    col1.metric("Temps total", f"{total_hours:.2f}h")
    col2.metric("Temps facturable", f"{billable_hours:.2f}h")
    col3.metric("Temps non facturable", f"{non_billable_hours:.2f}h")
    col5.metric("Disponibilité", f"{availability:.2f}h")
    col6.metric("Cible", f"{target:.2f}h")
    col4.metric("Ratio facturable", f"{billable_ratio:.1f}%")

    # Convertir target_hours en type numérique
    df['target_hours'] = pd.to_numeric(df['target_hours'], errors='coerce')
    df['target_hours'] = df['target_hours'].fillna(0)

    # # Graphique comparant les heures travaillées au budget
    # fig = px.bar(df, x='week_start_date', y=['billable_hours', 'target_hours'],
    #              title=f"Heures travaillées vs Budget pour {selected_employee}")
    # fig.update_layout(barmode='group')
    # st.plotly_chart(fig)

    # Créer une figure vide
    fig = go.Figure()

    # Ajouter la trace pour les barres (billable_hours)
    fig.add_trace(go.Bar(
        x=df['week_start_date'],
        y=df['billable_hours'],
        name='Heures facturables',
        marker_color='blue'  # Tu peux changer la couleur si nécessaire
    ))

    # Ajouter la trace pour la courbe (target_hours)
    fig.add_trace(go.Scatter(
        x=df['week_start_date'],
        y=df['target_hours'],
        name='Cible d\'heures',
        mode='lines+markers',  # Cela trace une courbe avec des points
        line=dict(color='red', width=2)  # Couleur et épaisseur de la ligne
    ))

    # Mettre à jour la mise en page du graphique
    fig.update_layout(
        title=f"Heures travaillées vs Cible pour {selected_employee}",
        xaxis_title='Semaine de début',
        yaxis_title='Heures',
        barmode='group'  # Les barres seront groupées par date
    )

    # Afficher le graphique dans Streamlit
    st.plotly_chart(fig)


    # Tableau détaillé
    st.subheader("Données détaillées")
    st.dataframe(df[['week_start_date', 'total_hours', 'billable_hours', 'non_billable_hours', 'budget_hours', 'target_hours']])

    # Analyse supplémentaire
    st.subheader("Analyse supplémentaire")
    avg_weekly_hours = df['total_hours'].mean()
    max_weekly_hours = df['total_hours'].max()
    min_weekly_hours = df['total_hours'].min()

    st.write(f"Moyenne hebdomadaire : {avg_weekly_hours:.2f}h")
    st.write(f"Maximum hebdomadaire : {max_weekly_hours:.2f}h")
    st.write(f"Minimum hebdomadaire : {min_weekly_hours:.2f}h")
    st.write(f"Utilisation du budget : {budget_utilization:.1f}%")

if __name__ == "__main__":
    main()
