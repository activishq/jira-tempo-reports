import streamlit as st

# Importez vos pages ici
from pages import billable_hours_dashboard, availability

def main():
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Aller à", ["Dashboard des heures facturables", "Gestion du budget de production"])

    if page == "Dashboard des heures facturables":
        billable_hours_dashboard.main()
    elif page == "Gestion du budget de production":
        availability.availability_management()

if __name__ == "__main__":
    main()
