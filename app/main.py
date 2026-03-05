import streamlit as st

# Importez vos pages ici
from pages import billable_hours_dashboard, availability, tempo_account

def main():
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Aller à", [
        "Dashboard des heures facturables", 
        "Gestion du budget de production",
        "Compte Tempo"
    ])

    if page == "Dashboard des heures facturables":
        billable_hours_dashboard.main()
    elif page == "Gestion du budget de production":
        availability.availability_management()
    elif page == "Compte Tempo":
        tempo_account.tempo_account_page()

if __name__ == "__main__":
    main()
