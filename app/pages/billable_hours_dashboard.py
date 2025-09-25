import streamlit as st
import pandas as pd
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

    budget_data = get_availability(selected_employee, start_date, end_date)
    target_data = get_target(selected_employee, start_date, end_date)

    df = pd.merge(df, budget_data, on='week_start_date', how='left')
    df['budget_hours'] = df['budget_hours'].fillna(0)

    df = pd.merge(df, target_data, on='week_start_date', how='left')
    df['target_hours'] = df['target_hours'].fillna(pd.NaT)

    return df


def main():
    st.title("Dashboard des Heures Facturables")

    employees = get_employees()
    selected_employee = st.selectbox("Sélectionnez un employé", employees)

    default_start_date = datetime(2024, 7, 29)
    default_end_date = datetime.now()

    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Date de début", value=default_start_date)
    with col2:
        end_date = st.date_input("Date de fin", value=default_end_date)

    if start_date > end_date:
        st.error("La date de fin doit être postérieure à la date de début.")
        return

    df = load_data(start_date, end_date, selected_employee)

    if df.empty:
        st.warning("Aucune donnée disponible pour la période sélectionnée.")
        return

    total_hours = df['total_hours'].sum()
    billable_hours = df['billable_hours'].sum()
    non_billable_hours = df['non_billable_hours'].sum()
    target = df['target_hours'].sum()
    availability = df['budget_hours'].sum()
    billable_ratio = (billable_hours / availability * 100) if availability > 0 else 0
    budget_utilization = (billable_hours / availability * 100) if availability > 0 else 0

    col1, col2, col3, col4, col5, col6 = st.columns(6)
    col1.metric("Temps total", f"{total_hours:.2f}h")
    col2.metric("Temps facturable", f"{billable_hours:.2f}h")
    col3.metric("Temps non facturable", f"{non_billable_hours:.2f}h")
    col5.metric("Disponibilité", f"{availability:.2f}h")
    col6.metric("Cible", f"{target:.2f}h")
    col4.metric("Ratio facturable", f"{billable_ratio:.1f}%")

    df['target_hours'] = pd.to_numeric(df['target_hours'], errors='coerce')
    df['target_hours'] = df['target_hours'].fillna(0)

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=df['week_start_date'],
        y=df['billable_hours'],
        name='Heures facturables',
        marker_color='#064742'
    ))

    fig.add_trace(go.Scatter(
        x=df['week_start_date'],
        y=df['target_hours'],
        name='Cible d\'heures',
        mode='lines+markers',
        line=dict(color='#39F780', width=3),
        marker=dict(color='#39F780', size=10)
    ))

    fig.update_layout(
        title=f"Heures travaillées vs Cible pour {selected_employee}",
        xaxis_title='Semaine de début',
        yaxis_title='Heures',
        barmode='group'
    )

    st.plotly_chart(fig)

    st.subheader("Données détaillées")
    st.dataframe(df[['week_start_date', 'total_hours', 'billable_hours', 'non_billable_hours', 'budget_hours', 'target_hours']], use_container_width=True)

if __name__ == "__main__":
    main()
