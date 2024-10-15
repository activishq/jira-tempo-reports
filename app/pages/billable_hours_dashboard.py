import streamlit as st
import pandas as pd
import plotly.express as px
from scripts.db_operations import get_db_connection

def load_data():
    with get_db_connection() as conn:
        query = """
        SELECT e.full_name, ewh.week_start_date, ewh.billable_hours, ewh.non_billable_hours, ewh.total_hours
        FROM employee_weekly_hours ewh
        JOIN employees e ON ewh.employee_id = e.employee_id
        ORDER BY e.full_name, ewh.week_start_date
        """
        df = pd.read_sql(query, conn)
    return df

def main():
    st.title("Tableau de bord des heures facturables")

    df = load_data()

    # Sélecteur d'employé
    employees = df['full_name'].unique()
    selected_employee = st.selectbox("Sélectionnez un employé", employees)

    # Filtrer les données pour l'employé sélectionné
    employee_data = df[df['full_name'] == selected_employee]

    # Calcul des métriques
    total_hours = employee_data['total_hours'].sum()
    billable_hours = employee_data['billable_hours'].sum()
    non_billable_hours = employee_data['non_billable_hours'].sum()
    billable_ratio = (billable_hours / total_hours * 100) if total_hours > 0 else 0
    mean_billable_hours = billable_hours / len(employee_data['week_start_date'].unique())

    # Affichage des métriques de l'utilisateur
    col1, col2, col3, col4 = st.columns(4)
    col1.metric(label="Temps total enregistré", value=f"{total_hours:.2f} h")
    col2.metric(label="Temps facturable moyen", value=f"{mean_billable_hours:.2f} h")
    col3.metric(label="Temps facturable", value=f"{billable_hours:.2f} h")
    col4.metric(label="Ratio facturable", value=f"{billable_ratio:.0f}%")

    # Graphique des heures facturables au fil du temps
    fig = px.line(employee_data, x='week_start_date', y=['billable_hours', 'non_billable_hours'],
                  title=f"Heures facturables et non facturables pour {selected_employee}")
    st.plotly_chart(fig)

    # Tableau des données
    st.write("Données détaillées:")
    st.dataframe(employee_data)

if __name__ == "__main__":
    main()
