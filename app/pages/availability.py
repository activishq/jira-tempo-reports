import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from scripts.db_operations import get_employees, get_availability, insert_availability, get_target, insert_target

def availability_management():
    st.title("Gestion du Budget de Production")

    # Sélection de l'employé
    employees = get_employees()
    selected_employee = st.selectbox("Sélectionnez un employé", employees)

    # Définition de la date de début (29 juillet 2024)
    start_date = datetime(2024, 7, 29).date()
    # Fin du trimestre (13 semaines après la date de début)
    end_date = start_date + timedelta(weeks=13)

    st.write(f"Période du budget : du {start_date} au {end_date}")

    if selected_employee:
        # Récupération du budget et de la cible existants
        existing_budget = get_availability(selected_employee, start_date, end_date)
        existing_target = get_target(selected_employee, start_date, end_date)

        # Création d'un DataFrame pour les entrées
        weeks = pd.date_range(start=start_date, end=end_date, freq='W-MON')
        budget_data = pd.DataFrame({'Week': weeks, 'Disponibilité': [0.0] * len(weeks), 'Target': [0.0] * len(weeks)})

        # Convertir la colonne 'Week' en date
        budget_data['Week'] = budget_data['Week'].dt.date

        # Fusionner avec le budget et la cible existants
        if not existing_budget.empty:
            existing_budget['week_start_date'] = pd.to_datetime(existing_budget['week_start_date']).dt.date
            budget_data = budget_data.merge(
                existing_budget,
                left_on='Week',
                right_on='week_start_date',
                how='left'
            )
            budget_data['Disponibilité'] = budget_data['budget_hours'].fillna(budget_data['Disponibilité'])

        if not existing_target.empty:
            existing_target['week_start_date'] = pd.to_datetime(existing_target['week_start_date']).dt.date
            budget_data = budget_data.merge(
                existing_target,
                left_on='Week',
                right_on='week_start_date',
                how='left',
                suffixes=('', '_target')
            )
            budget_data['Target'] = budget_data['target_hours'].fillna(budget_data['Target'])

        budget_data = budget_data[['Week', 'Disponibilité', 'Target']]

        # Interface pour entrer les heures budgétées et les cibles
        edited_df = st.data_editor(budget_data, num_rows="dynamic")

        if st.button("Enregistrer le budget et la cible"):
            save_budget_and_target(selected_employee, edited_df)
            st.success("Budget et cible enregistrés avec succès!")
    else:
        st.warning("Veuillez sélectionner un employé pour gérer son budget.")

def save_budget_and_target(employee_id, budget_df):
    print(f"Saving budget and target for employee {employee_id}")
    print(f"Budget and target data:\n{budget_df}")
    for _, row in budget_df.iterrows():
        week_start = row['Week']
        budget_hours = float(row['Disponibilité'])
        target_hours = float(row['Target'])
        print(f"Inserting: {employee_id}, {week_start}, Budget: {budget_hours}, Target: {target_hours}")
        insert_availability(employee_id, week_start, budget_hours)
        insert_target(employee_id, week_start, target_hours)
    print("Budget and target save completed")

if __name__ == "__main__":
    availability_management()
